"""YAML template rendering for Chaos Mesh resources."""

import uuid
import yaml
from typing import Dict, Any, Optional


def generate_name(prefix: str) -> str:
    """Generate unique name with UUID suffix.

    Args:
        prefix: Name prefix

    Returns:
        Unique name
    """
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def format_label_selectors(labels: Dict[str, str]) -> Dict[str, str]:
    """Format labels for YAML."""
    return labels


def render_network_chaos(
    name: str,
    namespace: str,
    action: str,
    target_labels: Dict[str, str],
    duration: str,
    mode: str = "all",
    **action_params
) -> str:
    """Render NetworkChaos YAML.

    Args:
        name: Chaos experiment name
        namespace: Target namespace
        action: Chaos action (delay, loss, corrupt, partition, etc.)
        target_labels: Target pod label selectors
        duration: Experiment duration
        mode: Selection mode
        **action_params: Action-specific parameters

    Returns:
        Rendered YAML string
    """
    spec = {
        "apiVersion": "chaos-mesh.org/v1alpha1",
        "kind": "NetworkChaos",
        "metadata": {
            "name": name,
            "namespace": namespace
        },
        "spec": {
            "action": action,
            "mode": mode,
            "selector": {
                "namespaces": [namespace],
                "labelSelectors": target_labels
            },
            "duration": duration
        }
    }

    # Add action-specific parameters
    if action == "delay":
        spec["spec"]["delay"] = {
            "latency": action_params.get("latency", "10ms"),
            "jitter": action_params.get("jitter", "0ms"),
            "correlation": action_params.get("correlation", "0")
        }
    elif action == "loss":
        spec["spec"]["loss"] = {
            "loss": action_params.get("loss", "50"),
            "correlation": action_params.get("correlation", "0")
        }
    elif action == "corrupt":
        spec["spec"]["corrupt"] = {
            "corrupt": action_params.get("corrupt", "50"),
            "correlation": action_params.get("correlation", "0")
        }
    elif action == "partition":
        # Partition requires target or externalTargets
        if "direction" in action_params:
            spec["spec"]["direction"] = action_params["direction"]
        if "target" in action_params:
            spec["spec"]["target"] = action_params["target"]

    # Optional direction parameter
    if "direction" in action_params and action != "partition":
        spec["spec"]["direction"] = action_params["direction"]

    # Optional external targets
    if "external_targets" in action_params:
        spec["spec"]["externalTargets"] = action_params["external_targets"]

    return yaml.dump(spec, default_flow_style=False, sort_keys=False)


def render_stress_chaos(
    name: str,
    namespace: str,
    target_labels: Dict[str, str],
    duration: str,
    mode: str = "all",
    cpu_workers: Optional[int] = None,
    cpu_load: Optional[int] = None,
    memory_workers: Optional[int] = None,
    memory_size: Optional[str] = None,
) -> str:
    """Render StressChaos YAML.

    Args:
        name: Chaos experiment name
        namespace: Target namespace
        target_labels: Target pod label selectors
        duration: Experiment duration
        mode: Selection mode
        cpu_workers: Number of CPU stress workers
        cpu_load: CPU load percentage
        memory_workers: Number of memory stress workers
        memory_size: Memory size to allocate

    Returns:
        Rendered YAML string
    """
    spec = {
        "apiVersion": "chaos-mesh.org/v1alpha1",
        "kind": "StressChaos",
        "metadata": {
            "name": name,
            "namespace": namespace
        },
        "spec": {
            "mode": mode,
            "selector": {
                "namespaces": [namespace],
                "labelSelectors": target_labels
            },
            "duration": duration,
            "stressors": {}
        }
    }

    # Add CPU stressor if specified
    if cpu_workers is not None:
        spec["spec"]["stressors"]["cpu"] = {"workers": cpu_workers}
        if cpu_load is not None:
            spec["spec"]["stressors"]["cpu"]["load"] = cpu_load

    # Add memory stressor if specified
    if memory_workers is not None or memory_size is not None:
        spec["spec"]["stressors"]["memory"] = {}
        if memory_workers:
            spec["spec"]["stressors"]["memory"]["workers"] = memory_workers
        if memory_size:
            spec["spec"]["stressors"]["memory"]["size"] = memory_size

    return yaml.dump(spec, default_flow_style=False, sort_keys=False)


