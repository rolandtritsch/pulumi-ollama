import json
from pathlib import Path
import shlex
from string import Template

import pulumi
import pulumi_aws as aws

from . import config
from . import monitoring
from . import network
from . import security
from . import storage

# Look up the latest Deep Learning Base GPU AMI (Ubuntu 22.04) so Ollama's
# install script auto-detects CUDA and enables GPU inference.
_ami = aws.ec2.get_ami(
    most_recent=True,
    owners=["amazon"],
    filters=[
        aws.ec2.GetAmiFilterArgs(
            name="name",
            values=["Deep Learning Base OSS Nvidia Driver GPU AMI (Ubuntu 22.04) *"],
        ),
        aws.ec2.GetAmiFilterArgs(name="state", values=["available"]),
    ],
)

_user_data_template = Template((Path(__file__).parent / "user_data.sh").read_text())


def _render_user_data(volume_id: str) -> str:
    cloudwatch_config = {
        "agent": {
            "metrics_collection_interval": 60,
            "run_as_user": "root",
        },
        "logs": {
            "logs_collected": {
                "files": {
                    "collect_list": [
                        {"file_path": "/var/log/ollama-setup.log", "log_group_name": monitoring.log_group_names["bootstrap"], "log_stream_name": "{instance_id}/setup"},
                        {"file_path": "/var/log/cloud-init-output.log", "log_group_name": monitoring.log_group_names["bootstrap"], "log_stream_name": "{instance_id}/cloud-init"},
                        {"file_path": "/var/log/ollama/ollama.log", "log_group_name": monitoring.log_group_names["ollama"], "log_stream_name": "{instance_id}"},
                        {"file_path": "/var/log/auth.log", "log_group_name": monitoring.log_group_names["system"], "log_stream_name": "{instance_id}/auth"},
                        {"file_path": "/var/log/syslog", "log_group_name": monitoring.log_group_names["system"], "log_stream_name": "{instance_id}/syslog"},
                        {"file_path": "/opt/aws/amazon-cloudwatch-agent/logs/amazon-cloudwatch-agent.log", "log_group_name": monitoring.log_group_names["cloudwatch-agent"], "log_stream_name": "{instance_id}"},
                    ]
                }
            }
        },
        "metrics": {
            "namespace": "Ollama/Host",
            "append_dimensions": {"InstanceId": "${aws:InstanceId}"},
            "metrics_collected": {
                "cpu": {"measurement": ["cpu_usage_idle", "cpu_usage_iowait"], "totalcpu": True},
                "disk": {"measurement": ["used_percent", "inodes_free"], "resources": ["/", f"/mnt/{config.volume_name}"]},
                "diskio": {"measurement": ["reads", "writes", "read_bytes", "write_bytes"], "resources": ["*"]},
                "mem": {"measurement": ["used_percent"]},
                "net": {"measurement": ["bytes_sent", "bytes_recv"], "resources": ["*"]},
                "nvidia_gpu": {"measurement": ["utilization_gpu", "utilization_memory", "memory_used", "memory_total", "temperature_gpu", "power_draw"]},
                "procstat": [{"pattern": "ollama", "measurement": ["pid_count", "cpu_usage", "memory_rss"]}],
            },
        },
    }
    return _user_data_template.safe_substitute(
        volume_id=volume_id,
        volume_id_clean=volume_id.replace("-", ""),
        volume_name=config.volume_name,
        models=shlex.join(config.models),
        cloudwatch_config=json.dumps(cloudwatch_config, indent=2),
    )


user_data = storage.volume.id.apply(_render_user_data)

# Create an EC2 Instance
instance = aws.ec2.Instance("ollama-instance",
    ami=_ami.id,
    instance_type=config.instance_type,
    key_name=security.key_pair.key_name,
    subnet_id=network.subnet.id,
    tags={"Name": "ollama-instance"},
    user_data=user_data,
    user_data_replace_on_change=True,
    vpc_security_group_ids=[security.security_group.id],
    iam_instance_profile=monitoring.instance_profile.name,
    monitoring=True,
    metadata_options=aws.ec2.InstanceMetadataOptionsArgs(
        http_endpoint="enabled",
        http_tokens="required",
        http_put_response_hop_limit=1,
    ),
    root_block_device=aws.ec2.InstanceRootBlockDeviceArgs(
        volume_size=config.root_volume_size,
        volume_type="gp3",
        encrypted=True,
        delete_on_termination=True,
    ),
    opts=pulumi.ResourceOptions(depends_on=[monitoring.policy]),
)

volume_attachment = aws.ec2.VolumeAttachment(
    "ollama-volumeAttachment",
    device_name=config.device_name,
    volume_id=storage.volume.id,
    instance_id=instance.id,
    opts=pulumi.ResourceOptions(delete_before_replace=True),
)

# Allocate an Elastic IP
eip = aws.ec2.Eip("ollama-eip",
    instance=instance.id,
    domain="vpc",
    tags={"Name": "ollama-eip"},
)
