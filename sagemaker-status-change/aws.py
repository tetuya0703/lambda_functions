import boto3
import re

client = boto3.client('sagemaker')


def is_highspec(instance_type: str) -> bool:
    gpu_info = re.search(r'ml\.p\d\.(\d+)?xlarge', instance_type)
    return gpu_info is not None and int(gpu_info.group(1) or '1') > 8


def is_spot(job_name: str) -> bool:
    response = client.describe_training_job(TrainingJobName=job_name)
    return response['EnableManagedSpotTraining']


def stop_job(job_name) -> None:
    client.stop_training_job(TrainingJobName=job_name)
