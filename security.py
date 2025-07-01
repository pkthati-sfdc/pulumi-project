import pulumi
import pulumi_aws as aws
from pulumi import ComponentResource, ResourceOptions

class SecurityGroupComponent(ComponentResource):
    def __init__(self, 
                 name: str,
                 vpc_id: pulumi.Input[str],
                 opts: ResourceOptions = None):
        super().__init__('custom:security:SecurityGroup', name, None, opts)

        # Create Security Group for web traffic
        self.security_group = aws.ec2.SecurityGroup(f'{name}-sg',
            vpc_id=vpc_id,
            description='Allow web traffic',
            ingress=[
                aws.ec2.SecurityGroupIngressArgs(
                    protocol='tcp',
                    from_port=80,
                    to_port=80,
                    cidr_blocks=['0.0.0.0/0'],
                ),
                aws.ec2.SecurityGroupIngressArgs(
                    protocol='tcp',
                    from_port=8080,
                    to_port=8080,
                    cidr_blocks=['0.0.0.0/0'],
                ),
            ],
            egress=[
                aws.ec2.SecurityGroupEgressArgs(
                    protocol='-1',
                    from_port=0,
                    to_port=0,
                    cidr_blocks=['0.0.0.0/0'],
                )
            ],
            opts=ResourceOptions(parent=self)
        )

        self.register_outputs({
            "security_group_id": self.security_group.id
        })