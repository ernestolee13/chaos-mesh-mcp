"""IOChaos tools for MCP."""

from typing import Dict, Any, Optional, List
from ..validators import (
    validate_duration,
    validate_percentage,
    validate_mode,
    validate_labels
)
from ..templates import generate_name, render_io_chaos
from ..kubectl import apply_yaml, check_target_exists


async def create_io_latency(
    namespace: str,
    target_labels: Dict[str, str],
    volume_path: str,
    path: str,
    delay: str,
    duration: str,
    percent: int = 100,
    mode: str = "all",
    methods: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Create IOChaos with latency action.

    Delays file system calls to simulate slow disk I/O.

    Args:
        namespace: Target namespace
        target_labels: Label selectors for target pods (e.g., {"app": "mysql"})
        volume_path: Volume mount path in the container (e.g., "/var/lib/mysql")
        path: File path pattern to target (e.g., "/var/lib/mysql/*", "**/*.log")
        delay: I/O delay duration (e.g., "10ms", "100ms", "1s")
        duration: Experiment duration (e.g., "60s", "5m")
        percent: Percentage of I/O operations to delay [0-100]. Default: 100
        mode: Selection mode (one/all/fixed/fixed-percent). Default: "all"
        methods: File system methods to target (e.g., ["read", "write"]). Default: all methods

    Returns:
        Experiment details with experiment_id and affected_pods

    Example:
        >>> await create_io_latency(
        ...     namespace="default",
        ...     target_labels={"app": "mysql"},
        ...     volume_path="/var/lib/mysql",
        ...     path="/var/lib/mysql/**/*",
        ...     delay="100ms",
        ...     duration="120s",
        ...     methods=["read", "write"]
        ... )
        {
            "experiment_id": "io-latency-a3f4b2c1",
            "kind": "IOChaos",
            "action": "latency",
            "affected_pods": ["mysql-0"],
            "parameters": {"delay": "100ms", "percent": 100}
        }
    """
    # Validate parameters
    validate_labels(target_labels)
    validate_duration(delay)
    validate_duration(duration)
    validate_percentage(str(percent))
    validate_mode(mode)

    if not volume_path or not volume_path.startswith("/"):
        raise ValueError(f"volume_path must be an absolute path, got: {volume_path}")

    if not path:
        raise ValueError("path is required")

    # Check if target pods exist
    target_check = check_target_exists(namespace, target_labels)
    if not target_check["exists"]:
        raise ValueError(
            f"No pods found with labels {target_labels} in namespace '{namespace}'. "
            f"Please verify the label selectors."
        )

    # Generate unique name
    name = generate_name("io-latency")

    # Render YAML
    yaml_content = render_io_chaos(
        name=name,
        namespace=namespace,
        action="latency",
        target_labels=target_labels,
        duration=duration,
        mode=mode,
        volume_path=volume_path,
        path=path,
        percent=percent,
        delay=delay,
        methods=methods
    )

    # Apply
    apply_yaml(yaml_content)

    return {
        "experiment_id": name,
        "kind": "IOChaos",
        "action": "latency",
        "namespace": namespace,
        "affected_pods": [p["name"] for p in target_check["pods"]],
        "parameters": {
            "volume_path": volume_path,
            "path": path,
            "delay": delay,
            "percent": percent,
            "methods": methods or "all"
        },
        "duration": duration
    }


async def create_io_fault(
    namespace: str,
    target_labels: Dict[str, str],
    volume_path: str,
    path: str,
    errno: int,
    duration: str,
    percent: int = 100,
    mode: str = "all",
    methods: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Create IOChaos with fault action.

    Returns errors for file system calls to simulate I/O failures.

    Args:
        namespace: Target namespace
        target_labels: Label selectors for target pods
        volume_path: Volume mount path in the container
        path: File path pattern to target
        errno: Error number to return (e.g., 5 for EIO, 28 for ENOSPC)
        duration: Experiment duration
        percent: Percentage of I/O operations to fail [0-100]. Default: 100
        mode: Selection mode. Default: "all"
        methods: File system methods to target. Default: all methods

    Returns:
        Experiment details

    Common errno values:
        - 5 (EIO): I/O error
        - 28 (ENOSPC): No space left on device
        - 13 (EACCES): Permission denied
        - 2 (ENOENT): No such file or directory

    Example:
        >>> await create_io_fault(
        ...     namespace="default",
        ...     target_labels={"app": "database"},
        ...     volume_path="/data",
        ...     path="/data/**/*.db",
        ...     errno=28,  # ENOSPC
        ...     duration="60s",
        ...     percent=50,
        ...     methods=["write"]
        ... )
    """
    # Validate
    validate_labels(target_labels)
    validate_duration(duration)
    validate_percentage(str(percent))
    validate_mode(mode)

    if not volume_path or not volume_path.startswith("/"):
        raise ValueError(f"volume_path must be an absolute path, got: {volume_path}")

    if not path:
        raise ValueError("path is required")

    if not isinstance(errno, int) or errno < 0:
        raise ValueError(f"errno must be a positive integer, got: {errno}")

    # Check target
    target_check = check_target_exists(namespace, target_labels)
    if not target_check["exists"]:
        raise ValueError(f"No pods found with labels {target_labels}")

    # Generate and apply
    name = generate_name("io-fault")
    yaml_content = render_io_chaos(
        name=name,
        namespace=namespace,
        action="fault",
        target_labels=target_labels,
        duration=duration,
        mode=mode,
        volume_path=volume_path,
        path=path,
        percent=percent,
        errno=errno,
        methods=methods
    )

    apply_yaml(yaml_content)

    return {
        "experiment_id": name,
        "kind": "IOChaos",
        "action": "fault",
        "namespace": namespace,
        "affected_pods": [p["name"] for p in target_check["pods"]],
        "parameters": {
            "volume_path": volume_path,
            "path": path,
            "errno": errno,
            "percent": percent,
            "methods": methods or "all"
        },
        "duration": duration
    }


async def create_io_attr_override(
    namespace: str,
    target_labels: Dict[str, str],
    volume_path: str,
    path: str,
    duration: str,
    perm: Optional[int] = None,
    size: Optional[int] = None,
    percent: int = 100,
    mode: str = "all",
    methods: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Create IOChaos with attrOverride action.

    Modifies file properties like permissions and size.

    Args:
        namespace: Target namespace
        target_labels: Label selectors for target pods
        volume_path: Volume mount path in the container
        path: File path pattern to target
        duration: Experiment duration
        perm: File permissions in octal (e.g., 0o444 for read-only). Optional
        size: Override file size in bytes. Optional
        percent: Percentage of operations to affect [0-100]. Default: 100
        mode: Selection mode. Default: "all"
        methods: File system methods to target. Default: all methods

    Returns:
        Experiment details

    Example:
        >>> await create_io_attr_override(
        ...     namespace="default",
        ...     target_labels={"app": "web-server"},
        ...     volume_path="/app/config",
        ...     path="/app/config/*.conf",
        ...     duration="60s",
        ...     perm=0o444,  # Read-only
        ...     methods=["getattr"]
        ... )
    """
    # Validate
    validate_labels(target_labels)
    validate_duration(duration)
    validate_percentage(str(percent))
    validate_mode(mode)

    if not volume_path or not volume_path.startswith("/"):
        raise ValueError(f"volume_path must be an absolute path, got: {volume_path}")

    if not path:
        raise ValueError("path is required")

    if perm is None and size is None:
        raise ValueError("At least one of 'perm' or 'size' must be specified")

    if perm is not None and (not isinstance(perm, int) or perm < 0):
        raise ValueError(f"perm must be a positive integer (octal), got: {perm}")

    if size is not None and (not isinstance(size, int) or size < 0):
        raise ValueError(f"size must be a positive integer, got: {size}")

    # Check target
    target_check = check_target_exists(namespace, target_labels)
    if not target_check["exists"]:
        raise ValueError(f"No pods found with labels {target_labels}")

    # Build attr dict
    attr = {}
    if perm is not None:
        attr["perm"] = perm
    if size is not None:
        attr["size"] = size

    # Generate and apply
    name = generate_name("io-attr-override")
    yaml_content = render_io_chaos(
        name=name,
        namespace=namespace,
        action="attrOverride",
        target_labels=target_labels,
        duration=duration,
        mode=mode,
        volume_path=volume_path,
        path=path,
        percent=percent,
        attr=attr,
        methods=methods
    )

    apply_yaml(yaml_content)

    return {
        "experiment_id": name,
        "kind": "IOChaos",
        "action": "attrOverride",
        "namespace": namespace,
        "affected_pods": [p["name"] for p in target_check["pods"]],
        "parameters": {
            "volume_path": volume_path,
            "path": path,
            "attr": attr,
            "percent": percent,
            "methods": methods or "all"
        },
        "duration": duration
    }


async def create_io_mistake(
    namespace: str,
    target_labels: Dict[str, str],
    volume_path: str,
    path: str,
    duration: str,
    filling: str = "zero",
    max_occurrences: int = 1,
    max_length: int = 1,
    percent: int = 100,
    mode: str = "all",
    methods: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Create IOChaos with mistake action.

    Makes files read or write wrong values (data corruption).

    Args:
        namespace: Target namespace
        target_labels: Label selectors for target pods
        volume_path: Volume mount path in the container
        path: File path pattern to target
        duration: Experiment duration
        filling: Error filling type: "zero" or "random". Default: "zero"
        max_occurrences: Maximum errors per operation. Default: 1
        max_length: Maximum error length in bytes. Default: 1
        percent: Percentage of operations to affect [0-100]. Default: 100
        mode: Selection mode. Default: "all"
        methods: File system methods to target (e.g., ["read", "write"]). Default: all

    Returns:
        Experiment details

    Example:
        >>> await create_io_mistake(
        ...     namespace="default",
        ...     target_labels={"app": "database"},
        ...     volume_path="/data",
        ...     path="/data/**/*.dat",
        ...     duration="30s",
        ...     filling="random",
        ...     max_occurrences=10,
        ...     max_length=100,
        ...     methods=["read"]
        ... )
    """
    # Validate
    validate_labels(target_labels)
    validate_duration(duration)
    validate_percentage(str(percent))
    validate_mode(mode)

    if not volume_path or not volume_path.startswith("/"):
        raise ValueError(f"volume_path must be an absolute path, got: {volume_path}")

    if not path:
        raise ValueError("path is required")

    if filling not in ["zero", "random"]:
        raise ValueError(f"filling must be 'zero' or 'random', got: {filling}")

    if not isinstance(max_occurrences, int) or max_occurrences < 1:
        raise ValueError(f"max_occurrences must be >= 1, got: {max_occurrences}")

    if not isinstance(max_length, int) or max_length < 1:
        raise ValueError(f"max_length must be >= 1, got: {max_length}")

    # Check target
    target_check = check_target_exists(namespace, target_labels)
    if not target_check["exists"]:
        raise ValueError(f"No pods found with labels {target_labels}")

    # Generate and apply
    name = generate_name("io-mistake")
    yaml_content = render_io_chaos(
        name=name,
        namespace=namespace,
        action="mistake",
        target_labels=target_labels,
        duration=duration,
        mode=mode,
        volume_path=volume_path,
        path=path,
        percent=percent,
        filling=filling,
        max_occurrences=max_occurrences,
        max_length=max_length,
        methods=methods
    )

    apply_yaml(yaml_content)

    return {
        "experiment_id": name,
        "kind": "IOChaos",
        "action": "mistake",
        "namespace": namespace,
        "affected_pods": [p["name"] for p in target_check["pods"]],
        "parameters": {
            "volume_path": volume_path,
            "path": path,
            "filling": filling,
            "max_occurrences": max_occurrences,
            "max_length": max_length,
            "percent": percent,
            "methods": methods or "all"
        },
        "duration": duration
    }
