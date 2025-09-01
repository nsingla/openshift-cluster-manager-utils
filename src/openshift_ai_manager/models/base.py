"""Base model with common functionality."""

import json
from pathlib import Path
from pydantic import BaseModel
from typing import TypeVar, Type

T = TypeVar('T', bound='BaseConfigModel')


class BaseConfigModel(BaseModel):
    """Base model with JSON file loading/saving capabilities."""
    
    @classmethod
    def from_json_file(cls: Type[T], file_path: Path | str) -> T:
        """Load configuration from JSON file."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        return cls(**data)


    @classmethod
    def from_json_data(cls: Type[T], json_data: str) -> T:
        """Load configuration from JSON file."""
        data = json.loads(json_data)
        return cls(**data)

    def to_json_file(self, file_path: Path | str) -> None:
        """Save configuration to JSON file."""
        with open(file_path, 'w') as f:
            json.dump(self.model_dump(exclude_none=True, by_alias=True), f, indent=2)