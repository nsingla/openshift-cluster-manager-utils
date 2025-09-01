"""Machine pool configuration models."""

from pydantic import Field
from .base import BaseConfigModel


class MachinePoolConfig(BaseConfigModel):
    """Machine pool configuration for GPU nodes."""
    name: str = Field(default="gpunode", description="Machine pool name")
    instance_type: str = Field(
        default="g4dn.xlarge", 
        description="Instance type for GPU nodes",
        alias="instanceType"
    )
    node_count: int = Field(
        default=1, 
        description="Number of nodes in the pool",
        alias="nodeCount"
    )
    reuse_existing: bool = Field(
        default=True, 
        description="Reuse existing machine pool if it exists",
        alias="reuseExisting"
    )