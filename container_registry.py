import pulumi_aws as aws
import pulumi_awsx as awsx
from pulumi import ComponentResource, ResourceOptions

class ContainerRegistryComponent(ComponentResource):
    def __init__(self, name: str, context_path: str = "./app", opts: ResourceOptions = None):
        super().__init__('custom:container:Registry', name, None, opts)

        # Create ECR repository
        self.repository = aws.ecr.Repository(f"{name}-repo",
            force_delete=True,
            opts=ResourceOptions(parent=self)
        )

        # Build and push image
        self.image = awsx.ecr.Image(f"{name}-image",
            repository_url=self.repository.repository_url,
            context=context_path,
            dockerfile=f"{context_path}/Dockerfile",
            platform="linux/amd64",
            opts=ResourceOptions(parent=self)
        )

        self.register_outputs({
            "repository_url": self.repository.repository_url,
            "image_uri": self.image.image_uri
        })