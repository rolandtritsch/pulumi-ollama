# Developer Guide

This file covers the structure of the repo and how to make and verify changes. See [README.md][] for user-facing documentation.

## Project Structure

```
pulumi-ollama/
├── Pulumi.yaml          # Pulumi project metadata (Python + uv)
├── pyproject.toml       # Python dependencies (managed by uv)
├── ollama.py            # Entry point; exports stack outputs
├── Makefile             # Convenience targets: up, destroy, help
├── src/
│   ├── __init__.py
│   ├── config.py        # Shared constants and Pulumi config values
│   ├── network.py       # VPC, IGW, subnet, route table
│   ├── security.py      # Key pair and security group
│   ├── compute.py       # EC2 instance and Elastic IP
│   ├── storage.py       # EBS volume and attachment
│   ├── dns.py           # Optional Route53 DNS record
│   └── user_data.sh     # EC2 bootstrap script (templated)
└── .gitignore
```

### Dependency / Import Graph

```
config.py
    ↓
network.py  →  vpc, subnet
    ↓
security.py →  key_pair, security_group
    ↓
compute.py  →  instance, eip
    ↓
storage.py  →  volume
dns.py      →  record (optional, only if dns_zone + dns_hostname are set)
    ↓
ollama.py   →  stack exports
```

## File Size Limit

Keep each source file under 400 lines of code.

## Making Changes

### Adding or changing resources

Each layer is isolated to its own module. Edit the relevant file:

- Networking changes → `src/network.py`
- Firewall / SSH key changes → `src/security.py`
- Instance type, AMI, user-data → `src/compute.py`
- EBS volume size or device → `src/storage.py` / `src/config.py`
- DNS record → `src/dns.py`

### Changing the models to pull

Models are configured at the Pulumi stack level, not in code:

```bash
pulumi config set models "deepseek-r1:8b,llama3.1:latest"
```

The default (if not set) is `llama3.2:latest`. The value is a comma-separated list; `src/config.py` splits it and `src/compute.py` passes the list to the `user_data.sh` template.

### Changing the SSH key

The path to the SSH public key is read from Pulumi config:

```bash
pulumi config set public_key_path ~/.ssh/your-key.pub
```

### Changing instance type or AMI

Edit `src/compute.py`. The current values are:

- AMI: dynamically resolved — latest Deep Learning Base OSS Nvidia Driver GPU AMI (Ubuntu 22.04) via `aws.ec2.get_ami`
- Instance type: `g5.2xlarge` (NVIDIA A10G, 24 GB VRAM)

### DNS (optional)

If `dns_zone` and `dns_hostname` are set in Pulumi config, `src/dns.py` creates a Route53 A record pointing to the Elastic IP. If either is unset, no DNS resources are created.

## Verifying Changes

### Syntax check

```bash
uv run python -c "import ollama"
```

### Pulumi preview (no AWS changes)

```bash
pulumi preview
```

Expected resources: VPC, IGW, subnet, route table, route table association, key pair, security group, EC2 instance, EIP, EBS volume, volume attachment. DNS record only if `dns_zone` and `dns_hostname` are configured.

### Config test

```bash
pulumi config set models "deepseek-r1:8b,llama3.1:latest"
pulumi preview
```

Verify the user-data section of the instance shows both models in the `for` loop.

### End-to-end deploy

```bash
make up
curl http://$(pulumi stack output eipPublicIp):11434
# Expected: Ollama is running
```

## Dependencies

Managed via `uv`. To add a package:

```bash
uv add <package>
```

This updates `pyproject.toml` automatically.

[README.md]: README.md
