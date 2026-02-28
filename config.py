import os

device_name = "/dev/sdf"
device_name_physical = "/dev/nvme2n1"  # g5 DLAMI: nvme1n1 is local SSD, nvme2n1 is EBS
volume_name = "ollama-volume"
public_key = open(os.path.expanduser("~/.ssh/aws-roland.pub")).read().strip()
models = ["qwen3-coder:30b", "codellama:34b"]
