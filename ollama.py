import pulumi

from src import compute
from src import dns
from src import storage

pulumi.export("instanceId", compute.instance.id)
pulumi.export("instancePublicIp", compute.instance.public_ip)
pulumi.export("eipPublicIp", compute.eip.public_ip)
pulumi.export("eipPublicDns", compute.eip.public_dns)
pulumi.export("volumeId", storage.volume.id)

if dns.record is not None:
    pulumi.export("dnsRecord", dns.record.name)
