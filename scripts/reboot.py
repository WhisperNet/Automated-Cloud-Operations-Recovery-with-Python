import boto3
import time
from utils.notify import notify
from utils.check_status import server_status
from restart import restart_container
from utils.state import Current_State
ec2_client = boto3.client('ec2')

def reboot(instance_id,url,to): 
    response = ec2_client.reboot_instances(
        InstanceIds=[instance_id]
    )
    print(server_status(instance_id))
    print(f"Instance :{instance_id} has been rebooted")
    notify(to,'Instance Reboot',f'Instance: {instance_id} has been rebooted')
    while server_status(instance_id)['Name'] != 'running':
        print('Waiting for the instance to be running...')
        time.sleep(10)
    print(f"Instance :{instance_id} is now running:Waiting for 60 seconds to restart containers")
    time.sleep(60)
    restart_container(url,to)
    return Current_State('rebooted','Instance has been rebooted and containers restarted')
    
