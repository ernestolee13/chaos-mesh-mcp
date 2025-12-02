"""PhysicalMachineChaos tools for injecting chaos on physical/virtual machines.

PhysicalMachineChaos requires Chaosd agent running on target machines.
Supports two targeting modes (mutually exclusive):
- address: Direct IP/hostname list
- selector: Label-based selection via Chaos Mesh Chaosd discovery
"""

import uuid
from typing import Dict, Any, List, Optional
from ..kubectl import KubectlRunner
from ..templates import render_physical_chaos


async def create_physical_stress_cpu(
    namespace: str,
    duration: str,
    address: Optional[List[str]] = None,
    selector: Optional[Dict[str, str]] = None,
    mode: str = "one",
    workers: int = 1,
    load: Optional[int] = None
) -> Dict[str, Any]:
    """Create PhysicalMachineChaos to stress CPU on physical/virtual machines.

    Injects CPU stress on target machines using stress-ng.

    Args:
        namespace: Namespace to create the chaos resource
        duration: Duration (e.g., "30s", "5m")
        address: List of target machine addresses (IP or hostname)
        selector: Label selectors for target machines
        mode: Selection mode ("one", "all", "fixed", "fixed-percent", "random-max-percent")
        workers: Number of CPU stress workers (default: 1)
        load: CPU load percentage per worker (0-100, optional)

    Returns:
        Chaos experiment details

    Note:
        - Requires Chaosd agent running on target machines
        - Must specify EITHER address OR selector, not both
        - Load parameter sets CPU load %, without it uses 100%

    Raises:
        ValueError: If both address and selector specified, or neither specified

    Example:
        result = await create_physical_stress_cpu(
            namespace="default",
            address=["192.168.1.100", "192.168.1.101"],
            duration="60s",
            workers=2,
            load=80
        )
    """
    # Validate targeting parameters
    if address and selector:
        raise ValueError("Cannot specify both 'address' and 'selector'. Choose one targeting mode.")
    if not address and not selector:
        raise ValueError("Must specify either 'address' or 'selector' for targeting.")

    name = f"physical-cpu-stress-{uuid.uuid4().hex[:8]}"

    action_params = {
        "workers": workers
    }
    if load is not None:
        if not 0 <= load <= 100:
            raise ValueError(f"CPU load must be between 0-100, got {load}")
        action_params["load"] = load

    yaml_content = render_physical_chaos(
        name=name,
        namespace=namespace,
        action="stress-cpu",
        duration=duration,
        mode=mode,
        address=address,
        selector=selector,
        **action_params
    )

    kubectl = KubectlRunner()
    result = await kubectl.apply_yaml(yaml_content, namespace)

    return {
        "experiment_id": name,
        "kind": "PhysicalMachineChaos",
        "action": "stress-cpu",
        "namespace": namespace,
        "target_mode": "address" if address else "selector",
        "targets": address if address else selector,
        "parameters": {
            "duration": duration,
            "mode": mode,
            "workers": workers,
            "load": load
        },
        "status": result
    }


async def create_physical_stress_memory(
    namespace: str,
    duration: str,
    address: Optional[List[str]] = None,
    selector: Optional[Dict[str, str]] = None,
    mode: str = "one",
    size: Optional[str] = None
) -> Dict[str, Any]:
    """Create PhysicalMachineChaos to stress memory on physical/virtual machines.

    Injects memory stress on target machines using stress-ng.

    Args:
        namespace: Namespace to create the chaos resource
        duration: Duration (e.g., "30s", "5m")
        address: List of target machine addresses (IP or hostname)
        selector: Label selectors for target machines
        mode: Selection mode ("one", "all", "fixed", "fixed-percent", "random-max-percent")
        size: Memory size to allocate (e.g., "256MB", "1GB"). If not specified, allocates all available memory.

    Returns:
        Chaos experiment details

    Note:
        - Requires Chaosd agent running on target machines
        - Must specify EITHER address OR selector, not both
        - Without size parameter, stress-ng will consume all available memory

    Raises:
        ValueError: If both address and selector specified, or neither specified

    Example:
        result = await create_physical_stress_memory(
            namespace="default",
            address=["192.168.1.100"],
            duration="60s",
            size="512MB"
        )
    """
    # Validate targeting parameters
    if address and selector:
        raise ValueError("Cannot specify both 'address' and 'selector'. Choose one targeting mode.")
    if not address and not selector:
        raise ValueError("Must specify either 'address' or 'selector' for targeting.")

    name = f"physical-mem-stress-{uuid.uuid4().hex[:8]}"

    action_params = {}
    if size:
        action_params["size"] = size

    yaml_content = render_physical_chaos(
        name=name,
        namespace=namespace,
        action="stress-mem",
        duration=duration,
        mode=mode,
        address=address,
        selector=selector,
        **action_params
    )

    kubectl = KubectlRunner()
    result = await kubectl.apply_yaml(yaml_content, namespace)

    return {
        "experiment_id": name,
        "kind": "PhysicalMachineChaos",
        "action": "stress-mem",
        "namespace": namespace,
        "target_mode": "address" if address else "selector",
        "targets": address if address else selector,
        "parameters": {
            "duration": duration,
            "mode": mode,
            "size": size
        },
        "status": result
    }


