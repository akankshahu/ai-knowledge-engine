import time
from collections import defaultdict
from typing import Dict

REQUEST_COUNTS: Dict[str, int] = defaultdict(int)
REQUEST_LATENCY_SECONDS: Dict[str, float] = defaultdict(float)


def record_request(path: str, latency_seconds: float) -> None:
    REQUEST_COUNTS[path] += 1
    REQUEST_LATENCY_SECONDS[path] += latency_seconds


def render_metrics_text() -> str:
    lines = ["# HELP app_requests_total Total HTTP requests", "# TYPE app_requests_total counter"]
    for path, count in sorted(REQUEST_COUNTS.items()):
        lines.append(f'app_requests_total{{path="{path}"}} {count}')

    lines.extend(["# HELP app_request_latency_seconds_total Total latency by path", "# TYPE app_request_latency_seconds_total counter"])
    for path, latency in sorted(REQUEST_LATENCY_SECONDS.items()):
        lines.append(f'app_request_latency_seconds_total{{path="{path}"}} {latency:.6f}')

    return "\n".join(lines) + "\n"
