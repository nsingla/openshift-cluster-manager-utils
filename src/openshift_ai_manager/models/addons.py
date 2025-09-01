"""Addon configuration models."""

from pydantic import Field
from .base import BaseConfigModel


class AddonConfig(BaseConfigModel):
    """Base configuration for addons."""
    notification_email: str = Field(
        description="Email for addon notifications",
        alias="notificationEmail"
    )


class RHODSConfig(AddonConfig):
    """Configuration for RHODS/RHOAI addon."""
    addon_name: str = Field(
        default="managed-odh", 
        description="Addon identifier",
        alias="addonName"
    )
    install_dependencies: bool = Field(
        default=True, 
        description="Install required dependency operators",
        alias="installDependencies"
    )


class GPUAddonConfig(BaseConfigModel):
    """Configuration for GPU addon."""
    addon_name: str = Field(
        default="nvidia-gpu-addon", 
        description="GPU addon identifier",
        alias="addonName"
    )