# Developer Guide

This guide describes repository structure and verification. See [README.md][]
for deployment and operator usage.

## Project structure

```text
pulumi-ollama/
├── Pulumi.yaml          # Pulumi Python and uv project metadata
├── pyproject.toml       # Python dependencies
├── ollama.py            # Entry point and stack outputs
├── Makefile             # Operator and verification commands
├── scripts/verify.py    # End-to-end readiness check
├── tests/               # Config and rendered-bootstrap tests
└── src/
    ├── config.py        # Pulumi configuration
    ├── validation.py    # Pure configuration validation helpers
    ├── network.py       # VPC, subnet, gateway, and route table
    ├── security.py      # Key pair and allowlisted security group
    ├── storage.py       # Encrypted model volume
    ├── monitoring.py    # Log groups and least-privilege instance IAM
    ├── compute.py       # EC2, attachment, EIP, and user-data rendering
    ├── dashboard.py     # CloudWatch dashboard
    ├── dns.py           # Optional Route53 record
    └── user_data.sh     # Idempotent instance bootstrap
```

The resource dependency graph is:

```text
validation → config
                ↓
           network → security
                ↓         ↓
           storage   monitoring
                └────┬────┘
                     ↓
                  compute → dns
                     ↓
                 dashboard
                     ↓
                  ollama.py
```

Keep implementation files under 400 lines where practical.

## Making changes

Edit the layer that owns the behavior:

- Networking and routes: `src/network.py`
- Inbound access and SSH key registration: `src/security.py`
- EBS resource properties and mount behavior: `src/storage.py` and
  `src/user_data.sh`
- Instance, AMI, or bootstrap wiring: `src/compute.py`
- Logs, instance IAM, metrics, or dashboard: `src/monitoring.py` and
  `src/dashboard.py`
- DNS: `src/dns.py`

Deployment settings belong in Pulumi config. Do not add environment-variable or
source-edit configuration for deployed infrastructure. Keep genuine internal
invariants in code until operators need to configure them.

`allowed_cidrs` is a required Pulumi list shared by SSH and Ollama:

```bash
pulumi config set --path 'allowed_cidrs[0]' 203.0.113.10/32
```

Model names remain a comma-separated Pulumi value:

```bash
pulumi config set models "qwen2.5-coder:0.5b"
```

The current AMI is resolved dynamically from the latest AWS Deep Learning Base
OSS NVIDIA Driver GPU AMI for Ubuntu 22.04. The instance type, optional
availability zone, volume sizes, and CloudWatch retention are Pulumi settings
with documented defaults.

## Verification

Run local tests and syntax checks:

```bash
make test
uv run python -m compileall -q ollama.py src scripts tests
bash -n src/user_data.sh
```

Run a Pulumi preview against configured AWS credentials:

```bash
make preview
```

Expected resources include the network, key pair, allowlisted security group,
encrypted EBS volumes, EC2 instance, EIP, least-privilege IAM profile, four log
groups, and CloudWatch dashboard. DNS exists only when both DNS settings are
configured.

The `[build-system]` table in `pyproject.toml` is required: Pulumi's Python
runtime (with `toolchain: uv`) invokes the venv's interpreter directly rather
than through `uv run`, so it does not add the project root to `sys.path`.
Without `[build-system]`, `uv sync` treats this as a non-buildable project and
never installs `src` into the venv, so `from src import compute` fails with
`ModuleNotFoundError` only when run through `pulumi preview`/`pulumi up` —
plain `uv run python ollama.py` will not reproduce it, since `uv run` does add
the project root.

For end-to-end verification:

```bash
make up
make verify
```

From a client outside the configured allowlist, confirm TCP ports 22 and 11434
are unreachable. In CloudWatch, confirm bootstrap, Ollama, system, and agent
logs arrive and that `Ollama/Host` contains CPU, memory, disk, process, network,
and NVIDIA GPU metrics.

## Dependencies

Dependencies are managed with [uv][]:

```bash
uv add <package>
```

[README.md]: README.md
[uv]: https://docs.astral.sh/uv/
