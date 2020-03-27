from datetime import datetime, timedelta
from pytz import timezone
from typing import List, Dict

from slack import send_slack
from aws import get_search_filter, get_jobs, TrainingJob


def get_long_attachments(long_jobs: List[TrainingJob]) -> List[Dict]:
    JOB_URL_FMT = '<https://us-west-2.console.aws.amazon.com/sagemaker/home#/jobs/%s|Job Detail>'
    fields = []
    for job in long_jobs:
        running_time = str(datetime.now(timezone('UTC')) - job.start_at)\
            .split('.')[0].replace(':', ' hours ', 1)\
            .replace(':', ' minutes ', 1) + ' seconds'
        value = f'Instance Type: {job.instance_type}\n' \
            + f'Running Time: {running_time}\n' \
            + JOB_URL_FMT % job.name
        fields.append({'title': job.name, 'value': value, 'short': False})

    attachments = [{
        'color': 'warning',
        'fields': fields
    }]
    return attachments


def lambda_handler(event, context):
    too_long_time = timedelta(hours=12)
    channel = 'sagemaker_monitor'
    # channel = ''  # debug

    long_jobs = get_jobs(get_search_filter(
        status='InProgress', start_by=datetime.now(timezone('UTC')) - too_long_time))
    if long_jobs:
        message = 'These jobs are running for a long time\n' \
            + 'If you just forget stopping it, please stop them from "Job Detail" link'
        send_slack(channel, message,
                   get_long_attachments(long_jobs))
    else:
        send_slack('iiso_all', 'No long training found')
    return {'statusCode': 200}


# lambda_handler(None, None)  # debug
