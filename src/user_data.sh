#!/bin/bash

set -Eeuo pipefail
trap 'echo "ERROR: setup failed at line $LINENO"' ERR
exec > >(tee -a /var/log/ollama-setup.log) 2>&1

export DEBIAN_FRONTEND=noninteractive
export HOME=/root

retry() {
  local attempts=0
  local maximum=5
  local delay=5
  until "$@"; do
    attempts=$((attempts + 1))
    if [ "$attempts" -ge "$maximum" ]; then
      echo "Command failed after $maximum attempts: $*"
      return 1
    fi
    sleep "$delay"
    delay=$((delay * 2))
  done
}

echo "Record deployed software versions ..."
echo "AMI: $(curl --fail --silent --show-error --connect-timeout 5 -X PUT -H 'X-aws-ec2-metadata-token-ttl-seconds: 60' http://169.254.169.254/latest/api/token | xargs -I TOKEN curl --fail --silent --show-error -H 'X-aws-ec2-metadata-token: TOKEN' http://169.254.169.254/latest/meta-data/ami-id)"
nvidia-smi || true

echo "Locate the model EBS volume ..."
volume_serial="${volume_id_clean}"
device=""
for attempt in $(seq 1 60); do
  device=$(lsblk --nodeps --noheadings --output NAME,SERIAL | awk -v serial="$volume_serial" '$2 == serial {print "/dev/" $1; exit}')
  if [ -n "$device" ] && [ -b "$device" ]; then
    break
  fi
  device=""
  echo "Waiting for EBS volume ${volume_id} (attempt $attempt/60) ..."
  sleep 5
done
if [ -z "$device" ]; then
  echo "Could not find EBS volume ${volume_id}"
  lsblk --output NAME,SERIAL,SIZE,FSTYPE,MOUNTPOINT
  exit 1
fi

echo "Prepare model storage on $device ..."
if ! blkid "$device" >/dev/null 2>&1; then
  mkfs.ext4 -L "${volume_name}" "$device"
fi
filesystem_uuid=$(blkid -s UUID -o value "$device")
mkdir -p "/mnt/${volume_name}"
if ! mountpoint -q "/mnt/${volume_name}"; then
  mount -U "$filesystem_uuid" "/mnt/${volume_name}"
fi
fstab_entry="UUID=$filesystem_uuid /mnt/${volume_name} ext4 defaults,nofail 0 2"
grep -qF "$fstab_entry" /etc/fstab || echo "$fstab_entry" >> /etc/fstab

echo "Harden SSH configuration ..."
cat > /etc/ssh/sshd_config.d/99-ollama-hardening.conf <<'EOF'
PasswordAuthentication no
PermitRootLogin no
KbdInteractiveAuthentication no
EOF
sshd -t
systemctl reload ssh

echo "Install and configure the CloudWatch agent ..."
retry curl --fail --silent --show-error --location --output /tmp/amazon-cloudwatch-agent.deb \
  https://amazoncloudwatch-agent.s3.amazonaws.com/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
dpkg --install /tmp/amazon-cloudwatch-agent.deb
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json <<'EOF'
${cloudwatch_config}
EOF
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config -m ec2 \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json -s

echo "Install Ollama and configure its service ..."
retry curl --fail --silent --show-error --location --output /tmp/install-ollama.sh \
  https://ollama.com/install.sh
sh /tmp/install-ollama.sh
install -d -o ollama -g ollama -m 0775 "/mnt/${volume_name}/ollama-models"
usermod -aG ollama ubuntu
install -d -o ollama -g ollama -m 0755 /var/log/ollama
mkdir -p /etc/systemd/system/ollama.service.d
cat > /etc/systemd/system/ollama.service.d/override.conf <<EOF
[Unit]
RequiresMountsFor=/mnt/${volume_name}
After=network-online.target
Wants=network-online.target

[Service]
Environment="OLLAMA_MODELS=/mnt/${volume_name}/ollama-models"
Environment="OLLAMA_HOST=0.0.0.0:11434"
Restart=on-failure
RestartSec=5
StandardOutput=append:/var/log/ollama/ollama.log
StandardError=append:/var/log/ollama/ollama.log
EOF
systemctl daemon-reload
systemctl enable --now ollama

echo "Wait for Ollama readiness ..."
for attempt in $(seq 1 150); do
  if curl --fail --silent http://localhost:11434/api/tags >/dev/null; then
    break
  fi
  if [ "$attempt" -eq 150 ]; then
    systemctl status ollama --no-pager
    exit 1
  fi
  sleep 2
done

echo "Pull configured models ..."
for model in ${models}; do
  retry /usr/local/bin/ollama pull "$model"
done

echo "Install current operating-system updates ..."
retry apt-get update
retry apt-get upgrade -y
systemctl restart ollama amazon-cloudwatch-agent

echo "Record final versions ..."
/usr/local/bin/ollama --version
nvidia-smi || true
systemctl --no-pager --full status ollama amazon-cloudwatch-agent
