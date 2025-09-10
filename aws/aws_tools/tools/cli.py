from typing import List
import sys
from .base import AWSCliTool, Arg
from kubiya_sdk.tools.registry import tool_registry

class CLITools:
    """AWS CLI wrapper tools."""

    def __init__(self):
        """Initialize and register all AWS CLI tools."""
        try:
            tools = [
                self.run_cli_command()
            ]
            
            for tool in tools:
                try:
                    tool_registry.register("aws_cli", tool)
                    print(f"✅ Registered: {tool.name}")
                except Exception as e:
                    print(f"❌ Failed to register {tool.name}: {str(e)}", file=sys.stderr)
                    raise
        except Exception as e:
            print(f"❌ Failed to register AWS CLI tools: {str(e)}", file=sys.stderr)
            raise

    def run_cli_command(self) -> AWSCliTool:
        """Execute an AWS CLI command."""
        return AWSCliTool(
            name="aws_cli_command",
            description="Execute any AWS CLI command",
            content="""
            # Validate required parameters
            if [ -z "$command" ]; then
                echo "Error: Command is required"
                exit 1
            fi
            
            echo "=== Executing AWS CLI Command ==="
            echo "Command: aws $command"
            echo ""
            
            # Execute the command
            aws $command
            """,
            args=[
                Arg(name="command", description="The command to pass to the AWS CLI (e.g., 's3 ls', 'ec2 describe-instances', 'iam list-users')", required=True)
            ],
            image="amazon/aws-cli:latest"
        )

CLITools()