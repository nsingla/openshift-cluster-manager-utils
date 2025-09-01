# OpenShift AI Manager

A Python tool for managing OpenShift clusters and deploying ODH/RHOAI using OCM (OpenShift Cluster Manager).

## Features

- **Cluster Management**: Create, delete, and manage OpenShift clusters on AWS and GCP
- **ODH/RHOAI Deployment**: Install Red Hat OpenShift Data Science / Red Hat OpenShift AI
- **GPU Support**: Add GPU-enabled machine pools and install GPU addons
- **Configuration-driven**: Uses Pydantic models with JSON configuration files
- **CLI Interface**: User-friendly command-line interface with rich output

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd openshift-ai-manager
```

2. Install using uv:
```bash
uv sync
```

3. Initialize configuration files:
```bash
oai-manager init
```

## Configuration

The tool uses JSON configuration files for different components:

- `configs/ocm-default.json`: OCM authentication and settings
- `configs/cluster-default.json`: AWS cluster configuration
- `configs/cluster-gcp.json`: GCP cluster configuration  
- `configs/rhods-default.json`: RHODS/RHOAI addon configuration
- `configs/gpu-addon-default.json`: GPU addon configuration
- `configs/machine-pool-default.json`: GPU machine pool configuration

### Required Setup

1. **OCM Token**: Update `configs/ocm-default.json` with your OCM token
2. **Cloud Credentials**: Update cluster config files with your AWS/GCP credentials
3. **Notification Email**: Update `configs/rhods-default.json` with your email

## Usage

### Cluster Operations

Create a cluster:
```bash
oai-manager cluster create --config configs/cluster-default.json
```

Get cluster information:
```bash
oai-manager cluster info my-cluster-name
```

Delete a cluster:
```bash
oai-manager cluster delete my-cluster-name --force
```

### Addon Operations

Install RHODS/RHOAI:
```bash
oai-manager addon install-rhods my-cluster-name
```

Install GPU addon:
```bash
oai-manager addon install-gpu my-cluster-name
```

Add GPU machine pool:
```bash
oai-manager addon add-machine-pool my-cluster-name
```

List installed addons:
```bash
oai-manager addon list my-cluster-name
```

Uninstall an addon:
```bash
oai-manager addon uninstall my-cluster-name managed-odh
```

## Configuration Schema

### Cluster Configuration

```json
{
  "name": "my-cluster",
  "cloudProvider": "aws",
  "region": {"id": "us-east-1"},
  "version": {"channelGroup": "stable"},
  "nodes": {
    "compute": 3,
    "computeMachineType": "m5.2xlarge"
  },
  "fips": false,
  "multiAz": false,
  "team": "data-science",
  "awsCredentials": {
    "accessKeyId": "...",
    "secretAccessKey": "...",
    "accountId": "..."
  }
}
```

### RHODS Configuration

```json
{
  "notificationEmail": "admin@example.com",
  "addonName": "managed-odh",
  "installDependencies": true
}
```

## Project Structure

```
openshift-ai-manager/
├── src/openshift_ai_manager/
│   ├── models/           # Pydantic models (each in separate files)
│   │   ├── base.py       # Base model with JSON loading/saving
│   │   ├── cluster.py    # Cluster configuration
│   │   ├── credentials.py # AWS/GCP credentials  
│   │   ├── addons.py     # RHODS/GPU addon configs
│   │   ├── machine_pool.py # Machine pool config
│   │   └── ocm.py        # OCM configuration
│   ├── core/            # Core business logic
│   │   ├── cluster_manager.py # Cluster operations
│   │   └── addon_manager.py   # Addon operations
│   └── cli.py           # CLI interface
├── configs/             # JSON configuration files
│   ├── cluster-default.json
│   ├── cluster-gcp.json
│   ├── rhods-default.json
│   ├── gpu-addon-default.json
│   ├── machine-pool-default.json
│   └── ocm-default.json
└── main.py              # Entry point
```

## Key Features

### 1. **Pydantic Models with camelCase Aliases**
- Each model is in a separate file
- All fields with underscores have camelCase aliases (e.g., `cloud_provider` → `cloudProvider`)
- Base model provides JSON loading/saving functionality

### 2. **JSON Configuration Instead of Jinja Templates**
- Default configurations stored in JSON files
- Easy to modify and version control
- Type-safe loading via Pydantic models

### 3. **Simplified API Methods**

**Cluster Management:**
```python
from openshift_ai_manager.core import ClusterManager
from openshift_ai_manager.models import ClusterConfig, OCMConfig

# Load configs from JSON
cluster_config = ClusterConfig.from_json_file("configs/cluster-default.json")
ocm_config = OCMConfig.from_json_file("configs/ocm-default.json")

# Create cluster
manager = ClusterManager(ocm_config)
manager.login()
cluster_id = manager.create_cluster(cluster_config)
manager.wait_for_cluster_ready(cluster_config.name)
```

**ODH/RHOAI Deployment:**
```python
from openshift_ai_manager.core import AddonManager
from openshift_ai_manager.models import RHODSConfig

# Load config and deploy
rhods_config = RHODSConfig.from_json_file("configs/rhods-default.json")
addon_manager = AddonManager(ocm_config)
addon_manager.install_rhods("my-cluster", rhods_config)
```

### 4. **Rich CLI Interface**
```bash
# Initialize configs
oai-manager init

# Create cluster
oai-manager cluster create --config configs/cluster-default.json

# Install RHODS
oai-manager addon install-rhods my-cluster

# Install GPU addon
oai-manager addon install-gpu my-cluster

# Add GPU machine pool
oai-manager addon add-machine-pool my-cluster
```

## Architecture

The project is structured with:

- **Models**: Pydantic models with camelCase JSON aliases
- **Core**: Business logic for cluster and addon management
- **CLI**: Typer-based command-line interface
- **Configs**: JSON configuration files with sensible defaults

## Requirements

- Python 3.13+
- OCM CLI (automatically installed)
- Valid OCM token
- Cloud provider credentials (AWS or GCP)

## Development

The project uses:
- **uv** for dependency management
- **Pydantic v2** for configuration validation
- **Typer** for CLI interface
- **Rich** for beautiful terminal output

To contribute:

1. Install development dependencies: `uv sync`
2. Run tests: `pytest` (when tests are added)
3. Format code: `ruff format`
4. Lint code: `ruff check`