async def create_physical_disk_fill(
    namespace: str,
    duration: str,
    path: str,
    size: str,
    address: Optional[List[str]] = None,
    selector: Optional[Dict[str, str]] = None,
    mode: str = "one",
    fill_by_fallocate: bool = True
) -> Dict[str, Any]:
    """Create PhysicalMachineChaos to fill disk space on physical/virtual machines.

    Fills disk space by creating large files at the specified path.

    Args:
        namespace: Namespace to create the chaos resource
        duration: Duration (e.g., "30s", "5m")
        path: Directory path to fill (must exist)
        size: Size to fill (e.g., "1GB", "500MB")
        address: List of target machine addresses (IP or hostname)
        selector: Label selectors for target machines
        mode: Selection mode ("one", "all", "fixed", "fixed-percent", "random-max-percent")
        fill_by_fallocate: Use fallocate for faster filling (default: True)

    Returns:
        Chaos experiment details

    Note:
        - Requires Chaosd agent running on target machines
        - Must specify EITHER address OR selector, not both
        - Target directory must exist and be writable
        - fallocate is faster but may not work on all filesystems

    Raises:
        ValueError: If both address and selector specified, or neither specified

    Example:
        result = await create_physical_disk_fill(
            namespace="default",
            address=["192.168.1.100"],
            path="/tmp/chaos-fill",
            size="2GB",
            duration="5m"
        )
    """
    # Validate targeting parameters
    if address and selector:
        raise ValueError("Cannot specify both 'address' and 'selector'. Choose one targeting mode.")
    if not address and not selector:
        raise ValueError("Must specify either 'address' or 'selector' for targeting.")

    name = f"physical-disk-fill-{uuid.uuid4().hex[:8]}"

    action_params = {
        "path": path,
        "size": size,
        "fill_by_fallocate": fill_by_fallocate
    }

    yaml_content = render_physical_chaos(
        name=name,
        namespace=namespace,
        action="disk-fill",
        duration=duration,
        mode=mode,
        address=address,
        selector=selector,
        **action_params
    )

    kubectl = KubectlRunner()
    result = await kubectl.apply_yaml(yaml_content, namespace)

    return {
        "experiment_id": name,
        "kind": "PhysicalMachineChaos",
        "action": "disk-fill",
        "namespace": namespace,
        "target_mode": "address" if address else "selector",
        "targets": address if address else selector,
        "parameters": {
            "duration": duration,
            "mode": mode,
            "path": path,
            "size": size,
            "fill_by_fallocate": fill_by_fallocate
        },
        "status": result
    }


