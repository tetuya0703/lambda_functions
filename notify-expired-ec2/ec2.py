import boto3
from datetime import datetime
from collections import defaultdict
from typing import Dict


def is_expired(due_date_str: str) -> bool:
    if due_date_str.lower() == 'no deadline' or not due_date_str:
        return False
    due_date = datetime.strptime(due_date_str, '%Y/%m/%d')
    return due_date.replace(hour=0, minute=0) < datetime.now()


def list_expired() -> Dict[str, str]:
    persons = defaultdict(str)
    for region in ['us-west-2', 'ap-northeast-1', 'ap-southeast-1']:
        boto3.setup_default_session(region_name=region)
        response = boto3.client('ec2').describe_instances(Filters=[{'Name': 'instance-state-code', 'Values': ['16']}])
        for reservation in response["Reservations"]:
            for instance in reservation["Instances"]:
                is_instance_expired = False
                person = 'not found'
                for tag in instance['Tags']:
                    if tag['Key'] == 'DueDate':
                        due_date = tag['Value']
                        is_instance_expired = is_expired(due_date)
                    if tag['Key'] == 'Person':
                        person = tag['Value']

                if is_instance_expired:
                    persons[person] += f"{instance['PublicIpAddress']}: expired on {due_date}\n"

    return persons
