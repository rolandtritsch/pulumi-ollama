import ipaddress
import re


_MODEL_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$")
_INSTANCE_TYPE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9.-]*$")
_LOG_RETENTION_VALUES = {
    1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731,
    1096, 1827, 2192, 2557, 2922, 3288, 3653,
}


def validate_allowed_cidrs(value: object) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ValueError("allowed_cidrs must be a non-empty list of IPv4 CIDRs")

    networks: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise ValueError("allowed_cidrs entries must be strings")
        if "/" not in item:
            raise ValueError(f"allowed CIDR {item!r} must include a prefix length")
        try:
            network = ipaddress.ip_network(item, strict=True)
        except ValueError as error:
            raise ValueError(f"invalid allowed CIDR {item!r}: {error}") from error
        if network.version != 4:
            raise ValueError(f"IPv6 CIDR {item!r} is not supported")
        if network.prefixlen == 0:
            raise ValueError("allowed_cidrs must not expose the service to 0.0.0.0/0")
        networks.append(str(network))

    return networks


def parse_models(value: str | None) -> list[str]:
    raw_models = ("llama3.2:latest" if value is None else value).split(",")
    models = [model.strip() for model in raw_models]
    if not models or any(not model or not _MODEL_PATTERN.fullmatch(model) for model in models):
        raise ValueError("models must be a comma-separated list of valid Ollama model names")
    return models


def positive_int(name: str, value: int, minimum: int = 1) -> int:
    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    return value


def validate_instance_type(value: str) -> str:
    if not _INSTANCE_TYPE_PATTERN.fullmatch(value):
        raise ValueError("instance_type is not a valid EC2 instance type")
    return value


def validate_log_retention(value: int) -> int:
    if value not in _LOG_RETENTION_VALUES:
        raise ValueError("log_retention_days must be a CloudWatch Logs retention value")
    return value
