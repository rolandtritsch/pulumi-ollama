# pulumi-ollama

A [Pulumi][] stack that runs [Ollama][] on a single AWS GPU instance. It is
intended for a private, allowlisted development service rather than a public
Ollama endpoint.

The stack creates:

- An EC2 GPU instance, defaulting to `g5.2xlarge` with one NVIDIA A10G GPU
- Encrypted `gp3` root and model-storage EBS volumes
- An Elastic IP and an IPv4 allowlist for SSH and the Ollama API
- An idempotent bootstrap process that installs Ollama and downloads models
- CloudWatch logs, host and GPU metrics, and a dashboard
- An optional Route 53 record

Model storage is disposable. Pulumi rebuilds the configured model baseline by
downloading models again when the volume is replaced.

> **Security:** Ollama listens over plain HTTP without authentication. The IP
> allowlist is the access boundary, and prompts and responses are not encrypted
> in transit. Do not expose this service to `0.0.0.0/0` or use it for sensitive
> data without adding a suitable authenticated TLS proxy.

## Before you run `make up`

Install [Pulumi][], [uv][], and the [AWS CLI][aws-cli]. Configure AWS
credentials and confirm which account and identity will receive the resources:

```bash
aws sts get-caller-identity
```

Install the Python project dependencies:

```bash
uv pip install -e .
```

Create a dedicated SSH key if you do not already have one. The Makefile uses
`~/.ssh/ollama-key` by default:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/ollama-key -C ollama
```

Keep the private key (`~/.ssh/ollama-key`) private and out of Git. Pulumi only
needs the public key (`~/.ssh/ollama-key.pub`).

Create or select a Pulumi stack:

```bash
pulumi stack init dev
# For an existing stack instead:
# pulumi stack select dev
```

Set the required configuration. Using your current public IP as a `/32` grants
access only from the network you are currently using:

```bash
pulumi config set aws:region eu-west-1
pulumi config set public_key_path ~/.ssh/ollama-key.pub
pulumi config set --path 'allowed_cidrs[0]' "$(curl -fsS https://checkip.amazonaws.com)/32"
```

Run the checks and inspect the proposed AWS changes before deploying:

```bash
make test
make preview
make up
make verify
```

Bootstrap includes the NVIDIA driver, Ollama, CloudWatch agent, and model
downloads, so the first deployment can take several minutes. Follow its
progress with `make logs-bootstrap`.

## Configuration

All deployment settings use `pulumi config`; there are no deployment settings
to edit directly in the source code.

| Key | Required | Default | Description |
| --- | --- | --- | --- |
| `aws:region` | Yes | None | AWS region in which to create the stack. |
| `public_key_path` | Yes | None | Local path to the SSH public key imported into EC2. `~` is supported. |
| `allowed_cidrs` | Yes | None | Nonempty list of IPv4 CIDRs allowed to use SSH and Ollama. IPv6 and `0.0.0.0/0` are rejected. |
| `models` | No | `qwen2.5-coder:0.5b` | Comma-separated Ollama model names downloaded during bootstrap. |
| `instance_type` | No | `g5.2xlarge` | EC2 instance type. It must be in the `g5` or `p4` family. |
| `availability_zone` | No | AWS-selected | Pins the subnet and EBS model volume to an Availability Zone, for example `eu-west-1c`. |
| `root_volume_size` | No | `200` | Encrypted root volume size in GiB; minimum 100. |
| `model_volume_size` | No | `500` | Encrypted model volume size in GiB; minimum 1. |
| `log_retention_days` | No | `30` | CloudWatch log retention using a [supported retention period][cloudwatch-retention]. |
| `dns_zone` | No | None | Existing Route 53 hosted-zone name, such as `example.com.`. Must be set with `dns_hostname`. |
| `dns_hostname` | No | None | Record name, such as `ollama.example.com`. Must be set with `dns_zone`. |

Examples:

```bash
# Use two baseline models.
pulumi config set models "qwen2.5-coder:0.5b,qwen3-coder:30b"

# Use a larger multi-GPU instance in a specific Availability Zone.
pulumi config set instance_type g5.12xlarge
pulumi config set availability_zone eu-west-1c

# Configure storage and log retention.
pulumi config set root_volume_size 250
pulumi config set model_volume_size 750
pulumi config set log_retention_days 90

