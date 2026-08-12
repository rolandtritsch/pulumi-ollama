from pathlib import Path
import sys

import pulumi

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src import compute
from src import dashboard
from src import dns
from src import monitoring
from src import storage

pulumi.export("instanceId", compute.instance.id)
pulumi.export("instancePublicIp", compute.instance.public_ip)
pulumi.export("eipPublicIp", compute.eip.public_ip)
pulumi.export("eipPublicDns", compute.eip.public_dns)
pulumi.export("volumeId", storage.volume.id)
pulumi.export("cloudwatchDashboard", dashboard.dashboard.dashboard_name)

_log_output_names = {
    "bootstrap": "BootstrapLogGroup",
    "ollama": "OllamaLogGroup",
    "system": "SystemLogGroup",
    "cloudwatch-agent": "CloudWatchAgentLogGroup",
}
for name, output_name in _log_output_names.items():
    pulumi.export(output_name, monitoring.log_groups[name].name)

if dns.record is not None:
    pulumi.export("dnsRecord", dns.record.name)
