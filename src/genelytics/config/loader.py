from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import ValidationError

from genelytics.config.settings import Settings

_REQUIRED_SECTIONS = ("llm", "database", "analytics", "few_shot")


def resolve_config_dir(config_dir: Optional[str | Path] = None) -> Path:
    """Locate the config/ directory (environments/ lives under it)."""
    if config_dir is not None:
        root = Path(config_dir)
        if not (root / "environments").is_dir():
            raise FileNotFoundError(
                f"Config dir '{root}' has no environments/ subdirectory."
            )
        return root

    explicit = os.environ.get("GENELYTICS_CONFIG_DIR")
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit))
    candidates.extend(
        [
            Path.cwd() / "config",
            Path.cwd().parent / "config",
            # src/genelytics/config/loader.py -> repo/config
            Path(__file__).resolve().parents[3] / "config",
        ]
    )
    for candidate in candidates:
        if candidate and (candidate / "environments").is_dir():
            return candidate
    raise FileNotFoundError(
        "Could not find config/environments. Set GENELYTICS_CONFIG_DIR "
        "or run from the project root."
    )


def list_environments(config_dir: Optional[str | Path] = None) -> list[str]:
    """Return available environment names (YAML stems under environments/)."""
    env_dir = resolve_config_dir(config_dir) / "environments"
    return sorted(p.stem for p in env_dir.glob("*.yaml") if p.is_file())


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _env_overrides(prefix: str = "GENELYTICS_") -> dict[str, Any]:
    """Parse GENELYTICS_SECTION__KEY env vars into a nested dict."""
    out: dict[str, Any] = {}
    for key, value in os.environ.items():
        if not key.startswith(prefix):
            continue
        rest = key[len(prefix) :]
        if rest == "ENV":
            out["env"] = value
            continue
        if rest == "CONFIG_DIR":
            continue
        parts = [p.lower() for p in rest.split("__") if p]
        if len(parts) < 2:
            continue
        cursor: dict[str, Any] = out
        for part in parts[:-1]:
            cursor = cursor.setdefault(part, {})
        cursor[parts[-1]] = _coerce(value)
    return out


def _coerce(value: str) -> Any:
    lowered = value.strip().lower()
    if lowered in {"true", "1", "yes"}:
        return True
    if lowered in {"false", "0", "no"}:
        return False
    if lowered in {"null", "none", ""}:
        return None
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


def load_yaml(path: Path | str) -> dict[str, Any]:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a mapping: {path}")
    return data


def _validate_sections(data: dict[str, Any], *, source: str) -> None:
    missing = [s for s in _REQUIRED_SECTIONS if s not in data]
    if missing:
        raise ValueError(
            f"Config '{source}' is missing required section(s): {', '.join(missing)}. "
            "Define them in the YAML environment file."
        )
    llm = data.get("llm") or {}
    if not isinstance(llm, dict) or not llm.get("provider") or not llm.get("model"):
        raise ValueError(
            f"Config '{source}' must set llm.provider and llm.model "
            "(no provider defaults are hard-coded in code)."
        )


def load_settings(
    env: Optional[str] = None,
    yaml_path: Optional[str | Path] = None,
    config_dir: Optional[str | Path] = None,
) -> Settings:
    """Load Settings from YAML for GENELYTICS_ENV, then apply env overrides.

    Resolution order:
      1. Select env: explicit `env` arg → GENELYTICS_ENV → error if neither
         (when using yaml_path, env name is informational only)
      2. Load config/environments/{env}.yaml (or yaml_path)
      3. Overlay GENELYTICS_*__* environment variables
    """
    if yaml_path:
        path = Path(yaml_path)
        data = load_yaml(path)
        env_name = env or os.environ.get("GENELYTICS_ENV") or path.stem
        source = str(path)
    else:
        env_name = env or os.environ.get("GENELYTICS_ENV")
        if not env_name:
            available = ", ".join(list_environments(config_dir)) or "(none found)"
            raise ValueError(
                "No environment selected. Set GENELYTICS_ENV to one of: "
                f"{available}, or pass env=... / yaml_path=..."
            )
        root = resolve_config_dir(config_dir)
        path = root / "environments" / f"{env_name}.yaml"
        if not path.is_file():
            available = ", ".join(list_environments(root)) or "(none found)"
            raise FileNotFoundError(
                f"Environment config not found: {path}. "
                f"Available: {available}"
            )
        data = load_yaml(path)
        source = str(path)

    data = _deep_merge(dict(data), _env_overrides())
    data["env"] = env_name
    _validate_sections(data, source=source)

    try:
        return Settings(**data)
    except ValidationError as exc:
        raise ValueError(
            f"Invalid config in '{source}'. Fix the YAML (or env overrides).\n{exc}"
        ) from exc


def settings_from_dict(data: dict[str, Any]) -> Settings:
    merged = _deep_merge(dict(data), _env_overrides())
    if "env" not in merged:
        merged["env"] = os.environ.get("GENELYTICS_ENV", "custom")
    _validate_sections(merged, source="<dict>")
    return Settings(**merged)
