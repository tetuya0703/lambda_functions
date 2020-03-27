from datetime import datetime, timedelta
from pytz import timezone
from typing import Iterator, NamedTuple, Dict, Tuple, List
import boto3


def get_metrics(namespace: str, metric: str,
                dimension: Dict[str, str],
                period: int, unit: str,
                start_at: datetime,
                end_at: datetime) -> Iterator[Tuple[datetime, float]]:
    client = boto3.client('cloudwatch')
    max_datapoints = 1000
    query = {
        'Id': 'm1',
        'MetricStat': {
            'Metric': {
                'Namespace': namespace,
                'MetricName': metric,
                'Dimensions': [dimension]
            },
            'Period': period,
            'Stat': 'Average',
            'Unit': unit
        },
        'ReturnData': True
    }
    response = client.get_metric_data(
        MetricDataQueries=[query],
        MaxDatapoints=max_datapoints,
        StartTime=start_at,
        EndTime=end_at
    )
    result = response['MetricDataResults'][0]
    for t, v in zip(result['Timestamps'], result['Values']):
        yield t, v

    next_token = response.get('NextToken')
    while next_token is not None:
        response = client.get_metric_data(
            MetricDataQueries=[query],
            MaxDatapoints=max_datapoints,
            StartTime=start_at,
            EndTime=end_at,
            NextToken=next_token
        )
        next_token = response.get('NextToken')
        result = response['MetricDataResults'][0]
        for t, v in zip(result['Timestamps'], result['Values']):
            yield t, v


def get_metric_values(namespace: str, metric: str,
                      dimension: Dict[str, str],
                      period: int, unit: str,
                      interval_hours: int,
                      end_at: datetime = None) -> Iterator[float]:
    if end_at is None:
        end_at = datetime.now(timezone('UTC'))
    start_at = end_at - timedelta(hours=interval_hours)
    for t, v in get_metrics(namespace, metric, dimension, period, unit, start_at, end_at):
        yield v


class AnalysisResult(NamedTuple):
    above_ratios: List[float]
    num_total: int
    average: float


def analyze(values: Iterator[float], thresholds: List[float]) -> AnalysisResult:
    num_total = 0
    num_above_thresholds = [0.0] * len(thresholds)
    sum_value = 0.0

    for v in values:
        num_total += 1
        sum_value += v
        for i, t in enumerate(thresholds):
            if v > t:
                num_above_thresholds[i] += 1
    if num_total == 0:
        return AnalysisResult(num_above_thresholds, 0, 0.0)
    return AnalysisResult([t / num_total for t in num_above_thresholds],
                          num_total,
                          sum_value / num_total)
