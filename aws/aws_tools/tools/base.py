from typing import List, Optional, Dict, Any
from kubiya_sdk.tools import Tool, Arg, FileSpec

AWS_ICON_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/9/93/Amazon_Web_Services_Logo.svg/2560px-Amazon_Web_Services_Logo.svg.png"

DEFAULT_MERMAID = """
```mermaid
classDiagram
    class Tool {
        <<interface>>
        +get_args()
        +get_content()
        +get_image()
    }
    class AWSCliTool {
        -content: str
        -args: List[Arg]
        -image: str
        +__init__(name, description, content, args, image)
        +get_args()
        +get_content()
        +get_image()
        +get_file_specs()
        +validate_args(args)
        +get_error_message(args)
        +get_environment()
    }
    Tool <|-- AWSCliTool
```
"""

class AWSCliTool(Tool):
    """Base class for all AWS CLI tools."""
    
    name: str
    description: str
    content: str = ""
    args: List[Arg] = []
    image: str = "amazon/aws-cli:latest"
    icon_url: str = AWS_ICON_URL
    type: str = "docker"
    mermaid: str = DEFAULT_MERMAID
    
    def __init__(self, name, description, content, args=None, image="amazon/aws-cli:latest"):
        # AWS credentials and config setup
        aws_setup = """
set -eu
# AWS credentials and config are mounted via with_files
if [ -f /root/.aws/credentials ] && [ -f /root/.aws/config ]; then
    echo "AWS credentials and config found"
else
    echo "Warning: AWS credentials or config not found"
fi
"""
        full_content = f"{aws_setup}\n{content}"

        file_specs = [
            FileSpec(
                source="$HOME/.aws/credentials",
                destination="/root/.aws/credentials"
            ),
            FileSpec(
                source="$HOME/.aws/config",
                destination="/root/.aws/config"
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
            env=["AWS_PROFILE"]
        )

    def get_args(self) -> List[Arg]:
        """Return the tool's arguments."""
        return self.args

    def get_content(self) -> str:
        """Return the tool's shell script content."""
        return self.content

    def get_image(self) -> str:
        """Return the Docker image to use."""
        return self.image

    def validate_args(self, args: Dict[str, Any]) -> bool:
        """Validate the provided arguments."""
        required_args = [arg.name for arg in self.args if arg.required]
        return all(arg in args and args[arg] for arg in required_args)

    def get_error_message(self, args: Dict[str, Any]) -> Optional[str]:
        """Return error message if arguments are invalid."""
        missing_args = []
        for arg in self.args:
            if arg.required and (arg.name not in args or not args[arg.name]):
                missing_args.append(arg.name)
        
        if missing_args:
            return f"Missing required arguments: {', '.join(missing_args)}"
        return None