"""Chaos Mesh MCP Server."""

import asyncio
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

from .tools.network import (
    create_network_delay,
    create_network_loss,
    create_network_partition,
    create_network_corrupt
)
from .tools.stress import (
    create_stress_cpu,
    create_stress_memory,
    create_stress_combined
)
from .tools.pod import (
    create_pod_kill,
    create_pod_failure,
    create_container_kill
)
from .tools.io import (
    create_io_latency,
    create_io_fault,
    create_io_attr_override,
    create_io_mistake
)
from .tools.http import (
    create_http_abort,
    create_http_delay,
    create_http_replace,
    create_http_patch
)
from .tools.dns import (
    create_dns_error,
    create_dns_random
)
from .tools.physical import (
    create_physical_stress_cpu,
    create_physical_stress_memory,
    create_physical_disk_fill,
    create_physical_process_kill,
    create_physical_clock_skew
)
from .tools.validation import (
    validate_environment,
    check_chaos_type_requirements,
    get_chaos_requirements
)
from .tools.management import (
    get_experiment_status,
    list_active_experiments,
    delete_experiment,
    pause_experiment,
    resume_experiment,
    get_experiment_events
)


# Create server instance
server = Server("chaos-mesh-mcp")


# ============================================================================
# Tool Definitions
# ============================================================================