# Add optional DNS.
pulumi config set dns_zone "example.com."
pulumi config set dns_hostname "ollama.example.com"
```

To add or change allowlist entries:

```bash
pulumi config set --path 'allowed_cidrs[0]' 198.51.100.25/32
pulumi config set --path 'allowed_cidrs[1]' 203.0.113.0/28
make preview
make up
```

Check your public IPv4 address before removing the network from which you
administer the instance.

## Choosing models

The best model depends on whether download speed, interactive speed, code
quality, or context size matters most. Model sizes below are approximate Ollama
downloads and can change with new releases.

| Model | Approximate size | Good fit | Notes |
| --- | ---: | --- | --- |
| [`qwen2.5-coder:0.5b`][qwen2.5-coder] | 0.4 GB | Any G5 | Default smoke-test model. Downloads quickly, but is not reliable enough for serious coding. |
| [`qwen3.5:9b`][qwen3.5] | 6.6 GB | One A10G | Fast, practical general model with useful coding ability. |
| [`qwen3.5:27b`][qwen3.5] | 17 GB | One A10G | Better quality while retaining comfortable room on a 24 GB GPU. |
| [`qwen3-coder:30b`][qwen3-coder] | 19 GB | One A10G | Strong coding-focused choice. Its memory use is tight with large contexts, so monitor GPU and system memory. |
| [`qwen3.5:35b`][qwen3.5] | 24 GB | Multi-GPU G5 | Too close to the capacity of a single 24 GB A10G once runtime and context memory are included. |
| [`qwen3-coder-next`][qwen3-coder-next] | 52 GB | `g5.12xlarge` | Larger coding model that needs substantially more aggregate GPU memory. |
| [`devstral-2:123b`][devstral-2] | 75 GB | `g5.12xlarge` | Large coding model; expect slower inference and higher cost. |
| [`qwen3.5:122b`][qwen3.5] | 81 GB | `g5.12xlarge` | Large general model with coding ability. |
| [`qwen3-coder:480b`][qwen3-coder] | 290 GB | `p4d.24xlarge` | Extremely expensive hardware requirement; usually impractical for this stack. |

Browse the [Ollama model library][ollama-library] for current tags and sizes.
Start with `qwen3.5:9b` or `qwen3.5:27b` for a balanced local model, and try
`qwen3-coder:30b` when coding quality is the priority on a single A10G.

### Pulumi baseline or manual model management?

Use `pulumi config set models ...` for models every replacement instance must
have. This is reproducible and works with `make verify`. Changing the model
configuration changes EC2 user data and can replace the instance. Bootstrap
downloads listed models but deliberately does not remove models that were added
manually.

For experiments, SSH into the running box and use Ollama directly:

```bash
make bash
ollama list
ollama pull qwen3.5:9b
ollama rm qwen3.5:9b
```

Once a model should be part of the durable baseline, put it in Pulumi config
and deploy the change.

## Choosing an instance type

GPU memory is normally the limiting factor. Increasing CPU and system RAM does
not make a larger model fit in GPU memory.

| Instance type | GPUs | Aggregate GPU memory | vCPUs | System memory | When to consider it |
| --- | --- | ---: | ---: | ---: | --- |
| `g5.2xlarge` | 1 A10G | 24 GB | 8 | 32 GiB | Default and lowest-cost option here for models that fit one A10G. |
| `g5.4xlarge` | 1 A10G | 24 GB | 16 | 64 GiB | More CPU and RAM, but no additional GPU memory. |
| `g5.8xlarge` | 1 A10G | 24 GB | 32 | 128 GiB | CPU/RAM-heavy workloads; still cannot fit a larger GPU-resident model. |
| `g5.12xlarge` | 4 A10G | 96 GB | 48 | 192 GiB | Larger 50–80 GB models and multi-GPU inference. |
| `g5.24xlarge` | 4 A10G | 96 GB | 96 | 384 GiB | More CPU/RAM than `g5.12xlarge`, with the same GPU capacity. |
| `p4d.24xlarge` | 8 A100 | 320 GB | 96 | 1,152 GiB | Very large models; substantially more expensive and often hard to obtain. |

See the AWS [G5][ec2-g5] and [P4][ec2-p4] specifications and check current
[EC2 On-Demand pricing][ec2-pricing] in the chosen region. GPU capacity varies
by Availability Zone. If AWS reports `InsufficientInstanceCapacity`, try a
different `availability_zone` or instance size. Changing Availability Zone
replaces the subnet and its Availability-Zone-bound model volume.

## Using the deployed service

Inspect outputs and wait for the configured models:

```bash
pulumi stack output
make verify
```

Send a request directly from an allowlisted machine:

```bash
EIP="$(pulumi stack output eipPublicIp)"
curl "http://${EIP}:11434/api/generate" \
  -H 'Content-Type: application/json' \
  -d '{"model":"qwen2.5-coder:0.5b","prompt":"Why is the sky blue?","stream":false}'
