from datetime import datetime, timedelta
from pytz import timezone

from sg import get_search_filter, get_jobs
from cw import get_total_metrics, put_total_metrics


def lambda_handler(event, context):
    end = datetime.now(timezone('UTC'))\
        .replace(minute=0, second=0, microsecond=0)\
        - timedelta(hours=1)
    # end = datetime(2019, 8, 18, hour=0, tzinfo=timezone('UTC'))  # debug
    start = end - timedelta(hours=1)

    gpu_jobs = get_jobs(get_search_filter(start=start, end=end))
    for gpu_type, jobs in get_jobs(get_search_filter(status='InProgress', end=end)).items():
        gpu_jobs[gpu_type] += jobs

    for gpu_type, jobs in gpu_jobs.items():
        for metric in ['GPUUtilization', 'GPUMemoryUtilization']:
            total_values = get_total_metrics(metric, jobs, start, end)
            put_total_metrics(metric, gpu_type, total_values)
    return {'statusCode': 200}


# from time import time  # debug
# start = time()  # debug
# lambda_handler(None, None)  # debug
# print('time:', time() - start)  # debug
