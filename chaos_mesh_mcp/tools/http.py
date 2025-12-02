"""HTTPChaos tools for MCP."""

from typing import Dict, Any, Optional, List
import base64
from ..validators import (
    validate_duration,
    validate_mode,
    validate_labels
)
from ..templates import generate_name, render_http_chaos
from ..kubectl import apply_yaml, check_target_exists


async def create_http_abort(
    namespace: str,
    target_labels: Dict[str, str],
    port: int,
    duration: str,
    target: str = "Request",
    method: Optional[str] = None,
    path: Optional[str] = None,
    mode: str = "all",
    request_headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Create HTTPChaos with abort action.

    Interrupts HTTP connections to simulate network failures.

    Args:
        namespace: Target namespace
        target_labels: Label selectors for target pods (e.g., {"app": "api-server"})
        port: TCP port the service listens on (e.g., 80, 8080)
        duration: Experiment duration (e.g., "60s", "5m")
        target: Target phase: "Request" or "Response". Default: "Request"
        method: HTTP method to target (e.g., "GET", "POST"). Default: all methods
        path: URI path pattern (e.g., "/api/*", "/users"). Default: all paths
        mode: Selection mode (one/all/fixed/fixed-percent). Default: "all"
        request_headers: Match specific request headers (e.g., {"Content-Type": "application/json"})

    Returns:
        Experiment details with experiment_id and affected_pods

    Example:
        >>> await create_http_abort(
        ...     namespace="default",
        ...     target_labels={"app": "nginx"},
        ...     port=80,
        ...     duration="60s",
        ...     method="GET",
        ...     path="/api/*"
        ... )
        {
            "experiment_id": "http-abort-a3f4b2c1",
            "kind": "HTTPChaos",
            "action": "abort",
            "affected_pods": ["nginx-0"],
            "parameters": {"port": 80, "method": "GET", "path": "/api/*"}
        }
    """
    # Validate parameters
    validate_labels(target_labels)
    validate_duration(duration)
    validate_mode(mode)

    if not isinstance(port, int) or port < 1 or port > 65535:
        raise ValueError(f"port must be between 1-65535, got: {port}")

    if target not in ["Request", "Response"]:
        raise ValueError(f"target must be 'Request' or 'Response', got: {target}")

    if method and method.upper() not in ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "CONNECT", "TRACE"]:
        raise ValueError(f"Invalid HTTP method: {method}")

    # Check if target pods exist
    target_check = check_target_exists(namespace, target_labels)
    if not target_check["exists"]:
        raise ValueError(
            f"No pods found with labels {target_labels} in namespace '{namespace}'. "
            f"Please verify the label selectors."
        )

    # Generate unique name
    name = generate_name("http-abort")

    # Render YAML
    yaml_content = render_http_chaos(
        name=name,
        namespace=namespace,
        target_labels=target_labels,
        duration=duration,
        mode=mode,
        port=port,
        target=target,
        method=method,
        path=path,
        request_headers=request_headers,
        abort=True
    )

    # Apply
    apply_yaml(yaml_content)

    return {
        "experiment_id": name,
        "kind": "HTTPChaos",
        "action": "abort",
        "namespace": namespace,
        "affected_pods": [p["name"] for p in target_check["pods"]],
        "parameters": {
            "port": port,
            "target": target,
            "method": method or "all",
            "path": path or "all",
            "request_headers": request_headers
        },
        "duration": duration
    }


async def create_http_delay(
    namespace: str,
    target_labels: Dict[str, str],
    port: int,
    delay: str,
    duration: str,
    target: str = "Request",
    method: Optional[str] = None,
    path: Optional[str] = None,
    mode: str = "all",
    request_headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Create HTTPChaos with delay action.

    Injects latency into HTTP requests or responses.

    Args:
        namespace: Target namespace
        target_labels: Label selectors for target pods
        port: TCP port the service listens on
        delay: Latency duration (e.g., "10ms", "1s", "5s")
        duration: Experiment duration
        target: Target phase: "Request" or "Response". Default: "Request"
        method: HTTP method to target. Default: all methods
        path: URI path pattern. Default: all paths
        mode: Selection mode. Default: "all"
        request_headers: Match specific request headers

    Returns:
        Experiment details

    Example:
        >>> await create_http_delay(
        ...     namespace="default",
        ...     target_labels={"app": "api-server"},
        ...     port=8080,
        ...     delay="2s",
        ...     duration="120s",
        ...     method="POST",
        ...     path="/api/v1/*"
        ... )
    """
    # Validate
    validate_labels(target_labels)
    validate_duration(delay)
    validate_duration(duration)
    validate_mode(mode)

    if not isinstance(port, int) or port < 1 or port > 65535:
        raise ValueError(f"port must be between 1-65535, got: {port}")

    if target not in ["Request", "Response"]:
        raise ValueError(f"target must be 'Request' or 'Response', got: {target}")

    if method and method.upper() not in ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "CONNECT", "TRACE"]:
        raise ValueError(f"Invalid HTTP method: {method}")

    # Check target
    target_check = check_target_exists(namespace, target_labels)
    if not target_check["exists"]:
        raise ValueError(f"No pods found with labels {target_labels}")

    # Generate and apply
    name = generate_name("http-delay")
    yaml_content = render_http_chaos(
        name=name,
        namespace=namespace,
        target_labels=target_labels,
        duration=duration,
        mode=mode,
        port=port,
        target=target,
        method=method,
        path=path,
        request_headers=request_headers,
        delay=delay
    )

    apply_yaml(yaml_content)

    return {
        "experiment_id": name,
        "kind": "HTTPChaos",
        "action": "delay",
        "namespace": namespace,
        "affected_pods": [p["name"] for p in target_check["pods"]],
        "parameters": {
            "port": port,
            "target": target,
            "delay": delay,
            "method": method or "all",
            "path": path or "all",
            "request_headers": request_headers
        },
        "duration": duration
    }


