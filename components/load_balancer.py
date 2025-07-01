import pulumi
import pulumi_aws as aws
from typing import List
from pulumi import ComponentResource, ResourceOptions

class ApplicationLoadBalancerComponent(ComponentResource):
    def __init__(self, 
                 name: str,
                 vpc_id: pulumi.Input[str],
                 subnet_ids: List[pulumi.Input[str]],
                 security_group_id: pulumi.Input[str],
                 opts: ResourceOptions = None):
        super().__init__('custom:network:ALB', name, None, opts)

        # Create ALB
        self.alb = aws.lb.LoadBalancer(f'{name}-alb',
            internal=False,
            load_balancer_type="application",
            security_groups=[security_group_id],
            subnets=subnet_ids,
            opts=ResourceOptions(parent=self)
        )

        # Create Target Group
        self.target_group = aws.lb.TargetGroup(f'{name}-tg',
            port=80,
            protocol="HTTP",
            target_type="ip",
            vpc_id=vpc_id,
            health_check={
                "enabled": True,
                "healthy_threshold": 2,
                "interval": 30,
                "path": "/",
                "port": "traffic-port",
                "protocol": "HTTP",
                "timeout": 5,
                "unhealthy_threshold": 2,
            },
            opts=ResourceOptions(parent=self)
        )

        # Create Listener
        self.listener = aws.lb.Listener(f'{name}-listener',
            load_balancer_arn=self.alb.arn,
            port=80,
            default_actions=[{
                "type": "forward",
                "target_group_arn": self.target_group.arn
            }],
            opts=ResourceOptions(parent=self)
        )

        self.register_outputs({
            "alb_dns_name": self.alb.dns_name,
            "target_group_arn": self.target_group.arn
        })
