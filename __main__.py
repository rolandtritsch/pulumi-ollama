import pulumi

import compute
import storage

pulumi.export("instanceId", compute.instance.id)
pulumi.export("instancePublicIp", compute.instance.public_ip)
pulumi.export("eipPublicIp", compute.eip.public_ip)
pulumi.export("eipPublicDns", compute.eip.public_dns)
pulumi.export("volumeId", storage.volume.id)
