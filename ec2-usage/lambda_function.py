from datetime import datetime, timedelta
from pytz import timezone
from slack import send_slack
from usage import get_metrics
from typing import List


def get_times(start: datetime, end: datetime, instance_id: str):
    res = get_metrics('AWS/EC2', 'CPUUtilization',
                      {'Name': 'InstanceId', 'Value': instance_id},
                      300, 'Percent', start, end)
    for t, _ in res:
        yield t


def get_running_time(start: datetime, end: datetime, instance_id: str) -> timedelta:
    duration = timedelta(seconds=0)
    current_end = None
    past = None
    for t in get_times(start, end, instance_id):
        if current_end is None:
            current_end = t
        elif past - timedelta(minutes=8) > t:
            duration += current_end - past
            current_end = t
        past = t

    if current_end is not None:
        duration += current_end - past
    return duration


def get_attachment(start: datetime, end: datetime,
                   instance_id: str, duration: timedelta) -> List[dict]:
    d_fmt = '%Y/%m/%d'
    text = 'period: {} - {}'.format(start.strftime(d_fmt), end.strftime(d_fmt))
    text += '\nrunning time: {}'.format(duration)
    return [{'color': 'good', 'fields': [{'title': instance_id, 'value': text}]}]


def lambda_handler(event, context):
    end = datetime.now(timezone('UTC'))
    start = end - timedelta(days=7)
    instance_id = 'i-002e95e4a32a852d8'
    channel = 'iiso_jp'
    # channel = ''  # debug

    min_duration = get_running_time(start, end, instance_id)
    attachments = get_attachment(start, end, instance_id, min_duration)
    message = 'EC2 running time'
    send_slack(channel, message, attachments)


# lambda_handler(None, None)  # debug
