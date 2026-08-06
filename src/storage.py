import pulumi_aws as aws

from . import config
from . import network

# Create an EBS volume
volume = aws.ebs.Volume("ollama-volume",
    availability_zone=network.subnet.availability_zone,
    size=config.model_volume_size,
    encrypted=True,
    type="gp3",
    tags={"Name": "ollama-volume"},
)
