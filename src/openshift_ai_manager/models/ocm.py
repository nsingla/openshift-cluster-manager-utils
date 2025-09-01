"""OCM configuration models."""

from typing import Literal
from pydantic import Field
from .base import BaseConfigModel


class OCMConfig(BaseConfigModel):
    """OCM configuration."""
    token: str = Field(description="OCM authentication token")
    platform: Literal["prod", "stage"] = Field(
        default="stage", 
        description="OCM platform"
    )
    cli_binary_url: str = Field(
        default="https://github.com/openshift-online/ocm-cli/releases/latest/download/ocm-linux-amd64",
        description="OCM CLI binary URL",
        alias="cliBinaryUrl"
    )
    verbose_level: int = Field(
        default=0, 
        description="OCM logging verbosity level",
        alias="verboseLevel"
    )