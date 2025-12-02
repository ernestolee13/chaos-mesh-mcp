"""Environment validation tools for Chaos Mesh prerequisites."""

from typing import Dict, Any, List, Optional
from ..kubectl import KubectlRunner


async def check_kubectl_available() -> Dict[str, Any]:
    """Check if kubectl is available and working.

    Returns:
        Validation result with kubectl version info
    """
    kubectl = KubectlRunner()
    try:
        result = await kubectl.run_command("version --client --output=json")
        return {
            "available": True,
            "version": result.get("clientVersion", {}).get("gitVersion", "unknown"),
            "message": "kubectl is available"
        }
    except Exception as e:
        return {
            "available": False,
            "version": None,
            "message": f"kubectl not available: {str(e)}"
        }


async def check_cluster_connection() -> Dict[str, Any]:
    """Check if cluster is reachable and accessible.

    Returns:
        Validation result with cluster info
    """
    kubectl = KubectlRunner()
    try:
        result = await kubectl.run_command("cluster-info")
        return {
            "connected": True,
            "cluster_info": result,
            "message": "Cluster is reachable"
        }
    except Exception as e:
        return {
            "connected": False,
            "cluster_info": None,
            "message": f"Cannot connect to cluster: {str(e)}"
        }


async def check_chaos_mesh_installed() -> Dict[str, Any]:
    """Check if Chaos Mesh is installed in the cluster.

    Returns:
        Validation result with installation status
    """
    kubectl = KubectlRunner()
    try:
        # Check for chaos-mesh namespace
        result = await kubectl.run_command("get namespace chaos-mesh -o json")

        # Check for Chaos Mesh pods
        pods = await kubectl.run_command("get pods -n chaos-mesh -o json")
        pod_items = pods.get("items", [])

        running_pods = [
            pod["metadata"]["name"]
            for pod in pod_items
            if pod.get("status", {}).get("phase") == "Running"
        ]

        total_pods = len(pod_items)

        return {
            "installed": True,
            "namespace": "chaos-mesh",
            "total_pods": total_pods,
            "running_pods": len(running_pods),
            "pod_names": running_pods,
            "message": f"Chaos Mesh is installed with {len(running_pods)}/{total_pods} pods running"
        }
    except Exception as e:
        return {
            "installed": False,
            "namespace": None,
            "total_pods": 0,
            "running_pods": 0,
            "pod_names": [],
            "message": f"Chaos Mesh not installed: {str(e)}"
        }


async def check_chaos_mesh_crds() -> Dict[str, Any]:
    """Check if Chaos Mesh CRDs are installed.

    Returns:
        Validation result with CRD list
    """
    kubectl = KubectlRunner()

    expected_crds = [
        "networkchaos.chaos-mesh.org",
        "podchaos.chaos-mesh.org",
        "stresschaos.chaos-mesh.org",
        "iochaos.chaos-mesh.org",
        "httpchaos.chaos-mesh.org",
        "dnschaos.chaos-mesh.org",
        "physicalmachinechaos.chaos-mesh.org",
    ]

    try:
        result = await kubectl.run_command("get crd -o json")
        installed_crds = [
            item["metadata"]["name"]
            for item in result.get("items", [])
            if item["metadata"]["name"].endswith("chaos-mesh.org")
        ]

        missing_crds = [crd for crd in expected_crds if crd not in installed_crds]

        return {
            "all_installed": len(missing_crds) == 0,
            "installed_count": len([crd for crd in expected_crds if crd in installed_crds]),
            "total_expected": len(expected_crds),
            "installed_crds": [crd for crd in expected_crds if crd in installed_crds],
            "missing_crds": missing_crds,
            "message": f"{len(expected_crds) - len(missing_crds)}/{len(expected_crds)} Chaos Mesh CRDs installed"
        }
    except Exception as e:
        return {
            "all_installed": False,
            "installed_count": 0,
            "total_expected": len(expected_crds),
            "installed_crds": [],
            "missing_crds": expected_crds,
            "message": f"Failed to check CRDs: {str(e)}"
        }


