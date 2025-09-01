"""Cluster configuration models."""

from typing import Optional, Literal
from pydantic import Field
from .base import BaseConfigModel
from .credentials import AWSCredentials, GCPCredentials


class ClusterNodes(BaseConfigModel):
    """Cluster compute node configuration."""
    compute: int = Field(default=3, description="Number of compute nodes")
    compute_machine_type: str = Field(
        default="m5.2xlarge", 
        description="Instance type for compute nodes",
        alias="computeMachineType"
    )


class ClusterVersion(BaseConfigModel):
    """OpenShift version configuration."""
    channel_group: str = Field(
        default="stable", 
        description="Channel group (stable, candidate)",
        alias="channelGroup"
    )
    id: Optional[str] = Field(
        default=None, 
        description="Specific OpenShift version ID"
    )


class ClusterRegion(BaseConfigModel):
    """Cluster region configuration."""
    id: str = Field(description="Region ID (e.g., us-east-1 for AWS, us-central1 for GCP)", default="us-east-1")


class ClusterConfig(BaseConfigModel):
    """Complete cluster configuration."""
    name: str = Field(description="Cluster name")
    cloud_provider: Literal["aws", "gcp"] = Field(
        default="aws", 
        description="Cloud provider",
        alias="cloudProvider"
    )
    region: ClusterRegion
    version: ClusterVersion = Field(default_factory=ClusterVersion)
    nodes: ClusterNodes = Field(default_factory=ClusterNodes)
    fips: bool = Field(default=False, description="Enable FIPS mode")
    multi_az: bool = Field(
        default=False, 
        description="Enable multi-AZ deployment",
        alias="multiAz"
    )
    team: str = Field(default="unknown-team", description="Team name for tagging")
    
    # Cloud-specific credentials
    aws_credentials: Optional[AWSCredentials] = Field(
        default=None,
        alias="awsCredentials"
    )
    gcp_credentials: Optional[GCPCredentials] = Field(
        default=None,
        alias="gcpCredentials"
    )

