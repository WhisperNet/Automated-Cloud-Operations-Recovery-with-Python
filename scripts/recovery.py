import boto3
import time
from utils.notify import notify
from restart import restart_container
from operator import itemgetter
ec2_client = boto3.client('ec2')

def recover(instance_id,host,to):

    print(f'Initiating recovery for {instance_id}')
    snapshots = ec2_client.describe_snapshots(
    OwnerIds=[
            'self',
        ],
    Filters=[
        {
            'Name': 'tag:InstanceID',
            'Values': [
                instance_id
            ]
        },
    ])
    latest_snapshot = sorted(snapshots['Snapshots'],key=itemgetter('StartTime'),reverse=True)[0]
    print(latest_snapshot['SnapshotId'])

    response = ec2_client.create_replace_root_volume_task(
        InstanceId = instance_id,
        SnapshotId = latest_snapshot['SnapshotId'],
        DeleteReplacedRootVolume=True
    )
    print(f'Recovery for Instance: {instance_id} initiated using Snapshot: {latest_snapshot["SnapshotId"]}')
    notify(to,'Recovery Initiated',f'Recovery for Instance: {instance_id} initiated using Snapshot: {latest_snapshot["SnapshotId"]}')
    task_id = response['ReplaceRootVolumeTask']['ReplaceRootVolumeTaskId']

    while True:
        task_info = ec2_client.describe_replace_root_volume_tasks(ReplaceRootVolumeTaskIds=[task_id])
        status = task_info['ReplaceRootVolumeTasks'][0]['TaskState']
        print(f"Task Status: {status}...")
        if status == 'succeeded':
            break
        elif status in ['failed', 'failing', 'cancelled']:
            raise Exception(f"Task failed with status: {status}")
        time.sleep(10)
    
    instance_waiter = ec2_client.get_waiter('instance_running')
    instance_waiter.wait(InstanceIds=[instance_id])

    status_waiter = ec2_client.get_waiter('instance_status_ok')
    status_waiter.wait(InstanceIds=[instance_id])

    print("Instance is now running.\n Waiting for 60 seconds to restart containers...")
    time.sleep(60)
    restart_container(host,to)


