from prometheus_client import Histogram, Gauge
import psutil


class MonitorService:
    def __init__(self):
        self.response_time = Histogram(
            "response_time",
            "Time used for single chat request",
            labelnames=("endpoint",),
            buckets=(0.001, 0.01, 0.1, 0.25, 0.5,
                     1.0, 2.0, 3.0, 3.5,
                     4.0, 4.25, 4.5, 4.75,
                     5.0, 5.25, 5.5, 5.75,
                     6.0, 6.5, 7.0, 8.0, 9.0, 10.0))
        self.cpu_percent = Gauge(
            "cpu_percent",
            "CPU usage percent"
        )

    def observe_time(self, amount: float, path: str):
        self.response_time.labels(path).observe(amount)


monitor_service = MonitorService()
