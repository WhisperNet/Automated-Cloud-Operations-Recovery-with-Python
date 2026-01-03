import time
import boto3
import schedule
from backup import create_vol_snaps
from cleaner import clean_snapshosts
from monitor import monitor

ec2_client = boto3.client('ec2')
to = 'ridowanqwe@gmail.com'
manual_intervention_flagged = [] 

def caller(action,func ):
    response = ec2_client.describe_instances(
        Filters=[
            {
                'Name': 'tag:env',
                'Values': ['prod']
            }
        ]
    )
    for reservation in response.get('Reservations'):
        for instance in reservation.get('Instances'):
            if instance['InstanceId'] not in manual_intervention_flagged:
                if action == 'monitor':
                    func(instance,manual_intervention_flagged,to)
                elif action == 'backup':
                    func(instance['InstanceId'],f"http://{instance['PublicIpAddress']}:8080",to)
                elif action == 'clean':
                    func(instance['InstanceId'])


def main():
    schedule.every(5).minutes.do(caller,'monitor',monitor)
    schedule.every().day.at("02:00").do(caller,'backup',create_vol_snaps)
    schedule.every().week.do(caller,'clean',clean_snapshosts)
    while True:
        print("Waiting for scheduled tasks...")
        schedule.run_pending()
        time.sleep(60)
main()