async def check_chaos_components() -> Dict[str, Any]:
    """Check status of Chaos Mesh components including optional ones.

    Returns:
        Validation result with component status
    """
    kubectl = KubectlRunner()

    # Component requirements
    required_components = [
        "chaos-controller-manager",
        "chaos-daemon"
    ]

    optional_components = {
        "chaos-dns-server": "Required for DNSChaos",
        "chaos-dashboard": "Optional web UI"
    }

    try:
        pods = await kubectl.run_command("get pods -n chaos-mesh -o json")
        pod_items = pods.get("items", [])

        component_status = {}

        # Check required components
        for component in required_components:
            matching_pods = [
                pod for pod in pod_items
                if component in pod["metadata"]["name"]
            ]

            running = sum(
                1 for pod in matching_pods
                if pod.get("status", {}).get("phase") == "Running"
            )

            component_status[component] = {
                "type": "required",
                "total": len(matching_pods),
                "running": running,
                "status": "OK" if running > 0 else "MISSING",
                "required_for": "All chaos types"
            }

        # Check optional components
        for component, purpose in optional_components.items():
            matching_pods = [
                pod for pod in pod_items
                if component in pod["metadata"]["name"]
            ]

            running = sum(
                1 for pod in matching_pods
                if pod.get("status", {}).get("phase") == "Running"
            )

            component_status[component] = {
                "type": "optional",
                "total": len(matching_pods),
                "running": running,
                "status": "OK" if running > 0 else "NOT_INSTALLED",
                "required_for": purpose
            }

        # Overall status
        all_required_ok = all(
            status["status"] == "OK"
            for name, status in component_status.items()
            if status["type"] == "required"
        )

        return {
            "all_required_ok": all_required_ok,
            "components": component_status,
            "message": "All required components running" if all_required_ok else "Some required components missing"
        }

    except Exception as e:
        return {
            "all_required_ok": False,
            "components": {},
            "message": f"Failed to check components: {str(e)}"
        }


async def get_chaos_requirements(chaos_type: str) -> Dict[str, Any]:
    """Get specific requirements for a chaos type.

    Args:
        chaos_type: Type of chaos (e.g., "dns", "physical", "network")

    Returns:
        Requirements for the specified chaos type
    """
    requirements_map = {
        "dns": {
            "chaos_kind": "DNSChaos",
            "crd": "dnschaos.chaos-mesh.org",
            "required_components": ["chaos-controller-manager", "chaos-daemon", "chaos-dns-server"],
            "optional_components": [],
            "additional_notes": [
                "chaos-dns-server pod must be running in chaos-mesh namespace",
                "Only supports A and AAAA DNS record types",
                "Wildcard patterns (*) must be at end of domain"
            ]
        },
        "physical": {
            "chaos_kind": "PhysicalMachineChaos",
            "crd": "physicalmachinechaos.chaos-mesh.org",
            "required_components": ["chaos-controller-manager"],
            "optional_components": [],
            "external_requirements": [
                "Chaosd agent must be running on target physical/virtual machines",
                "Chaosd must be configured to connect to Chaos Mesh controller",
                "Target machines must be registered via address or selector"
            ],
            "additional_notes": [
                "Does not require chaos-daemon (operates outside cluster)",
                "Supports: stress-cpu, stress-mem, disk-fill, process-kill, clock-skew actions",
                "Must specify EITHER address OR selector for targeting"
            ]
        },
        "network": {
            "chaos_kind": "NetworkChaos",
            "crd": "networkchaos.chaos-mesh.org",
            "required_components": ["chaos-controller-manager", "chaos-daemon"],
            "optional_components": [],
            "additional_notes": [
                "Supports: delay, loss, corrupt, duplicate, partition, bandwidth actions"
            ]
        },
        "pod": {
            "chaos_kind": "PodChaos",
            "crd": "podchaos.chaos-mesh.org",
            "required_components": ["chaos-controller-manager", "chaos-daemon"],
            "optional_components": [],
            "additional_notes": [
                "Supports: pod-kill, pod-failure, container-kill actions"
            ]
        },
        "stress": {
            "chaos_kind": "StressChaos",
            "crd": "stresschaos.chaos-mesh.org",
            "required_components": ["chaos-controller-manager", "chaos-daemon"],
            "optional_components": [],
            "additional_notes": [
                "Uses stress-ng inside target containers"
            ]
        },
        "io": {
            "chaos_kind": "IOChaos",
            "crd": "iochaos.chaos-mesh.org",
            "required_components": ["chaos-controller-manager", "chaos-daemon"],
            "optional_components": [],
            "additional_notes": [
                "Supports: latency, fault, attrOverride, mistake actions",
                "Requires volume path and file path pattern"
            ]
        },
        "http": {
            "chaos_kind": "HTTPChaos",
            "crd": "httpchaos.chaos-mesh.org",
            "required_components": ["chaos-controller-manager", "chaos-daemon"],
            "optional_components": [],
            "additional_notes": [
                "Supports: abort, delay, replace, patch actions",
                "Requires port number of target service"
            ]
        }
    }

    if chaos_type.lower() not in requirements_map:
        return {
            "error": f"Unknown chaos type: {chaos_type}",
            "supported_types": list(requirements_map.keys())
        }

    return requirements_map[chaos_type.lower()]


