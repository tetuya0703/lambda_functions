from aws import LowUsageJob
from typing import List, Dict
from slack import UserList


def get_attachments(low_jobs: List[LowUsageJob]) -> List[Dict]:
    JOB_URL_FMT = '<https://us-west-2.console.aws.amazon.com/sagemaker/home#/jobs/%s|Job Detail>'

    def _get_field(job: LowUsageJob) -> Dict:
        proc = 'GPU' if job.is_gpu else 'CPU'
        value = f'Instance Type: {job.job.instance_type}\n' \
            + JOB_URL_FMT % job.job.name + '\n' \
            + '{0} usage per {0}: {1:.5g} %\n'.format(proc, job.proc_percent) \
            + '{0} Memory usage per {0}: {1:.5g} %'.format(proc, job.mem_percent)

        return {'title': job.job.name, 'value': value, 'short': False}

    attachments = [{
        'color': 'danger',
        'fields': [_get_field(job) for job in low_jobs]
    }]
    return attachments


def get_low_usage_users(low_jobs: List[LowUsageJob]) -> str:
    userlist = UserList()
    users = set([])
    for job in low_jobs:
        user_id = userlist.get_user_id(job.job.name.split('-')[0])
        if user_id is not None:
            users.add(f'<@{user_id}>')
    return ' '.join(users)
