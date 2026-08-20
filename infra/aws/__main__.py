import json

import pulumi
import pulumi_aws as aws


config = pulumi.Config()

stack = pulumi.get_stack()
region = aws.config.region or "eu-central-1"

jwt_secret_key = config.require_secret("jwt_secret_key")

project_tags = {
    "Project": "RedPA-AI",
    "Stack": stack,
    "Release": "19.2.0",
}


# ------------------------------------------------------------
# Existing V19 foundation
# ------------------------------------------------------------

vpc = aws.ec2.Vpc(
    "redpa-vpc",
    cidr_block="10.42.0.0/16",
    enable_dns_support=True,
    enable_dns_hostnames=True,
    tags=project_tags,
)

logs = aws.cloudwatch.LogGroup(
    "redpa-logs",
    retention_in_days=30,
    tags=project_tags,
)

cluster = aws.ecs.Cluster(
    "redpa-cluster",
    settings=[
        {
            "name": "containerInsights",
            "value": "enabled",
        }
    ],
    tags=project_tags,
)

ecr = aws.ecr.Repository(
    "redpa-backend",
    image_scanning_configuration={
        "scan_on_push": True,
    },
    image_tag_mutability="IMMUTABLE",
    tags=project_tags,
)


# ------------------------------------------------------------
# V19.2 public networking
# ------------------------------------------------------------

availability_zones = aws.get_availability_zones(
    state="available",
)

subnet_a = aws.ec2.Subnet(
    "redpa-public-a",
    vpc_id=vpc.id,
    cidr_block="10.42.10.0/24",
    availability_zone=availability_zones.names[0],
    map_public_ip_on_launch=True,
    tags={
        **project_tags,
        "Name": "redpa-public-a",
        "Tier": "public",
    },
)

subnet_b = aws.ec2.Subnet(
    "redpa-public-b",
    vpc_id=vpc.id,
    cidr_block="10.42.20.0/24",
    availability_zone=availability_zones.names[1],
    map_public_ip_on_launch=True,
    tags={
        **project_tags,
        "Name": "redpa-public-b",
        "Tier": "public",
    },
)

internet_gateway = aws.ec2.InternetGateway(
    "redpa-igw",
    vpc_id=vpc.id,
    tags=project_tags,
)

public_route_table = aws.ec2.RouteTable(
    "redpa-public-routes",
    vpc_id=vpc.id,
    routes=[
        {
            "cidr_block": "0.0.0.0/0",
            "gateway_id": internet_gateway.id,
        }
    ],
    tags=project_tags,
)

route_a = aws.ec2.RouteTableAssociation(
    "redpa-public-a-route",
    subnet_id=subnet_a.id,
    route_table_id=public_route_table.id,
)

route_b = aws.ec2.RouteTableAssociation(
    "redpa-public-b-route",
    subnet_id=subnet_b.id,
    route_table_id=public_route_table.id,
)


# ------------------------------------------------------------
# Security group
#
# V19.2 intentionally exposes the runtime directly on port
# 8000 for validation only. This is not the final production
# ingress architecture.
# ------------------------------------------------------------

backend_security_group = aws.ec2.SecurityGroup(
    "redpa-backend-sg",
    vpc_id=vpc.id,
    description="RedPA AI V19.2 backend runtime validation",
    ingress=[
        {
            "protocol": "tcp",
            "from_port": 8000,
            "to_port": 8000,
            "cidr_blocks": ["0.0.0.0/0"],
            "description": "Temporary V19.2 public runtime validation",
        }
    ],
    egress=[
        {
            "protocol": "-1",
            "from_port": 0,
            "to_port": 0,
            "cidr_blocks": ["0.0.0.0/0"],
        }
    ],
    tags=project_tags,
)


# ------------------------------------------------------------
# ECS task execution role
# ------------------------------------------------------------

execution_role = aws.iam.Role(
    "redpa-ecs-execution-role",
    name="redpa-ecs-execution-role",
    assume_role_policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "ecs-tasks.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole",
                }
            ],
        }
    ),
    tags=project_tags,
)

execution_role_attachment = aws.iam.RolePolicyAttachment(
    "redpa-ecs-execution-policy",
    role=execution_role.name,
    policy_arn=(
        "arn:aws:iam::aws:policy/"
        "service-role/AmazonECSTaskExecutionRolePolicy"
    ),
)


# ------------------------------------------------------------
# Fargate task definition
# ------------------------------------------------------------

image_uri = ecr.repository_url.apply(
    lambda repository_url:
        f"{repository_url}:v19.2.0"
)

