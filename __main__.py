import pulumi
from components.vpc import VPCComponent
from components.security import SecurityGroupComponent
from components.container_registry import ContainerRegistryComponent
from components.load_balancer import ApplicationLoadBalancerComponent
from components.ecs import ECSClusterComponent


def main():
    # Get configuration
    config = pulumi.Config()
    app_message = config.require('message')

    # Create VPC
    vpc = VPCComponent('main')

    # Create Security Group
    security = SecurityGroupComponent('webapp', vpc_id=vpc.vpc.id)

    # Create Container Registry and Build Image
    registry = ContainerRegistryComponent('webapp')

    # Create Load Balancer
    alb = ApplicationLoadBalancerComponent('webapp',
        vpc_id=vpc.vpc.id,
        subnet_ids=[vpc.public_subnet_1.id, vpc.public_subnet_2.id],
        security_group_id=security.security_group.id
    )

    # Create ECS Cluster
    ecs = ECSClusterComponent('webapp',
        vpc_id=vpc.vpc.id,
        subnet_ids=[vpc.public_subnet_1.id, vpc.public_subnet_2.id],
        security_group_id=security.security_group.id,
        image_uri=registry.image.image_uri,
        target_group_arn=alb.target_group.arn,
        app_message=app_message
    )

    # Export resource information
    pulumi.export('app_message', app_message)
    pulumi.export('application_lb_url', alb.alb.dns_name)
    pulumi.export('vpc_id', vpc.vpc.id)
    pulumi.export('cluster_id', ecs.cluster.id)
    pulumi.export('image_uri', registry.image.image_uri)

if __name__ == "__main__":
    main()