async def create_physical_process_kill(
    namespace: str,
    duration: str,
    process: str,
    address: Optional[List[str]] = None,
    selector: Optional[Dict[str, str]] = None,
    mode: str = "one",
    signal: int = 9
) -> Dict[str, Any]:
    """Create PhysicalMachineChaos to kill processes on physical/virtual machines.

    Kills processes matching the specified name or pattern.

    Args:
        namespace: Namespace to create the chaos resource
        duration: Duration (e.g., "30s", "5m")
        process: Process name or pattern to kill
        address: List of target machine addresses (IP or hostname)
        selector: Label selectors for target machines
        mode: Selection mode ("one", "all", "fixed", "fixed-percent", "random-max-percent")
        signal: Signal number to send (default: 9 for SIGKILL)

    Returns:
        Chaos experiment details

    Note:
        - Requires Chaosd agent running on target machines
        - Must specify EITHER address OR selector, not both
        - Common signals: 9 (SIGKILL), 15 (SIGTERM), 2 (SIGINT)
        - Process matching is done via pattern matching

    Raises:
        ValueError: If both address and selector specified, or neither specified

    Example:
        result = await create_physical_process_kill(
            namespace="default",
            address=["192.168.1.100"],
            process="nginx",
            duration="60s",
            signal=15  # SIGTERM for graceful shutdown
        )
    """
    # Validate targeting parameters
    if address and selector:
        raise ValueError("Cannot specify both 'address' and 'selector'. Choose one targeting mode.")
    if not address and not selector:
        raise ValueError("Must specify either 'address' or 'selector' for targeting.")

    name = f"physical-proc-kill-{uuid.uuid4().hex[:8]}"

    action_params = {
        "process": process,
        "signal": signal
    }

    yaml_content = render_physical_chaos(
        name=name,
        namespace=namespace,
        action="process",
        duration=duration,
        mode=mode,
        address=address,
        selector=selector,
        **action_params
    )

    kubectl = KubectlRunner()
    result = await kubectl.apply_yaml(yaml_content, namespace)

    return {
        "experiment_id": name,
        "kind": "PhysicalMachineChaos",
        "action": "process-kill",
        "namespace": namespace,
        "target_mode": "address" if address else "selector",
        "targets": address if address else selector,
        "parameters": {
            "duration": duration,
            "mode": mode,
            "process": process,
            "signal": signal
        },
        "status": result
    }


async def create_physical_clock_skew(
    namespace: str,
    duration: str,
    time_offset: str,
    pid: int,
    address: Optional[List[str]] = None,
    selector: Optional[Dict[str, str]] = None,
    mode: str = "one",
    clock_ids: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Create PhysicalMachineChaos to skew system clock on physical/virtual machines.

    Offsets the system clock by the specified duration for a target process.

    Args:
        namespace: Namespace to create the chaos resource
        duration: Duration (e.g., "30s", "5m")
        time_offset: Time offset to apply (e.g., "5m", "-10s", "1h")
        pid: Process ID to inject clock skew (required)
        address: List of target machine addresses (IP or hostname)
        selector: Label selectors for target machines
        mode: Selection mode ("one", "all", "fixed", "fixed-percent", "random-max-percent")
        clock_ids: Clock IDs to skew (default: ["CLOCK_REALTIME"])

    Returns:
        Chaos experiment details

    Note:
        - Requires Chaosd agent running on target machines
        - Must specify EITHER address OR selector, not both
        - PID is REQUIRED for clock skew injection
        - Positive offset moves clock forward, negative moves backward
        - Common clock IDs: CLOCK_REALTIME, CLOCK_MONOTONIC
        - Requires appropriate permissions on target machines

    Raises:
        ValueError: If both address and selector specified, or neither specified

    Example:
        result = await create_physical_clock_skew(
            namespace="default",
            address=["192.168.1.100"],
            time_offset="10m",
            pid=1234,
            duration="5m",
            clock_ids=["CLOCK_REALTIME"]
        )
    """
    # Validate targeting parameters
    if address and selector:
        raise ValueError("Cannot specify both 'address' and 'selector'. Choose one targeting mode.")
    if not address and not selector:
        raise ValueError("Must specify either 'address' or 'selector' for targeting.")

    name = f"physical-clock-skew-{uuid.uuid4().hex[:8]}"

    action_params = {
        "time_offset": time_offset,
        "pid": pid
    }
    if clock_ids:
        action_params["clock_ids"] = clock_ids

    yaml_content = render_physical_chaos(
        name=name,
        namespace=namespace,
        action="clock",
        duration=duration,
        mode=mode,
        address=address,
        selector=selector,
        **action_params
    )

    kubectl = KubectlRunner()
    result = await kubectl.apply_yaml(yaml_content, namespace)

    return {
        "experiment_id": name,
        "kind": "PhysicalMachineChaos",
        "action": "clock-skew",
        "namespace": namespace,
        "target_mode": "address" if address else "selector",
        "targets": address if address else selector,
        "parameters": {
            "duration": duration,
            "mode": mode,
            "time_offset": time_offset,
            "pid": pid,
            "clock_ids": clock_ids or ["CLOCK_REALTIME"]
        },
        "status": result
    }
