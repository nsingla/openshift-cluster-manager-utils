"""CLI interface for OpenShift AI Manager."""

from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table

from .models import ClusterConfig, RHODSConfig, GPUAddonConfig, MachinePoolConfig, OCMConfig
from .core import ClusterManager, AddonManager
from typing import TypeVar, Type

app = typer.Typer(name="oai-manager", help="OpenShift AI Manager - Manage clusters and deploy ODH/RHOAI")
console = Console()

# Sub-commands
cluster_app = typer.Typer(name="cluster", help="Cluster management commands")
addon_app = typer.Typer(name="addon", help="Addon management commands")

app.add_typer(cluster_app)
app.add_typer(addon_app)

T = TypeVar('T', bound='BaseConfigModel')


@cluster_app.command("create")
def create_cluster(
    cluster_conf_file: Path = typer.Option(
        Path("configs/cluster-default.json"),
        "--config", "-c",
        help="Path to cluster configuration JSON file"
    ),
    ocm_conf_file: Path = typer.Option(
        Path("configs/ocm-default.json"),
        "--ocm-config",
        help="Path to OCM configuration JSON file"
    ),
    wait: bool = typer.Option(
        True,
        "--wait/--no-wait",
        help="Wait for cluster to be ready"
    )
):
    """Create a new OpenShift cluster."""
    try:
        # Load configurations
        cluster_config = ClusterConfig.from_json_file(cluster_conf_file)
        ocm_config = OCMConfig.from_json_file(ocm_conf_file)

        console.print(f"[bold blue]Creating cluster: {cluster_config.name}[/bold blue]")

        # Initialize cluster manager
        cluster_manager = ClusterManager(ocm_config)
        cluster_manager.install_ocm_cli()
        cluster_manager.login()

        # Create cluster
        cluster_id = cluster_manager.create_cluster(cluster_config)
        console.print(f"[green]Cluster creation initiated. ID: {cluster_id}[/green]")

        if wait:
            cluster_manager.wait_for_cluster_ready(cluster_config.name)
            console.print(f"[bold green]Cluster {cluster_config.name} is ready![/bold green]")

            # Display cluster info
            info = cluster_manager.get_cluster_info(cluster_config.name)
            _display_cluster_info(info)

    except Exception as e:
        console.print(f"[bold red]Error creating cluster: {e}[/bold red]")
        raise typer.Exit(1)


@cluster_app.command("delete")
def delete_cluster(
    cluster_name: str = typer.Argument(help="Name of the cluster to delete"),
    ocm_conf_file: Path = typer.Option(
        Path("configs/ocm-default.json"),
        "--ocm-config",
        help="Path to OCM configuration JSON file"
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Skip confirmation prompt"
    )
):
    """Delete an OpenShift cluster."""
    if not force:
        confirm = typer.confirm(f"Are you sure you want to delete cluster '{cluster_name}'?")
        if not confirm:
            console.print("Operation cancelled.")
            raise typer.Exit()

    try:
        ocm_config = OCMConfig.from_json_file(ocm_conf_file)

        cluster_manager = ClusterManager(ocm_config)
        cluster_manager.login()
        cluster_manager.delete_cluster(cluster_name)

        console.print(f"[bold green]Cluster {cluster_name} deleted successfully![/bold green]")

    except Exception as e:
        console.print(f"[bold red]Error deleting cluster: {e}[/bold red]")
        raise typer.Exit(1)


@cluster_app.command("info")
def cluster_info(
    cluster_name: str = typer.Argument(help="Name of the cluster"),
    ocm_conf_file: Path = typer.Option(
        Path("configs/ocm-default.json"),
        "--ocm-config",
        help="Path to OCM configuration JSON file"
    )
):
    """Get cluster information."""
    try:
        ocm_config = OCMConfig.from_json_file(ocm_conf_file)

        cluster_manager = ClusterManager(ocm_config)
        cluster_manager.login()

        info = cluster_manager.get_cluster_info(cluster_name)
        _display_cluster_info(info)

    except Exception as e:
        console.print(f"[bold red]Error getting cluster info: {e}[/bold red]")
        raise typer.Exit(1)


