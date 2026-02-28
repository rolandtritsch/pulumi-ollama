#!/bin/bash

set -euxo pipefail
trap 'echo "ERROR: script failed at line $LINENO"' ERR
exec > >(tee /var/log/ollama-setup.log) 2>&1

export HOME=/root

echo "Check if the volume is already mounted ..."
if mount | grep ${volume_name}; then
  echo "Volume ${volume_name} already mounted!"
else
  echo "Wait for the EBS volume to be attached ..."
  while [ ! -e ${device_name_physical} ]; do
    echo "Waiting for ${device_name_physical} to be available..."
    sleep 5
  done

  echo "Create a file system on the volume ..."
  mkfs -t ext4 ${device_name_physical}
  echo "Create a mount point ..."
  mkdir -p /mnt/${volume_name}
  echo "Mount the volume ..."
  mount ${device_name_physical} /mnt/${volume_name}
  echo "Ensure the volume is mounted on reboot ..."
  echo "${device_name_physical} /mnt/${volume_name} ext4 defaults,nofail 0 2" >> /etc/fstab
fi

echo "Check if the ollama service is already running ..."
if pgrep ollama > /dev/null; then
  echo "Ollama service already running!"
else
  echo "Install ollama; detects CUDA from the DLAMI and enables GPU inference ..."
  curl -fsSL https://ollama.com/install.sh | sh

  echo "Create the directory for ollama models ..."
  mkdir -p /mnt/${volume_name}/ollama-models
  chmod 775 /mnt/${volume_name}/ollama-models
  chgrp ollama /mnt/${volume_name}/ollama-models
  usermod -aG ollama ubuntu

  echo "Set the directory and host for the service ..."
  mkdir -p /etc/systemd/system/ollama.service.d
  cat > /etc/systemd/system/ollama.service.d/override.conf <<EOF
[Service]
Environment="OLLAMA_MODELS=/mnt/${volume_name}/ollama-models"
Environment="OLLAMA_HOST=0.0.0.0"
EOF

  echo "Enable and start the ollama service ..."
  systemctl daemon-reload
  systemctl enable ollama
  systemctl start ollama

  echo "Waiting for ollama to be ready ..."
  until curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; do
    sleep 2
  done
fi

echo "Pull the configured model(s) ..."
for model in ${models}; do
  /usr/local/bin/ollama pull ${model}
done

echo "Refresh the package list ..."
sudo apt update && sudo apt upgrade -y

echo "Restart ollama service after system updates ..."
systemctl restart ollama
