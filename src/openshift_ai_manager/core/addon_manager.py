"""Addon management functionality for ODH/RHOAI."""

import json
import subprocess
import time
import tempfile
from pathlib import Path
from typing import Optional

from ..models import RHODSConfig, GPUAddonConfig, MachinePoolConfig, OCMConfig


class AddonManager:
    """Manages OpenShift addons including ODH/RHOAI."""
    
    def __init__(self, ocm_config: OCMConfig):
        self.ocm_config = ocm_config
    
    def install_rhods(self, cluster_name: str, config: RHODSConfig) -> None:
        """Install RHODS/RHOAI addon on the cluster."""
        print(f"Installing RHODS on cluster: {cluster_name}")
        
        cluster_id = self._get_cluster_id(cluster_name)
        
        # Install dependency operators if enabled
        if config.install_dependencies:
            self._install_dependency_operators()
        
        # Install RHODS addon
        addon_spec = {
            "kind": "Cluster",
            "href": f"/api/clusters_mgmt/v1/clusters/{cluster_id}",
            "addon": {
                "kind": "AddOn",
                "href": f"/api/clusters_mgmt/v1/addons/{config.addon_name}",
                "id": config.addon_name
            },
            "parameters": {
                "items": [
                    {
                        "id": "notification-email",
                        "value": config.notification_email
                    }
                ]
            }
        }
        
        self._install_addon(cluster_id, addon_spec)
        self._wait_for_addon_ready(cluster_id, config.addon_name)
        
        print("RHODS installation completed")
        
        # Additional wait for services to stabilize
        print("Waiting additional 5 minutes for services to stabilize...")
        time.sleep(300)
    
    def install_gpu_addon(self, cluster_name: str, config: GPUAddonConfig) -> None:
        """Install GPU addon on the cluster."""
        print(f"Installing GPU addon on cluster: {cluster_name}")
        
        cluster_id = self._get_cluster_id(cluster_name)
        
        addon_spec = {
            "kind": "Cluster",
            "href": f"/api/clusters_mgmt/v1/clusters/{cluster_id}",
            "addon": {
                "kind": "AddOn",
                "href": f"/api/clusters_mgmt/v1/addons/{config.addon_name}",
                "id": config.addon_name
            }
        }
        
        self._install_addon(cluster_id, addon_spec)
        self._wait_for_addon_ready(cluster_id, config.addon_name)
        
        print("GPU addon installation completed")
        
        # Additional wait for services to stabilize
        print("Waiting additional 5 minutes for services to stabilize...")
        time.sleep(300)
    
    def add_machine_pool(self, cluster_name: str, config: MachinePoolConfig) -> None:
        """Add a machine pool to the cluster (typically for GPU nodes)."""
        print(f"Adding machine pool '{config.name}' to cluster: {cluster_name}")
        
        cluster_id = self._get_cluster_id(cluster_name)
        
        # Check if machine pool already exists and reuse if configured
        if config.reuse_existing and self._machine_pool_exists(cluster_id, config.name):
            print(f"Machine pool '{config.name}' already exists, reusing it")
            return
        
        cmd = [
            "ocm", f"--v={self.ocm_config.verbose_level}",
            "create", "machinepool",
            "--cluster", cluster_id,
            "--instance-type", config.instance_type,
            "--replicas", str(config.node_count),
            config.name
        ]
        
        subprocess.run(cmd, check=True)
        print(f"Machine pool '{config.name}' added successfully")
        
        # Wait for machine pool to be ready
        time.sleep(60)
    
    def uninstall_addon(self, cluster_name: str, addon_name: str) -> None:
        """Uninstall an addon from the cluster."""
        print(f"Uninstalling addon '{addon_name}' from cluster: {cluster_name}")
        
        cluster_id = self._get_cluster_id(cluster_name)
        
        cmd = [
            "ocm", f"--v={self.ocm_config.verbose_level}",
            "delete", f"/api/clusters_mgmt/v1/clusters/{cluster_id}/addons/{addon_name}"
        ]
        
        subprocess.run(cmd, check=True)
        self._wait_for_addon_uninstalled(cluster_id, addon_name)
        
        print(f"Addon '{addon_name}' uninstalled successfully")
    
    def get_addon_state(self, cluster_name: str, addon_name: str) -> str:
        """Get the state of an addon."""
        cluster_id = self._get_cluster_id(cluster_name)
        
        cmd = [
            "ocm", "list", "addons",
            "--cluster", cluster_id,
            "--columns", "id,state"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        for line in result.stdout.split('\n'):
            if addon_name in line:
                parts = line.strip().split()
                if len(parts) >= 2:
                    return parts[1]
        
        return "not installed"
    
    def list_addons(self, cluster_name: str) -> list[dict]:
        """List all addons installed on the cluster."""
        cluster_id = self._get_cluster_id(cluster_name)
        
        cmd = [
            "ocm", "list", "addons",
            "--cluster", cluster_id,
            "--output", "json"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        addons_data = json.loads(result.stdout)
        
        return addons_data.get("items", [])
    
    def _install_dependency_operators(self) -> None:
        """Install dependency operators required for RHOAI."""
        print("Installing dependency operators...")
        
        dependencies = [
            ("authorino-operator", "tech-preview-v1", "redhat-operators"),
            ("servicemeshoperator", "stable", "redhat-operators"),
            ("serverless-operator", "stable", "redhat-operators")
        ]
        
        for operator_name, channel, source in dependencies:
            print(f"Installing {operator_name}...")
            self._install_operator(operator_name, channel, source)
            self._wait_for_operator_ready(operator_name)
    
    def _install_operator(self, operator_name: str, channel: str, source: str) -> None:
        """Install an operator via OLM."""
        subscription_spec = {
            "apiVersion": "operators.coreos.com/v1alpha1",
            "kind": "Subscription",
            "metadata": {
                "name": operator_name,
                "namespace": "openshift-operators"
            },
            "spec": {
                "channel": channel,
                "name": operator_name,
                "source": source,
                "sourceNamespace": "openshift-marketplace"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            import yaml
            yaml.dump(subscription_spec, f)
            temp_file = f.name
        
        try:
            subprocess.run(["oc", "apply", "-f", temp_file], check=True)
        finally:
            Path(temp_file).unlink(missing_ok=True)
    
    def _wait_for_operator_ready(self, operator_name: str, timeout: int = 300) -> None:
        """Wait for an operator to be ready."""
        print(f"Waiting for {operator_name} to be ready...")
        
        count = 0
        while count <= timeout:
            cmd = [
                "oc", "get", "csv", "-n", "openshift-operators",
                "-o", "json"
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                csvs = json.loads(result.stdout)
                
                for csv in csvs.get("items", []):
                    name = csv.get("metadata", {}).get("name", "")
                    if operator_name in name.lower():
                        phase = csv.get("status", {}).get("phase", "")
                        if phase == "Succeeded":
                            print(f"{operator_name} is ready")
                            return
                        break
            except subprocess.CalledProcessError:
                pass
            
            time.sleep(10)
            count += 10
        
        print(f"Warning: {operator_name} may not be fully ready")
    
    def _install_addon(self, cluster_id: str, addon_spec: dict) -> None:
        """Install an addon using OCM API."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(addon_spec, f, indent=2)
            temp_file = f.name
        
        try:
            cmd = [
                "ocm", f"--v={self.ocm_config.verbose_level}",
                "post", f"/api/clusters_mgmt/v1/clusters/{cluster_id}/addons",
                f"--body={temp_file}"
            ]
            
            subprocess.run(cmd, check=True)
            
        finally:
            Path(temp_file).unlink(missing_ok=True)
    
    def _wait_for_addon_ready(self, cluster_id: str, addon_name: str, timeout: int = 3600) -> None:
        """Wait for addon to be in ready state."""
        print(f"Waiting for addon '{addon_name}' to be ready...")
        
        count = 0
        while count <= timeout:
            state = self._get_addon_state_by_id(cluster_id, addon_name)
            
            if state == "ready":
                print(f"Addon '{addon_name}' is ready")
                return
            elif state == "failed":
                raise RuntimeError(f"Addon '{addon_name}' installation failed")
            
            print(f"Addon state: {state}. Waiting...")
            time.sleep(60)
            count += 60
        
        raise TimeoutError(f"Addon '{addon_name}' not ready after {timeout/60} minutes")
    
    def _wait_for_addon_uninstalled(self, cluster_id: str, addon_name: str, timeout: int = 3600) -> None:
        """Wait for addon to be uninstalled."""
        print(f"Waiting for addon '{addon_name}' to be uninstalled...")
        
        count = 0
        while count <= timeout:
            state = self._get_addon_state_by_id(cluster_id, addon_name)
            
            if state == "not installed":
                print(f"Addon '{addon_name}' uninstalled successfully")
                return
            
            print(f"Addon state: {state}. Waiting...")
            time.sleep(60)
            count += 60
        
        raise TimeoutError(f"Addon '{addon_name}' not uninstalled after {timeout/60} minutes")
    
    def _get_addon_state_by_id(self, cluster_id: str, addon_name: str) -> str:
        """Get addon state by cluster ID."""
        cmd = [
            "ocm", "list", "addons",
            "--cluster", cluster_id,
            "--columns", "id,state"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        for line in result.stdout.split('\n'):
            if addon_name in line:
                parts = line.strip().split()
                if len(parts) >= 2:
                    return parts[1]
        
        return "not installed"
    
    def _machine_pool_exists(self, cluster_id: str, pool_name: str) -> bool:
        """Check if a machine pool exists."""
        cmd = [
            "ocm", "list", "machinepools",
            "--cluster", cluster_id
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return pool_name in result.stdout
    
    def _get_cluster_id(self, cluster_name: str) -> str:
        """Get cluster ID by name."""
        cmd = [
            "ocm", "list", "clusters", 
            f"-p", f"search=\"name = '{cluster_name}' or id = '{cluster_name}' or external_id = '{cluster_name}'\"",
            "--columns", "id", "--no-headers"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        cluster_id = result.stdout.strip()
        
        if not cluster_id:
            raise ValueError(f"Cluster not found: {cluster_name}")
        
        return cluster_id