```

Run Codex against Ollama at the stack's Elastic IP:

```bash
make run-codex
```

The target uses `qwen2.5-coder:0.5b` by default. Select another installed model
with `OLLAMA_MODEL`:

```bash
make run-codex OLLAMA_MODEL=qwen3-coder:30b
```

`run-codex` creates an invocation-scoped Codex model provider, so it does not
modify `~/.codex/config.toml`. It connects directly over unauthenticated HTTP;
the machine running Codex must be in `allowed_cidrs`.

Or open an SSH tunnel in one terminal and use localhost from another:

```bash
make tunnel
curl http://localhost:11434/api/tags
```

Override the default private-key path when necessary:

```bash
make bash SSH_KEY=~/.ssh/another-key
make tunnel SSH_KEY=~/.ssh/another-key
```

The `ollama-list` and `ollama-run` Make targets invoke an Ollama client on your
local machine. Point `OLLAMA_HOST` at the server or an active tunnel before
using them; `make bash` is the simplest way to manage models remotely.

## Operations

Follow centralized bootstrap and service logs:

```bash
make logs-bootstrap
make logs-ollama
```

The `cloudwatchDashboard` stack output names the CloudWatch dashboard. The
stack creates logs and metrics but no alarms or notification channels.

Stop compute when it is not needed, then start it again later:

```bash
make instance-stop
make instance-start
```

The Elastic IP and EBS volumes continue to exist while the instance is stopped
and may still incur charges. After starting, the service may need a short time
to become ready; run `make verify`.

Destroy all stack resources, including the disposable model volume:

```bash
make destroy
```

## Replacement and recovery behavior

- Changing `models`, `instance_type`, or other EC2 bootstrap inputs can replace
  the instance. Always inspect `make preview`.
- Changing `availability_zone` replaces the subnet and model EBS volume because
  EBS volumes belong to one Availability Zone.
- A replacement instance recognizes and mounts an existing model filesystem
  when the volume remains compatible.
- When model storage is replaced, bootstrap downloads every configured model.
- Manually downloaded models are experiments, not part of the reproducible
  baseline, unless they are added to Pulumi config.

## Troubleshooting

- Run `make logs-bootstrap` when setup or a model download fails.
- Run `make logs-ollama` for service and inference failures.
- On the instance, the same logs are at `/var/log/ollama-setup.log` and
  `/var/log/ollama/ollama.log`.
- CloudWatch agent diagnostics are under
  `/opt/aws/amazon-cloudwatch-agent/logs/` and in the
  `CloudWatchAgentLogGroup` stack output.
- For an AWS capacity error, try another `availability_zone`, then run
  `make preview` before `make up`.
- If your public IP changes, update `allowed_cidrs` from a network that still
  has access, or update the Pulumi configuration before replacing the stack.

See [CLAUDE.md][] for repository structure and development guidance.

[Pulumi]: https://www.pulumi.com
[Ollama]: https://ollama.com
[ollama-library]: https://ollama.com/library
[qwen2.5-coder]: https://ollama.com/library/qwen2.5-coder
[qwen3-coder]: https://ollama.com/library/qwen3-coder
[qwen3-coder-next]: https://ollama.com/library/qwen3-coder-next
[qwen3.5]: https://ollama.com/library/qwen3.5
[devstral-2]: https://ollama.com/library/devstral-2
[uv]: https://docs.astral.sh/uv/
[aws-cli]: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
[cloudwatch-retention]: https://docs.aws.amazon.com/AmazonCloudWatchLogs/latest/APIReference/API_PutRetentionPolicy.html
[ec2-g5]: https://aws.amazon.com/ec2/instance-types/g5/
[ec2-p4]: https://aws.amazon.com/ec2/instance-types/p4/
[ec2-pricing]: https://aws.amazon.com/ec2/pricing/on-demand/
[CLAUDE.md]: CLAUDE.md
