import time
import boto3
from restart import restart_container
from reboot import reboot
from utils.check_status import app_status
from utils.notify import notify
from recovery import recover
ec2_client = boto3.client('ec2')

def monitor(instance,manual_intervention_flagged,to):
    current_state = app_status(f"http://{instance['PublicIpAddress']}:8080",to).state

    print(f'{instance["PublicIpAddress"]} current state: {current_state}')

    if current_state == 'unhealthy':
        restart_container(instance['PublicIpAddress'],to)
        after_restart_state = app_status(f"http://{instance['PublicIpAddress']}:8080",to).state
        time.sleep(60)
        if after_restart_state == 'unresponsive' or after_restart_state == 'unhealthy':
            current_state = 'unresponsive'  # escalate to reboot

    if current_state == 'unresponsive':
        reboot(instance['InstanceId'],instance['PublicIpAddress'],to)
        after_reboot_state = app_status(f"http://{instance['PublicIpAddress']}:8080",to).state
        time.sleep(60)
        if after_reboot_state == 'unresponsive' or after_reboot_state == 'unhealthy':
            current_state = 'tainted' 

    if current_state == 'tainted':
        recover(instance['InstanceId'],instance['PublicIpAddress'],to)
        after_recovery_state = app_status(f"http://{instance['PublicIpAddress']}:8080",to).state
        time.sleep(60)
        if after_recovery_state == 'unresponsive' or after_reboot_state == 'unhealthy':
            manual_intervention_flagged.append(instance['InstanceId'])
            print(f'All automation recovery for Instance: {instance["InstanceId"]} has failed')
            print(f'Any automated task on this Instance:{instance["InstanceId"]} will be skipped until manual intervention')
            notify(to,'Manual Intervention Required',f'All automation recovery for Instance: {instance["InstanceId"]} has failed. Manual intervention is required.')