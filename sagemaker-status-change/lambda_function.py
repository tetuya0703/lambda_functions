from check import Checker, is_just_started


def lambda_handler(event, context):
    channel = 'sagemaker_monitor'
    # channel = ''  # debugging
    checker = Checker(channel)

    job_name = event['detail']['TrainingJobName']
    status = event['detail']['TrainingJobStatus']
    instance_type = event['detail']['ResourceConfig']['InstanceType']
    params = event['detail']['HyperParameters']

    if is_just_started(event):
        checker.check_highspec(job_name, instance_type)
        checker.check_spot(job_name)
        checker.check_ngrok(params, job_name)
    checker.check_ending(job_name, status)
    return {'statusCode': 200}


# import json
# with open('sample.json') as f:
#     lambda_handler(json.loads(f.read()), None)