@addon_app.command("install-rhods")
def install_rhods(
    cluster_name: str = typer.Argument(help="Name of the cluster"),
    rhods_conf_file: Path = typer.Option(
        Path("configs/rhods-default.json"),
        "--config", "-c",
        help="Path to RHODS configuration JSON file"
    ),
    ocm_conf_file: Path = typer.Option(
        Path("configs/ocm-default.json"),
        "--ocm-config",
        help="Path to OCM configuration JSON file"
    )
):
    """Install RHODS/RHOAI addon on a cluster."""
    try:
        # Load configurations
        rhods_config = RHODSConfig.from_json_file(rhods_conf_file)
        ocm_config = OCMConfig.from_json_file(ocm_conf_file)

        console.print(f"[bold blue]Installing RHODS on cluster: {cluster_name}[/bold blue]")

        # Initialize addon manager
        addon_manager = AddonManager(ocm_config)
        addon_manager.install_rhods(cluster_name, rhods_config)

        console.print(f"[bold green]RHODS installed successfully on {cluster_name}![/bold green]")

    except Exception as e:
        console.print(f"[bold red]Error installing RHODS: {e}[/bold red]")
        raise typer.Exit(1)


@addon_app.command("install-gpu")
def install_gpu_addon(
    cluster_name: str = typer.Argument(help="Name of the cluster"),
    gpu_addon_conf_file: Path = typer.Option(
        Path("configs/gpu-addon-default.json"),
        "--config", "-c",
        help="Path to GPU addon configuration JSON file"
    ),
    ocm_conf_file: Path = typer.Option(
        Path("configs/ocm-default.json"),
        "--ocm-config",
        help="Path to OCM configuration JSON file"
    )
):
    """Install GPU addon on a cluster."""
    try:
        # Load configurations
        gpu_config = GPUAddonConfig.from_json_file(gpu_addon_conf_file)
        ocm_config = OCMConfig.from_json_file(ocm_conf_file)

        console.print(f"[bold blue]Installing GPU addon on cluster: {cluster_name}[/bold blue]")

        # Initialize addon manager
        addon_manager = AddonManager(ocm_config)
        addon_manager.install_gpu_addon(cluster_name, gpu_config)

        console.print(f"[bold green]GPU addon installed successfully on {cluster_name}![/bold green]")

    except Exception as e:
        console.print(f"[bold red]Error installing GPU addon: {e}[/bold red]")
        raise typer.Exit(1)


@addon_app.command("add-machine-pool")
def add_machine_pool(
    cluster_name: str = typer.Argument(help="Name of the cluster"),
    pool_conf_file: Path = typer.Option(
        Path("configs/machine-pool-default.json"),
        "--config", "-c",
        help="Path to machine pool configuration JSON file"
    ),
    ocm_conf_file: Path = typer.Option(
        Path("configs/ocm-default.json"),
        "--ocm-config",
        help="Path to OCM configuration JSON file"
    )
):
    """Add a machine pool to a cluster."""
    try:
        # Load configurations
        pool_config = MachinePoolConfig.from_json_file(pool_conf_file)
        ocm_config = OCMConfig.from_json_file(ocm_conf_file)

        console.print(f"[bold blue]Adding machine pool '{pool_config.name}' to cluster: {cluster_name}[/bold blue]")

        # Initialize addon manager
        addon_manager = AddonManager(ocm_config)
        addon_manager.add_machine_pool(cluster_name, pool_config)

        console.print(f"[bold green]Machine pool '{pool_config.name}' added successfully![/bold green]")

    except Exception as e:
        console.print(f"[bold red]Error adding machine pool: {e}[/bold red]")
        raise typer.Exit(1)


