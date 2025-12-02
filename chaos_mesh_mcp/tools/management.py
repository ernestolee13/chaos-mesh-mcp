"""Management tools for Chaos Mesh experiments."""

from typing import Dict, Any, List, Optional
from ..kubectl import get_resource, list_resources, delete_resource, KubectlError
from ..templates import interpret_chaos_status


# All Chaos Mesh kinds
CHAOS_KINDS = [
    "NetworkChaos",
    "StressChaos",
    "PodChaos",
    "IOChaos",
    "HTTPChaos",
    "DNSChaos",
    "PhysicalMachineChaos",
    "TimeChaos",
    "KernelChaos"
]


async def get_experiment_status(experiment_id: str, namespace: str = "default") -> Dict[str, Any]:
    """Get status of a Chaos experiment.

    Automatically detects the experiment kind and returns detailed status.

    Args:
        experiment_id: Experiment name/ID
        namespace: Kubernetes namespace. Default: "default"

    Returns:
        Status dictionary with phase, affected pods, and details

    Example:
        >>> await get_experiment_status("network-delay-a3f4b2c1")
        {
            "experiment_id": "network-delay-a3f4b2c1",
            "kind": "NetworkChaos",
            "namespace": "default",
            "phase": "Running",
            "injected_pods": 1,
            "message": "Successfully injected chaos",
            "spec": {...}
        }

    Raises:
        ValueError: If experiment not found
    """
    # Try each chaos kind
    for kind in CHAOS_KINDS:
        try:
            chaos_obj = get_resource(kind, experiment_id, namespace)

            # Interpret status
            status = interpret_chaos_status(chaos_obj)

            return {
                "experiment_id": experiment_id,
                "kind": kind,
                "namespace": namespace,
                "phase": status["phase"],
                "injected_pods": status["injected_pods"],
                "message": status["message"],
                "records": status["records"],
                "spec": chaos_obj.get("spec", {})
            }
        except KubectlError:
            continue

    raise ValueError(
        f"Experiment '{experiment_id}' not found in namespace '{namespace}'. "
        f"Checked: {', '.join(CHAOS_KINDS)}"
    )


