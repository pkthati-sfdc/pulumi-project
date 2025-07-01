import pulumi
import pulumi_aws as aws
from typing import List
import json
from pulumi import ComponentResource, ResourceOptions

class ECSClusterComponent(ComponentResource):
    def __init__(self, 
                 name: str, 
                 vpc_id: pulumi.Input[str],
                 subnet_ids: List[pulumi.Input[str]],
                 security_group_id: pulumi.Input[str],
                 image_uri: pulumi.Input[str],
                 target_group_arn: pulumi.Input[str],
                 app_message: str,
                 container_port: int = 8080,
                 opts: ResourceOptions = None):
        super().__init__('custom:compute:ECSCluster', name, None, opts)

        # Create ECS Task Execution Role
        self.task_execution_role = aws.iam.Role(f'{name}-task-execution-role',
            assume_role_policy=json.dumps({
                'Version': '2012-10-17',
                'Statement': [{
                    'Action': 'sts:AssumeRole',
                    'Effect': 'Allow',
                    'Principal': {
                        'Service': 'ecs-tasks.amazonaws.com'
                    }
                }]
            }),
            opts=ResourceOptions(parent=self)
        )

        # Attach ECS Task Execution Policy
        aws.iam.RolePolicyAttachment(
            f'{name}-task-execution-policy',
            role=self.task_execution_role.name,
            policy_arn='arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy',
            opts=ResourceOptions(parent=self)
        )

        # Add ECR and CloudWatch Logs permissions
        aws.iam.RolePolicy(
            f'{name}-additional-policy',
            role=self.task_execution_role.name,
            policy=json.dumps({
                'Version': '2012-10-17',
                'Statement': [{
                    'Effect': 'Allow',
                    'Action': [
                        'ecr:GetAuthorizationToken',
                        'ecr:BatchCheckLayerAvailability',
                        'ecr:GetDownloadUrlForLayer',
                        'ecr:BatchGetImage',
                        'logs:CreateLogStream',
                        'logs:PutLogEvents'
                    ],
                    'Resource': '*'
                }]
            }),
            opts=ResourceOptions(parent=self)
        )

        # Create ECS Cluster
        self.cluster = aws.ecs.Cluster(f'{name}-cluster',
            opts=ResourceOptions(parent=self)
        )

        # Create CloudWatch Log Group
        self.log_group = aws.cloudwatch.LogGroup(f'{name}-logs',
            name=f'/ecs/{name}',
            retention_in_days=30,
            opts=ResourceOptions(parent=self)
        )

        # Create ECS Task Definition
        self.task_definition = aws.ecs.TaskDefinition(f"{name}-task",
            family=f"{name}-task-definition",
            cpu="256",
            memory="512",
            network_mode="awsvpc",
            requires_compatibilities=["FARGATE"],
            execution_role_arn=self.task_execution_role.arn,
            container_definitions=pulumi.Output.all(image_uri).apply(
                lambda args: json.dumps([{
                    "name": f"{name}-container",
                    "image": args[0],
                    "portMappings": [{
                        "containerPort": container_port,
                        "protocol": "tcp"
                    }],
                    "environment": [{
                        "name": "APP_MESSAGE",
                        "value": app_message
                    }],
                    "logConfiguration": {
                        "logDriver": "awslogs",
                        "options": {
                            "awslogs-group": f"/ecs/{name}",
                            "awslogs-region": "us-east-1",
                            "awslogs-stream-prefix": "ecs"
                        }
                    }
                }])
            ),
            opts=ResourceOptions(parent=self)
        )

        # Create ECS Service
        self.service = aws.ecs.Service(f'{name}-service',
            cluster=self.cluster.id,
            desired_count=1,
            launch_type='FARGATE',
            task_definition=self.task_definition.arn,
            network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
                assign_public_ip=True,
                subnets=subnet_ids,
                security_groups=[security_group_id]
            ),
            load_balancers=[aws.ecs.ServiceLoadBalancerArgs(
                target_group_arn=target_group_arn,
                container_name=f"{name}-container",
                container_port=container_port
            )],
            opts=ResourceOptions(parent=self, depends_on=[self.task_definition])
        )

        self.register_outputs({
            "cluster_id": self.cluster.id,
            "service_name": self.service.name
        })