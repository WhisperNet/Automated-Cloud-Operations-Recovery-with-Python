import boto3
import requests
from .state import Current_State
from .notify import notify

ec2_client = boto3.client('ec2')

def app_status(url,to):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return Current_State('healthy','Healthy:No action required')
        else:
            sub = f'Application Unhealthy: {url}'
            msg = f'Application returned {response.status_code} instead of 200'
            notify(to,sub,msg)
            return Current_State('unhealthy','Unhealthy:Container Restart required')
    except Exception as ex:
        print(type(ex))
        if isinstance(ex, requests.exceptions.RequestException):
            sub = f'Application Down: {url}'
            msg = f'Application is down due to {str(ex)}'
            notify(to,sub,msg)
            return Current_State('unresponsive','Unresponsive:Server reboot required')
        else:
            raise ex

def server_status(instance_id):
    res = ec2_client.describe_instance_status(
        InstanceIds = [instance_id]
    )
    return res.get('InstanceStatuses')[0].get('InstanceState')
