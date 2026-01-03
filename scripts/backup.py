import boto3
import schedule
from utils.notify import notify
from utils.check_status import app_status
ec2_client = boto3.client('ec2')

def create_vol_snaps(instance_id,url,to):
    if app_status(url,to).state != 'healthy':
            print(f"Instance {instance_id} is not healthy. Skipping backup.")
            notify(to,'Backup Skipped',f'Backup for Instance: {instance_id} skipped due to unhealthy application state.')
            return

    volumes = ec2_client.describe_volumes(
    Filters=[
        {
            'Name' : 'attachment.instance-id',
            'Values' : [instance_id]
        }
    ]
    )
    for volume in volumes['Volumes']:
        new_snapshot = ec2_client.create_snapshot(
            VolumeId = volume['VolumeId'],
            TagSpecifications = [
                {
                    'ResourceType': 'snapshot',
                   'Tags': [
                        {
                        'Key': 'InstanceID',
                        'Value': instance_id
                        }
                    ]
                }
            ]
        )
        print(f"New snapshot {new_snapshot['SnapshotId']} created for Instance: {instance_id}")