def get_tools() -> list[Tool]:
    """Get all available Chaos Mesh tools. Exported for external use."""
    return [
        # NetworkChaos tools
        Tool(
            name="create_network_delay",
            description="Inject network latency to target pods. Use this to simulate slow network connections or high latency scenarios.",
            inputSchema={
                "type": "object",
                "properties": {
                    "namespace": {"type": "string", "description": "Target namespace"},
                    "target_labels": {"type": "object", "description": "Label selectors for target pods (e.g., {'app': 'mongodb'})"},
                    "latency": {"type": "string", "description": "Network delay (e.g., '800ms', '1s')"},
                    "duration": {"type": "string", "description": "Experiment duration (e.g., '60s', '5m')"},
                    "jitter": {"type": "string", "description": "Delay variance (default: '0ms')"},
                    "correlation": {"type": "string", "description": "Correlation to previous delay 0-100 (default: '0')"},
                    "mode": {"type": "string", "description": "Selection mode: one/all/fixed/fixed-percent (default: 'all')"},
                    "direction": {"type": "string", "description": "Traffic direction: to/from/both (default: 'to')"},
                },
                "required": ["namespace", "target_labels", "latency", "duration"]
            }
        ),
        Tool(
            name="create_network_loss",
            description="Simulate packet loss. Use this to test how applications handle unreliable network connections.",
            inputSchema={
                "type": "object",
                "properties": {
                    "namespace": {"type": "string"},
                    "target_labels": {"type": "object"},
                    "loss": {"type": "string", "description": "Packet loss probability 0-100 (e.g., '10' for 10%)"},
                    "duration": {"type": "string"},
                    "correlation": {"type": "string", "description": "Default: '0'"},
                    "mode": {"type": "string", "description": "Default: 'all'"},
                    "direction": {"type": "string", "description": "Default: 'to'"},
                },
                "required": ["namespace", "target_labels", "loss", "duration"]
            }
        ),
        Tool(
            name="create_network_partition",
            description="Simulate network partition (network split). Use this to test split-brain scenarios or network isolation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "namespace": {"type": "string"},
                    "target_labels": {"type": "object"},
                    "duration": {"type": "string"},
                    "direction": {"type": "string", "description": "Default: 'both'"},
                    "mode": {"type": "string", "description": "Default: 'all'"},
                },
                "required": ["namespace", "target_labels", "duration"]
            }
        ),
        Tool(
            name="create_network_corrupt",
            description="Corrupt network packets. Use this to test error handling in network protocols.",
            inputSchema={
                "type": "object",
                "properties": {
                    "namespace": {"type": "string"},
                    "target_labels": {"type": "object"},
                    "corrupt": {"type": "string", "description": "Corruption probability 0-100"},
                    "duration": {"type": "string"},
                    "correlation": {"type": "string"},
                    "mode": {"type": "string"},
                    "direction": {"type": "string"},
                },
                "required": ["namespace", "target_labels", "corrupt", "duration"]
            }
        ),

        # StressChaos tools
        Tool(
            name="create_stress_cpu",
            description="Apply CPU stress to containers. Use this to test behavior under high CPU load.",
            inputSchema={
                "type": "object",
                "properties": {
                    "namespace": {"type": "string"},
                    "target_labels": {"type": "object"},
                    "workers": {"type": "integer", "description": "Number of CPU stress workers (1-16)"},
                    "duration": {"type": "string"},
                    "load": {"type": "integer", "description": "CPU load percentage 0-100 (optional)"},
                    "mode": {"type": "string", "description": "Default: 'all'"},
                },
                "required": ["namespace", "target_labels", "workers", "duration"]
            }
        ),
        Tool(
            name="create_stress_memory",
            description="Apply memory stress by allocating memory. Use this to test OOM behavior or memory pressure.",
            inputSchema={
                "type": "object",
                "properties": {
                    "namespace": {"type": "string"},
                    "target_labels": {"type": "object"},
                    "size": {"type": "string", "description": "Memory size to allocate (e.g., '256MB', '1GB')"},
                    "duration": {"type": "string"},
                    "workers": {"type": "integer", "description": "Number of workers (default: 1)"},
                    "mode": {"type": "string"},
                },
                "required": ["namespace", "target_labels", "size", "duration"]
            }
        ),
        Tool(
            name="create_stress_combined",
            description="Apply both CPU and memory stress simultaneously.",
            inputSchema={
                "type": "object",
                "properties": {
                    "namespace": {"type": "string"},
                    "target_labels": {"type": "object"},
                    "duration": {"type": "string"},
                    "cpu_workers": {"type": "integer"},
                    "cpu_load": {"type": "integer"},
                    "memory_workers": {"type": "integer"},
                    "memory_size": {"type": "string"},
                    "mode": {"type": "string"},
                },
                "required": ["namespace", "target_labels", "duration", "cpu_workers", "cpu_load", "memory_workers", "memory_size"]
            }
        ),

        # PodChaos tools
        Tool(
            name="create_pod_kill",
            description="Kill pods (they will be recreated). Use this to test resilience to pod failures.",
            inputSchema={
                "type": "object",
                "properties": {
                    "namespace": {"type": "string"},
                    "target_labels": {"type": "object"},
                    "duration": {"type": "string"},
                    "mode": {"type": "string", "description": "Default: 'one' (safer)"},
                    "grace_period": {"type": "integer", "description": "Seconds before killing (default: 0)"},
                },
                "required": ["namespace", "target_labels", "duration"]
            }
        ),
        Tool(
            name="create_pod_failure",
            description="Make pods temporarily unavailable without killing them. Pods recover after experiment ends.",
            inputSchema={
                "type": "object",
                "properties": {
                    "namespace": {"type": "string"},
                    "target_labels": {"type": "object"},
                    "duration": {"type": "string"},
                    "mode": {"type": "string"},
                },
                "required": ["namespace", "target_labels", "duration"]
            }
        ),
        Tool(
            name="create_container_kill",
            description="Kill specific containers within pods. Containers will be restarted by kubelet.",
            inputSchema={
                "type": "object",
                "properties": {
                    "namespace": {"type": "string"},
                    "target_labels": {"type": "object"},
                    "container_names": {"type": "array", "items": {"type": "string"}},
                    "duration": {"type": "string"},
                    "mode": {"type": "string"},
                },
                "required": ["namespace", "target_labels", "container_names", "duration"]
            }
        ),

        # IOChaos tools
        Tool(
            name="create_io_latency",
            description="Inject I/O latency to simulate slow disk operations. Use this to test application behavior with slow disk I/O.",
            inputSchema={
                "type": "object",
                "properties": {
                    "namespace": {"type": "string", "description": "Target namespace"},
                    "target_labels": {"type": "object", "description": "Label selectors for target pods"},
                    "volume_path": {"type": "string", "description": "Volume mount path (e.g., '/var/lib/mysql')"},
                    "path": {"type": "string", "description": "File path pattern (e.g., '**/*.db', '/data/*')"},
                    "delay": {"type": "string", "description": "I/O delay (e.g., '10ms', '100ms', '1s')"},
                    "duration": {"type": "string", "description": "Experiment duration"},
                    "percent": {"type": "integer", "description": "Percentage of I/O operations to delay 0-100 (default: 100)"},
                    "mode": {"type": "string", "description": "Selection mode (default: 'all')"},
                    "methods": {"type": "array", "items": {"type": "string"}, "description": "File system methods (e.g., ['read', 'write'])"},
                },
                "required": ["namespace", "target_labels", "volume_path", "path", "delay", "duration"]
            }
        ),
        Tool(
            name="create_io_fault",
            description="Inject I/O errors to simulate disk failures. Returns error codes for file operations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "namespace": {"type": "string"},
                    "target_labels": {"type": "object"},
                    "volume_path": {"type": "string"},
                    "path": {"type": "string"},
                    "errno": {"type": "integer", "description": "Error number (e.g., 5=EIO, 28=ENOSPC, 13=EACCES)"},
                    "duration": {"type": "string"},
                    "percent": {"type": "integer", "description": "Default: 100"},
                    "mode": {"type": "string", "description": "Default: 'all'"},
                    "methods": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["namespace", "target_labels", "volume_path", "path", "errno", "duration"]
            }
        ),
        Tool(
            name="create_io_attr_override",
            description="Override file attributes like permissions or size. Use this to test permission errors or size changes.",
            inputSchema={
                "type": "object",
                "properties": {
                    "namespace": {"type": "string"},
                    "target_labels": {"type": "object"},
                    "volume_path": {"type": "string"},
                    "path": {"type": "string"},
                    "duration": {"type": "string"},
                    "perm": {"type": "integer", "description": "File permissions in octal (e.g., 292 for 0o444 read-only)"},
                    "size": {"type": "integer", "description": "Override file size in bytes"},
                    "percent": {"type": "integer", "description": "Default: 100"},
                    "mode": {"type": "string", "description": "Default: 'all'"},
                    "methods": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["namespace", "target_labels", "volume_path", "path", "duration"]
            }
        ),
        Tool(
            name="create_io_mistake",
            description="Inject wrong data into file read/write operations (data corruption). Use this to test data validation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "namespace": {"type": "string"},
                    "target_labels": {"type": "object"},
                    "volume_path": {"type": "string"},
                    "path": {"type": "string"},
                    "duration": {"type": "string"},
                    "filling": {"type": "string", "description": "Error filling: 'zero' or 'random' (default: 'zero')"},
                    "max_occurrences": {"type": "integer", "description": "Max errors per operation (default: 1)"},
                    "max_length": {"type": "integer", "description": "Max error length in bytes (default: 1)"},
                    "percent": {"type": "integer", "description": "Default: 100"},
                    "mode": {"type": "string", "description": "Default: 'all'"},
                    "methods": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["namespace", "target_labels", "volume_path", "path", "duration"]
            }
        ),

        # HTTPChaos tools
        Tool(
            name="create_http_abort",
            description="Abort HTTP connections to simulate network failures. Use this to test retry logic and error handling.",
            inputSchema={
                "type": "object",
                "properties": {
                    "namespace": {"type": "string", "description": "Target namespace"},
                    "target_labels": {"type": "object", "description": "Label selectors for target pods"},
                    "port": {"type": "integer", "description": "TCP port (e.g., 80, 8080)"},
                    "duration": {"type": "string", "description": "Experiment duration"},
                    "target": {"type": "string", "description": "Target phase: 'Request' or 'Response' (default: 'Request')"},
                    "method": {"type": "string", "description": "HTTP method (e.g., 'GET', 'POST')"},
                    "path": {"type": "string", "description": "URI path pattern (e.g., '/api/*')"},
                    "mode": {"type": "string", "description": "Selection mode (default: 'all')"},
                    "request_headers": {"type": "object", "description": "Match specific headers"},
                },
                "required": ["namespace", "target_labels", "port", "duration"]
            }
        ),
        Tool(
            name="create_http_delay",
            description="Inject latency into HTTP requests or responses. Use this to test timeout handling.",
            inputSchema={
                "type": "object",
                "properties": {
                    "namespace": {"type": "string"},
                    "target_labels": {"type": "object"},
                    "port": {"type": "integer"},
                    "delay": {"type": "string", "description": "Latency duration (e.g., '10ms', '2s')"},
                    "duration": {"type": "string"},
                    "target": {"type": "string", "description": "Default: 'Request'"},
                    "method": {"type": "string"},
                    "path": {"type": "string"},
                    "mode": {"type": "string"},
                    "request_headers": {"type": "object"},
                },
                "required": ["namespace", "target_labels", "port", "delay", "duration"]
            }
        ),
        Tool(
            name="create_http_replace",
            description="Replace content in HTTP messages. Use this to test error response handling.",
            inputSchema={
                "type": "object",
                "properties": {
                    "namespace": {"type": "string"},
                    "target_labels": {"type": "object"},
                    "port": {"type": "integer"},
                    "duration": {"type": "string"},
                    "target": {"type": "string", "description": "Default: 'Request'"},
                    "method": {"type": "string"},
                    "path": {"type": "string"},
                    "replace_headers": {"type": "object", "description": "Headers to replace"},
                    "replace_body": {"type": "string", "description": "Body content to replace"},
                    "mode": {"type": "string"},
                    "request_headers": {"type": "object"},
                },
                "required": ["namespace", "target_labels", "port", "duration"]
            }
        ),
        Tool(
            name="create_http_patch",
            description="Add content to HTTP messages. Use this to test additional header/body handling.",
            inputSchema={
                "type": "object",
                "properties": {
                    "namespace": {"type": "string"},
                    "target_labels": {"type": "object"},
                    "port": {"type": "integer"},
                    "duration": {"type": "string"},
                    "target": {"type": "string", "description": "Default: 'Request'"},
                    "method": {"type": "string"},
                    "path": {"type": "string"},
                    "patch_headers": {"type": "array", "items": {"type": "array"}, "description": "Headers as [['key', 'value']] pairs"},
                    "patch_body_value": {"type": "string", "description": "JSON body content to add"},
                    "mode": {"type": "string"},
                    "request_headers": {"type": "object"},
                },
                "required": ["namespace", "target_labels", "port", "duration"]
            }
        ),

        # DNSChaos tools
        Tool(
            name="create_dns_error",
            description="Return DNS errors for specified domain patterns. Use this to test DNS failure handling.",
            inputSchema={
                "type": "object",
                "properties": {
                    "namespace": {"type": "string", "description": "Target namespace"},
                    "target_labels": {"type": "object", "description": "Label selectors for target pods"},
                    "duration": {"type": "string", "description": "Experiment duration"},
                    "patterns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "DNS patterns (e.g., ['google.com', '*.example.com']). Wildcard (*) at end. Default: all domains"
                    },
                    "mode": {"type": "string", "description": "Selection mode (default: 'all')"},
                },
                "required": ["namespace", "target_labels", "duration"]
            }
        ),
        Tool(
            name="create_dns_random",
            description="Return random IP addresses for DNS queries. Use this to test service discovery failures.",
            inputSchema={
                "type": "object",
                "properties": {
                    "namespace": {"type": "string"},
                    "target_labels": {"type": "object"},
                    "duration": {"type": "string"},
                    "patterns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "DNS patterns (e.g., ['api.example.com']). Default: all domains"
                    },
                    "mode": {"type": "string"},
                },
                "required": ["namespace", "target_labels", "duration"]
            }
        ),

        # PhysicalMachineChaos tools
        Tool(
            name="create_physical_stress_cpu",
            description="Inject CPU stress on physical/virtual machines. Requires Chaosd agent on target machines.",
            inputSchema={
                "type": "object",
                "properties": {
                    "namespace": {"type": "string", "description": "Namespace for chaos resource"},
                    "duration": {"type": "string", "description": "Experiment duration (e.g., '60s', '5m')"},
                    "address": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Target machine addresses (IP or hostname). Mutually exclusive with selector."
                    },
                    "selector": {
                        "type": "object",
                        "description": "Label selectors for target machines. Mutually exclusive with address."
                    },
                    "mode": {"type": "string", "description": "Selection mode (default: 'one')"},
                    "workers": {"type": "integer", "description": "Number of CPU stress workers (default: 1)"},
                    "load": {"type": "integer", "description": "CPU load percentage 0-100 per worker"},
                },
                "required": ["namespace", "duration"]
            }
        ),
        Tool(
            name="create_physical_stress_memory",
            description="Inject memory stress on physical/virtual machines. Requires Chaosd agent on target machines.",
            inputSchema={
                "type": "object",
                "properties": {
                    "namespace": {"type": "string"},
                    "duration": {"type": "string"},
                    "address": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Target machine addresses. Mutually exclusive with selector."
                    },
                    "selector": {
                        "type": "object",
                        "description": "Label selectors. Mutually exclusive with address."
                    },
                    "mode": {"type": "string", "description": "Default: 'one'"},
                    "size": {"type": "string", "description": "Memory size to allocate (e.g., '256MB', '1GB'). If not specified, allocates all available memory."},
                },
                "required": ["namespace", "duration"]
            }
        ),
        Tool(
            name="create_physical_disk_fill",
            description="Fill disk space on physical/virtual machines. Requires Chaosd agent on target machines.",
            inputSchema={
                "type": "object",
                "properties": {
                    "namespace": {"type": "string"},
                    "duration": {"type": "string"},
                    "path": {"type": "string", "description": "Directory path to fill (must exist)"},
                    "size": {"type": "string", "description": "Size to fill (e.g., '1GB', '500MB')"},
                    "address": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Target machine addresses. Mutually exclusive with selector."
                    },
                    "selector": {
                        "type": "object",
                        "description": "Label selectors. Mutually exclusive with address."
                    },
                    "mode": {"type": "string", "description": "Default: 'one'"},
                    "fill_by_fallocate": {"type": "boolean", "description": "Use fallocate for faster filling (default: true)"},
                },
                "required": ["namespace", "duration", "path", "size"]
            }
        ),
        Tool(
            name="create_physical_process_kill",
            description="Kill processes on physical/virtual machines. Requires Chaosd agent on target machines.",
            inputSchema={
                "type": "object",
                "properties": {
                    "namespace": {"type": "string"},
                    "duration": {"type": "string"},
                    "process": {"type": "string", "description": "Process name or pattern to kill"},
                    "address": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Target machine addresses. Mutually exclusive with selector."
                    },
                    "selector": {
                        "type": "object",
                        "description": "Label selectors. Mutually exclusive with address."
                    },
                    "mode": {"type": "string", "description": "Default: 'one'"},
                    "signal": {"type": "integer", "description": "Signal number to send (default: 9 for SIGKILL). Common: 9=SIGKILL, 15=SIGTERM, 2=SIGINT"},
                },
                "required": ["namespace", "duration", "process"]
            }
        ),
        Tool(
            name="create_physical_clock_skew",
            description="Skew system clock on physical/virtual machines. Requires Chaosd agent on target machines.",
            inputSchema={
                "type": "object",
                "properties": {
                    "namespace": {"type": "string"},
                    "duration": {"type": "string"},
                    "time_offset": {"type": "string", "description": "Time offset to apply (e.g., '5m', '-10s', '1h'). Positive=forward, negative=backward"},
                    "address": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Target machine addresses. Mutually exclusive with selector."
                    },
                    "selector": {
                        "type": "object",
                        "description": "Label selectors. Mutually exclusive with address."
                    },
                    "mode": {"type": "string", "description": "Default: 'one'"},
                    "clock_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Clock IDs to skew (default: ['CLOCK_REALTIME']). Options: CLOCK_REALTIME, CLOCK_MONOTONIC"
                    },
                },
                "required": ["namespace", "duration", "time_offset"]
            }
        ),

        # Validation tools
        Tool(
            name="validate_environment",
            description="Validate complete Chaos Mesh environment setup. Checks kubectl, cluster, Chaos Mesh installation, CRDs, and components.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="check_chaos_type_requirements",
            description="Check if environment meets requirements for specific chaos type (dns, physical, network, pod, stress, io, http).",
            inputSchema={
                "type": "object",
                "properties": {
                    "chaos_type": {
                        "type": "string",
                        "description": "Chaos type: dns, physical, network, pod, stress, io, or http"
                    }
                },
                "required": ["chaos_type"]
            }
        ),
        Tool(
            name="get_chaos_requirements",
            description="Get detailed requirements for a specific chaos type including CRDs, components, and notes.",
            inputSchema={
                "type": "object",
                "properties": {
                    "chaos_type": {
                        "type": "string",
                        "description": "Chaos type: dns, physical, network, pod, stress, io, or http"
                    }
                },
                "required": ["chaos_type"]
            }
        ),

        # Management tools
        Tool(
            name="get_experiment_status",
            description="Get detailed status of a Chaos experiment. Auto-detects experiment kind.",
            inputSchema={
                "type": "object",
                "properties": {
                    "experiment_id": {"type": "string", "description": "Experiment name/ID"},
                    "namespace": {"type": "string", "description": "Default: 'default'"},
                },
                "required": ["experiment_id"]
            }
        ),
        Tool(
            name="list_active_experiments",
            description="List all active Chaos experiments in a namespace.",
            inputSchema={
                "type": "object",
                "properties": {
                    "namespace": {"type": "string", "description": "Default: 'default'"},
                    "kind": {"type": "string", "description": "Optional filter by kind (e.g., 'NetworkChaos')"},
                },
            }
        ),
        Tool(
            name="delete_experiment",
            description="Delete (stop and remove) a Chaos experiment.",
            inputSchema={
                "type": "object",
                "properties": {
                    "experiment_id": {"type": "string"},
                    "namespace": {"type": "string", "description": "Default: 'default'"},
                },
                "required": ["experiment_id"]
            }
        ),
        Tool(
            name="pause_experiment",
            description="Pause a running experiment. Chaos injection stops but experiment remains.",
            inputSchema={
                "type": "object",
                "properties": {
                    "experiment_id": {"type": "string"},
                    "namespace": {"type": "string"},
                },
                "required": ["experiment_id"]
            }
        ),
        Tool(
            name="resume_experiment",
            description="Resume a paused experiment.",
            inputSchema={
                "type": "object",
                "properties": {
                    "experiment_id": {"type": "string"},
                    "namespace": {"type": "string"},
                },
                "required": ["experiment_id"]
            }
        ),
        Tool(
            name="get_experiment_events",
            description="Get Kubernetes events related to an experiment for debugging.",
            inputSchema={
                "type": "object",
                "properties": {
                    "experiment_id": {"type": "string"},
                    "namespace": {"type": "string"},
                },
                "required": ["experiment_id"]
            }
        ),
    ]