task_definition = aws.ecs.TaskDefinition(
    "redpa-backend-task",
    family="redpa-backend-v192",
    cpu="256",
    memory="1024",
    network_mode="awsvpc",
    requires_compatibilities=["FARGATE"],
    execution_role_arn=execution_role.arn,
    container_definitions=pulumi.Output.all(
        image_uri,
        logs.name,
        jwt_secret_key,
    ).apply(
        lambda values: json.dumps(
            [
                {
                    "name": "redpa-backend",
                    "image": values[0],
                    "essential": True,
                    "portMappings": [
                        {
                            "containerPort": 8000,
                            "hostPort": 8000,
                            "protocol": "tcp",
                        }
                    ],
                    "environment": [
                        {
                            "name": "APP_NAME",
                            "value": "RedPA AI",
                        },
                        {
                            "name": "APP_VERSION",
                            "value": "19.2.0",
                        },
                        {
                            "name": "ENVIRONMENT",
                            "value": "development",
                        },
                        {
                            "name": "DEBUG",
                            "value": "false",
                        },
                        {
                            "name": "DATABASE_URL",
                            "value": (
                                "postgresql+asyncpg://"
                                "redpa:redpa@127.0.0.1:5432/redpa"
                            ),
                        },
                        {
                            "name": "JWT_SECRET_KEY",
                            "value": values[2],
                        },
                        {
                            "name": "QDRANT_URL",
                            "value": "http://127.0.0.1:6333",
                        },
                        {
                            "name": "REDIS_URL",
                            "value": "redis://127.0.0.1:6379/0",
                        },
                        {
                            "name": "OTEL_ENABLED",
                            "value": "false",
                        },
                        {
                            "name": "REQUIRE_HTTPS",
                            "value": "false",
                        },
                        {
                            "name": "ALLOWED_HOSTS",
                            "value": "*",
                        },
                    ],
                    "healthCheck": {
                        "command": [
                            "CMD-SHELL",
                            (
                                "curl -fsS "
                                "http://localhost:8000/"
                                "api/v1/platform/live "
                                "|| exit 1"
                            ),
                        ],
                        "interval": 30,
                        "timeout": 5,
                        "retries": 3,
                        "startPeriod": 30,
                    },
                    "logConfiguration": {
                        "logDriver": "awslogs",
                        "options": {
                            "awslogs-group": values[1],
                            "awslogs-region": region,
                            "awslogs-stream-prefix": "backend",
                        },
                    },
                    "dependsOn": [
                        {
                            "containerName": "redis",
                            "condition": "HEALTHY",
                        }
                    ],
                },
                {
                    "name": "redis",
                    "image": "redis:7-alpine",
                    "essential": True,
                    "portMappings": [
                        {
                            "containerPort": 6379,
                            "protocol": "tcp",
                        }
                    ],
                    "healthCheck": {
                        "command": [
                            "CMD-SHELL",
                            "redis-cli ping | grep PONG || exit 1",
                        ],
                        "interval": 10,
                        "timeout": 5,
                        "retries": 3,
                        "startPeriod": 10,
                    },
                    "logConfiguration": {
                        "logDriver": "awslogs",
                        "options": {
                            "awslogs-group": values[1],
                            "awslogs-region": region,
                            "awslogs-stream-prefix": "redis",
                        },
                    },
                }
            ]
        )
    ),
    tags=project_tags,
    opts=pulumi.ResourceOptions(
        depends_on=[
            execution_role_attachment,
        ]
    ),
)


# ------------------------------------------------------------
# ECS service
# ------------------------------------------------------------

service = aws.ecs.Service(
    "redpa-backend-service",
    name="redpa-backend-v192",
    cluster=cluster.arn,
    task_definition=task_definition.arn,
    desired_count=1,
    launch_type="FARGATE",
    network_configuration={
        "subnets": [
            subnet_a.id,
            subnet_b.id,
        ],
        "security_groups": [
            backend_security_group.id,
        ],
        "assign_public_ip": True,
    },
    deployment_minimum_healthy_percent=0,
    deployment_maximum_percent=100,
    tags=project_tags,
    opts=pulumi.ResourceOptions(
        depends_on=[
            route_a,
            route_b,
        ]
    ),
)


# ------------------------------------------------------------
# Outputs
# ------------------------------------------------------------

pulumi.export(
    "vpc_id",
    vpc.id,
)

pulumi.export(
    "cluster_arn",
    cluster.arn,
)

pulumi.export(
    "repository_url",
    ecr.repository_url,
)

pulumi.export(
    "log_group",
    logs.name,
)

pulumi.export(
    "public_subnet_a",
    subnet_a.id,
)

pulumi.export(
    "public_subnet_b",
    subnet_b.id,
)

pulumi.export(
    "backend_security_group",
    backend_security_group.id,
)

pulumi.export(
    "task_definition_arn",
    task_definition.arn,
)

pulumi.export(
    "backend_service_name",
    service.name,
)