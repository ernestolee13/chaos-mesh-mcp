"""StressChaos tools for MCP."""

from typing import Dict, Any, Optional
from ..validators import validate_duration, validate_memory_size, validate_mode, validate_labels
from ..templates import generate_name, render_stress_chaos
from ..kubectl import apply_yaml, check_target_exists


async def create_stress_cpu(
    namespace: str,
    target_labels: Dict[str, str],
    workers: int,
    duration: str,
    load: Optional[int] = None,
    mode: str = "all"
) -> Dict[str, Any]:
    """Create StressChaos with CPU stress.

    Applies CPU stress to target containers.

    Args:
        namespace: Target namespace
        target_labels: Label selectors for target pods
        workers: Number of CPU stress workers (threads)
        duration: Experiment duration (e.g., "60s", "5m")
        load: CPU load percentage per worker (0-100). Optional.
              0 = no load, 100 = full load on one core
        mode: Selection mode (one/all/fixed/fixed-percent). Default: "all"

    Returns:
        Experiment details

    Example:
        >>> await create_stress_cpu(
        ...     namespace="default",
        ...     target_labels={"app": "api-server"},
        ...     workers=4,
        ...     load=80,
        ...     duration="120s"
        ... )
        {
            "experiment_id": "stress-cpu-f3a2b1c4",
            "kind": "StressChaos",
            "stressor": "cpu",
            "affected_pods": ["api-server-0"],
            "parameters": {"workers": 4, "load": 80}
        }
    """
    # Validate
    validate_labels(target_labels)
    validate_duration(duration)
    validate_mode(mode)

    if workers < 1 or workers > 16:
        raise ValueError(f"CPU workers must be 1-16, got {workers}")

    if load is not None and (load < 0 or load > 100):
        raise ValueError(f"CPU load must be 0-100, got {load}")

    # Check target
    target_check = check_target_exists(namespace, target_labels)
    if not target_check["exists"]:
        raise ValueError(f"No pods found with labels {target_labels} in namespace '{namespace}'")

    # Generate and apply
    name = generate_name("stress-cpu")
    yaml_content = render_stress_chaos(
        name=name,
        namespace=namespace,
        target_labels=target_labels,
        duration=duration,
        mode=mode,
        cpu_workers=workers,
        cpu_load=load
    )

    apply_yaml(yaml_content)

    return {
        "experiment_id": name,
        "kind": "StressChaos",
        "stressor": "cpu",
        "namespace": namespace,
        "affected_pods": [p["name"] for p in target_check["pods"]],
        "parameters": {
            "workers": workers,
            "load": load
        },
        "duration": duration
    }


async def create_stress_memory(
    namespace: str,
    target_labels: Dict[str, str],
    size: str,
    duration: str,
    workers: int = 1,
    mode: str = "all"
) -> Dict[str, Any]:
    """Create StressChaos with memory stress.

    Applies memory stress to target containers by allocating and using memory.

    Args:
        namespace: Target namespace
        target_labels: Label selectors for target pods
        size: Memory size to allocate (e.g., "256MB", "1GB", "512MB")
        duration: Experiment duration
        workers: Number of memory stress workers. Default: 1
        mode: Selection mode. Default: "all"

    Returns:
        Experiment details

    Example:
        >>> await create_stress_memory(
        ...     namespace="default",
        ...     target_labels={"app": "vllm-generate"},
        ...     size="1GB",
        ...     workers=4,
        ...     duration="300s"
        ... )
    """
    # Validate
    validate_labels(target_labels)
    validate_memory_size(size)
    validate_duration(duration)
    validate_mode(mode)

    if workers < 1 or workers > 8:
        raise ValueError(f"Memory workers must be 1-8, got {workers}")

    # Check target
    target_check = check_target_exists(namespace, target_labels)
    if not target_check["exists"]:
        raise ValueError(f"No pods found with labels {target_labels}")

    # Generate and apply
    name = generate_name("stress-memory")
    yaml_content = render_stress_chaos(
        name=name,
        namespace=namespace,
        target_labels=target_labels,
        duration=duration,
        mode=mode,
        memory_workers=workers,
        memory_size=size
    )

    apply_yaml(yaml_content)

    return {
        "experiment_id": name,
        "kind": "StressChaos",
        "stressor": "memory",
        "namespace": namespace,
        "affected_pods": [p["name"] for p in target_check["pods"]],
        "parameters": {
            "workers": workers,
            "size": size
        },
        "duration": duration
    }


async def create_stress_combined(
    namespace: str,
    target_labels: Dict[str, str],
    duration: str,
    cpu_workers: int,
    cpu_load: Optional[int],
    memory_workers: int,
    memory_size: str,
    mode: str = "all"
) -> Dict[str, Any]:
    """Create StressChaos with both CPU and memory stress.

    Applies both CPU and memory stress simultaneously.

    Args:
        namespace: Target namespace
        target_labels: Label selectors for target pods
        duration: Experiment duration
        cpu_workers: Number of CPU stress workers
        cpu_load: CPU load percentage
        memory_workers: Number of memory stress workers
        memory_size: Memory size to allocate
        mode: Selection mode. Default: "all"

    Returns:
        Experiment details
    """
    # Validate
    validate_labels(target_labels)
    validate_duration(duration)
    validate_memory_size(memory_size)
    validate_mode(mode)

    # Check target
    target_check = check_target_exists(namespace, target_labels)
    if not target_check["exists"]:
        raise ValueError(f"No pods found with labels {target_labels}")

    # Generate and apply
    name = generate_name("stress-combined")
    yaml_content = render_stress_chaos(
        name=name,
        namespace=namespace,
        target_labels=target_labels,
        duration=duration,
        mode=mode,
        cpu_workers=cpu_workers,
        cpu_load=cpu_load,
        memory_workers=memory_workers,
        memory_size=memory_size
    )

    apply_yaml(yaml_content)

    return {
        "experiment_id": name,
        "kind": "StressChaos",
        "stressor": "combined",
        "namespace": namespace,
        "affected_pods": [p["name"] for p in target_check["pods"]],
        "parameters": {
            "cpu_workers": cpu_workers,
            "cpu_load": cpu_load,
            "memory_workers": memory_workers,
            "memory_size": memory_size
        },
        "duration": duration
    }
