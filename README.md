# Chaos Mesh MCP Server

**Model Context Protocol (MCP) server for Chaos Mesh chaos engineering operations.**

This MCP server provides AI assistants like Claude with direct access to Chaos Mesh for automated chaos engineering and resilience testing. Create, manage, and validate chaos experiments through natural language conversations.

## Features

### Chaos Types (24 tools)

- **NetworkChaos** (4 tools): Simulate network delays, packet loss, partitions, and corruption
- **StressChaos** (3 tools): Apply CPU and memory stress to containers
- **PodChaos** (3 tools): Kill pods, fail pods, or kill specific containers
- **IOChaos** (4 tools): Inject I/O latency, faults, attribute changes, and data corruption
- **HTTPChaos** (4 tools): Abort connections, inject delays, replace/patch HTTP content
- **DNSChaos** (2 tools): Return DNS errors or random IPs for specified domains
- **PhysicalMachineChaos** (5 tools): Inject chaos on physical/virtual machines (requires Chaosd)

### Management & Validation (9 tools)

- **Environment Validation** (3 tools): Check prerequisites, verify component status, get chaos-specific requirements
- **Experiment Management** (6 tools): Query status, list experiments, delete, pause, resume, get events

## Tested Environment

This package has been tested and verified with:
- **Chaos Mesh**: v2.8.0
- **Kubernetes**: v1.27+ (tested with v1.27.6)
- **kubectl**: v1.27.6+
- **Python**: 3.10, 3.11, 3.12

## Prerequisites

Before using this MCP server, ensure you have:

1. **kubectl** installed and configured
2. **Kubernetes cluster** accessible via kubectl (v1.15+)
3. **Chaos Mesh** installed in the cluster (v2.6+ recommended)

### Component-Specific Requirements

- **DNSChaos**: Requires `chaos-dns-server` pod running in chaos-mesh namespace
- **PhysicalMachineChaos**: Requires Chaosd agent on target physical/virtual machines
- **Other chaos types**: Only require standard Chaos Mesh components (controller-manager, daemon)

**Tip**: Use the `validate_environment` tool to check your setup!

## Installation

### Step 1: Install Chaos Mesh

If Chaos Mesh is not already installed on your cluster:

```bash
# Using Helm (Recommended)
helm repo add chaos-mesh https://charts.chaos-mesh.org
helm install chaos-mesh chaos-mesh/chaos-mesh \
  --namespace chaos-mesh \
  --create-namespace \
  --version 2.8.0

# Verify installation
kubectl get pods -n chaos-mesh
# Should see: chaos-controller-manager, chaos-daemon, chaos-dashboard
```

### Step 2: Install MCP Server

#### Option 1: Install from GitHub (Recommended)

```bash
pip install git+https://github.com/ernestolee13/chaos-mesh-mcp.git
```

#### Option 2: Install from Source

```bash
git clone https://github.com/ernestolee13/chaos-mesh-mcp.git
cd chaos-mesh-mcp
pip install -e .
```

## Quick Start

### 1. Configure Claude Desktop

Edit `~/.config/claude/claude_desktop_config.json` (Linux/Mac) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "chaos-mesh": {
      "command": "python",
      "args": ["-m", "chaos_mesh_mcp.server"]
    }
  }
}
```

### 2. Restart Claude Desktop

Restart Claude Desktop to load the MCP server.

### 3. Validate Your Environment

In Claude Desktop, ask:

```
You: "Validate my Chaos Mesh environment"
Claude: [Checks kubectl, cluster connection, Chaos Mesh installation, and components]
```

### 4. Start Using Chaos Engineering

Example conversations:

```
You: "Create a network delay of 500ms for pods with label app=api for 2 minutes"
Claude: [Creates NetworkChaos experiment]

You: "Check if DNSChaos is available"
Claude: [Runs check_chaos_type_requirements for dns]

You: "List all active chaos experiments in default namespace"
Claude: [Lists current experiments with their status]
```

## Architecture

```
chaos-mesh-mcp/
├── chaos_mesh_mcp/
│   ├── server.py           # MCP server main entry point
│   ├── kubectl.py          # Kubectl command runner
│   ├── templates.py        # YAML template rendering
│   ├── validators.py       # Parameter validation
│   └── tools/
│       ├── network.py      # NetworkChaos (4 tools)
│       ├── stress.py       # StressChaos (3 tools)
│       ├── pod.py          # PodChaos (3 tools)
│       ├── io.py           # IOChaos (4 tools)
│       ├── http.py         # HTTPChaos (4 tools)
│       ├── dns.py          # DNSChaos (2 tools)
│       ├── physical.py     # PhysicalMachineChaos (5 tools)
│       ├── validation.py   # Environment validation (3 tools)
│       └── management.py   # Experiment management (6 tools)
├── pyproject.toml          # Package metadata
├── LICENSE                 # MIT License
└── README.md               # This file
```

## Environment Validation

This MCP includes comprehensive environment validation:

```
validate_environment
├─ Check kubectl availability & version
├─ Check cluster connectivity
├─ Check Chaos Mesh installation
├─ Check CRDs (7 chaos types)
└─ Check components
   ├─ chaos-controller-manager (required)
   ├─ chaos-daemon (required)
   ├─ chaos-dns-server (optional, for DNSChaos)
   └─ chaos-dashboard (optional)

check_chaos_type_requirements(chaos_type)
├─ Verify specific CRD installed
├─ Check required components running
└─ Show external requirements (e.g., Chaosd for Physical)
```

## Troubleshooting

### DNSChaos Not Working

```bash
# Check if chaos-dns-server is running
kubectl get pods -n chaos-mesh | grep dns