# Export tools list for external use
TOOLS = get_tools()


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available Chaos Mesh tools."""
    return TOOLS


# ============================================================================
# Tool Handlers
# ============================================================================

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    try:
        # NetworkChaos
        if name == "create_network_delay":
            result = await create_network_delay(**arguments)
        elif name == "create_network_loss":
            result = await create_network_loss(**arguments)
        elif name == "create_network_partition":
            result = await create_network_partition(**arguments)
        elif name == "create_network_corrupt":
            result = await create_network_corrupt(**arguments)

        # StressChaos
        elif name == "create_stress_cpu":
            result = await create_stress_cpu(**arguments)
        elif name == "create_stress_memory":
            result = await create_stress_memory(**arguments)
        elif name == "create_stress_combined":
            result = await create_stress_combined(**arguments)

        # PodChaos
        elif name == "create_pod_kill":
            result = await create_pod_kill(**arguments)
        elif name == "create_pod_failure":
            result = await create_pod_failure(**arguments)
        elif name == "create_container_kill":
            result = await create_container_kill(**arguments)

        # IOChaos
        elif name == "create_io_latency":
            result = await create_io_latency(**arguments)
        elif name == "create_io_fault":
            result = await create_io_fault(**arguments)
        elif name == "create_io_attr_override":
            result = await create_io_attr_override(**arguments)
        elif name == "create_io_mistake":
            result = await create_io_mistake(**arguments)

        # HTTPChaos
        elif name == "create_http_abort":
            result = await create_http_abort(**arguments)
        elif name == "create_http_delay":
            result = await create_http_delay(**arguments)
        elif name == "create_http_replace":
            result = await create_http_replace(**arguments)
        elif name == "create_http_patch":
            result = await create_http_patch(**arguments)

        # DNSChaos
        elif name == "create_dns_error":
            result = await create_dns_error(**arguments)
        elif name == "create_dns_random":
            result = await create_dns_random(**arguments)

        # PhysicalMachineChaos
        elif name == "create_physical_stress_cpu":
            result = await create_physical_stress_cpu(**arguments)
        elif name == "create_physical_stress_memory":
            result = await create_physical_stress_memory(**arguments)
        elif name == "create_physical_disk_fill":
            result = await create_physical_disk_fill(**arguments)
        elif name == "create_physical_process_kill":
            result = await create_physical_process_kill(**arguments)
        elif name == "create_physical_clock_skew":
            result = await create_physical_clock_skew(**arguments)

        # Validation
        elif name == "validate_environment":
            result = await validate_environment()
        elif name == "check_chaos_type_requirements":
            result = await check_chaos_type_requirements(**arguments)
        elif name == "get_chaos_requirements":
            result = await get_chaos_requirements(**arguments)

        # Management
        elif name == "get_experiment_status":
            result = await get_experiment_status(**arguments)
        elif name == "list_active_experiments":
            result = await list_active_experiments(**arguments)
        elif name == "delete_experiment":
            result = await delete_experiment(**arguments)
        elif name == "pause_experiment":
            result = await pause_experiment(**arguments)
        elif name == "resume_experiment":
            result = await resume_experiment(**arguments)
        elif name == "get_experiment_events":
            result = await get_experiment_events(**arguments)

        else:
            raise ValueError(f"Unknown tool: {name}")

        import json
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


# ============================================================================
# Main Entry Point
# ============================================================================

async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
