# pulumi-ollama

A [Pulumi][] stack that provisions an AWS EC2 instance to run large language models via [Ollama][].

The idea is to run models that are too large for a laptop — for example, `deepseek-r1:70b` requires ~45 GB of VRAM.

The stack provisions:

- A `g5.2xlarge` EC2 instance (NVIDIA A10G, 24 GB VRAM) running the Deep Learning Base GPU AMI (Ubuntu 22.04)
- A 500 GB EBS volume for model storage
- A public Elastic IP so the instance is reachable from anywhere
- Ollama installed and started automatically on boot, with GPU inference enabled
- One or more models pre-pulled, configurable via `pulumi config`

See [CLAUDE.md][] for the repo structure and developer workflow.

## Prerequisites

- [Pulumi][] installed and configured
- [uv][] installed (Python toolchain)
- AWS credentials configured (e.g. via [aws-cli][])
- An SSH key pair (e.g. `~/.ssh/ollama-key` / `~/.ssh/ollama-key.pub`):

```bash
cd ~/.ssh
ssh-keygen -t ed25519 -f ollama-key
```

## Setup

Install Python dependencies into the local virtual environment:

```bash
uv pip install -e .
```

Create a Pulumi stack (name it whatever you like, e.g. `dev`):

```bash
pulumi stack init dev
```

## Configuration

Set the required and optional config values before deploying.

### Required

```bash
# Path to your SSH public key
pulumi config set public_key_path ~/.ssh/ollama-key.pub

# AWS region to deploy into
pulumi config set aws:region us-east-1
```

### Optional

```bash
# Models to pre-pull (comma-separated); default: llama3.2:latest
pulumi config set models "deepseek-r1:8b,llama3.1:latest"

# Route53 DNS zone and hostname (omit both to skip DNS record creation)
pulumi config set dns_zone "example.com."
pulumi config set dns_hostname "ollama.example.com"
```

## Usage

### Deploy

```bash
make up
```

### Check the instance is running

```bash
curl http://$(pulumi stack output eipPublicIp):11434
```

The response should be `Ollama is running`.

### SSH into the instance

```bash
make bash SSH_KEY=~/.ssh/ollama-key
```

Or set `SSH_KEY` in your environment to avoid passing it every time:

```bash
export SSH_KEY=~/.ssh/ollama-key
make bash
```

### Open a local tunnel

Forward `localhost:11434` to the remote Ollama service:

```bash
make tunnel SSH_KEY=~/.ssh/ollama-key
```

### Start / stop the instance

To save costs when not in use:

```bash
make instance-stop
make instance-start
```

### Tear down

```bash
make destroy
```

## Troubleshooting

- **Model pull fails on first boot** — SSH into the instance and pull manually:

  ```bash
  ollama pull deepseek-r1:8b
  ```

- **EBS volume attached to wrong device** — Run `lsblk` on the instance to find the correct device, then mount it manually.

- **Setup logs** — The `user_data.sh` script writes to `/var/log/ollama-setup.log` on the instance.

[Pulumi]: https://www.pulumi.com
[Ollama]: https://ollama.com
[uv]: https://docs.astral.sh/uv/
[aws-cli]: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
[CLAUDE.md]: CLAUDE.md
