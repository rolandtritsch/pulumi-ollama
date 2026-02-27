import pulumi
import pulumi_aws as aws

import config
import compute

# Create an EBS volume
volume = aws.ebs.Volume("ollama-volume",
    availability_zone=compute.instance.availability_zone,
    size=500,
    tags={"Name": "ollama-volume"},
)

# Attach the EBS Volume to the instance
volume_attachment = aws.ec2.VolumeAttachment("ollama-volumeAttachment",
    device_name=config.device_name,
    volume_id=volume.id,
    instance_id=compute.instance.id,
    opts=pulumi.ResourceOptions(delete_before_replace=True),
)
