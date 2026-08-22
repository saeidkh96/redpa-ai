import json
from urllib.parse import quote

import pulumi
import pulumi_aws as aws


config = pulumi.Config()

stack = pulumi.get_stack()
region = aws.config.region or "eu-central-1"

jwt_secret_key = config.require_secret("jwt_secret_key")
rds_password = config.require_secret("rds_password")

# ------------------------------------------------------------
# V20 stack-aware deployment identity
#
# The existing dev stack MUST preserve all V19 physical resource
# names to avoid replacements. The prod stack receives isolated
# V20 production resource names.
# ------------------------------------------------------------

is_prod = stack == "prod"

release_version = "20.0.0" if is_prod else "19.7.0"
runtime_environment = "production" if is_prod else "development"
runtime_image_tag = "v20.0.0" if is_prod else "v19.7.0"

# V20 production capacity / recovery boundaries.
#
# RDS remains Single-AZ with one-day backup retention by default
# because the current AWS account rejected higher retention under
# its present free-tier/account boundary.
prod_ecs_min_capacity = 2
prod_ecs_max_capacity = 4

prod_rds_multi_az = (
    config.get_bool("rds_multi_az")
    if is_prod
    else False
)

if prod_rds_multi_az is None:
    prod_rds_multi_az = False

prod_rds_backup_retention = (
    config.get_int("rds_backup_retention")
    if is_prod
    else 1
)

if prod_rds_backup_retention is None:
    prod_rds_backup_retention = 1

alert_email = config.get("alert_email") if is_prod else None

alb_name = "redpa-prod-v20-alb" if is_prod else "redpa-v194-alb"
target_group_name = (
    "redpa-prod-v20-backend"
    if is_prod
    else "redpa-v194-backend"
)

db_subnet_group_name = (
    "redpa-prod-v20-db-subnets"
    if is_prod
    else "redpa-v193-db-subnets"
)

database_identifier = (
    "redpa-prod-v20-postgres"
    if is_prod
    else "redpa-v193-postgres"
)

database_secret_name = (
    "redpa-prod-v20/database"
    if is_prod
    else "redpa-v193/database"
)

execution_role_name = (
    "redpa-prod-v20-ecs-execution-role"
    if is_prod
    else "redpa-ecs-execution-role"
)

task_family_name = (
    "redpa-prod-v20-backend"
    if is_prod
    else "redpa-backend-v192"
)

service_name = (
    "redpa-prod-v20-backend"
    if is_prod
    else "redpa-backend-v192"
)

ecs_cpu_alarm_name = (
    "redpa-prod-v20-ecs-cpu-high"
    if is_prod
    else "redpa-v196-ecs-cpu-high"
)

ecs_memory_alarm_name = (
    "redpa-prod-v20-ecs-memory-high"
    if is_prod
    else "redpa-v196-ecs-memory-high"
)

alb_unhealthy_alarm_name = (
    "redpa-prod-v20-alb-unhealthy-host"
    if is_prod
    else "redpa-v196-alb-unhealthy-host"
)

alb_5xx_alarm_name = (
    "redpa-prod-v20-alb-target-5xx"
    if is_prod
    else "redpa-v196-alb-target-5xx"
)

alb_latency_alarm_name = (
    "redpa-prod-v20-alb-response-time"
    if is_prod
    else "redpa-v196-alb-response-time"
)

rds_cpu_alarm_name = (
    "redpa-prod-v20-rds-cpu-high"
    if is_prod
    else "redpa-v196-rds-cpu-high"
)

rds_storage_alarm_name = (
    "redpa-prod-v20-rds-low-storage"
    if is_prod
    else "redpa-v196-rds-low-storage"
)

project_tags = {
    "Project": "RedPA-AI",
    "Stack": stack,
    "Release": release_version,
}

if is_prod:
    project_tags["Environment"] = runtime_environment


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
# V19.4 controlled application ingress
#
# Phase A keeps the temporary direct :8000 ingress available
# while ALB routing is validated.
# ------------------------------------------------------------

