from datetime import datetime, timedelta
import boto3
from slack import send_slack
from typing import List, Tuple


def get_metrics(billing_date: datetime, service_name: str = '') -> List[Tuple[str, float]]:
    client = boto3.client('ce')
    time_period = {'Start': billing_date.strftime('%Y-%m-%d'),
                   'End': (billing_date + timedelta(days=1)).strftime('%Y-%m-%d')}
    filters = {
        'Dimensions': {
            'Key': 'SERVICE',
            'Values': [
                'Amazon SageMaker',
                'EC2 - Other',
                'Amazon Elastic Compute Cloud - Compute',
            ]
        }
    }
    metric = 'UnblendedCost'

    result = []  # type: List[Tuple[str, float]]
    res = client.get_cost_and_usage(
        TimePeriod=time_period,
        Granularity='DAILY',
        Metrics=[metric]
    )
    result.append(('Total', res['ResultsByTime'][0]['Total'][metric]['Amount']))
    res = client.get_cost_and_usage(
        TimePeriod=time_period,
        Granularity='DAILY',
        Filter=filters,
        Metrics=[metric],
        GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
    )
    for group in res['ResultsByTime'][0]['Groups']:
        result.append((group['Keys'][0], group['Metrics'][metric]['Amount']))
    return result


def get_attachment(metrics: List[Tuple[str, float]]) -> List[dict]:
    fields = []
    for service, fee in metrics:
        fee_str = '${:.2f}'.format(float(fee))
        fields.append({'title': service, 'value': fee_str})
    return [{'color': 'good', 'fields': fields}]


def lambda_handler(event, context):
    billing_date = datetime.today() - timedelta(days=3)
    date_str = billing_date.strftime('%Y-%m-%d')
    url = ('https://console.aws.amazon.com/cost-reports/home?#/custom?groupBy=Service&hasBlended=false'
           + '&hasAmortized=false&excludeDiscounts=true&excludeTaggedResources=false&timeRangeOption=Custom'
           + '&granularity=Daily&reportName=&reportType=CostUsage&isTemplate=true&startDate={0}&endDate={0}'
           + '&filter=%5B%5D&forecastTimeRangeOption=None&usageAs=usageQuantity&chartStyle=Stack').format(date_str)
    channel = 'iiso_jp'
    # channel = ''  # debug

    attachments = get_attachment(get_metrics(billing_date))
    message = 'AWS Billing in {}\n Detail: <{}|Dashboard Link>'.format(date_str, url)
    send_slack(channel, message, attachments)


# lambda_handler(None, None)  # debug