def render_pod_chaos(
    name: str,
    namespace: str,
    action: str,
    target_labels: Dict[str, str],
    duration: str,
    mode: str = "one",
    container_names: Optional[list] = None,
    grace_period: Optional[int] = None
) -> str:
    """Render PodChaos YAML.

    Args:
        name: Chaos experiment name
        namespace: Target namespace
        action: Chaos action (pod-kill, pod-failure, container-kill)
        target_labels: Target pod label selectors
        duration: Experiment duration
        mode: Selection mode
        container_names: Container names for container-kill
        grace_period: Grace period for pod-kill

    Returns:
        Rendered YAML string
    """
    spec = {
        "apiVersion": "chaos-mesh.org/v1alpha1",
        "kind": "PodChaos",
        "metadata": {
            "name": name,
            "namespace": namespace
        },
        "spec": {
            "action": action,
            "mode": mode,
            "selector": {
                "namespaces": [namespace],
                "labelSelectors": target_labels
            },
            "duration": duration
        }
    }

    # Add container names for container-kill
    if action == "container-kill" and container_names:
        spec["spec"]["containerNames"] = container_names

    # Add grace period for pod-kill
    if action == "pod-kill" and grace_period is not None:
        spec["spec"]["gracePeriod"] = grace_period

    return yaml.dump(spec, default_flow_style=False, sort_keys=False)


def render_io_chaos(
    name: str,
    namespace: str,
    action: str,
    target_labels: Dict[str, str],
    duration: str,
    volume_path: str,
    path: str,
    percent: int = 100,
    mode: str = "all",
    **action_params
) -> str:
    """Render IOChaos YAML.

    Args:
        name: Chaos experiment name
        namespace: Target namespace
        action: Chaos action (latency, fault, attrOverride, mistake)
        target_labels: Target pod label selectors
        duration: Experiment duration
        volume_path: Volume mount path in the container
        path: File path pattern to target
        percent: Percentage of I/O operations to affect
        mode: Selection mode
        **action_params: Action-specific parameters

    Returns:
        Rendered YAML string
    """
    spec = {
        "apiVersion": "chaos-mesh.org/v1alpha1",
        "kind": "IOChaos",
        "metadata": {
            "name": name,
            "namespace": namespace
        },
        "spec": {
            "action": action,
            "mode": mode,
            "selector": {
                "namespaces": [namespace],
                "labelSelectors": target_labels
            },
            "duration": duration,
            "volumePath": volume_path,
            "path": path,
            "percent": percent
        }
    }

    # Add methods filter if specified
    if "methods" in action_params and action_params["methods"]:
        spec["spec"]["methods"] = action_params["methods"]

    # Add action-specific parameters
    if action == "latency":
        spec["spec"]["delay"] = action_params.get("delay", "10ms")

    elif action == "fault":
        spec["spec"]["errno"] = action_params.get("errno", 5)

    elif action == "attrOverride":
        attr = action_params.get("attr", {})
        if attr:
            spec["spec"]["attr"] = attr

    elif action == "mistake":
        mistake_spec = {}
        if "filling" in action_params:
            mistake_spec["filling"] = action_params["filling"]
        if "max_occurrences" in action_params:
            mistake_spec["maxOccurrences"] = action_params["max_occurrences"]
        if "max_length" in action_params:
            mistake_spec["maxLength"] = action_params["max_length"]
        if mistake_spec:
            spec["spec"]["mistake"] = mistake_spec

    return yaml.dump(spec, default_flow_style=False, sort_keys=False)


def render_http_chaos(
    name: str,
    namespace: str,
    target_labels: Dict[str, str],
    duration: str,
    port: int,
    target: str = "Request",
    mode: str = "all",
    method: Optional[str] = None,
    path: Optional[str] = None,
    request_headers: Optional[Dict[str, str]] = None,
    **action_params
) -> str:
    """Render HTTPChaos YAML.

    Args:
        name: Chaos experiment name
        namespace: Target namespace
        target_labels: Target pod label selectors
        duration: Experiment duration
        port: TCP port the service listens on
        target: Target phase (Request or Response)
        mode: Selection mode
        method: HTTP method filter
        path: URI path filter
        request_headers: Request header filters
        **action_params: Action-specific parameters

    Returns:
        Rendered YAML string
    """
    spec = {
        "apiVersion": "chaos-mesh.org/v1alpha1",
        "kind": "HTTPChaos",
        "metadata": {
            "name": name,
            "namespace": namespace
        },
        "spec": {
            "mode": mode,
            "selector": {
                "namespaces": [namespace],
                "labelSelectors": target_labels
            },
            "duration": duration,
            "port": port,
            "target": target
        }
    }

    # Add method filter if specified
    if method:
        spec["spec"]["method"] = method.upper()

    # Add path filter if specified
    if path:
        spec["spec"]["path"] = path

    # Add request header filters if specified
    if request_headers:
        spec["spec"]["request_headers"] = request_headers

    # Add action-specific parameters
    if "abort" in action_params and action_params["abort"]:
        spec["spec"]["abort"] = True

    if "delay" in action_params and action_params["delay"]:
        spec["spec"]["delay"] = action_params["delay"]

    if "replace_headers" in action_params or "replace_body" in action_params:
        replace_spec = {}
        if action_params.get("replace_headers"):
            replace_spec["headers"] = action_params["replace_headers"]
        if action_params.get("replace_body"):
            replace_spec["body"] = action_params["replace_body"]
        if replace_spec:
            spec["spec"]["replace"] = replace_spec

    if "patch_headers" in action_params or "patch_body_value" in action_params:
        patch_spec = {}
        if action_params.get("patch_headers"):
            patch_spec["headers"] = action_params["patch_headers"]
        if action_params.get("patch_body_value"):
            patch_spec["body"] = {"value": action_params["patch_body_value"]}
        if patch_spec:
            spec["spec"]["patch"] = patch_spec

    return yaml.dump(spec, default_flow_style=False, sort_keys=False)


