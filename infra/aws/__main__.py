import pulumi
import pulumi_aws as aws
cfg=pulumi.Config(); project=pulumi.get_project(); stack=pulumi.get_stack()
vpc=aws.ec2.Vpc("redpa-vpc",cidr_block="10.42.0.0/16",enable_dns_hostnames=True,tags={"Project":"RedPA-AI","Stack":stack})
logs=aws.cloudwatch.LogGroup("redpa-logs",retention_in_days=30)
cluster=aws.ecs.Cluster("redpa-cluster",settings=[{"name":"containerInsights","value":"enabled"}])
ecr=aws.ecr.Repository("redpa-backend",image_scanning_configuration={"scan_on_push":True},image_tag_mutability="IMMUTABLE")
pulumi.export("vpc_id",vpc.id); pulumi.export("cluster_arn",cluster.arn); pulumi.export("repository_url",ecr.repository_url); pulumi.export("log_group",logs.name)
