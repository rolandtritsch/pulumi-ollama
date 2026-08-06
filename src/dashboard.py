import json

import pulumi
import pulumi_aws as aws

from . import compute
from . import monitoring


def _dashboard_body(values: list[str]) -> str:
    instance_id, bootstrap_logs, ollama_logs = values
    return json.dumps({
        "widgets": [
            {
                "type": "metric",
                "width": 12,
                "height": 6,
                "properties": {
                    "title": "EC2 health and utilization",
                    "region": aws.config.region,
                    "view": "timeSeries",
                    "metrics": [
                        ["AWS/EC2", "StatusCheckFailed", "InstanceId", instance_id],
                        [".", "CPUUtilization", ".", "."],
                        ["Ollama/Host", "mem_used_percent", ".", "."],
                        [".", "procstat_lookup_pid_count", ".", "."],
                        [{
                            "expression": f"SEARCH('{{Ollama/Host,InstanceId}} MetricName=\"disk_used_percent\" InstanceId=\"{instance_id}\"', 'Average', 300)",
                            "label": "Disk used",
                            "id": "disk_used",
                        }],
                    ],
                },
            },
            {
                "type": "metric",
                "width": 12,
                "height": 6,
                "properties": {
                    "title": "NVIDIA GPU",
                    "region": aws.config.region,
                    "view": "timeSeries",
                    "metrics": [
                        ["Ollama/Host", "nvidia_smi_utilization_gpu", "InstanceId", instance_id],
                        [".", "nvidia_smi_utilization_memory", ".", "."],
                        [".", "nvidia_smi_memory_used", ".", "."],
                        [".", "nvidia_smi_temperature_gpu", ".", "."],
                    ],
                },
            },
            {
                "type": "log",
                "width": 12,
                "height": 6,
                "properties": {
                    "title": "Recent bootstrap logs",
                    "region": aws.config.region,
                    "query": f"SOURCE '{bootstrap_logs}' | fields @timestamp, @message | sort @timestamp desc | limit 50",
                    "view": "table",
                },
            },
            {
                "type": "log",
                "width": 12,
                "height": 6,
                "properties": {
                    "title": "Recent Ollama logs",
                    "region": aws.config.region,
                    "query": f"SOURCE '{ollama_logs}' | fields @timestamp, @message | sort @timestamp desc | limit 50",
                    "view": "table",
                },
            },
        ]
    })


dashboard = aws.cloudwatch.Dashboard(
    "ollama-dashboard",
    dashboard_name=f"ollama-{pulumi.get_stack()}",
    dashboard_body=pulumi.Output.all(
        compute.instance.id,
        monitoring.log_groups["bootstrap"].name,
        monitoring.log_groups["ollama"].name,
    ).apply(_dashboard_body),
)
