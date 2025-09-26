from typing import List, Optional, Dict, Any
from kubiya_sdk.tools import Tool, Arg, FileSpec

AWS_ICON_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/9/93/Amazon_Web_Services_Logo.svg/2560px-Amazon_Web_Services_Logo.svg.png"

class AWSCliTool(Tool):
    """Base AWS CLI tool for LocalStack with Kubernetes context injection."""

    def __init__(self, name, description, content, args=None, image="amazon/aws-cli:latest"):
        setup_script = """
set -eu

# Install kubectl for Kubernetes context setup (Amazon Linux uses yum)
yum update -y -q
yum install -y -q curl
curl -LO "https://dl.k8s.io/release/v1.27.1/bin/linux/amd64/kubectl"
chmod +x kubectl
mv kubectl /usr/local/bin/

# Inject Kubernetes context for LocalStack communication
TOKEN_LOCATION="/tmp/kubernetes_context_token"
CERT_LOCATION="/tmp/kubernetes_context_cert"
if [ -f $TOKEN_LOCATION ] && [ -f $CERT_LOCATION ]; then
    KUBE_TOKEN=$(cat $TOKEN_LOCATION)
    mkdir -p ~/.kube
    kubectl config set-cluster in-cluster --server=https://kubernetes.default.svc \
        --certificate-authority=$CERT_LOCATION >/dev/null 2>&1
    kubectl config set-credentials in-cluster --token=$KUBE_TOKEN >/dev/null 2>&1
    kubectl config set-context in-cluster --cluster=in-cluster --user=in-cluster >/dev/null 2>&1
    kubectl config use-context in-cluster >/dev/null 2>&1
else
    echo "Warning: Kubernetes context files not found, LocalStack communication may fail"
fi
"""

        full_content = f"{setup_script}\n{content}"

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

        super().__init__(
            name=name,
            description=description,
            content=full_content,
            args=args or [],
            image=image,
            icon_url=AWS_ICON_URL,
            type="docker",
            with_files=file_specs,
            env=["AWS_ACCESS_KEY_ID","AWS_SECRET_ACCESS_KEY","AWS_DEFAULT_REGION","AWS_ENDPOINT_URL"]
        )

    def validate_args(self, args: Dict[str, Any]) -> bool:
        required_args = [arg.name for arg in self.args if arg.required]
        return all(arg in args and args[arg] for arg in required_args)

    def get_error_message(self, args: Dict[str, Any]) -> Optional[str]:
        missing = [arg.name for arg in self.args if arg.required and not args.get(arg.name)]
        return f"Missing required arguments: {', '.join(missing)}" if missing else None
