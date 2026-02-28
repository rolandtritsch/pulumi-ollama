# pulumi-ollama

A [Pulumi][] stack that provisions an AWS EC2 instance to run large language models via [Ollama][].

The idea is to run models that are too large for a laptop — for example, `deepseek-r1:70b` requires ~45 GB of RAM.

The stack provisions:

- An `m5.2xlarge` EC2 instance (32 GB RAM) running Ubuntu 22.04
- A 500 GB EBS volume for model storage
- A public Elastic IP so the instance is reachable from anywhere
- Ollama installed and started automatically on boot
- One or more models pre-pulled, configurable via `pulumi config`

See [CLAUDE.md][] for the repo structure and developer workflow.

## Prerequisites

- [Pulumi][] installed and configured
- [uv][] installed (Python toolchain)
- AWS credentials configured (e.g. via [aws-cli][])
- An SSH key pair at `~/.ssh/aws-roland` / `~/.ssh/aws-roland.pub`:

```bash
cd ~/.ssh
ssh-keygen -t rsa -b 2048 -f aws-roland
```

## Setup

Install the Python dependencies into the local virtual environment before running any Pulumi commands:

```bash
uv pip install -e .
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
ssh -i ~/.ssh/aws-roland ubuntu@$(pulumi stack output eipPublicIp)
```

### Tear down

```bash
make destroy
```

## Configuring models

By default the stack pulls `llama3.2:latest`. To pull different models, set the `models` config key (comma-separated) before deploying:

```bash
pulumi config set models "deepseek-r1:8b,llama3.1:latest"
make up
```

## Troubleshooting

- **Model pull fails on first boot** — SSH into the instance and pull manually:

  ```bash
  ollama pull deepseek-r1:8b
  ```

- **EBS volume attached to wrong device** — Run `lsblk` on the instance to find the correct device, then mount it manually.

[Pulumi]: https://www.pulumi.com
[Ollama]: https://ollama.com
[uv]: https://docs.astral.sh/uv/
[aws-cli]: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
[CLAUDE.md]: CLAUDE.md
