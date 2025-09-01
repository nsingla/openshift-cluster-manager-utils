"""Cluster management functionality."""

import json
import subprocess
import time
import tempfile
from pathlib import Path
from typing import Optional

from ..models import ClusterConfig, OCMConfig


class ClusterManager:
    """Manages OpenShift cluster lifecycle using OCM."""
    
    def __init__(self, ocm_config: OCMConfig):
        self.ocm_config = ocm_config
        self.cluster_id: Optional[str] = None
    
    def install_ocm_cli(self) -> None:
        """Install OCM CLI if not already installed."""
        try:
            subprocess.run(["ocm", "version"], capture_output=True, check=True)
            print("OCM CLI already installed")
            return
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        print("Installing OCM CLI...")
        subprocess.run([
            "sudo", "curl", "-Lo", "/bin/ocm", self.ocm_config.cli_binary_url
        ], check=True)
        subprocess.run(["sudo", "chmod", "+x", "/bin/ocm"], check=True)
        print("OCM CLI installed successfully")
    
    def login(self) -> None:
        """Login to OCM using token."""
        cmd = ["ocm", "login", f"--token={self.ocm_config.token}"]
        
        if self.ocm_config.platform == "stage":
            cmd.append("--url=staging")
        
        # Set OCM config environment
        env = {"OCM_CONFIG": f"ocm.json.{self.ocm_config.platform}"}
        
        subprocess.run(cmd, env=env, check=True)
        print(f"Logged in to OCM ({self.ocm_config.platform})")
    
    def create_cluster(self, config: ClusterConfig) -> str:
        """Create a new OpenShift cluster."""
        print(f"Creating cluster: {config.name}")
        
        # Generate cluster specification
        cluster_spec = self._generate_cluster_spec(config)
        
        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(cluster_spec, f, indent=2)
            temp_file = f.name
        
        try:
            # Create cluster via OCM API
            cmd = [
                "ocm", f"--v={self.ocm_config.verbose_level}",
                "post", "/api/clusters_mgmt/v1/clusters",
                f"--body={temp_file}"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Parse response to get cluster ID
            response = json.loads(result.stdout)
            self.cluster_id = response.get("id")
            
            print(f"Cluster creation initiated. ID: {self.cluster_id}")
            return self.cluster_id
            
        finally:
            Path(temp_file).unlink(missing_ok=True)
    
    def wait_for_cluster_ready(self, cluster_name: str, timeout: int = 7200) -> None:
        """Wait for cluster to be in ready state."""
        print("Waiting for cluster to be ready...")
        
        cluster_id = self._get_cluster_id(cluster_name)
        count = 0
        
        while count <= timeout:
            state = self._get_cluster_state(cluster_id)
            
            if state == "ready":
                print(f"Cluster {cluster_name} is ready")
                # Additional wait for services to stabilize
                print("Waiting additional 5 minutes for services to stabilize...")
                time.sleep(300)
                return
            elif state == "error":
                raise RuntimeError(f"Cluster {cluster_name} is in error state")
            
            print(f"Cluster state: {state}. Waiting...")
            time.sleep(60)
            count += 60
        
        raise TimeoutError(f"Cluster {cluster_name} not ready after {timeout/60} minutes")
    
    def delete_cluster(self, cluster_name: str) -> None:
        """Delete a cluster."""
        cluster_id = self._get_cluster_id(cluster_name)
        
        cmd = [
            "ocm", f"--v={self.ocm_config.verbose_level}",
            "delete", "cluster", cluster_id
        ]
        
        subprocess.run(cmd, check=True)
        print(f"Cluster deletion initiated: {cluster_name}")
        
        # Wait for deletion to complete
        self._wait_for_cluster_deleted(cluster_name)
    
    def get_cluster_info(self, cluster_name: str) -> dict:
        """Get cluster information."""
        cluster_id = self._get_cluster_id(cluster_name)
        
        cmd = ["ocm", "describe", "cluster", cluster_id, "--json"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        cluster_info = json.loads(result.stdout)
        
        # Extract useful information
        info = {
            "name": cluster_info.get("name"),
            "id": cluster_info.get("id"),
            "state": cluster_info.get("state"),
            "version": cluster_info.get("version", {}).get("raw_id"),
            "console_url": cluster_info.get("console", {}).get("url"),
            "api_url": cluster_info.get("api", {}).get("url"),
        }
        
        return info
    
    def _generate_cluster_spec(self, config: ClusterConfig) -> dict:
        """Generate cluster specification from config."""
        spec = {
            "name": config.name,
            "cloud_provider": {"id": config.cloud_provider},
            "version": {
                "channel_group": config.version.channel_group,
            },
            "fips": config.fips,
            "region": {"id": config.region.id},
            "multi_az": config.multi_az,
            "product": {"id": "osd"},
            "ccs": {"enabled": True},
            "nodes": {
                "compute": config.nodes.compute,
                "compute_machine_type": {"id": config.nodes.compute_machine_type}
            }
        }
        
        # Add version ID if specified
        if config.version.id:
            spec["version"]["id"] = f"openshift-v{config.version.id}"
        
        # Add cloud-specific credentials
        if config.cloud_provider == "aws" and config.aws_credentials:
            spec["aws"] = {
                "access_key_id": config.aws_credentials.access_key_id,
                "secret_access_key": config.aws_credentials.secret_access_key,
                "account_id": config.aws_credentials.account_id,
                "tags": {"team": config.team}
            }
        elif config.cloud_provider == "gcp" and config.gcp_credentials:
            spec["gcp"] = {
                "project_id": config.gcp_credentials.project_id,
                "private_key_id": config.gcp_credentials.private_key_id,
                "private_key": config.gcp_credentials.private_key,
                "client_id": config.gcp_credentials.client_id,
                "client_email": config.gcp_credentials.client_email,
                "client_x509_cert_url": config.gcp_credentials.client_x509_cert_url,
                "type": config.gcp_credentials.auth_type,
                "auth_uri": config.gcp_credentials.auth_uri,
                "token_uri": config.gcp_credentials.token_uri,
                "auth_provider_x509_cert_url": config.gcp_credentials.auth_provider_x509_cert_url
            }
        
        return spec
    
    def _get_cluster_id(self, cluster_name: str) -> str:
        """Get cluster ID by name."""
        if self.cluster_id:
            return self.cluster_id
        
        cmd = [
            "ocm", "list", "clusters", 
            f"-p", f"search=\"name = '{cluster_name}' or id = '{cluster_name}' or external_id = '{cluster_name}'\"",
            "--columns", "id", "--no-headers"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        cluster_id = result.stdout.strip()
        
        if not cluster_id:
            raise ValueError(f"Cluster not found: {cluster_name}")
        
        self.cluster_id = cluster_id
        return cluster_id
    
    def _get_cluster_state(self, cluster_id: str) -> str:
        """Get cluster state."""
        cmd = ["ocm", "describe", "cluster", cluster_id, "--json"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        cluster_info = json.loads(result.stdout)
        return cluster_info.get("state", "unknown")
    
    def _wait_for_cluster_deleted(self, cluster_name: str, timeout: int = 5400) -> None:
        """Wait for cluster to be deleted."""
        print("Waiting for cluster deletion to complete...")
        
        count = 0
        while count <= timeout:
            try:
                self._get_cluster_id(cluster_name)
                print("Cluster still exists, waiting...")
                time.sleep(60)
                count += 60
            except ValueError:
                print(f"Cluster {cluster_name} deleted successfully")
                return
        
        raise TimeoutError(f"Cluster {cluster_name} not deleted after {timeout/60} minutes")