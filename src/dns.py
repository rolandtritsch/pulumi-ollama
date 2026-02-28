import pulumi_aws as aws

from . import compute

# Get the existing hosted zone for tritsch.org
zone = aws.route53.get_zone(name="tritsch.org.")

# Create/Update A record for ollama.tritsch.org pointing to the EIP
record = aws.route53.Record("ollama-dns-record",
    zone_id=zone.zone_id,
    name="ollama.tritsch.org",
    type="A",
    ttl=300,
    records=[compute.eip.public_ip],
)
