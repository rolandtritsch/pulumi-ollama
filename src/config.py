import os

import pulumi

cfg = pulumi.Config()

device_name = "/dev/sdf"
device_name_physical = "/dev/nvme2n1"  # g5 DLAMI: nvme1n1 is local SSD, nvme2n1 is EBS
volume_name = "ollama-volume"

public_key_path = cfg.require("public_key_path")
public_key = open(os.path.expanduser(public_key_path)).read().strip()

models_raw = cfg.get("models") or "llama3.2:latest"
models = [m.strip() for m in models_raw.split(",")]

dns_zone = cfg.get("dns_zone")
dns_hostname = cfg.get("dns_hostname")
