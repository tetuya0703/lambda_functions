import boto3
import re
from datetime import datetime
from typing import List, Optional, Dict, NamedTuple


class TrainingJob(NamedTuple):
    name: str
    instance_type: str
    cnt: int


def get_search_filter(status: Optional[str] = None,
                      start: Optional[datetime] = None,
                      end: Optional[datetime] = None) -> Dict:
    datetime_format = '%Y-%m-%dT%H:%M:%S.%fZ'

    filters = [{"Name": "ResourceConfig.InstanceType",
                "Operator": "Contains",
                "Value": 'ml.p'}]
    if status is not None:
        filters.append({"Name": "TrainingJobStatus",
                        "Operator": "Equals",
                        "Value": status})
    if end is not None:
        filters.append({"Name": "TrainingStartTime",
                        "Operator": "LessThan",
                        "Value": end.strftime(datetime_format)})
    if start is not None:
        filters.append({"Name": "TrainingEndTime",
                        "Operator": "GreaterThan",
                        "Value": start.strftime(datetime_format)})
    return {"Filters": filters}


def get_jobs(search_filter: Dict) -> Dict[str, List[TrainingJob]]:
    client = boto3.client('sagemaker')
    response = client.search(Resource='TrainingJob', SearchExpression=search_filter, MaxResults=100)

    jobs = {'p2': [], 'p3': []}  # type: Dict[str, List[TrainingJob]]
    for r in response['Results']:
        job = r['TrainingJob']
        instance_type = job['ResourceConfig']['InstanceType']
        gpu_type = re.search(r'ml\.(p\d)\.', instance_type)
        if gpu_type is None:
            raise ValueError('Failed to get instance type')
        jobs[gpu_type.group(1)].append(TrainingJob(
            name=job['TrainingJobName'],
            instance_type=instance_type,
            cnt=job['ResourceConfig']['InstanceCount']))

    return jobs