async def validate_environment() -> Dict[str, Any]:
    """Perform comprehensive environment validation.

    Checks:
    - kubectl availability
    - cluster connectivity
    - Chaos Mesh installation
    - CRDs installation
    - Component status

    Returns:
        Complete validation report
    """
    results = {}

    # 1. Check kubectl
    results["kubectl"] = await check_kubectl_available()
    if not results["kubectl"]["available"]:
        return {
            "valid": False,
            "checks": results,
            "message": "kubectl is not available. Install kubectl first.",
            "next_steps": ["Install kubectl: https://kubernetes.io/docs/tasks/tools/"]
        }

    # 2. Check cluster connection
    results["cluster"] = await check_cluster_connection()
    if not results["cluster"]["connected"]:
        return {
            "valid": False,
            "checks": results,
            "message": "Cannot connect to Kubernetes cluster.",
            "next_steps": [
                "Ensure kubeconfig is properly configured",
                "Check if cluster is running",
                "Verify network connectivity"
            ]
        }

    # 3. Check Chaos Mesh installation
    results["chaos_mesh"] = await check_chaos_mesh_installed()
    if not results["chaos_mesh"]["installed"]:
        return {
            "valid": False,
            "checks": results,
            "message": "Chaos Mesh is not installed.",
            "next_steps": [
                "Install Chaos Mesh: https://chaos-mesh.org/docs/production-installation-using-helm/",
                "Or quick install: kubectl apply -f https://mirrors.chaos-mesh.org/latest/install.yaml"
            ]
        }

    # 4. Check CRDs
    results["crds"] = await check_chaos_mesh_crds()

    # 5. Check components
    results["components"] = await check_chaos_components()

    # Determine overall validity
    all_valid = (
        results["kubectl"]["available"] and
        results["cluster"]["connected"] and
        results["chaos_mesh"]["installed"] and
        results["components"]["all_required_ok"]
    )

    warnings = []
    if not results["crds"]["all_installed"]:
        warnings.append(f"Missing CRDs: {', '.join(results['crds']['missing_crds'])}")

    # Check for optional components
    dns_server_ok = results["components"]["components"].get("chaos-dns-server", {}).get("status") == "OK"
    if not dns_server_ok:
        warnings.append("chaos-dns-server not running - DNSChaos will not work")

    return {
        "valid": all_valid,
        "checks": results,
        "warnings": warnings,
        "message": "Environment is ready for Chaos Mesh" if all_valid else "Environment validation failed",
        "next_steps": [] if all_valid else ["Fix the issues listed above"]
    }


async def check_chaos_type_requirements(chaos_type: str) -> Dict[str, Any]:
    """Check if environment meets requirements for specific chaos type.

    Args:
        chaos_type: Type of chaos (e.g., "dns", "physical", "network")

    Returns:
        Validation result specific to the chaos type
    """
    # Get requirements
    requirements = await get_chaos_requirements(chaos_type)

    if "error" in requirements:
        return requirements

    # Check CRD
    crds_check = await check_chaos_mesh_crds()
    crd_installed = requirements["crd"] in crds_check["installed_crds"]

    # Check components
    components_check = await check_chaos_components()

    component_status = {}
    all_required_ok = True

    for component in requirements["required_components"]:
        status = components_check["components"].get(component, {})
        component_status[component] = status
        if status.get("status") != "OK":
            all_required_ok = False

    # Build result
    result = {
        "chaos_type": chaos_type,
        "chaos_kind": requirements["chaos_kind"],
        "ready": crd_installed and all_required_ok,
        "crd_installed": crd_installed,
        "required_components_ok": all_required_ok,
        "component_status": component_status,
        "requirements": requirements
    }

    # Add specific messages
    if not crd_installed:
        result["message"] = f"CRD {requirements['crd']} is not installed"
    elif not all_required_ok:
        missing = [name for name, status in component_status.items() if status.get("status") != "OK"]
        result["message"] = f"Required components not running: {', '.join(missing)}"
    else:
        result["message"] = f"{requirements['chaos_kind']} is ready to use"

    return result
