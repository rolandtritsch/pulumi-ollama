# Developer Guide

This file covers the structure of the repo and how to make and verify changes. See [README.md][] for user-facing documentation.

## Project Structure

```
pulumi-ollama/
├── Pulumi.yaml          # Pulumi project metadata (Python + uv)
├── pyproject.toml       # Python dependencies (managed by uv)
├── __main__.py          # Entry point; exports stack outputs
├── config.py            # Shared constants and Pulumi config values
├── network.py           # VPC, IGW, subnet, route table
├── security.py          # Key pair and security group
├── compute.py           # EC2 instance and Elastic IP
├── storage.py           # EBS volume and attachment
├── Makefile             # Convenience targets: up, destroy, help
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
    ↓
__main__.py →  stack exports
```

## File Size Limit

Keep each source file under 400 lines of code.

## Making Changes

### Adding or changing resources

Each layer is isolated to its own module. Edit the relevant file:

- Networking changes → `network.py`
- Firewall / SSH key changes → `security.py`
- Instance type, AMI, user-data → `compute.py`
- EBS volume size or device → `storage.py` / `config.py`

### Changing the models to pull

Models are configured at the Pulumi stack level, not in code:

```bash
pulumi config set models "deepseek-r1:8b,llama3.1:latest"
```

The default (if not set) is `llama3.2:latest`. The value is a comma-separated list; `compute.py` splits it and loops over each entry in the `userData` script.

### Changing instance type or AMI

Edit `compute.py`. The current values are:

- AMI: `ami-0da39a8bb51a828e3` (Ubuntu 22.04, us-east-1)
- Instance type: `m5.2xlarge`

## Verifying Changes

### Syntax check

```bash
uv run python -c "import __main__"
```

### Pulumi preview (no AWS changes)

```bash
pulumi preview
```

Expected resources: VPC, IGW, subnet, route table, route table association, key pair, security group, EC2 instance, EIP, EBS volume, volume attachment.

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
