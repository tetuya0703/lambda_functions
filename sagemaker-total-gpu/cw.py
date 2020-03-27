import boto3
from datetime import datetime, timedelta
from typing import List, Dict, Iterator, Tuple

from usage import get_metrics
from sg import TrainingJob


def get_sg_metrics(metric: str, job_name: str,
                   start_at: datetime, end_at: datetime,
                   period: int, idx: int = 1,
                   unit: str = 'Percent') -> Iterator[Tuple[datetime, float]]:
    return get_metrics(
        '/aws/sagemaker/TrainingJobs', metric,
        {'Name': 'Host', 'Value': f'{job_name}/algo-{idx}'},
        period, unit, start_at, end_at)


def get_total_metrics(metric: str, jobs: List[TrainingJob],
                      start_at: datetime, end_at: datetime,
                      period_sec: int = 300) -> List[Tuple[datetime, float]]:
    metric_time = {}  # type: Dict[datetime, float]
    current_date = start_at
    while current_date < end_at:
        metric_time[current_date] = 0.0
        current_date += timedelta(seconds=period_sec)

    for job in jobs:
        for i in range(job.cnt):
            for t, v in get_sg_metrics(metric, job.name, start_at, end_at,
                                       period_sec, idx=i + 1):
                metric_time[t] += v

    return sorted(metric_time.items(), key=lambda x: x[0])


def put_total_metrics(metric: str, gpu_type: str, data: List[Tuple[datetime, float]]) -> None:
    metric_data = []
    max_size_per_req = 20
    for timestamp, value in data:
        metric_data.append({
           "MetricName": metric,
           "Dimensions": [{"Name": "Service", "Value": 'SageMaker'},
                          {"Name": "GPUType", "Value": gpu_type}],
           "Value": value, "Unit": "Percent",
           'Timestamp': timestamp
        })
    for i in range(0, len(metric_data), max_size_per_req):
        boto3.client("cloudwatch").put_metric_data(
            Namespace="GPU_Total", MetricData=metric_data[i:i+max_size_per_req])
    # debug
    # msg = '=========Params of put_metric_data=========='
    # msg += '\nMetric: ' + metric
    # msg += '\nGPU Type: ' + gpu_type
    # msg += '\nFrom: ' + data[0][0].strftime("%m/%d/%Y, %H:%M:%S")
    # msg += '\nTo: ' + data[-1][0].strftime("%m/%d/%Y, %H:%M:%S")
    # msg += '\nData Size: ' + str(len(data))
    # msg += '\nSome values: ' + ', '.join(str(d[1]) for d in data[:5])
    # print(msg)