async def list_active_experiments(namespace: str = "default", kind: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all active Chaos experiments.

    Args:
        namespace: Kubernetes namespace. Default: "default"
        kind: Optional filter by kind (e.g., "NetworkChaos"). If None, lists all.

    Returns:
        List of experiment summaries

    Example:
        >>> await list_active_experiments()
        [
            {
                "experiment_id": "network-delay-a3f4b2c1",
                "kind": "NetworkChaos",
                "phase": "Running",
                "created": "2025-01-07T12:30:45Z",
                "duration": "120s"
            },
            {
                "experiment_id": "stress-cpu-f3a2b1c4",
                "kind": "StressChaos",
                "phase": "Finished",
                "created": "2025-01-07T12:25:30Z",
                "duration": "60s"
            }
        ]
    """
    experiments = []

    # Determine which kinds to check
    kinds_to_check = [kind] if kind else CHAOS_KINDS

    for chaos_kind in kinds_to_check:
        try:
            resources = list_resources(chaos_kind, namespace=namespace)

            for resource in resources:
                metadata = resource.get("metadata", {})
                spec = resource.get("spec", {})
                status_info = interpret_chaos_status(resource)

                experiments.append({
                    "experiment_id": metadata.get("name"),
                    "kind": chaos_kind,
                    "namespace": metadata.get("namespace", namespace),
                    "phase": status_info["phase"],
                    "created": metadata.get("creationTimestamp"),
                    "duration": spec.get("duration"),
                    "action": spec.get("action"),
                    "mode": spec.get("mode")
                })
        except Exception:
            # Skip if kind doesn't exist or error
            continue

    return experiments


async def delete_experiment(experiment_id: str, namespace: str = "default") -> Dict[str, Any]:
    """Delete a Chaos experiment.

    Stops the experiment and removes it from the cluster.

    Args:
        experiment_id: Experiment name/ID
        namespace: Kubernetes namespace. Default: "default"

    Returns:
        Deletion result

    Example:
        >>> await delete_experiment("network-delay-a3f4b2c1")
        {
            "status": "deleted",
            "experiment_id": "network-delay-a3f4b2c1",
            "kind": "NetworkChaos"
        }

    Raises:
        ValueError: If experiment not found
    """
    # Find the experiment kind first
    found_kind = None
    for kind in CHAOS_KINDS:
        try:
            get_resource(kind, experiment_id, namespace)
            found_kind = kind
            break
        except KubectlError:
            continue

    if not found_kind:
        raise ValueError(f"Experiment '{experiment_id}' not found in namespace '{namespace}'")

    # Delete it
    delete_resource(found_kind, experiment_id, namespace)

    return {
        "status": "deleted",
        "experiment_id": experiment_id,
        "kind": found_kind,
        "namespace": namespace
    }


async def pause_experiment(experiment_id: str, namespace: str = "default") -> Dict[str, Any]:
    """Pause a running Chaos experiment.

    Uses Chaos Mesh annotation to pause the experiment.

    Args:
        experiment_id: Experiment name/ID
        namespace: Kubernetes namespace

    Returns:
        Pause result

    Example:
        >>> await pause_experiment("network-delay-a3f4b2c1")
    """
    import subprocess

    # Find experiment kind
    found_kind = None
    for kind in CHAOS_KINDS:
        try:
            get_resource(kind, experiment_id, namespace)
            found_kind = kind
            break
        except KubectlError:
            continue

    if not found_kind:
        raise ValueError(f"Experiment '{experiment_id}' not found")

    # Annotate to pause
    result = subprocess.run(
        [
            "kubectl", "annotate",
            f"{found_kind.lower()}/{experiment_id}",
            "-n", namespace,
            "experiment.chaos-mesh.org/pause=true",
            "--overwrite"
        ],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"Failed to pause experiment: {result.stderr}")

    return {
        "status": "paused",
        "experiment_id": experiment_id,
        "kind": found_kind
    }


async def resume_experiment(experiment_id: str, namespace: str = "default") -> Dict[str, Any]:
    """Resume a paused Chaos experiment.

    Args:
        experiment_id: Experiment name/ID
        namespace: Kubernetes namespace

    Returns:
        Resume result
    """
    import subprocess

    # Find experiment kind
    found_kind = None
    for kind in CHAOS_KINDS:
        try:
            get_resource(kind, experiment_id, namespace)
            found_kind = kind
            break
        except KubectlError:
            continue

    if not found_kind:
        raise ValueError(f"Experiment '{experiment_id}' not found")

    # Remove pause annotation
    result = subprocess.run(
        [
            "kubectl", "annotate",
            f"{found_kind.lower()}/{experiment_id}",
            "-n", namespace,
            "experiment.chaos-mesh.org/pause-"
        ],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"Failed to resume experiment: {result.stderr}")

    return {
        "status": "resumed",
        "experiment_id": experiment_id,
        "kind": found_kind
    }


async def get_experiment_events(experiment_id: str, namespace: str = "default") -> List[Dict[str, Any]]:
    """Get Kubernetes events related to an experiment.

    Args:
        experiment_id: Experiment name/ID
        namespace: Kubernetes namespace

    Returns:
        List of events

    Example:
        >>> await get_experiment_events("network-delay-a3f4b2c1")
        [
            {
                "type": "Normal",
                "reason": "Created",
                "message": "Successfully created chaos experiment",
                "timestamp": "2025-01-07T12:30:45Z"
            }
        ]
    """
    import subprocess
    import json

    result = subprocess.run(
        [
            "kubectl", "get", "events",
            "-n", namespace,
            "--field-selector", f"involvedObject.name={experiment_id}",
            "-o", "json"
        ],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return []

    data = json.loads(result.stdout)
    events = []

    for item in data.get("items", []):
        events.append({
            "type": item.get("type"),
            "reason": item.get("reason"),
            "message": item.get("message"),
            "timestamp": item.get("lastTimestamp") or item.get("firstTimestamp"),
            "count": item.get("count", 1)
        })

    return events