async def create_http_replace(
    namespace: str,
    target_labels: Dict[str, str],
    port: int,
    duration: str,
    target: str = "Request",
    method: Optional[str] = None,
    path: Optional[str] = None,
    replace_headers: Optional[Dict[str, str]] = None,
    replace_body: Optional[str] = None,
    mode: str = "all",
    request_headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Create HTTPChaos with replace action.

    Replaces content in HTTP request or response messages.

    Args:
        namespace: Target namespace
        target_labels: Label selectors for target pods
        port: TCP port the service listens on
        duration: Experiment duration
        target: Target phase: "Request" or "Response". Default: "Request"
        method: HTTP method to target. Default: all methods
        path: URI path pattern. Default: all paths
        replace_headers: Headers to replace (e.g., {"Content-Type": "text/plain"})
        replace_body: Body content to replace (will be base64 encoded automatically)
        mode: Selection mode. Default: "all"
        request_headers: Match specific request headers

    Returns:
        Experiment details

    Note:
        At least one of replace_headers or replace_body must be specified.

    Example:
        >>> await create_http_replace(
        ...     namespace="default",
        ...     target_labels={"app": "web-server"},
        ...     port=80,
        ...     duration="60s",
        ...     target="Response",
        ...     replace_body='{"error": "Service unavailable"}',
        ...     replace_headers={"Content-Type": "application/json"}
        ... )
    """
    # Validate
    validate_labels(target_labels)
    validate_duration(duration)
    validate_mode(mode)

    if not isinstance(port, int) or port < 1 or port > 65535:
        raise ValueError(f"port must be between 1-65535, got: {port}")

    if target not in ["Request", "Response"]:
        raise ValueError(f"target must be 'Request' or 'Response', got: {target}")

    if not replace_headers and not replace_body:
        raise ValueError("At least one of replace_headers or replace_body must be specified")

    if method and method.upper() not in ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "CONNECT", "TRACE"]:
        raise ValueError(f"Invalid HTTP method: {method}")

    # Check target
    target_check = check_target_exists(namespace, target_labels)
    if not target_check["exists"]:
        raise ValueError(f"No pods found with labels {target_labels}")

    # Base64 encode body if provided
    replace_body_encoded = None
    if replace_body:
        replace_body_encoded = base64.b64encode(replace_body.encode()).decode()

    # Generate and apply
    name = generate_name("http-replace")
    yaml_content = render_http_chaos(
        name=name,
        namespace=namespace,
        target_labels=target_labels,
        duration=duration,
        mode=mode,
        port=port,
        target=target,
        method=method,
        path=path,
        request_headers=request_headers,
        replace_headers=replace_headers,
        replace_body=replace_body_encoded
    )

    apply_yaml(yaml_content)

    return {
        "experiment_id": name,
        "kind": "HTTPChaos",
        "action": "replace",
        "namespace": namespace,
        "affected_pods": [p["name"] for p in target_check["pods"]],
        "parameters": {
            "port": port,
            "target": target,
            "method": method or "all",
            "path": path or "all",
            "replace_headers": replace_headers,
            "replace_body": replace_body if replace_body else None,
            "request_headers": request_headers
        },
        "duration": duration
    }


async def create_http_patch(
    namespace: str,
    target_labels: Dict[str, str],
    port: int,
    duration: str,
    target: str = "Request",
    method: Optional[str] = None,
    path: Optional[str] = None,
    patch_headers: Optional[List[List[str]]] = None,
    patch_body_value: Optional[str] = None,
    mode: str = "all",
    request_headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Create HTTPChaos with patch action.

    Adds additional content to HTTP request or response messages.

    Args:
        namespace: Target namespace
        target_labels: Label selectors for target pods
        port: TCP port the service listens on
        duration: Experiment duration
        target: Target phase: "Request" or "Response". Default: "Request"
        method: HTTP method to target. Default: all methods
        path: URI path pattern. Default: all paths
        patch_headers: Headers to add as list of [key, value] pairs (e.g., [["X-Custom", "value"]])
        patch_body_value: JSON body content to add (e.g., '{"extra": "data"}')
        mode: Selection mode. Default: "all"
        request_headers: Match specific request headers

    Returns:
        Experiment details

    Note:
        At least one of patch_headers or patch_body_value must be specified.

    Example:
        >>> await create_http_patch(
        ...     namespace="default",
        ...     target_labels={"app": "api-server"},
        ...     port=8080,
        ...     duration="60s",
        ...     target="Request",
        ...     patch_headers=[["X-Request-ID", "test-123"], ["X-Debug", "true"]],
        ...     patch_body_value='{"debug": true}'
        ... )
    """
    # Validate
    validate_labels(target_labels)
    validate_duration(duration)
    validate_mode(mode)

    if not isinstance(port, int) or port < 1 or port > 65535:
        raise ValueError(f"port must be between 1-65535, got: {port}")

    if target not in ["Request", "Response"]:
        raise ValueError(f"target must be 'Request' or 'Response', got: {target}")

    if not patch_headers and not patch_body_value:
        raise ValueError("At least one of patch_headers or patch_body_value must be specified")

    if method and method.upper() not in ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "CONNECT", "TRACE"]:
        raise ValueError(f"Invalid HTTP method: {method}")

    if patch_headers:
        for header in patch_headers:
            if not isinstance(header, list) or len(header) != 2:
                raise ValueError(f"Each patch_header must be a [key, value] pair, got: {header}")

    # Check target
    target_check = check_target_exists(namespace, target_labels)
    if not target_check["exists"]:
        raise ValueError(f"No pods found with labels {target_labels}")

    # Generate and apply
    name = generate_name("http-patch")
    yaml_content = render_http_chaos(
        name=name,
        namespace=namespace,
        target_labels=target_labels,
        duration=duration,
        mode=mode,
        port=port,
        target=target,
        method=method,
        path=path,
        request_headers=request_headers,
        patch_headers=patch_headers,
        patch_body_value=patch_body_value
    )

    apply_yaml(yaml_content)

    return {
        "experiment_id": name,
        "kind": "HTTPChaos",
        "action": "patch",
        "namespace": namespace,
        "affected_pods": [p["name"] for p in target_check["pods"]],
        "parameters": {
            "port": port,
            "target": target,
            "method": method or "all",
            "path": path or "all",
            "patch_headers": patch_headers,
            "patch_body_value": patch_body_value,
            "request_headers": request_headers
        },
        "duration": duration
    }
