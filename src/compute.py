from pathlib import Path
from string import Template

import pulumi_aws as aws

from . import config
from . import network
from . import security

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

_user_data_script = Path(__file__).parent / "user_data.sh"
user_data = Template(_user_data_script.read_text()).safe_substitute(
    volume_name=config.volume_name,
    device_name_physical=config.device_name_physical,
    models=" ".join(config.models),
)

# Create an EC2 Instance
instance = aws.ec2.Instance("ollama-instance",
    ami=_ami.id,
    instance_type="g5.2xlarge",
    key_name=security.key_pair.key_name,
    subnet_id=network.subnet.id,
    tags={"Name": "ollama-instance"},
    user_data=user_data,
    vpc_security_group_ids=[security.security_group.id],
    root_block_device=aws.ec2.InstanceRootBlockDeviceArgs(
        volume_size=200,  # DLAMI pre-installed packages consume ~50 GB
    ),
)

# Allocate an Elastic IP
eip = aws.ec2.Eip("ollama-eip",
    instance=instance.id,
    domain="vpc",
    tags={"Name": "ollama-eip"},
)
