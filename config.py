import os
import pulumi

_cfg = pulumi.Config()

device_name = "/dev/sdf"
device_name_physical = "/dev/nvme1n1"
volume_name = "ollama-volume"
public_key = open(os.path.expanduser("~/.ssh/aws-roland.pub")).read().strip()
models = (_cfg.get("models") or "llama3.2:latest").split(",")