# If not present, install with DNS support:
helm upgrade chaos-mesh chaos-mesh/chaos-mesh --namespace=chaos-mesh --set dnsServer.create=true
```

### PhysicalMachineChaos Not Working

PhysicalMachineChaos requires Chaosd agent on target machines:

#### Setup Instructions

1. **Install Chaosd on Target Machine** (physical or virtual):
   ```bash
   wget https://mirrors.chaos-mesh.org/chaosd-latest-linux-amd64.tar.gz
   tar -xzf chaosd-latest-linux-amd64.tar.gz
   sudo cp chaosd-latest-linux-amd64/chaosd /usr/local/bin/
   sudo apt-get install -y stress-ng  # Required for CPU/Memory stress
   ```

2. **Start Chaosd Server**:
   ```bash
   sudo chaosd server --port 31767
   ```

3. **Use the Correct Address Format** (⚠️ Important):
   ```python
   # ✓ CORRECT - No protocol prefix
   await create_physical_stress_cpu(
       namespace="default",
       address=["192.168.1.100:31767"],  # IP:PORT only
       duration="60s",
       workers=2,
       load=80
   )

   # ✗ WRONG - Including http:// causes HTTPS error
   await create_physical_stress_cpu(
       namespace="default",
       address=["http://192.168.1.100:31767"],  # Don't do this!
       duration="60s"
   )
   ```

#### Important Notes

- **Address format**: Use `IP:PORT` or `hostname:PORT` without `http://` or `https://` prefix
- **Chaosd can run on localhost**: The machine can inject chaos on itself
- **TLS**: For production, configure Chaosd with HTTPS (optional for testing)
- **Clock action**: Requires `pid` parameter to target specific process

See: [Chaosd Documentation](https://chaos-mesh.org/docs/simulate-physical-machine-chaos/)

### Permission Errors

Ensure your Kubernetes user has appropriate RBAC permissions:

```bash
# Check if you can create chaos experiments
kubectl auth can-i create networkchaos --all-namespaces
```

## Documentation

Based on Chaos Mesh official documentation:

- [NetworkChaos](https://chaos-mesh.org/docs/simulate-network-chaos-on-kubernetes/)
- [StressChaos](https://chaos-mesh.org/docs/simulate-heavy-stress-on-kubernetes/)
- [PodChaos](https://chaos-mesh.org/docs/simulate-pod-chaos-on-kubernetes/)
- [IOChaos](https://chaos-mesh.org/docs/simulate-io-chaos-on-kubernetes/)
- [HTTPChaos](https://chaos-mesh.org/docs/simulate-http-chaos-on-kubernetes/)
- [DNSChaos](https://chaos-mesh.org/docs/simulate-dns-chaos-on-kubernetes/)
- [PhysicalMachineChaos](https://chaos-mesh.org/docs/simulate-physical-machine-chaos/)

## Available Tools (33 total)

### NetworkChaos (4 tools)
- `create_network_delay` - Inject network latency to simulate slow connections
- `create_network_loss` - Simulate packet loss for unreliable networks
- `create_network_partition` - Create network splits to test split-brain scenarios
- `create_network_corrupt` - Corrupt network packets to test data integrity

### StressChaos (3 tools)
- `create_stress_cpu` - Apply CPU load to test performance under stress
- `create_stress_memory` - Apply memory pressure to test OOM scenarios
- `create_stress_combined` - Apply both CPU and memory stress simultaneously

### PodChaos (3 tools)
- `create_pod_kill` - Kill pods to test recovery mechanisms
- `create_pod_failure` - Make pods temporarily unavailable without killing
- `create_container_kill` - Kill specific containers within pods

### IOChaos (4 tools)
- `create_io_latency` - Inject I/O delays to simulate slow disks
- `create_io_fault` - Return error codes for file operations (ENOSPC, EIO, etc.)
- `create_io_attr_override` - Modify file attributes (permissions, size)
- `create_io_mistake` - Inject data corruption into read/write operations

### HTTPChaos (4 tools)
- `create_http_abort` - Abort HTTP connections to simulate network failures
- `create_http_delay` - Inject latency into HTTP requests/responses
- `create_http_replace` - Replace HTTP message content (headers, body)
- `create_http_patch` - Add content to HTTP messages

### DNSChaos (2 tools)
- `create_dns_error` - Return DNS errors for specified domain patterns
- `create_dns_random` - Return random IP addresses for DNS queries

### PhysicalMachineChaos (5 tools)
- `create_physical_stress_cpu` - Inject CPU stress on physical/virtual machines
- `create_physical_stress_memory` - Inject memory stress on physical/virtual machines
- `create_physical_disk_fill` - Fill disk space on physical/virtual machines
- `create_physical_process_kill` - Kill processes on physical/virtual machines
- `create_physical_clock_skew` - Skew system clock on physical/virtual machines

### Environment Validation (3 tools)
- `validate_environment` - Comprehensive environment validation (kubectl, cluster, Chaos Mesh, CRDs, components)
- `check_chaos_type_requirements` - Check requirements for specific chaos type
- `get_chaos_requirements` - Get detailed requirements for a chaos type

### Experiment Management (6 tools)
- `get_experiment_status` - Get detailed status of a chaos experiment
- `list_active_experiments` - List all active experiments in cluster
- `delete_experiment` - Delete a chaos experiment
- `pause_experiment` - Pause a running experiment
- `resume_experiment` - Resume a paused experiment
- `get_experiment_events` - Get Kubernetes events for debugging

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

This is part of the chaos-agents project. Issues and pull requests are welcome!

## Credits

Built on top of:
- [Chaos Mesh](https://chaos-mesh.org/) - Cloud-native chaos engineering platform
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) - Protocol for AI model context management
