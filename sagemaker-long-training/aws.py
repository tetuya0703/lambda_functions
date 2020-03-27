import boto3
from datetime import datetime
from typing import List, Optional, Dict, NamedTuple


class TrainingJob(NamedTuple):
    name: str
    output_path: str
    instance_type: str
    cnt: int
    status: str
    start_at: datetime
    end_at: Optional[datetime]


def get_search_filter(status: Optional[str] = None,
                      start_by: Optional[datetime] = None) -> Dict:
    datetime_format = '%Y-%m-%dT%H:%M:%S.%fZ'
    filters = []
    if status is not None:
        filters.append({"Name": "TrainingJobStatus",
                        "Operator": "Equals",
                        "Value": status})
    if start_by is not None:
        filters.append({"Name": "CreationTime",
                        "Operator": "LessThan",
                        "Value": start_by.strftime(datetime_format)})
    return {"Filters": filters}


def get_jobs(search_filter: Dict) -> List[TrainingJob]:
    client = boto3.client('sagemaker')
    response = client.search(Resource='TrainingJob', SearchExpression=search_filter, MaxResults=100)

    # ref: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sagemaker.html#SageMaker.Client.search
    def format_job_response(response: Dict) -> List[TrainingJob]:
        jobs = []
        for r in response['Results']:
            job = r['TrainingJob']
            jobs.append(TrainingJob(
                name=job['TrainingJobName'],
                output_path=job['OutputDataConfig']['S3OutputPath'],
                instance_type=job['ResourceConfig']['InstanceType'],
                cnt=job['ResourceConfig']['InstanceCount'],
                status=job['TrainingJobStatus'],
                start_at=job['CreationTime'],
                end_at=job.get('TrainingEndTime')))
        return jobs

    return format_job_response(response)
