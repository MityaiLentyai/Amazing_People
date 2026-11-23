"""Configuration parsing and validation for A-Maze-ing."""

import sys
from typing import Literal

from pydantic import (
    BaseModel,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)


class ConfigError(ValueError):
    """Raised when a maze configuration cannot be parsed safely."""


def format_validation_error(error: ValidationError) -> str:
    """Convert Pydantic validation details into short, readable messages."""
    messages: list[str] = []

    for detail in error.errors(
        include_url=False,
        include_context=False,
        include_input=False,
    ):
        location = ".".join(str(part) for part in detail["loc"])
        message = detail["msg"]

        if message.startswith("Value error, "):
            message = message.removeprefix("Value error, ")
        elif message == "Field required":
            message = "Missing required value"

        if location:
            formatted = f"{location}: {message}"
        else:
            formatted = message

        if formatted not in messages:
            messages.append(formatted)

    return "; ".join(messages)


class Config(BaseModel):
    """Validated A-Maze-ing configuration."""

    width: int = Field(ge=1, strict=True, alias="WIDTH")
    height: int = Field(ge=1, strict=True, alias="HEIGHT")
    entry: tuple[int, int] = Field(alias="ENTRY")
    exit: tuple[int, int] = Field(alias="EXIT")
    output: str = Field(alias="OUTPUT_FILE")
    is_perfect: bool = Field(alias="PERFECT")
    seed: int | None = Field(default=None, alias="SEED")
    algorithm: Literal["dfs", "prim"] = Field(
        default="dfs",
        alias="ALGORITHM",
    )

    @field_validator("width", "height", mode="before")
    @classmethod
    def parse_positive_integer(cls, value: object) -> object:
        """Parse positive integer fields read from text configuration."""
        if isinstance(value, str):
            try:
                return int(value.strip())
            except ValueError as error:
                raise ValueError("Maze dimensions must be integers") from error
        return value

    @model_validator(mode="after")
    def validate_entry(self) -> "Config":
        """Validate that the entry is inside the maze."""
        x, y = self.entry
        if not (0 <= x < self.width):
            raise ValueError("Entry point X is outside the maze")
        if not (0 <= y < self.height):
            raise ValueError("Entry point Y is outside the maze")
        return self

    @model_validator(mode="after")
    def validate_exit(self) -> "Config":
        """Validate that the exit is inside the maze."""
        x, y = self.exit
        if not (0 <= x < self.width):
            raise ValueError("Exit point X is outside the maze")
        if not (0 <= y < self.height):
            raise ValueError("Exit point Y is outside the maze")
        return self

    @model_validator(mode="after")
    def validate_distinct_endpoints(self) -> "Config":
        """Validate that entry and exit are different."""
        if self.entry == self.exit:
            raise ValueError("Entry and exit cells must be different")
        return self

    @field_validator("entry", "exit", mode="before")
    @classmethod
    def parse_coordinates(cls, value: object) -> object:
        """Parse an ``x,y`` coordinate string."""
        if isinstance(value, str):
            parts = value.split(",")
            if len(parts) != 2:
                raise ValueError("Coordinates must use the format x,y")
            try:
                return int(parts[0].strip()), int(parts[1].strip())
            except ValueError as error:
                raise ValueError(
                    "Coordinates must contain two integers"
                ) from error
        return value

    @field_validator("algorithm", mode="before")
    @classmethod
    def normalize_algorithm(cls, value: object) -> object:
        """Normalize the optional algorithm name."""
        return value.lower() if isinstance(value, str) else value

    @field_validator("is_perfect", mode="before")
    @classmethod
    def normalize_perfect(cls, value: object) -> object:
        """Accept only the explicit boolean values True or False."""
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in ("true", "false"):
                return normalized == "true"
            raise ValueError("PERFECT must be True or False")
        return value


def parse_input(config_name: str) -> Config:
    """Read and validate a maze configuration file."""
    config: dict[str, str] = {}
    try:
        with open(config_name, "r", encoding="utf-8") as file:
            for line in file:
                parsed_line = line.split("#", 1)[0].strip()
                if "=" in parsed_line:
                    key, value = parsed_line.split("=", 1)
                    config[key.strip()] = value.strip()
        return Config.model_validate(config)
    except FileNotFoundError as error:
        raise ConfigError(
            f"Config file not found: {config_name}"
        ) from error
    except PermissionError as error:
        raise ConfigError(
            f"Not enough access rights to read {config_name}"
        ) from error
    except ValidationError as error:
        raise ConfigError(format_validation_error(error)) from error


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 -m src.file_input config.txt")
        raise SystemExit(1)
    try:
        print(parse_input(sys.argv[1]))
    except ConfigError as error:
        print(f"Invalid configuration: {error}")
        raise SystemExit(1) from error
