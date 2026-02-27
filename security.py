import pulumi_aws as aws

import config
import network

# Create an AWS key pair
key_pair = aws.ec2.KeyPair("ollama-keyPair",
    public_key=config.public_key,
    tags={"Name": "ollama-keyPair"},
)

# Create a SecurityGroup
security_group = aws.ec2.SecurityGroup("ollama-securityGroup",
    vpc_id=network.vpc.id,
    ingress=[
        {"protocol": "tcp", "from_port": 22, "to_port": 22, "cidr_blocks": ["0.0.0.0/0"]},
        {"protocol": "tcp", "from_port": 11434, "to_port": 11434, "cidr_blocks": ["0.0.0.0/0"]},
    ],
    egress=[
        {"protocol": "tcp", "from_port": 80, "to_port": 80, "cidr_blocks": ["0.0.0.0/0"]},
        {"protocol": "tcp", "from_port": 443, "to_port": 443, "cidr_blocks": ["0.0.0.0/0"]},
    ],
    tags={"Name": "ollama-securityGroup"},
)
