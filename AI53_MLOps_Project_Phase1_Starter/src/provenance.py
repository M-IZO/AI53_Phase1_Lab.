from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from importlib import metadata
from pathlib import Path


def training_data_identity(
    train_manifest: Path = Path("data/processed/manifests/train.csv"),
    validation_manifest: Path = Path("data/processed/manifests/validation.csv"),
) -> str:
    """Return a deterministic identity for the training + validation manifests.

    This helper is provided because the final evaluator uses the same identity
    to verify that the selected MLflow Run matches the current prepared data.
    Do not hard-code the value.
    """
    paths = (train_manifest, validation_manifest)
    if any(not path.exists() for path in paths):
        return "unavailable"

    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def build_run_manifest(params: dict, device: str, mlflow_run_id: str) -> dict:
    """Build experiment provenance metadata.

    TODO: collect at least:
      - Git commit SHA and whether the working tree is dirty;
      - identity of the prepared training + validation manifests;
      - Python, PyTorch, torchvision, DVC and MLflow versions;
      - OS/platform and CUDA runtime (when available);
      - compute device; random seed; image size; training parameters;
      - MLflow Run ID.

    Hints: subprocess, platform, importlib.metadata, torch,
    training_data_identity().
    """
    import torch

    commit = _git("rev-parse", "HEAD")
    status = _git("status", "--porcelain")
    train_cfg = params["train"]
    aug = params["augmentation"]

    return {
        "git": {
            "commit": commit or "unavailable",
            # None when Git is unavailable (not a repo, git not installed).
            "dirty": None if status is None else bool(status.strip()),
        },
        "data": {"training_data_identity": training_data_identity()},
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "torch": _package_version("torch"),
            "torchvision": _package_version("torchvision"),
            "dvc": _package_version("dvc"),
            "mlflow": _package_version("mlflow"),
            "cuda": torch.version.cuda if torch.cuda.is_available() else None,
        },
        "configuration": {
            "image_size": int(params["data"]["image_size"]),
            "batch_size": int(train_cfg["batch_size"]),
            "epochs": int(train_cfg["epochs"]),
            "learning_rate": float(train_cfg["learning_rate"]),
            "dropout": float(train_cfg["dropout"]),
            "augmentation_enabled": bool(aug["enabled"]),
            "horizontal_flip": float(aug["horizontal_flip"]),
            "rotation_degrees": float(aug["rotation_degrees"]),
        },
        "execution": {
            "device": str(device),
            "random_state": int(train_cfg["random_state"]),
            "mlflow_run_id": mlflow_run_id,
        },
    }


def _git(*args: str) -> str | None:
    """Run a git command and return its stdout, or None if it fails."""
    try:
        result = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    except OSError:
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def _package_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def write_run_manifest(params: dict, device: str, mlflow_run_id: str, path: Path) -> dict:
    manifest = build_run_manifest(params, device, mlflow_run_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest
