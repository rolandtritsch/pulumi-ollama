import pulumi_aws as aws

import config
import network
import security

_models_str = " ".join(config.models)

user_data = f"""#!/bin/bash
  # Check if the volume is already mounted
  if mount | grep {config.volume_name}; then
    echo "Volume {config.volume_name} already mounted!"
  else
    # Wait for the EBS volume to be attached
    while [ ! -e {config.device_name_physical} ]; do
      echo "Waiting for {config.device_name_physical} to be available..."
      sleep 5
    done

    # Create a file system on the volume
    mkfs -t ext4 {config.device_name_physical}
    # Create a mount point
    mkdir -p /mnt/{config.volume_name}
    # Mount the volume
    mount {config.device_name_physical} /mnt/{config.volume_name}
    # Ensure the volume is mounted on reboot
    echo "{config.device_name_physical} /mnt/{config.volume_name} ext4 defaults,nofail 0 2" >> /etc/fstab
  fi

  # Check if the ollama service is already running
  if pgrep ollama > /dev/null; then
    echo "Ollama service already running!"
  else
    # Install the latest version of ollama
    curl -fsSL https://ollama.com/install.sh | sh

    # Create the directory for ollama models
    mkdir -p /mnt/{config.volume_name}/ollama-models
    chmod 775 /mnt/{config.volume_name}/ollama-models
    chgrp ollama /mnt/{config.volume_name}/ollama-models
    usermod -aG ollama ubuntu

    # Set the directory and host for the service
    echo -e "\\n[Service]\\nEnvironment=\\"OLLAMA_MODELS=/mnt/{config.volume_name}/ollama-models\\"\\nEnvironment=\\"OLLAMA_HOST=0.0.0.0\\"\\n" >> /etc/systemd/system/ollama.service

    # (Re)Start the ollama service
    systemctl daemon-reload
    systemctl restart ollama
  fi

  # Pull the configured model(s)
  for model in {_models_str}; do
    /usr/local/bin/ollama pull $model
  done

  # Refresh the package list
  sudo apt update && sudo apt upgrade -y
"""

# Create an EC2 Instance
instance = aws.ec2.Instance("ollama-instance",
    ami="ami-09d0c9a85bf1b9ea7",  # Ubuntu 22.04 LTS, eu-west-1
    instance_type="m5.2xlarge",
    key_name=security.key_pair.key_name,
    subnet_id=network.subnet.id,
    tags={"Name": "ollama-instance"},
    user_data=user_data,
    vpc_security_group_ids=[security.security_group.id],
)

# Allocate an Elastic IP
eip = aws.ec2.Eip("ollama-eip",
    instance=instance.id,
    domain="vpc",
    tags={"Name": "ollama-eip"},
)
