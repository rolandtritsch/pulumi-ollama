import pulumi
import pulumi_aws as aws

from . import config

# Create a new VPC
vpc = aws.ec2.Vpc("ollama-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_support=True,
    enable_dns_hostnames=True,
    tags={"Name": "ollama-vpc"},
)

# Create an InternetGateway
internet_gateway = aws.ec2.InternetGateway("ollama-internetGateway",
    vpc_id=vpc.id,
    tags={"Name": "ollama-internetGateway"},
)

# Create a public Subnet
subnet = aws.ec2.Subnet("ollama-subnet",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    availability_zone=config.availability_zone,
    map_public_ip_on_launch=True,
    tags={"Name": "ollama-subnet"},
    opts=pulumi.ResourceOptions(delete_before_replace=True),
)

vpc_dns_resolver_cidr = "10.0.0.2/32"

# Create a RouteTable
route_table = aws.ec2.RouteTable("ollama-routeTable",
    vpc_id=vpc.id,
    routes=[{
        "cidr_block": "0.0.0.0/0",
        "gateway_id": internet_gateway.id,
    }],
    tags={"Name": "ollama-routeTable"},
)

# Associate the RouteTable with the subnet
route_table_association = aws.ec2.RouteTableAssociation("ollama-routeTableAssociation",
    subnet_id=subnet.id,
    route_table_id=route_table.id,
)
