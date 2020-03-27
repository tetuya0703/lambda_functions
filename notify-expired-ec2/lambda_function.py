import json
from typing import Dict

from slack import send_slack, UserList
from ec2 import list_expired


def lambda_handler(event, context):
    persons = list_expired()
    if persons:
        message = get_message(persons)
        channel = 'it_aws_instance_req'
    else:
        message = 'No expired instances are found, but send message as healthcheck'
        channel = 'iiso_jp'
    send_slack(channel, message)
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }


def get_message(persons: Dict[str, str]) -> str:
    message = 'The following instances are (or will be) expired. Can I delete them?'
    message += '\nWith no response in one day, I will delete them.\n'
    user_list = UserList()
    for p, msg in persons.items():
        message += f'\nPerson in charege: <@{user_list.get_user_id(p)}>\n{msg}'
    return message
