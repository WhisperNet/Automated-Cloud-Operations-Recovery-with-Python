from utils.notify import notify
import paramiko


def restart_container(host,to):
    print('Restarting the containers...')
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=host, username='ec2-user', key_filename='/home/whisper_net/.ssh/id_rsa')
    stdin, stdout, stderr = ssh.exec_command('docker restart $(docker ps -a -q)')
    print(f"Host: {host},The following containers have been restarted")
    print(stdout.readlines())
    notify(to,'Container Restarted',f'Host: {host},containers have been restarted with IDS: {stdout.readlines()}')
    ssh.close()