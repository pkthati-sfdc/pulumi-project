import pulumi_aws as aws
from pulumi import ComponentResource, ResourceOptions

# Base infrastructure Deployment
class VPCComponent(ComponentResource):
    def __init__(self, name: str, opts: ResourceOptions = None):
        super().__init__('custom:network:VPC', name, None, opts)

        # Create VPC
        self.vpc = aws.ec2.Vpc(
            f'{name}-vpc',
            cidr_block='10.0.0.0/16',
            enable_dns_hostnames=True,
            enable_dns_support=True,
            opts=ResourceOptions(parent=self)
        )

        # Create public subnets
        self.public_subnet_1 = aws.ec2.Subnet(
            f'{name}-public-subnet-1',
            vpc_id=self.vpc.id,
            cidr_block='10.0.1.0/24',
            availability_zone='us-east-1a',
            map_public_ip_on_launch=True,
            opts=ResourceOptions(parent=self)
        )

        self.public_subnet_2 = aws.ec2.Subnet(
            f'{name}-public-subnet-2',
            vpc_id=self.vpc.id,
            cidr_block='10.0.2.0/24',
            availability_zone='us-east-1b',
            map_public_ip_on_launch=True,
            opts=ResourceOptions(parent=self)
        )

        # Create Internet Gateway
        self.igw = aws.ec2.InternetGateway(
            f'{name}-igw',
            vpc_id=self.vpc.id,
            opts=ResourceOptions(parent=self)
        )

        # Create Route Table
        self.route_table = aws.ec2.RouteTable(
            f'{name}-rt',
            vpc_id=self.vpc.id,
            routes=[
                aws.ec2.RouteTableRouteArgs(
                    cidr_block='0.0.0.0/0',
                    gateway_id=self.igw.id,
                )
            ],
            opts=ResourceOptions(parent=self)
        )

        # Associate Route Table with Subnets
        self.rt_association_1 = aws.ec2.RouteTableAssociation(
            f'{name}-rta-1',
            subnet_id=self.public_subnet_1.id,
            route_table_id=self.route_table.id,
            opts=ResourceOptions(parent=self)
        )

        self.rt_association_2 = aws.ec2.RouteTableAssociation(
            f'{name}-rta-2',
            subnet_id=self.public_subnet_2.id,
            route_table_id=self.route_table.id,
            opts=ResourceOptions(parent=self)
        )

        self.register_outputs({
            "vpc_id": self.vpc.id,
            "public_subnet_ids": [self.public_subnet_1.id, self.public_subnet_2.id]
        })
