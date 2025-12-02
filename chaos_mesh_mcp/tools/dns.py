"""DNSChaos tools for MCP."""

from typing import Dict, Any, Optional, List
from ..validators import (
    validate_duration,
    validate_mode,
    validate_labels
)
from ..templates import generate_name, render_dns_chaos
from ..kubectl import apply_yaml, check_target_exists


async def create_dns_error(
    namespace: str,
    target_labels: Dict[str, str],
    duration: str,
    patterns: Optional[List[str]] = None,
    mode: str = "all"
) -> Dict[str, Any]:
    """Create DNSChaos with error action.

    Returns DNS errors for specified domain patterns.

    Args:
        namespace: Target namespace
        target_labels: Label selectors for target pods (e.g., {"app": "web-server"})
        duration: Experiment duration (e.g., "60s", "5m")
        patterns: DNS patterns to match (e.g., ["google.com", "*.github.com", "example.?om"])
                 Supports wildcard (*) and single char (?) matching
                 If not specified, affects all domains
        mode: Selection mode (one/all/fixed/fixed-percent). Default: "all"

    Returns:
        Experiment details with experiment_id and affected_pods

    Example:
        >>> await create_dns_error(
        ...     namespace="default",
        ...     target_labels={"app": "web-server"},
        ...     duration="60s",
        ...     patterns=["google.com", "*.example.com"]
        ... )
        {
            "experiment_id": "dns-error-a3f4b2c1",
            "kind": "DNSChaos",
            "action": "error",
            "affected_pods": ["web-server-0"],
            "parameters": {"patterns": ["google.com", "*.example.com"]}
        }

    Note:
        - Requires chaos-dns-server pod running in chaos-mesh namespace
        - Only supports A and AAAA DNS record types
        - Wildcard (*) must be at the end of the pattern
    """
    # Validate parameters
    validate_labels(target_labels)
    validate_duration(duration)
    validate_mode(mode)

    # Validate patterns if specified
    if patterns:
        for pattern in patterns:
            if not isinstance(pattern, str) or not pattern:
                raise ValueError(f"Invalid pattern: {pattern}. Patterns must be non-empty strings")
            # Check wildcard placement
            if "*" in pattern and not (pattern.endswith("*") or pattern.startswith("*.")):
                raise ValueError(
                    f"Invalid pattern: {pattern}. "
                    f"Wildcard (*) must be at the end of the string (e.g., 'chaos-mesh.*' or '*.example.com')"
                )

    # Check if target pods exist
    target_check = check_target_exists(namespace, target_labels)
    if not target_check["exists"]:
        raise ValueError(
            f"No pods found with labels {target_labels} in namespace '{namespace}'. "
            f"Please verify the label selectors."
        )

    # Generate unique name
    name = generate_name("dns-error")

    # Render YAML
    yaml_content = render_dns_chaos(
        name=name,
        namespace=namespace,
        action="error",
        target_labels=target_labels,
        duration=duration,
        mode=mode,
        patterns=patterns
    )

    # Apply
    apply_yaml(yaml_content)

    return {
        "experiment_id": name,
        "kind": "DNSChaos",
        "action": "error",
        "namespace": namespace,
        "affected_pods": [p["name"] for p in target_check["pods"]],
        "parameters": {
            "patterns": patterns if patterns else "all domains",
            "mode": mode
        },
        "duration": duration
    }


async def create_dns_random(
    namespace: str,
    target_labels: Dict[str, str],
    duration: str,
    patterns: Optional[List[str]] = None,
    mode: str = "all"
) -> Dict[str, Any]:
    """Create DNSChaos with random action.

    Returns random IP addresses for DNS queries.

    Args:
        namespace: Target namespace
        target_labels: Label selectors for target pods
        duration: Experiment duration (e.g., "60s", "5m")
        patterns: DNS patterns to match (e.g., ["google.com", "*.github.com"])
                 Supports wildcard (*) and single char (?) matching
                 If not specified, affects all domains
        mode: Selection mode (one/all/fixed/fixed-percent). Default: "all"

    Returns:
        Experiment details

    Example:
        >>> await create_dns_random(
        ...     namespace="default",
        ...     target_labels={"app": "api-client"},
        ...     duration="120s",
        ...     patterns=["api.example.com"]
        ... )

    Note:
        - Requires chaos-dns-server pod running in chaos-mesh namespace
        - Only supports A and AAAA DNS record types
        - Random IPs are generated for each query
    """
    # Validate
    validate_labels(target_labels)
    validate_duration(duration)
    validate_mode(mode)

    # Validate patterns if specified
    if patterns:
        for pattern in patterns:
            if not isinstance(pattern, str) or not pattern:
                raise ValueError(f"Invalid pattern: {pattern}. Patterns must be non-empty strings")
            # Check wildcard placement
            if "*" in pattern and not (pattern.endswith("*") or pattern.startswith("*.")):
                raise ValueError(
                    f"Invalid pattern: {pattern}. "
                    f"Wildcard (*) must be at the end of the string"
                )

    # Check target
    target_check = check_target_exists(namespace, target_labels)
    if not target_check["exists"]:
        raise ValueError(f"No pods found with labels {target_labels}")

    # Generate and apply
    name = generate_name("dns-random")
    yaml_content = render_dns_chaos(
        name=name,
        namespace=namespace,
        action="random",
        target_labels=target_labels,
        duration=duration,
        mode=mode,
        patterns=patterns
    )

    apply_yaml(yaml_content)

    return {
        "experiment_id": name,
        "kind": "DNSChaos",
        "action": "random",
        "namespace": namespace,
        "affected_pods": [p["name"] for p in target_check["pods"]],
        "parameters": {
            "patterns": patterns if patterns else "all domains",
            "mode": mode
        },
        "duration": duration
    }
