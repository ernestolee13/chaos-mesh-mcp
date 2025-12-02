"""PodChaos tools for MCP."""

from typing import Dict, Any, Optional, List
from ..validators import validate_duration, validate_mode, validate_labels
from ..templates import generate_name, render_pod_chaos
from ..kubectl import apply_yaml, check_target_exists


async def create_pod_kill(
    namespace: str,
    target_labels: Dict[str, str],
    duration: str,
    mode: str = "one",
    grace_period: int = 0
) -> Dict[str, Any]:
    """Create PodChaos with pod-kill action.

    Kills target pods. Pods will be recreated by their controller (Deployment, StatefulSet, etc.).

    Args:
        namespace: Target namespace
        target_labels: Label selectors for target pods
        duration: Experiment duration (kills will repeat during this period)
        mode: Selection mode (one/all/fixed/fixed-percent). Default: "one" (safer)
        grace_period: Grace period in seconds before killing. Default: 0 (immediate)

    Returns:
        Experiment details

    Example:
        >>> await create_pod_kill(
        ...     namespace="default",
        ...     target_labels={"app": "test-service"},
        ...     duration="60s",
        ...     mode="one",
        ...     grace_period=5
        ... )
        {
            "experiment_id": "pod-kill-a1b2c3d4",
            "kind": "PodChaos",
            "action": "pod-kill",
            "affected_pods": ["test-service-0"],
            "parameters": {"grace_period": 5}
        }
    """
    # Validate
    validate_labels(target_labels)
    validate_duration(duration)
    validate_mode(mode)

    if grace_period < 0:
        raise ValueError(f"Grace period must be >= 0, got {grace_period}")

    # Check target
    target_check = check_target_exists(namespace, target_labels)
    if not target_check["exists"]:
        raise ValueError(f"No pods found with labels {target_labels} in namespace '{namespace}'")

    # Safety check: warn if mode is "all"
    if mode == "all" and target_check["count"] > 1:
        # This will kill ALL pods - potentially dangerous
        pass  # MCP will log this, user should be aware

    # Generate and apply
    name = generate_name("pod-kill")
    yaml_content = render_pod_chaos(
        name=name,
        namespace=namespace,
        action="pod-kill",
        target_labels=target_labels,
        duration=duration,
        mode=mode,
        grace_period=grace_period
    )

    apply_yaml(yaml_content)

    return {
        "experiment_id": name,
        "kind": "PodChaos",
        "action": "pod-kill",
        "namespace": namespace,
        "affected_pods": [p["name"] for p in target_check["pods"]],
        "parameters": {
            "grace_period": grace_period,
            "mode": mode
        },
        "duration": duration,
        "warning": "Pods will be killed and recreated during the duration" if mode == "all" else None
    }


async def create_pod_failure(
    namespace: str,
    target_labels: Dict[str, str],
    duration: str,
    mode: str = "one"
) -> Dict[str, Any]:
    """Create PodChaos with pod-failure action.

    Makes target pods temporarily unavailable without actually killing them.
    Pods become available again after the experiment ends.

    Args:
        namespace: Target namespace
        target_labels: Label selectors for target pods
        duration: Experiment duration
        mode: Selection mode. Default: "one"

    Returns:
        Experiment details

    Example:
        >>> await create_pod_failure(
        ...     namespace="default",
        ...     target_labels={"app": "mongodb"},
        ...     duration="30s",
        ...     mode="one"
        ... )
    """
    # Validate
    validate_labels(target_labels)
    validate_duration(duration)
    validate_mode(mode)

    # Check target
    target_check = check_target_exists(namespace, target_labels)
    if not target_check["exists"]:
        raise ValueError(f"No pods found with labels {target_labels}")

    # Generate and apply
    name = generate_name("pod-failure")
    yaml_content = render_pod_chaos(
        name=name,
        namespace=namespace,
        action="pod-failure",
        target_labels=target_labels,
        duration=duration,
        mode=mode
    )

    apply_yaml(yaml_content)

    return {
        "experiment_id": name,
        "kind": "PodChaos",
        "action": "pod-failure",
        "namespace": namespace,
        "affected_pods": [p["name"] for p in target_check["pods"]],
        "parameters": {
            "mode": mode
        },
        "duration": duration
    }


async def create_container_kill(
    namespace: str,
    target_labels: Dict[str, str],
    container_names: List[str],
    duration: str,
    mode: str = "one"
) -> Dict[str, Any]:
    """Create PodChaos with container-kill action.

    Kills specific containers within pods. Containers will be restarted by kubelet.

    Args:
        namespace: Target namespace
        target_labels: Label selectors for target pods
        container_names: List of container names to kill
        duration: Experiment duration
        mode: Selection mode. Default: "one"

    Returns:
        Experiment details

    Example:
        >>> await create_container_kill(
        ...     namespace="default",
        ...     target_labels={"app": "vllm-generate"},
        ...     container_names=["vllm"],
        ...     duration="60s"
        ... )
    """
    # Validate
    validate_labels(target_labels)
    validate_duration(duration)
    validate_mode(mode)

    if not container_names:
        raise ValueError("container_names cannot be empty for container-kill action")

    # Check target
    target_check = check_target_exists(namespace, target_labels)
    if not target_check["exists"]:
        raise ValueError(f"No pods found with labels {target_labels}")

    # Generate and apply
    name = generate_name("container-kill")
    yaml_content = render_pod_chaos(
        name=name,
        namespace=namespace,
        action="container-kill",
        target_labels=target_labels,
        duration=duration,
        mode=mode,
        container_names=container_names
    )

    apply_yaml(yaml_content)

    return {
        "experiment_id": name,
        "kind": "PodChaos",
        "action": "container-kill",
        "namespace": namespace,
        "affected_pods": [p["name"] for p in target_check["pods"]],
        "parameters": {
            "container_names": container_names,
            "mode": mode
        },
        "duration": duration
    }