alb_security_group = aws.ec2.SecurityGroup(
    "redpa-alb-sg",
    vpc_id=vpc.id,
    description="RedPA AI V19.4 public ALB ingress",
    ingress=[
        {
            "protocol": "tcp",
            "from_port": 80,
            "to_port": 80,
            "cidr_blocks": ["0.0.0.0/0"],
            "description": "HTTP ingress to RedPA ALB",
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
    tags={
        **project_tags,
        "Name": "redpa-alb-sg",
        "Tier": "ingress",
    },
)

alb_to_backend_ingress = aws.ec2.SecurityGroupRule(
    "redpa-alb-to-backend-8000",
    type="ingress",
    security_group_id=backend_security_group.id,
    source_security_group_id=alb_security_group.id,
    protocol="tcp",
    from_port=8000,
    to_port=8000,
    description="RedPA ALB to ECS backend",
)

application_load_balancer = aws.lb.LoadBalancer(
    "redpa-alb",
    name=alb_name,
    load_balancer_type="application",
    internal=False,
    security_groups=[
        alb_security_group.id,
    ],
    subnets=[
        subnet_a.id,
        subnet_b.id,
    ],
    enable_deletion_protection=is_prod,
    tags={
        **project_tags,
        "Name": alb_name,
        "Tier": "ingress",
    },
)

backend_target_group = aws.lb.TargetGroup(
    "redpa-backend-tg",
    name=target_group_name,
    port=8000,
    protocol="HTTP",
    target_type="ip",
    vpc_id=vpc.id,
    deregistration_delay=30,
    health_check={
        "enabled": True,
        "protocol": "HTTP",
        "path": "/api/v1/platform/live",
        "port": "traffic-port",
        "healthy_threshold": 2,
        "unhealthy_threshold": 3,
        "interval": 30,
        "timeout": 5,
        "matcher": "200",
    },
    tags={
        **project_tags,
        "Name": target_group_name,
        "Tier": "ingress",
    },
)

http_listener = aws.lb.Listener(
    "redpa-http-listener",
    load_balancer_arn=application_load_balancer.arn,
    port=80,
    protocol="HTTP",
    default_actions=[
        {
            "type": "forward",
            "target_group_arn": backend_target_group.arn,
        }
    ],
    tags={
        **project_tags,
        "Name": "redpa-v194-http",
    },
)


# ------------------------------------------------------------
# V19.3 managed PostgreSQL data layer
#
# RDS is isolated from public ingress. The database is placed
# in dedicated subnets spanning two availability zones and
# accepts PostgreSQL traffic only from the ECS backend
# security group.
# ------------------------------------------------------------

db_subnet_a = aws.ec2.Subnet(
    "redpa-db-a",
    vpc_id=vpc.id,
    cidr_block="10.42.30.0/24",
    availability_zone=availability_zones.names[0],
    map_public_ip_on_launch=False,
    tags={
        **project_tags,
        "Name": "redpa-db-a",
        "Tier": "database",
    },
)

db_subnet_b = aws.ec2.Subnet(
    "redpa-db-b",
    vpc_id=vpc.id,
    cidr_block="10.42.40.0/24",
    availability_zone=availability_zones.names[1],
    map_public_ip_on_launch=False,
    tags={
        **project_tags,
        "Name": "redpa-db-b",
        "Tier": "database",
    },
)

db_subnet_group = aws.rds.SubnetGroup(
    "redpa-db-subnet-group",
    name=db_subnet_group_name,
    subnet_ids=[
        db_subnet_a.id,
        db_subnet_b.id,
    ],
    tags={
        **project_tags,
        "Name": db_subnet_group_name,
    },
)

db_security_group = aws.ec2.SecurityGroup(
    "redpa-db-sg",
    vpc_id=vpc.id,
    description="RedPA AI V19.3 PostgreSQL access from ECS only",
    ingress=[
        {
            "protocol": "tcp",
            "from_port": 5432,
            "to_port": 5432,
            "security_groups": [
                backend_security_group.id,
            ],
            "description": "PostgreSQL from RedPA ECS backend",
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
    tags={
        **project_tags,
        "Name": "redpa-db-sg",
        "Tier": "database",
    },
)

database = aws.rds.Instance(
    "redpa-postgres",
    identifier=database_identifier,
    engine="postgres",
    instance_class="db.t4g.micro",
    allocated_storage=20,
    storage_type="gp3",
    storage_encrypted=True,
    db_name="redpa",
    username="redpa",
    password=rds_password,
    port=5432,
    db_subnet_group_name=db_subnet_group.name,
    vpc_security_group_ids=[
        db_security_group.id,
    ],
    publicly_accessible=False,
    multi_az=prod_rds_multi_az,
    backup_retention_period=prod_rds_backup_retention,
    deletion_protection=True,
    copy_tags_to_snapshot=True,
    skip_final_snapshot=not is_prod,
    final_snapshot_identifier=(
        "redpa-prod-v20-final-snapshot"
        if is_prod
        else None
    ),
    auto_minor_version_upgrade=True,
    apply_immediately=True,
    tags={
        **project_tags,
        "Name": database_identifier,
        "Tier": "database",
    },
)

database_secret = aws.secretsmanager.Secret(
    "redpa-database-secret",
    name=database_secret_name,
    description="RedPA AI V19.3 managed PostgreSQL connection metadata",
    recovery_window_in_days=0,
    tags=project_tags,
)

database_secret_value = aws.secretsmanager.SecretVersion(
    "redpa-database-secret-value",
    secret_id=database_secret.id,
    secret_string=pulumi.Output.all(
        database.address,
        database.port,
        rds_password,
    ).apply(
        lambda values: json.dumps(
            {
                "engine": "postgresql",
                "host": values[0],
                "port": values[1],
                "database": "redpa",
                "username": "redpa",
                "password": values[2],
            }
        )
    ),
)

# ------------------------------------------------------------
# ECS task execution role
# ------------------------------------------------------------

execution_role = aws.iam.Role(
    "redpa-ecs-execution-role",
    name=execution_role_name,
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
        f"{repository_url}:{runtime_image_tag}"
)

task_definition = aws.ecs.TaskDefinition(
    "redpa-backend-task",
    family=task_family_name,
    cpu="256",
    memory="1024",
    network_mode="awsvpc",
    requires_compatibilities=["FARGATE"],
    execution_role_arn=execution_role.arn,
    container_definitions=pulumi.Output.all(
        image_uri,
        logs.name,
        jwt_secret_key,
        database.address,
        database.port,
        rds_password,
        application_load_balancer.dns_name,
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
                            "value": release_version,
                        },
                        {
                            "name": "ENVIRONMENT",
                            "value": runtime_environment,
                        },
                        {
                            "name": "DEBUG",
                            "value": "false",
                        },
                        {
                            "name": "DATABASE_URL",
                            "value": (
                                "postgresql+asyncpg://"
                                f"redpa:{quote(values[5], safe='')}@"
                                f"{values[3]}:{values[4]}/redpa"
                            ),
                        },
                        {
                            "name": "JWT_SECRET_KEY",
                            "value": values[2],
                        },
                        {
                            "name": "SECRET_KEY",
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
                            "value": (
                                values[6]
                                if is_prod
                                else "*"
                            ),
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
    name=service_name,
    cluster=cluster.arn,
    task_definition=task_definition.arn,
    load_balancers=[
        {
            "target_group_arn": backend_target_group.arn,
            "container_name": "redpa-backend",
            "container_port": 8000,
        }
    ],
    desired_count=prod_ecs_min_capacity if is_prod else 1,
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
    deployment_circuit_breaker={
        "enable": True,
        "rollback": True,
    },
    health_check_grace_period_seconds=60,
    availability_zone_rebalancing="ENABLED",
    deployment_minimum_healthy_percent=100,
    deployment_maximum_percent=200,
    tags=project_tags,
    opts=pulumi.ResourceOptions(
        depends_on=[
            route_a,
            route_b,
            http_listener,
        ],
        ignore_changes=(
            ["desired_count"]
            if is_prod
            else None
        ),
    ),
)



# ------------------------------------------------------------
# V20 production alerting and ECS service auto scaling
# ------------------------------------------------------------

production_alert_topic = None
production_alarm_actions = None
production_alert_subscription = None

ecs_scalable_target = None
ecs_cpu_scaling_policy = None
ecs_memory_scaling_policy = None

if is_prod:
    production_alert_topic = aws.sns.Topic(
        "redpa-production-alerts",
        name="redpa-prod-v20-alerts",
        tags={
            **project_tags,
            "Tier": "observability",
            "Purpose": "production-alerting",
        },
    )

    production_alarm_actions = [
        production_alert_topic.arn,
    ]

    if alert_email:
        production_alert_subscription = aws.sns.TopicSubscription(
            "redpa-production-alert-email",
            topic=production_alert_topic.arn,
            protocol="email",
            endpoint=alert_email,
        )

    ecs_scalable_target = aws.appautoscaling.Target(
        "redpa-backend-scalable-target",
        max_capacity=prod_ecs_max_capacity,
        min_capacity=prod_ecs_min_capacity,
        resource_id=pulumi.Output.concat(
            "service/",
            cluster.name,
            "/",
            service.name,
        ),
        scalable_dimension="ecs:service:DesiredCount",
        service_namespace="ecs",
    )

    ecs_cpu_scaling_policy = aws.appautoscaling.Policy(
        "redpa-backend-cpu-scaling",
        policy_type="TargetTrackingScaling",
        resource_id=ecs_scalable_target.resource_id,
        scalable_dimension=ecs_scalable_target.scalable_dimension,
        service_namespace=ecs_scalable_target.service_namespace,
        target_tracking_scaling_policy_configuration={
            "target_value": 60.0,
            "predefined_metric_specification": {
                "predefined_metric_type": (
                    "ECSServiceAverageCPUUtilization"
                ),
            },
            "scale_in_cooldown": 300,
            "scale_out_cooldown": 60,
        },
    )

    ecs_memory_scaling_policy = aws.appautoscaling.Policy(
        "redpa-backend-memory-scaling",
        policy_type="TargetTrackingScaling",
        resource_id=ecs_scalable_target.resource_id,
        scalable_dimension=ecs_scalable_target.scalable_dimension,
        service_namespace=ecs_scalable_target.service_namespace,
        target_tracking_scaling_policy_configuration={
            "target_value": 70.0,
            "predefined_metric_specification": {
                "predefined_metric_type": (
                    "ECSServiceAverageMemoryUtilization"
                ),
            },
            "scale_in_cooldown": 300,
            "scale_out_cooldown": 60,
        },
    )


# ------------------------------------------------------------
# V19.6 AWS observability
#
# CloudWatch alarms provide infrastructure-level visibility
# across ECS, ALB, and RDS. Alarm actions are intentionally
# omitted in this development validation environment; alarms
# remain visible in CloudWatch without requiring SNS/email
# notification infrastructure.
# ------------------------------------------------------------

ecs_cpu_high_alarm = aws.cloudwatch.MetricAlarm(
    "redpa-ecs-cpu-high",
    name=ecs_cpu_alarm_name,
    alarm_description=(
        "RedPA ECS backend CPU utilization is above 80 percent."
    ),
    namespace="AWS/ECS",
    metric_name="CPUUtilization",
    statistic="Average",
    period=300,
    evaluation_periods=2,
    datapoints_to_alarm=2,
    threshold=80,
    comparison_operator="GreaterThanThreshold",
    treat_missing_data="notBreaching",
    alarm_actions=production_alarm_actions,
    dimensions={
        "ClusterName": cluster.name,
        "ServiceName": service.name,
    },
    tags={
        **project_tags,
        "Tier": "observability",
        "Signal": "ecs-cpu",
    },
)

ecs_memory_high_alarm = aws.cloudwatch.MetricAlarm(
    "redpa-ecs-memory-high",
    name=ecs_memory_alarm_name,
    alarm_description=(
        "RedPA ECS backend memory utilization is above 80 percent."
    ),
    namespace="AWS/ECS",
    metric_name="MemoryUtilization",
    statistic="Average",
    period=300,
    evaluation_periods=2,
    datapoints_to_alarm=2,
    threshold=80,
    comparison_operator="GreaterThanThreshold",
    treat_missing_data="notBreaching",
    alarm_actions=production_alarm_actions,
    dimensions={
        "ClusterName": cluster.name,
        "ServiceName": service.name,
    },
    tags={
        **project_tags,
        "Tier": "observability",
        "Signal": "ecs-memory",
    },
)

alb_unhealthy_host_alarm = aws.cloudwatch.MetricAlarm(
    "redpa-alb-unhealthy-host",
    name=alb_unhealthy_alarm_name,
    alarm_description=(
        "RedPA ALB has one or more unhealthy backend targets."
    ),
    namespace="AWS/ApplicationELB",
    metric_name="UnHealthyHostCount",
    statistic="Maximum",
    period=60,
    evaluation_periods=2,
    datapoints_to_alarm=2,
    threshold=1,
    comparison_operator="GreaterThanOrEqualToThreshold",
    treat_missing_data="notBreaching",
    alarm_actions=production_alarm_actions,
    dimensions={
        "LoadBalancer": application_load_balancer.arn_suffix,
        "TargetGroup": backend_target_group.arn_suffix,
    },
    tags={
        **project_tags,
        "Tier": "observability",
        "Signal": "alb-health",
    },
)

alb_target_5xx_alarm = aws.cloudwatch.MetricAlarm(
    "redpa-alb-target-5xx",
    name=alb_5xx_alarm_name,
    alarm_description=(
        "RedPA backend returned at least five HTTP 5xx responses "
        "within a five-minute period."
    ),
    namespace="AWS/ApplicationELB",
    metric_name="HTTPCode_Target_5XX_Count",
    statistic="Sum",
    period=300,
    evaluation_periods=1,
    datapoints_to_alarm=1,
    threshold=5,
    comparison_operator="GreaterThanOrEqualToThreshold",
    treat_missing_data="notBreaching",
    alarm_actions=production_alarm_actions,
    dimensions={
        "LoadBalancer": application_load_balancer.arn_suffix,
        "TargetGroup": backend_target_group.arn_suffix,
    },
    tags={
        **project_tags,
        "Tier": "observability",
        "Signal": "alb-5xx",
    },
)

alb_response_time_alarm = aws.cloudwatch.MetricAlarm(
    "redpa-alb-response-time",
    name=alb_latency_alarm_name,
    alarm_description=(
        "RedPA ALB target response time is above two seconds."
    ),
    namespace="AWS/ApplicationELB",
    metric_name="TargetResponseTime",
    statistic="Average",
    period=300,
    evaluation_periods=2,
    datapoints_to_alarm=2,
    threshold=2,
    comparison_operator="GreaterThanThreshold",
    treat_missing_data="notBreaching",
    alarm_actions=production_alarm_actions,
    dimensions={
        "LoadBalancer": application_load_balancer.arn_suffix,
        "TargetGroup": backend_target_group.arn_suffix,
    },
    tags={
        **project_tags,
        "Tier": "observability",
        "Signal": "alb-latency",
    },
)

rds_cpu_high_alarm = aws.cloudwatch.MetricAlarm(
    "redpa-rds-cpu-high",
    name=rds_cpu_alarm_name,
    alarm_description=(
        "RedPA PostgreSQL CPU utilization is above 80 percent."
    ),
    namespace="AWS/RDS",
    metric_name="CPUUtilization",
    statistic="Average",
    period=300,
    evaluation_periods=2,
    datapoints_to_alarm=2,
    threshold=80,
    comparison_operator="GreaterThanThreshold",
    treat_missing_data="notBreaching",
    alarm_actions=production_alarm_actions,
    dimensions={
        "DBInstanceIdentifier": database_identifier,
    },
    tags={
        **project_tags,
        "Tier": "observability",
        "Signal": "rds-cpu",
    },
)

rds_low_storage_alarm = aws.cloudwatch.MetricAlarm(
    "redpa-rds-low-storage",
    name=rds_storage_alarm_name,
    alarm_description=(
        "RedPA PostgreSQL free storage is below two GiB."
    ),
    namespace="AWS/RDS",
    metric_name="FreeStorageSpace",
    statistic="Average",
    period=300,
    evaluation_periods=2,
    datapoints_to_alarm=2,
    threshold=2147483648,
    comparison_operator="LessThanThreshold",
    treat_missing_data="notBreaching",
    alarm_actions=production_alarm_actions,
    dimensions={
        "DBInstanceIdentifier": database_identifier,
    },
    tags={
        **project_tags,
        "Tier": "observability",
        "Signal": "rds-storage",
    },
)


# ------------------------------------------------------------
# Outputs
# ------------------------------------------------------------

if is_prod:
    pulumi.export(
        "production_alert_topic_arn",
        production_alert_topic.arn,
    )

    pulumi.export(
        "ecs_autoscaling_min_capacity",
        prod_ecs_min_capacity,
    )

    pulumi.export(
        "ecs_autoscaling_max_capacity",
        prod_ecs_max_capacity,
    )

    pulumi.export(
        "runtime_environment",
        runtime_environment,
    )


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

pulumi.export(
    "alb_dns_name",
    application_load_balancer.dns_name,
)

pulumi.export(
    "alb_arn",
    application_load_balancer.arn,
)

pulumi.export(
    "backend_target_group_arn",
    backend_target_group.arn,
)

pulumi.export(
    "alb_security_group",
    alb_security_group.id,
)

pulumi.export(
    "db_subnet_a",
    db_subnet_a.id,
)

pulumi.export(
    "db_subnet_b",
    db_subnet_b.id,
)

pulumi.export(
    "db_security_group",
    db_security_group.id,
)

pulumi.export(
    "database_endpoint",
    database.endpoint,
)

pulumi.export(
    "database_secret_arn",
    database_secret.arn,
)
