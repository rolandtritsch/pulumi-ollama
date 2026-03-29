import pulumi_aws as aws

from . import compute
from . import config

record = None

if config.dns_zone and config.dns_hostname:
    zone = aws.route53.get_zone(name=config.dns_zone)

    record = aws.route53.Record("ollama-dns-record",
        zone_id=zone.zone_id,
        name=config.dns_hostname,
        type="A",
        ttl=300,
        records=[compute.eip.public_ip],
    )
