# pulumi-ollama

A [Pulumi][] stack that provisions a single AWS GPU instance for running large
language models with [Ollama][].

The stack provisions:

- A configurable EC2 instance, defaulting to `g5.2xlarge` with an NVIDIA A10G
- Encrypted root and model-storage EBS volumes
- An Elastic IP restricted to explicitly configured IPv4 networks
- Ollama installation, GPU inference, and configurable model downloads
- CloudWatch logs, host metrics, NVIDIA GPU metrics, and a dashboard

This is a single-node service. Model storage is disposable and is rebuilt by
downloading the configured models when necessary.

> **Security:** Ollama is served over plain HTTP and does not authenticate
> callers. The IP allowlist is the access boundary. Prompts and responses are
> not encrypted in transit, so use this stack only where that limitation is
> acceptable.

See [CLAUDE.md][] for repository structure and development guidance.

## Prerequisites

- [Pulumi][] installed and configured
- [uv][] installed
- AWS credentials configured, for example with the [AWS CLI][aws-cli]
- An SSH key pair such as `~/.ssh/ollama-key` and
  `~/.ssh/ollama-key.pub`

## Setup

```bash
uv pip install -e .
pulumi stack init dev
```

## Configuration

Set required deployment values through Pulumi config:

```bash
pulumi config set public_key_path ~/.ssh/ollama-key.pub
pulumi config set aws:region us-east-1
pulumi config set --path 'allowed_cidrs[0]' 203.0.113.10/32
```

The same allowlist controls SSH and Ollama. It must contain specific IPv4
CIDRs; empty lists, IPv6, malformed networks, and `0.0.0.0/0` are rejected.

Optional values and their defaults are:

```bash
pulumi config set models "deepseek-r1:8b,llama3.1:latest"
pulumi config set instance_type g5.2xlarge
pulumi config set root_volume_size 200
pulumi config set model_volume_size 500
pulumi config set log_retention_days 30
```

DNS is created only when both optional values are present:

```bash
pulumi config set dns_zone "example.com."
pulumi config set dns_hostname "ollama.example.com"
```

## Usage

Preview, deploy, and wait for Ollama and its configured models:

```bash
make preview
make up
make verify
```

SSH into the instance or open a local client tunnel:

```bash
make bash SSH_KEY=~/.ssh/ollama-key
make tunnel SSH_KEY=~/.ssh/ollama-key
```

The tunnel is a local client convenience; it does not add a security boundary
while port 11434 remains accessible to the configured allowlist.

Follow centralized setup or service logs:

```bash
make logs-bootstrap
make logs-ollama
```

The `cloudwatchDashboard` stack output contains the dashboard name. Logs are
retained for `log_retention_days`. The stack deliberately creates no alarms or
notification channels yet.

Stop and start the GPU instance to control compute costs:

```bash
make instance-stop
make instance-start
```

Destroy the complete stack, including disposable model storage and monitoring
resources:

```bash
make destroy
```

## Updating access

Change list entries through Pulumi config and redeploy:

```bash
pulumi config set --path 'allowed_cidrs[0]' 198.51.100.25/32
pulumi config set --path 'allowed_cidrs[1]' 203.0.113.0/28
make up
```

Check your current public IPv4 address before removing the address from which
you administer the instance.

## Troubleshooting

- Run `make logs-bootstrap` when initial setup or a model download fails.
- Run `make logs-ollama` for service and inference failures.
- The same logs remain available on the instance at
  `/var/log/ollama-setup.log` and `/var/log/ollama/ollama.log`.
- CloudWatch agent diagnostics are under
  `/opt/aws/amazon-cloudwatch-agent/logs/` and in the
  `CloudWatchAgentLogGroup` stack output.
- Instance replacement safely recognizes an existing filesystem, but normal
  recovery is to re-download all models from Pulumi configuration.

[Pulumi]: https://www.pulumi.com
[Ollama]: https://ollama.com
[uv]: https://docs.astral.sh/uv/
[aws-cli]: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
[CLAUDE.md]: CLAUDE.md
