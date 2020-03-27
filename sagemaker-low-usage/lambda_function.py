from aws import JobDetector, Condition
from slack import send_slack
from slack_helper import get_attachments, get_low_usage_users


def lambda_handler(event, context):
    ratio_threshold = 0.05
    interval_hours = 2
    period_sec = 60
    gpu_conditions = [Condition(30, 30),
                      Condition(5, 90)]
    cpu_conditions = [Condition(20, 20)]

    username = 'SageMaker Supervisor'
    channel = 'sagemaker_monitor'
    whitelist = []
    # channel = ''  # debugging

    detector = JobDetector()
    low_jobs = detector.get_low_usage_jobs(period_sec, ratio_threshold,
                                           interval_hours, gpu_conditions,
                                           cpu_conditions, whitelist)
    if low_jobs:
        users = get_low_usage_users(low_jobs)
        msg = f'{users} These jobs do not use GPU efficiently in {interval_hours} hours.\n' \
            + 'Please stop them from "Job Detail" link and restart with moderate instance type'
        send_slack(username, channel, msg, get_attachments(low_jobs))


# from time import time
# start = time()
# lambda_handler(None, None)  # debug
# print('*****************')
# print(time() - start, 'seconds')
# print('*****************')