def render_dns_chaos(
    name: str,
    namespace: str,
    action: str,
    target_labels: Dict[str, str],
    duration: str,
    mode: str = "all",
    patterns: Optional[list] = None
) -> str:
    """Render DNSChaos YAML.

    Args:
        name: Chaos experiment name
        namespace: Target namespace
        action: Chaos action ("error" or "random")
        target_labels: Target pod label selectors
        duration: Experiment duration
        mode: Selection mode
        patterns: DNS patterns to match (optional)

    Returns:
        Rendered YAML string
    """
    spec = {
        "apiVersion": "chaos-mesh.org/v1alpha1",
        "kind": "DNSChaos",
        "metadata": {
            "name": name,
            "namespace": namespace
        },
        "spec": {
            "action": action,
            "mode": mode,
            "selector": {
                "namespaces": [namespace],
                "labelSelectors": target_labels
            },
            "duration": duration
        }
    }

    # Add patterns if specified
    if patterns:
        spec["spec"]["patterns"] = patterns

    return yaml.dump(spec, default_flow_style=False, sort_keys=False)


def render_physical_chaos(
    name: str,
    namespace: str,
    action: str,
    duration: str,
    mode: str = "one",
    address: Optional[list] = None,
    selector: Optional[Dict[str, str]] = None,
    **action_params
) -> str:
    """Render PhysicalMachineChaos YAML.

    Args:
        name: Chaos experiment name
        namespace: Target namespace
        action: Chaos action (stress-cpu, stress-mem, disk-fill, process-kill, clock-skew)
        duration: Experiment duration
        mode: Selection mode
        address: List of target machine addresses (mutually exclusive with selector)
        selector: Label selectors for target machines (mutually exclusive with address)
        **action_params: Action-specific parameters

    Returns:
        Rendered YAML string
    """
    spec = {
        "apiVersion": "chaos-mesh.org/v1alpha1",
        "kind": "PhysicalMachineChaos",
        "metadata": {
            "name": name,
            "namespace": namespace
        },
        "spec": {
            "action": action,
            "mode": mode,
            "duration": duration
        }
    }

    # Add targeting (address or selector, mutually exclusive)
    if address:
        spec["spec"]["address"] = address
    elif selector:
        spec["spec"]["selector"] = {
            "labelSelectors": selector
        }

    # Add action-specific parameters
    if action == "stress-cpu":
        stress_cpu = {"workers": action_params.get("workers", 1)}
        if "load" in action_params:
            stress_cpu["load"] = action_params["load"]
        spec["spec"]["stress-cpu"] = stress_cpu

    elif action == "stress-mem":
        stress_mem = {}
        if "size" in action_params:
            stress_mem["size"] = action_params["size"]
        spec["spec"]["stress-mem"] = stress_mem

    elif action == "disk-fill":
        spec["spec"]["disk-fill"] = {
            "path": action_params["path"],
            "size": action_params["size"],
            "fill-by-fallocate": action_params.get("fill_by_fallocate", True)
        }

    elif action == "process":
        spec["spec"]["process"] = {
            "process": action_params["process"],
            "signal": action_params.get("signal", 9)
        }

    elif action == "clock":
        clock_spec = {
            "time-offset": action_params["time_offset"],
            "pid": action_params["pid"]
        }
        if "clock_ids" in action_params:
            # Convert list to comma-separated string
            clock_spec["clock-ids-slice"] = ",".join(action_params["clock_ids"])
        spec["spec"]["clock"] = clock_spec

    return yaml.dump(spec, default_flow_style=False, sort_keys=False)


def interpret_chaos_status(chaos_obj: Dict[str, Any]) -> Dict[str, Any]:
    """Interpret Chaos Mesh status object.

    Args:
        chaos_obj: Chaos resource object from kubectl

    Returns:
        Simplified status dictionary
    """
    status = chaos_obj.get("status", {})
    conditions = status.get("conditions", [])

    # Default phase
    phase = "Pending"
    injected_count = 0
    message = ""

    # Check conditions
    for condition in conditions:
        if condition.get("type") == "AllInjected":
            if condition.get("status") == "True":
                phase = "Running"
            message = condition.get("message", "")
        elif condition.get("type") == "Selected":
            if condition.get("status") == "True":
                injected_count = condition.get("reason", "0")

    # Check if experiment is finished
    if "experiment" in status:
        exp_status = status["experiment"]
        if exp_status.get("phase") == "Finished":
            phase = "Finished"

    return {
        "phase": phase,
        "injected_pods": injected_count,
        "message": message,
        "records": status.get("experiment", {}).get("records", [])
    }
