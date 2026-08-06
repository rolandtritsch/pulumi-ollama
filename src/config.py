import os

import pulumi

from .validation import parse_models
from .validation import positive_int
from .validation import validate_allowed_cidrs
from .validation import validate_instance_type
from .validation import validate_log_retention

cfg = pulumi.Config()

device_name = "/dev/sdf"
volume_name = "ollama-volume"

public_key_path = cfg.require("public_key_path")
public_key = open(os.path.expanduser(public_key_path)).read().strip()

allowed_cidrs = validate_allowed_cidrs(cfg.require_object("allowed_cidrs"))
models = parse_models(cfg.get("models"))

instance_type_raw = cfg.get("instance_type")
instance_type = validate_instance_type("g5.2xlarge" if instance_type_raw is None else instance_type_raw)

root_volume_size_raw = cfg.get_int("root_volume_size")
root_volume_size = positive_int(
    "root_volume_size",
    200 if root_volume_size_raw is None else root_volume_size_raw,
    100,
)
model_volume_size_raw = cfg.get_int("model_volume_size")
model_volume_size = positive_int(
    "model_volume_size",
    500 if model_volume_size_raw is None else model_volume_size_raw,
)
log_retention_days_raw = cfg.get_int("log_retention_days")
log_retention_days = validate_log_retention(
    30 if log_retention_days_raw is None else log_retention_days_raw
)

dns_zone = cfg.get("dns_zone")
dns_hostname = cfg.get("dns_hostname")

if bool(dns_zone) != bool(dns_hostname):
    raise ValueError("dns_zone and dns_hostname must be configured together")
