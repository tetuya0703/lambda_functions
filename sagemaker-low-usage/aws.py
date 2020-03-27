import boto3
import re
from typing import Iterator, NamedTuple, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor

from usage import get_metric_values, analyze, AnalysisResult


class TrainingJob:
    def __init__(self, name: str, instance_type: str):
        self.name = name
        self.instance_type = instance_type
        self.num_gpu = self.__get_num_gpu()
        self.num_cpu = self.__get_num_cpu()

    def __get_num_gpu(self) -> int:
        gpu_info = re.search(r'ml\.p(\d)\.(\d+)?xlarge', self.instance_type)
        if gpu_info is None:
            return 0
        # ref: https://aws.amazon.com/jp/sagemaker/pricing/instance-types/
        return int(int(gpu_info.group(2) or '1') / (int(gpu_info.group(1)) - 1))

    def __get_num_cpu(self) -> int:
        core_info = re.search(r'ml\..+?\.(\d+)?xlarge', self.instance_type)
        if core_info is None:
            return 2
        return int(core_info.group(1) or '1') * 4


class Condition(NamedTuple):
    threshold: int
    mem_threshold: int


def get_sg_metrics(metric: str, job_name: str,
                   period: int, unit: str = 'Percent',
                   interval_hours: int = 1) -> Iterator[float]:
    return get_metric_values(
        '/aws/sagemaker/TrainingJobs', metric,
        {'Name': 'Host', 'Value': f'{job_name}/algo-1'},
        period, unit, interval_hours)


class LowUsageJob(NamedTuple):
    job: TrainingJob
    util: float
    mem_util: float

    @property
    def proc_percent(self) -> float:
        return self.util / self.get_cores()

    @property
    def mem_percent(self) -> float:
        return self.mem_util / self.get_cores()

    @property
    def is_gpu(self) -> bool:
        return self.job.num_gpu > 0

    def get_cores(self) -> int:
        return self.job.num_gpu if self.is_gpu else self.job.num_cpu


class JobDetector:
    def __init__(self):
        self.inprogress_jobs = []

    def __get_inprogress_jobs(self, whitelist: List[str]) -> List[TrainingJob]:
        if self.inprogress_jobs:
            return self.inprogress_jobs
        search_filter = {'Filters': [{"Name": "TrainingJobStatus",
                                      "Operator": "Equals",
                                      "Value": 'InProgress'}]}
        client = boto3.client('sagemaker')
        response = client.search(Resource='TrainingJob',
                                 SearchExpression=search_filter,
                                 MaxResults=100)

        for r in response['Results']:
            job = r['TrainingJob']
            if job['TrainingJobName'] in whitelist:
                continue
            self.inprogress_jobs.append(TrainingJob(job['TrainingJobName'], job['ResourceConfig']['InstanceType']))
        return self.inprogress_jobs

    def __is_low_usage(self, proc_result: AnalysisResult, mem_result: AnalysisResult,
                       total_threshold: int, ratio_threshold: float) -> bool:
        if mem_result.num_total < total_threshold:
            return False
        for proc_ratio, mem_ratio in zip(proc_result.above_ratios, mem_result.above_ratios):
            if proc_ratio < ratio_threshold and mem_ratio < ratio_threshold:
                return True
        return False

    def __analyze(self, job: TrainingJob, period_sec: int, interval_hours: int,
                  proc_metric_name: str, mem_metric_name: str,
                  conditions: List[Condition]) -> Tuple[AnalysisResult, AnalysisResult]:
        proc_values = get_sg_metrics(proc_metric_name, job.name, period_sec,
                                     interval_hours=interval_hours)
        proc_result = analyze(proc_values,
                              self.__get_thresholds([c.threshold for c in conditions], job, 1.0))
        mem_values = get_sg_metrics(mem_metric_name, job.name,
                                    period_sec, interval_hours=interval_hours)
        mem_result = analyze(mem_values,
                             self.__get_thresholds([c.mem_threshold for c in conditions], job, 5.0))
        return proc_result, mem_result

    def __get_low_usage_job(self, job: TrainingJob, total_threshold: int,
                            ratio_threshold: float, interval_hours: int, period_sec: int,
                            gpu_conditions: List[Condition],
                            cpu_conditions: List[Condition]) -> Optional[LowUsageJob]:
        if job.num_gpu == 0:
            conditions = cpu_conditions
            proc_metric_name = 'CPUUtilization'
            mem_metric_name = 'MemoryUtilization'
        else:
            conditions = gpu_conditions
            proc_metric_name = 'GPUUtilization'
            mem_metric_name = 'GPUMemoryUtilization'

        proc_result, mem_result = self.__analyze(job, period_sec, interval_hours,
                                                 proc_metric_name, mem_metric_name,
                                                 conditions)
        if self.__is_low_usage(proc_result, mem_result,
                               total_threshold, ratio_threshold):
            return LowUsageJob(job, proc_result.average, mem_result.average)
        else:
            return None

    def get_low_usage_jobs(self, period_sec: int,
                           ratio_threshold: float, interval_hours: int,
                           gpu_conditions: List[Condition],
                           cpu_conditions: List[Condition],
                           whitelist: List[str]) -> List[Optional[LowUsageJob]]:
        total_threshold = int((interval_hours * 60 * 60 / period_sec) * 0.9)
        with ThreadPoolExecutor(max_workers=20, thread_name_prefix="thread") as executor:
            args = []
            for job in self.__get_inprogress_jobs(whitelist):
                args.append((job, total_threshold,
                             ratio_threshold, interval_hours, period_sec,
                             gpu_conditions, cpu_conditions))
            results = executor.map(lambda p: self.__get_low_usage_job(*p), args)

        return list(filter(lambda x: x is not None, results))

    def __get_thresholds(self, thresholds: List[int],
                         job: TrainingJob, lowest_usage: float) -> List[float]:
        if job.num_gpu > 0:
            if job.instance_type == 'ml.p2.xlarge':
                return [lowest_usage]
            else:
                return [t * job.num_gpu for t in thresholds]
        else:
            if job.instance_type.split('.')[-1] == 'large':
                return [lowest_usage]
            else:
                return [t * job.num_cpu for t in thresholds]
