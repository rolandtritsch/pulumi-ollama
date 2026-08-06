import json

import pulumi
import pulumi_aws as aws

from . import config


LOG_NAMES = ("bootstrap", "ollama", "system", "cloudwatch-agent")
log_group_names = {
    name: f"/ollama/{pulumi.get_stack()}/{name}"
    for name in LOG_NAMES
}

log_groups = {
    name: aws.cloudwatch.LogGroup(
        f"ollama-{name}-logs",
        name=log_group_names[name],
        retention_in_days=config.log_retention_days,
        tags={"Name": f"ollama-{name}-logs"},
    )
    for name in LOG_NAMES
}

role = aws.iam.Role(
    "ollama-instance-role",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "ec2.amazonaws.com"},
            "Action": "sts:AssumeRole",
        }],
    }),
    tags={"Name": "ollama-instance-role"},
)

_log_arns = [group.arn.apply(lambda arn: f"{arn}:*") for group in log_groups.values()]
policy = aws.iam.RolePolicy(
    "ollama-cloudwatch-policy",
    role=role.id,
    policy=pulumi.Output.all(*_log_arns).apply(lambda arns: json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["logs:CreateLogStream", "logs:DescribeLogStreams", "logs:PutLogEvents"],
                "Resource": arns,
            },
            {
                "Effect": "Allow",
                "Action": "cloudwatch:PutMetricData",
                "Resource": "*",
                "Condition": {"StringEquals": {"cloudwatch:namespace": "Ollama/Host"}},
            },
        ],
    })),
)

instance_profile = aws.iam.InstanceProfile(
    "ollama-instance-profile",
    role=role.name,
    tags={"Name": "ollama-instance-profile"},
)
