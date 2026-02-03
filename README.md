# WhisperNet DevOps Python Automation

A small ops-automation service for AWS EC2 instances running a web workload (default: Dockerized NGINX on port 8080). It continuously checks application health and applies a staged recovery playbook (restart containers -> reboot instance -> restore root volume from latest snapshot). It also performs scheduled EBS snapshots and snapshot retention cleanup.

This repository contains two parts:

- Python automation (under `scripts/`)
- Terraform to provision a demo workload and EC2 hosts (under `terraform/`)

## What It Does

**Monitoring & self-healing (every 5 minutes)**

- Discovers EC2 instances tagged `env=prod`
- Checks `http://<public-ip>:8080` (expects HTTP 200)
- If unhealthy: SSH in and restart all Docker containers
- If still unhealthy/unresponsive: reboot the instance, then restart containers
- If still failing: replace the instance root volume using the most recent EBS snapshot tagged for that instance, then restart containers
- If all automated recovery fails: flags the instance to **skip further automation** until manual intervention, and emails an alert

**Backups (daily 02:00)**

- For each `env=prod` instance, snapshots all attached EBS volumes
- Adds snapshot tag `InstanceID=<instance-id>`
- Skips backups if the app health check is not healthy

**Snapshot retention (weekly)**

- Keeps the newest snapshot per instance (by `StartTime`) and deletes older ones (filtered by `tag:InstanceID=<instance-id>`)

## High-level Flow

```
             +-------------------------+
             |  Scheduler (scripts/)   |
             |  main.py                |
             +-----------+-------------+
                         |
                         v
            Discover EC2 instances where tag env=prod
                         |
                         v
             Health check http://IP:8080 (200?)
                         |
          +--------------+--------------+
          |                             |
        healthy                       unhealthy
          |                             |
          v                             v
      do nothing                 SSH: docker restart ...
                                         |
                                         v
                                 still failing?
                                         |
                                         v
                                  EC2 reboot instance
                                         |
                                         v
                                 still failing?
                                         |
                                         v
                         EC2 replace root volume from latest snapshot
                                         |
                                         v
                          still failing? -> flag for manual intervention
```

## Repository Layout

- `scripts/main.py`: Scheduler/entrypoint (monitor/backup/cleanup)
- `scripts/monitor.py`: Recovery escalation logic
- `scripts/backup.py`: EBS snapshot creation (tagged per instance)
- `scripts/cleaner.py`: Snapshot cleanup (keeps newest)
- `scripts/reboot.py`: EC2 reboot + container restart
- `scripts/recovery.py`: Root-volume replacement from latest snapshot + restart
- `scripts/restart.py`: SSH + `docker restart $(docker ps -a -q)`
- `scripts/utils/check_status.py`: HTTP health check + basic instance status helper
- `scripts/utils/notify.py`: SMTP email notifications (Gmail)
- `terraform/`: VPC, subnet, security group rules, and 2 EC2 instances running Dockerized NGINX on port 8080

## Prerequisites

### Python side

- Python 3.9+
- AWS credentials available to `boto3` (env vars, shared config, or instance profile)
- Network access to EC2 public IPs on:
  - `8080/tcp` for HTTP health checks
  - `22/tcp` for SSH from the machine running the scripts

Python libraries used in the code:

- `boto3`
- `schedule`
- `requests`
- `paramiko`

### AWS IAM permissions (minimum set)

The automation calls EC2 APIs including:

- `ec2:DescribeInstances`, `ec2:DescribeVolumes`, `ec2:DescribeSnapshots`
- `ec2:CreateSnapshot`, `ec2:DeleteSnapshot`
- `ec2:RebootInstances`, `ec2:DescribeInstanceStatus`
- `ec2:CreateReplaceRootVolumeTask`, `ec2:DescribeReplaceRootVolumeTasks`

## Configuration

### Email notifications

The notifier reads these environment variables (see `scripts/.env.exmaple`):

- `EMAIL_ADDR`
- `EMAIL_ACCESS_TOKEN`

Notes:

- `scripts/utils/notify.py` uses Gmail SMTP (`smtp.gmail.com:587`). For most Gmail accounts you will need an App Password.
- The recipient email address is currently hardcoded in `scripts/main.py` (`to = 'ridowanqwe@gmail.com'`).

### SSH access for container restart

`scripts/restart.py` connects via SSH with:

- username: `ec2-user`
- key path (currently hardcoded): `/home/whisper_net/.ssh/id_rsa`

Make sure:

- the key path exists on the machine running the automation
- the corresponding public key is installed on the EC2 instances
- port 22 is reachable (Terraform limits SSH to `var.my_ip_cidr`)

## Running the Automation

From the repo root:

1. Create and activate a virtualenv

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies

```bash
pip install boto3 schedule requests paramiko
```

3. Export email settings (optional but recommended)

```bash
export EMAIL_ADDR='your_email@example.com'
export EMAIL_ACCESS_TOKEN='your_access_token'
```

4. Run the scheduler

```bash
python scripts/main.py
```

The scheduler runs:

- monitor every 5 minutes
- backup daily at 02:00
- snapshot cleanup weekly

## Terraform (demo workload)

Terraform provisions:

- a VPC, subnet, internet gateway, and security group
- two EC2 instances tagged `env=prod`
- user-data that installs Docker and runs `nginx` mapped to host port `8080`

Typical flow:

```bash
cd terraform
terraform init
terraform apply
```

After apply, Terraform outputs the public IPs. The Python automation discovers these instances via the `env=prod` tag.

## Operational Notes / Gotchas

- **Health check is naive**: it only checks HTTP status code 200 at `http://<ip>:8080/`.
- **Container restart restarts everything**: `docker restart $(docker ps -a -q)` restarts all containers (including stopped ones).
- **Snapshot cleanup keeps only 1** snapshot per instance (newest). If you need a longer retention window, adjust `scripts/cleaner.py`.
- **Manual intervention flag**: once an instance is flagged as unrecoverable, the scheduler will skip all actions for it until the process restarts.
- **Root-volume replace**: recovery uses the newest snapshot tagged `InstanceID=<instance-id>`. Ensure your snapshots include a valid root-volume snapshot.
