from typing import List, Optional, Dict, Any
from kubiya_sdk.tools import Tool, Arg, FileSpec

AWS_ICON_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/9/93/Amazon_Web_Services_Logo.svg/2560px-Amazon_Web_Services_Logo.svg.png"

class AWSCliTool(Tool):
    """Base class for all AWS CLI tools that run in LocalStack and always inject Kubernetes context."""

    def __init__(self, name, description, content, args=None, image="amazon/aws-cli:latest"):
        # Step 1: Inject Kube context
        inject_kubernetes_context = """
set -eu
TOKEN_LOCATION="/tmp/kubernetes_context_token"
CERT_LOCATION="/tmp/kubernetes_context_cert"
if [ -f $TOKEN_LOCATION ] && [ -f $CERT_LOCATION ]; then
    KUBE_TOKEN=$(cat $TOKEN_LOCATION)
    kubectl config set-cluster in-cluster --server=https://kubernetes.default.svc \
                                          --certificate-authority=$CERT_LOCATION > /dev/null 2>&1
    kubectl config set-credentials in-cluster --token=$KUBE_TOKEN > /dev/null 2>&1
    kubectl config set-context in-cluster --cluster=in-cluster --user=in-cluster > /dev/null 2>&1
    kubectl config use-context in-cluster > /dev/null 2>&1
else
    echo "Kubernetes context token or cert not found."
    exit 1
fi
"""

        # Step 2: Set AWS + LocalStack environment
        aws_env = """
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
export AWS_ENDPOINT_URL=http://localstack.localstack.svc.cluster.local:4566
"""

        full_content = f"""
{inject_kubernetes_context}
{aws_env}
{content}
"""

        file_specs = [
            FileSpec(
                source="/var/run/secrets/kubernetes.io/serviceaccount/token",
                destination="/tmp/kubernetes_context_token"
            ),
            FileSpec(
                source="/var/run/secrets/kubernetes.io/serviceaccount/ca.crt",
                destination="/tmp/kubernetes_context_cert"
            )
        ]

        env_vars = [
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "AWS_DEFAULT_REGION",
            "AWS_ENDPOINT_URL"
        ]

        super().__init__(
            name=name,
            description=description,
            content=full_content,
            args=args or [],
            image=image,
            icon_url=AWS_ICON_URL,
            type="docker",
            env=env_vars,
            with_files=file_specs
        )

    def validate_args(self, args: Dict[str, Any]) -> bool:
        required_args = [arg.name for arg in self.args if arg.required]
        return all(arg in args and args[arg] for arg in required_args)

    def get_error_message(self, args: Dict[str, Any]) -> Optional[str]:
        missing = [arg.name for arg in self.args if arg.required and not args.get(arg.name)]
        return f"Missing required arguments: {', '.join(missing)}" if missing else None
