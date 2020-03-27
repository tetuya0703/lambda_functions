from aws import is_highspec, is_spot, stop_job
from slack import send_slack, UserList
from typing import Dict


def is_just_started(event: Dict) -> bool:
    return event['detail']['CreationTime'] == event['detail']['LastModifiedTime'] \
        and event['detail']['SecondaryStatus'] == 'Starting'


class Checker:
    def __init__(self, channel: str):
        self.channel = channel
        self.JOB_URL_FMT = '<https://us-west-2.console.aws.amazon.com/sagemaker/home#/jobs/%s|Job Detail>'
        self.user_list = UserList()

    def __get_slack_user(self, username: str) -> str:
        user_id = self.user_list.get_user_id(username)
        if user_id is not None:
            return f'<@{user_id}> '
        else:
            return ''

    def check_ngrok(self, params: Dict, job_name: str):
        if 'ngrok' in ''.join(params.keys()):
            stop_job(job_name)

    def check_highspec(self, job_name: str, instance_type: str):
        if is_highspec(instance_type):
            value = f'Instance Type: {instance_type}\n' + self.JOB_URL_FMT % job_name
            attachments = [{'color': 'danger', 'fields': [{'title': job_name, 'value': value}]}]
            slack_user = self.__get_slack_user(job_name.split('-')[0])
            send_slack(self.channel,
                       slack_user + 'The instance is too high-spec. I will stop now',
                       attachments)
            stop_job(job_name)

    def check_ending(self, job_name: str, status: str):
        ending_statuses = ['Failed', 'Completed']
        if status not in ending_statuses:
            return

        attachments = [{'color': 'danger' if status == 'Failed' else 'good',
                        'fields': [{'title': job_name, 'value': self.JOB_URL_FMT % job_name}]}]
        slack_user = self.__get_slack_user(job_name.split('-')[0])
        send_slack(self.channel,
                   f'{slack_user}The following job is {status.lower()}',
                   attachments)

    def check_spot(self, job_name: str):
        if not is_spot(job_name):
            value = self.JOB_URL_FMT % job_name
            slack_user = self.__get_slack_user(job_name.split('-')[0])
            attachments = [{'color': 'danger', 'fields': [{'title': job_name, 'value': value}]}]
            send_slack(self.channel,
                       slack_user + 'The instance is not spot-training. I will stop now',
                       attachments)
            stop_job(job_name)
