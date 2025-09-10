from typing import List, Optional, Dict, Any
from kubiya_sdk.tools import Tool, Arg, FileSpec

AWS_ICON_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/9/93/Amazon_Web_Services_Logo.svg/2560px-Amazon_Web_Services_Logo.svg.png"

class AWSCliTool(Tool):
    """AWS CLI Tool for LocalStack. Injects kube context + installs aws-cli and kubectl. No env var values hardcoded."""

    def __init__(self, name, description, content, args=None, image="alpine"):
        setup_script = """
set -eu

# Inject Kubernetes context from service account
TOKEN_LOCATION="/tmp/kubernetes_context_token"
CERT_LOCATION="/tmp/kubernetes_context_cert"
if [ -f $TOKEN_LOCATION ] && [ -f $CERT_LOCATION ]; then
    echo "Injecting Kubernetes context..."
    KUBE_TOKEN=$(cat $TOKEN_LOCATION)
    mkdir -p ~/.kube
    kubectl config set-cluster in-cluster --server=https://kubernetes.default.svc \
                                          --certificate-authority=$CERT_LOCATION > /dev/null 2>&1
    kubectl config set-credentials in-cluster --token=$KUBE_TOKEN > /dev/null 2>&1
    kubectl config set-context in-cluster --cluster=in-cluster --user=in-cluster > /dev/null 2>&1
    kubectl config use-context in-cluster > /dev/null 2>&1
else
    echo "ERROR: Kubernetes context token or cert not found."
    exit 1
fi

# Install AWS CLI and kubectl
echo "Installing AWS CLI and kubectl..."
apk add --no-cache curl unzip bash >/dev/null

curl -s "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip -q awscliv2.zip
./aws/install >/dev/null
rm -rf awscliv2.zip aws

curl -sLO "https://dl.k8s.io/release/v1.27.1/bin/linux/amd64/kubectl"
install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
rm -f kubectl

# Debug output (no hardcoded values)
echo "Kubernetes and AWS CLI are ready."
echo "AWS CLI version: $(aws --version)"
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

        # No env values passed here — Kubiya will inject them
        super().__init__(
            name=name,
            description=description,
            content=full_content,
            args=args or [],
            image=image,
            icon_url=AWS_ICON_URL,
            type="docker",
            with_files=file_specs,
        )

    def validate_args(self, args: Dict[str, Any]) -> bool:
        required_args = [arg.name for arg in self.args if arg.required]
        return all(arg in args and args[arg] for arg in required_args)

    def get_error_message(self, args: Dict[str, Any]) -> Optional[str]:
        missing = [arg.name for arg in self.args if arg.required and not args.get(arg.name)]
        return f"Missing required arguments: {', '.join(missing)}" if missing else None
