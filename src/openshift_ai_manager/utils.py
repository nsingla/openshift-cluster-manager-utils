"""Utility functions for OpenShift AI Manager."""

import json
from pathlib import Path
from typing import TypeVar, Type

from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)


def load_config_from_json(config_class: Type[T], file_path: Path | str) -> T:
    """Load a Pydantic model from a JSON file."""
    with open(file_path, 'r') as f:
        data = json.load(f)
    return config_class(**data)


def save_config_to_json(config: BaseModel, file_path: Path | str) -> None:
    """Save a Pydantic model to a JSON file."""
    with open(file_path, 'w') as f:
        json.dump(config.model_dump(exclude_none=True, by_alias=True), f, indent=2)


def validate_file_exists(file_path: Path | str) -> Path:
    """Validate that a file exists and return Path object."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    return path