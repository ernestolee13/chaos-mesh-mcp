"""NetworkChaos tools for MCP."""

from typing import Dict, Any, Optional, List
from ..validators import (
    validate_duration,
    validate_percentage,
    validate_direction,
    validate_bandwidth,
    validate_mode,
    validate_labels
)
from ..templates import generate_name, render_network_chaos
from ..kubectl import apply_yaml, check_target_exists


async def create_network_delay(
    namespace: str,
    target_labels: Dict[str, str],
    latency: str,
    duration: str,
    jitter: str = "0ms",
    correlation: str = "0",
    mode: str = "all",
    direction: str = "to",
    external_targets: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Create NetworkChaos with delay action.

    Injects network latency to target pods.

    Args:
        namespace: Target namespace
        target_labels: Label selectors for target pods (e.g., {"app": "mongodb"})
        latency: Network delay amount (e.g., "10ms", "800ms", "1s")
        duration: Experiment duration (e.g., "60s", "5m")
        jitter: Delay variance (e.g., "100ms"). Default: "0ms"
        correlation: Correlation to previous delay [0-100]. Default: "0"
        mode: Selection mode (one/all/fixed/fixed-percent). Default: "all"
        direction: Traffic direction (to/from/both). Default: "to"
        external_targets: Optional external IPs/domains (e.g., ["1.1.1.1", "google.com"])

    Returns:
        Experiment details with experiment_id and affected_pods

    Example:
        >>> await create_network_delay(
        ...     namespace="default",
        ...     target_labels={"app": "mongodb"},
        ...     latency="800ms",
        ...     jitter="100ms",
        ...     duration="120s"
        ... )
        {
            "experiment_id": "network-delay-a3f4b2c1",
            "kind": "NetworkChaos",
            "action": "delay",
            "affected_pods": ["mongodb-0"],
            "parameters": {"latency": "800ms", "jitter": "100ms"}
        }
    """
    # Validate parameters
    validate_labels(target_labels)
    validate_duration(latency)
    validate_duration(duration)
    validate_duration(jitter)
    validate_percentage(correlation)
    validate_mode(mode)
    validate_direction(direction)

    # Check if target pods exist
    target_check = check_target_exists(namespace, target_labels)
    if not target_check["exists"]:
        raise ValueError(
            f"No pods found with labels {target_labels} in namespace '{namespace}'. "
            f"Please verify the label selectors."
        )

    # Generate unique name
    name = generate_name("network-delay")

    # Render YAML
    yaml_content = render_network_chaos(
        name=name,
        namespace=namespace,
        action="delay",
        target_labels=target_labels,
        duration=duration,
        mode=mode,
        latency=latency,
        jitter=jitter,
        correlation=correlation,
        direction=direction,
        external_targets=external_targets
    )

    # Apply
    apply_yaml(yaml_content)

    return {
        "experiment_id": name,
        "kind": "NetworkChaos",
        "action": "delay",
        "namespace": namespace,
        "affected_pods": [p["name"] for p in target_check["pods"]],
        "parameters": {
            "latency": latency,
            "jitter": jitter,
            "correlation": correlation,
            "direction": direction
        },
        "duration": duration
    }


async def create_network_loss(
    namespace: str,
    target_labels: Dict[str, str],
    loss: str,
    duration: str,
    correlation: str = "0",
    mode: str = "all",
    direction: str = "to"
) -> Dict[str, Any]:
    """Create NetworkChaos with packet loss action.

    Drops network packets to simulate packet loss.

    Args:
        namespace: Target namespace
        target_labels: Label selectors for target pods
        loss: Packet loss probability [0-100] (e.g., "50" for 50%)
        duration: Experiment duration
        correlation: Correlation to previous loss [0-100]. Default: "0"
        mode: Selection mode. Default: "all"
        direction: Traffic direction. Default: "to"

    Returns:
        Experiment details

    Example:
        >>> await create_network_loss(
        ...     namespace="default",
        ...     target_labels={"app": "api-server"},
        ...     loss="10",  # 10% packet loss
        ...     duration="60s"
        ... )
    """
    # Validate
    validate_labels(target_labels)
    validate_percentage(loss)
    validate_duration(duration)
    validate_percentage(correlation)
    validate_mode(mode)
    validate_direction(direction)

    # Check target
    target_check = check_target_exists(namespace, target_labels)
    if not target_check["exists"]:
        raise ValueError(f"No pods found with labels {target_labels}")

    # Generate and apply
    name = generate_name("network-loss")
    yaml_content = render_network_chaos(
        name=name,
        namespace=namespace,
        action="loss",
        target_labels=target_labels,
        duration=duration,
        mode=mode,
        loss=loss,
        correlation=correlation,
        direction=direction
    )

    apply_yaml(yaml_content)

    return {
        "experiment_id": name,
        "kind": "NetworkChaos",
        "action": "loss",
        "namespace": namespace,
        "affected_pods": [p["name"] for p in target_check["pods"]],
        "parameters": {
            "loss": loss + "%",
            "correlation": correlation,
            "direction": direction
        },
        "duration": duration
    }


async def create_network_partition(
    namespace: str,
    target_labels: Dict[str, str],
    duration: str,
    direction: str = "both",
    mode: str = "all",
    external_targets: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Create NetworkChaos with partition action.

    Simulates network partition (network split).

    Args:
        namespace: Target namespace
        target_labels: Label selectors for target pods
        duration: Experiment duration
        direction: Partition direction (to/from/both). Default: "both"
        mode: Selection mode. Default: "all"
        external_targets: Optional external targets to partition from

    Returns:
        Experiment details

    Example:
        >>> await create_network_partition(
        ...     namespace="default",
        ...     target_labels={"app": "etcd"},
        ...     duration="30s",
        ...     direction="both"
        ... )
    """
    # Validate
    validate_labels(target_labels)
    validate_duration(duration)
    validate_direction(direction)
    validate_mode(mode)

    # Check target
    target_check = check_target_exists(namespace, target_labels)
    if not target_check["exists"]:
        raise ValueError(f"No pods found with labels {target_labels}")

    # Generate and apply
    name = generate_name("network-partition")
    yaml_content = render_network_chaos(
        name=name,
        namespace=namespace,
        action="partition",
        target_labels=target_labels,
        duration=duration,
        mode=mode,
        direction=direction,
        external_targets=external_targets
    )

    apply_yaml(yaml_content)

    return {
        "experiment_id": name,
        "kind": "NetworkChaos",
        "action": "partition",
        "namespace": namespace,
        "affected_pods": [p["name"] for p in target_check["pods"]],
        "parameters": {
            "direction": direction
        },
        "duration": duration
    }


async def create_network_corrupt(
    namespace: str,
    target_labels: Dict[str, str],
    corrupt: str,
    duration: str,
    correlation: str = "0",
    mode: str = "all",
    direction: str = "to"
) -> Dict[str, Any]:
    """Create NetworkChaos with corrupt action.

    Corrupts network packets.

    Args:
        namespace: Target namespace
        target_labels: Label selectors for target pods
        corrupt: Corruption probability [0-100] (e.g., "50" for 50%)
        duration: Experiment duration
        correlation: Correlation to previous corruption [0-100]. Default: "0"
        mode: Selection mode. Default: "all"
        direction: Traffic direction. Default: "to"

    Returns:
        Experiment details
    """
    # Validate
    validate_labels(target_labels)
    validate_percentage(corrupt)
    validate_duration(duration)
    validate_percentage(correlation)
    validate_mode(mode)
    validate_direction(direction)

    # Check target
    target_check = check_target_exists(namespace, target_labels)
    if not target_check["exists"]:
        raise ValueError(f"No pods found with labels {target_labels}")

    # Generate and apply
    name = generate_name("network-corrupt")
    yaml_content = render_network_chaos(
        name=name,
        namespace=namespace,
        action="corrupt",
        target_labels=target_labels,
        duration=duration,
        mode=mode,
        corrupt=corrupt,
        correlation=correlation,
        direction=direction
    )

    apply_yaml(yaml_content)

    return {
        "experiment_id": name,
        "kind": "NetworkChaos",
        "action": "corrupt",
        "namespace": namespace,
        "affected_pods": [p["name"] for p in target_check["pods"]],
        "parameters": {
            "corrupt": corrupt + "%",
            "correlation": correlation,
            "direction": direction
        },
        "duration": duration
    }
