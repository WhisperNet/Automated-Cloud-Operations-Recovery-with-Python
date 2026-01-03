import boto3
from operator import itemgetter
ec2_client = boto3.client('ec2')



def clean_snapshosts(instance_id):
    print(f'Cleaning snapshots for Instance: {instance_id}')
    snapshots = ec2_client.describe_snapshots(
    OwnerIds = ['self'],
    Filters=[
        {
            'Name': 'tag:InstanceID',
            'Values': [instance_id]
        }
    ])
    sorted_by_date = sorted(snapshots['Snapshots'], key=itemgetter('StartTime'), reverse=True)
    for snap in sorted_by_date[1:]:
        response = ec2_client.delete_snapshot(
            SnapshotId = snap['SnapshotId']
        )
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print(f"Deleted snapshot {snap['SnapshotId']} for Instance: {instance_id}")
        else:
            print(f"Failed to delete snapshot {snap['SnapshotId']} for Instance: {instance_id}")
