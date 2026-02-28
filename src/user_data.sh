#!/bin/bash

export HOME=/root

# Check if the volume is already mounted
if mount | grep ${volume_name}; then
  echo "Volume ${volume_name} already mounted!"
else
  # Wait for the EBS volume to be attached
  while [ ! -e ${device_name_physical} ]; do
    echo "Waiting for ${device_name_physical} to be available..."
    sleep 5
  done

  # Create a file system on the volume
  mkfs -t ext4 ${device_name_physical}
  # Create a mount point
  mkdir -p /mnt/${volume_name}
  # Mount the volume
  mount ${device_name_physical} /mnt/${volume_name}
  # Ensure the volume is mounted on reboot
  echo "${device_name_physical} /mnt/${volume_name} ext4 defaults,nofail 0 2" >> /etc/fstab
fi

# Check if the ollama service is already running
if pgrep ollama > /dev/null; then
  echo "Ollama service already running!"
else
  # Install ollama; detects CUDA from the DLAMI and enables GPU inference
  curl -fsSL https://ollama.com/install.sh | sh

  # Create the directory for ollama models
  mkdir -p /mnt/${volume_name}/ollama-models
  chmod 775 /mnt/${volume_name}/ollama-models
  chgrp ollama /mnt/${volume_name}/ollama-models
  usermod -aG ollama ubuntu

  # Set the directory and host for the service
  echo -e "\n[Service]\nEnvironment=\"OLLAMA_MODELS=/mnt/${volume_name}/ollama-models\"\nEnvironment=\"OLLAMA_HOST=0.0.0.0\"\n" >> /etc/systemd/system/ollama.service

  # Enable and start the ollama service
  systemctl daemon-reload
  systemctl enable ollama
  systemctl start ollama
fi

# Pull the configured model(s)
for model in ${models}; do
  /usr/local/bin/ollama pull ${model}
done

# Refresh the package list
sudo apt update && sudo apt upgrade -y

# Restart ollama service after system updates
systemctl restart ollama
