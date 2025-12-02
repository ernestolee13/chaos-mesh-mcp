"""Kubectl wrapper utilities."""

import json
import subprocess
from typing import Dict, List, Optional, Any


class KubectlError(Exception):
    """Error executing kubectl command."""
    pass


class KubectlRunner:
    """Async kubectl command runner for validation and operations."""

    async def run_command(self, command: str) -> Dict[str, Any]:
        """Run kubectl command and return JSON output.

        Args:
            command: kubectl command (without 'kubectl' prefix)

        Returns:
            Parsed JSON output

        Raises:
            KubectlError: If command fails
        """
        cmd = ["kubectl"] + command.split()
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise KubectlError(f"kubectl {command} failed: {result.stderr}")

        # Try to parse as JSON
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            # Return raw output for non-JSON commands
            return {"output": result.stdout.strip()}

    async def apply_yaml(self, yaml_content: str, namespace: str = "default") -> Dict[str, Any]:
        """Apply YAML content using kubectl.

        Args:
            yaml_content: YAML content as string
            namespace: Target namespace

        Returns:
            Result dictionary with status

        Raises:
            KubectlError: If apply fails
        """
        result = apply_yaml(yaml_content)
        return result


def apply_yaml(yaml_content: str) -> Dict[str, Any]:
    """Apply YAML content using kubectl.

    Args:
        yaml_content: YAML content as string

    Returns:
        Result dictionary with status and details

    Raises:
        KubectlError: If kubectl command fails
    """
    result = subprocess.run(
        ["kubectl", "apply", "-f", "-"],
        input=yaml_content.encode(),
        capture_output=True
    )

    if result.returncode != 0:
        raise KubectlError(f"kubectl apply failed: {result.stderr.decode()}")

    return {
        "status": "applied",
        "output": result.stdout.decode().strip()
    }


def validate_yaml(yaml_content: str) -> Dict[str, Any]:
    """Validate YAML using kubectl dry-run.

    Args:
        yaml_content: YAML content as string

    Returns:
        Validation result with valid flag and optional error

    """
    result = subprocess.run(
        ["kubectl", "apply", "--dry-run=client", "-f", "-"],
        input=yaml_content.encode(),
        capture_output=True
    )

    return {
        "valid": result.returncode == 0,
        "error": result.stderr.decode().strip() if result.returncode != 0 else None
    }


def get_resource(kind: str, name: str, namespace: str = "default") -> Dict[str, Any]:
    """Get Kubernetes resource as JSON.

    Args:
        kind: Resource kind (e.g., 'networkchaos', 'podchaos')
        name: Resource name
        namespace: Kubernetes namespace

    Returns:
        Resource as dictionary

    Raises:
        KubectlError: If resource not found or command fails
    """
    result = subprocess.run(
        ["kubectl", "get", kind.lower(), name, "-n", namespace, "-o", "json"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise KubectlError(f"Resource not found: {kind}/{name} in namespace {namespace}")

    return json.loads(result.stdout)


def list_resources(kind: str, namespace: str = "default", labels: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
    """List Kubernetes resources.

    Args:
        kind: Resource kind
        namespace: Kubernetes namespace
        labels: Optional label selectors

    Returns:
        List of resources
    """
    cmd = ["kubectl", "get", kind.lower(), "-n", namespace, "-o", "json"]

    if labels:
        label_str = ",".join([f"{k}={v}" for k, v in labels.items()])
        cmd.extend(["-l", label_str])

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        return []

    data = json.loads(result.stdout)
    return data.get("items", [])


def delete_resource(kind: str, name: str, namespace: str = "default") -> Dict[str, Any]:
    """Delete Kubernetes resource.

    Args:
        kind: Resource kind
        name: Resource name
        namespace: Kubernetes namespace

    Returns:
        Deletion result

    Raises:
        KubectlError: If deletion fails
    """
    result = subprocess.run(
        ["kubectl", "delete", kind.lower(), name, "-n", namespace],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise KubectlError(f"Failed to delete {kind}/{name}: {result.stderr}")

    return {
        "status": "deleted",
        "output": result.stdout.strip()
    }


def get_pods(namespace: str, labels: Dict[str, str]) -> List[Dict[str, Any]]:
    """Get pods matching label selectors.

    Args:
        namespace: Kubernetes namespace
        labels: Label selectors

    Returns:
        List of pod dictionaries
    """
    return list_resources("pod", namespace=namespace, labels=labels)


def check_target_exists(namespace: str, labels: Dict[str, str]) -> Dict[str, Any]:
    """Check if target pods exist.

    Args:
        namespace: Kubernetes namespace
        labels: Label selectors

    Returns:
        Dictionary with existence info and pod list
    """
    pods = get_pods(namespace, labels)

    return {
        "exists": len(pods) > 0,
        "count": len(pods),
        "pods": [
            {
                "name": p["metadata"]["name"],
                "status": p["status"]["phase"]
            }
            for p in pods
        ]
    }