@addon_app.command("uninstall")
def uninstall_addon(
    cluster_name: str = typer.Argument(help="Name of the cluster"),
    addon_name: str = typer.Argument(help="Name of the addon to uninstall"),
    ocm_config_file: Path = typer.Option(
        Path("configs/ocm-default.json"),
        "--ocm-config",
        help="Path to OCM configuration JSON file"
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Skip confirmation prompt"
    )
):
    """Uninstall an addon from a cluster."""
    if not force:
        confirm = typer.confirm(f"Are you sure you want to uninstall addon '{addon_name}' from cluster '{cluster_name}'?")
        if not confirm:
            console.print("Operation cancelled.")
            raise typer.Exit()

    try:
        ocm_config = OCMConfig.from_json_file(ocm_config_file)
        addon_manager = AddonManager(ocm_config)
        addon_manager.uninstall_addon(cluster_name, addon_name)

        console.print(f"[bold green]Addon '{addon_name}' uninstalled successfully![/bold green]")

    except Exception as e:
        console.print(f"[bold red]Error uninstalling addon: {e}[/bold red]")
        raise typer.Exit(1)


@addon_app.command("list")
def list_addons(
    cluster_name: str = typer.Argument(help="Name of the cluster"),
    ocm_config_file: Path = typer.Option(
        Path("configs/ocm-default.json"),
        "--ocm-config",
        help="Path to OCM configuration JSON file"
    )
):
    """List all addons installed on a cluster."""
    try:
        ocm_config = OCMConfig.from_json_file(ocm_config_file)
        addon_manager = AddonManager(ocm_config)
        addons = addon_manager.list_addons(cluster_name)
        
        _display_addons_table(addons)
        
    except Exception as e:
        console.print(f"[bold red]Error listing addons: {e}[/bold red]")
        raise typer.Exit(1)


@app.command("init")
def init_configs(
    target_dir: Path = typer.Option(
        Path("."),
        "--target", "-t",
        help="Target directory to create configs"
    )
):
    """Initialize default configuration files."""
    configs_dir = target_dir / "configs"
    configs_dir.mkdir(exist_ok=True)
    
    # Copy default configs
    import shutil
    
    config_files = [
        "cluster-default.json",
        "cluster-gcp.json", 
        "rhods-default.json",
        "gpu-addon-default.json",
        "machine-pool-default.json",
        "ocm-default.json"
    ]
    
    for config_file in config_files:
        src = Path(__file__).parent.parent.parent / "configs" / config_file
        dst = configs_dir / config_file
        
        if not dst.exists():
            shutil.copy2(src, dst)
            console.print(f"[green]Created: {dst}[/green]")
        else:
            console.print(f"[yellow]Exists: {dst}[/yellow]")
    
    console.print(f"[bold green]Configuration files initialized in {configs_dir}[/bold green]")
    console.print("\n[bold yellow]Next steps:[/bold yellow]")
    console.print("1. Update OCM token in configs/ocm-default.json")
    console.print("2. Update cloud credentials in cluster config files")
    console.print("3. Update notification email in configs/rhods-default.json")


def _display_cluster_info(info: dict):
    """Display cluster information in a formatted table."""
    table = Table(title="Cluster Information")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    for key, value in info.items():
        if value:
            table.add_row(key.replace("_", " ").title(), str(value))
    
    console.print(table)


def _display_addons_table(addons: list[dict]):
    """Display addons in a formatted table."""
    table = Table(title="Installed Addons")
    table.add_column("Name", style="cyan")
    table.add_column("State", style="green")
    table.add_column("Version", style="yellow")
    
    for addon in addons:
        name = addon.get("id", "Unknown")
        state = addon.get("state", "Unknown")
        version = addon.get("version", "N/A")
        table.add_row(name, state, version)
    
    if not addons:
        console.print("[yellow]No addons found[/yellow]")
    else:
        console.print(table)

if __name__ == "__main__":
    app()