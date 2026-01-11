from fastapi import APIRouter, HTTPException
from ..docker_client import docker_client
from ..models import DockerStack, GraphData, ContainerInfo, NetworkDetail, VolumeDetail
from datetime import datetime

router = APIRouter(prefix="/api/docker", tags=["docker"])


@router.get("/ping")
async def ping():
    """Check Docker daemon connectivity"""
    if docker_client.ping():
        return {"status": "ok", "message": "Docker daemon is accessible"}
    raise HTTPException(status_code=503, detail="Cannot connect to Docker daemon")


@router.get("/containers", response_model=list[ContainerInfo])
async def get_containers():
    """Get all containers with detailed information"""
    try:
        return docker_client.get_containers()
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/containers/{container_id}", response_model=ContainerInfo)
async def get_container(container_id: str):
    """Get a specific container by ID or name"""
    try:
        containers = docker_client.get_containers()
        for container in containers:
            if container.id.startswith(container_id) or container.name == container_id:
                return container
        raise HTTPException(status_code=404, detail=f"Container {container_id} not found")
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/networks", response_model=list[NetworkDetail])
async def get_networks():
    """Get all Docker networks"""
    try:
        return docker_client.get_networks()
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/volumes", response_model=list[VolumeDetail])
async def get_volumes():
    """Get all Docker volumes"""
    try:
        return docker_client.get_volumes()
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/stack", response_model=DockerStack)
async def get_stack():
    """Get complete Docker stack information"""
    try:
        return docker_client.get_stack()
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/graph", response_model=GraphData)
async def get_graph():
    """Get graph data for visualization"""
    try:
        return docker_client.get_graph_data()
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


def _generate_ascii_box(title: str, content: list[str], width: int = 60) -> list[str]:
    """Generate an ASCII box diagram"""
    lines = []
    inner_width = width - 4
    lines.append("┌" + "─" * (width - 2) + "┐")
    # Title centered
    title_padded = title.center(inner_width)
    lines.append("│ " + title_padded + " │")
    lines.append("├" + "─" * (width - 2) + "┤")
    # Content
    for c in content:
        if len(c) > inner_width:
            c = c[:inner_width-3] + "..."
        lines.append("│ " + c.ljust(inner_width) + " │")
    lines.append("└" + "─" * (width - 2) + "┘")
    return lines


def _generate_network_diagram(containers: list, networks: list) -> list[str]:
    """Generate ASCII network topology diagram"""
    lines = []
    
    # Filter custom networks
    custom_networks = [n for n in networks if n.name not in ['bridge', 'host', 'none']]
    
    if not custom_networks:
        return ["No custom networks found."]
    
    for net in custom_networks:
        lines.append(f"╔{'═' * 58}╗")
        lines.append(f"║  🌐 Network: {net.name:<42} ║")
        lines.append(f"║  Driver: {net.driver:<45} ║")
        lines.append(f"╠{'═' * 58}╣")
        
        # Find containers in this network
        net_containers = [c for c in containers if any(n.network_name == net.name for n in c.networks)]
        
        if net_containers:
            for i, c in enumerate(net_containers):
                net_info = next((n for n in c.networks if n.network_name == net.name), None)
                ip = net_info.ip_address if net_info and net_info.ip_address else "N/A"
                status_char = "●" if c.status.value == "running" else "○"
                
                if i == len(net_containers) - 1:
                    lines.append(f"║  └── {status_char} {c.name:<30} ({ip:<15}) ║")
                else:
                    lines.append(f"║  ├── {status_char} {c.name:<30} ({ip:<15}) ║")
        else:
            lines.append("║  (no containers)                                        ║")
        
        lines.append(f"╚{'═' * 58}╝")
        lines.append("")
    
    return lines


def _generate_architecture_ascii(containers: list, networks: list) -> list[str]:
    """Generate ASCII architecture diagram showing tiers"""
    from ..docker_client import CATEGORY_TIERS
    
    lines = []
    
    # Group containers by tier
    tier_containers = {}
    for c in containers:
        tier = CATEGORY_TIERS.get(c.category, 2)
        if tier not in tier_containers:
            tier_containers[tier] = []
        tier_containers[tier].append(c)
    
    tier_names = {
        0: "Entry Point (Reverse Proxy)",
        1: "Security Layer",
        2: "Application Layer",
        3: "Cache / Messaging",
        4: "Data Layer (Database / Storage)",
        5: "Monitoring"
    }
    
    lines.append("```")
    lines.append("┌" + "─" * 70 + "┐")
    lines.append("│" + "Docker Stack Architecture".center(70) + "│")
    lines.append("└" + "─" * 70 + "┘")
    lines.append("         │")
    lines.append("         ▼")
    
    for tier_num in sorted(tier_containers.keys()):
        tier_name = tier_names.get(tier_num, f"Tier {tier_num}")
        ctrs = tier_containers[tier_num]
        
        lines.append("┌" + "─" * 70 + "┐")
        lines.append("│ " + f"[{tier_name}]".ljust(69) + "│")
        lines.append("│" + " " * 70 + "│")
        
        # Show containers in this tier (max 3 per line)
        for i in range(0, len(ctrs), 3):
            chunk = ctrs[i:i+3]
            boxes = []
            for c in chunk:
                status = "🟢" if c.status.value == "running" else "🔴"
                box = f"{status} {c.name[:18]}"
                boxes.append(box.center(22))
            line = "  ".join(boxes)
            lines.append("│ " + line.ljust(69) + "│")
        
        lines.append("└" + "─" * 70 + "┘")
        lines.append("         │")
        lines.append("         ▼")
    
    lines.append("    [Docker Daemon]")
    lines.append("```")
    
    return lines


@router.get("/docs")
async def get_docs():
    """Generate complete markdown documentation with multiple sections"""
    try:
        stack = docker_client.get_stack()
        
        doc = {
            "overview": _generate_overview_section(stack),
            "architecture": _generate_architecture_section(stack),
            "containers": _generate_containers_section(stack),
            "networks": _generate_networks_section(stack),
            "volumes": _generate_volumes_section(stack),
            "full": ""  # Combined full markdown
        }
        
        # Build full markdown
        md = []
        md.append(doc["overview"])
        md.append(doc["architecture"])
        md.append(doc["containers"])
        md.append(doc["networks"])
        md.append(doc["volumes"])
        md.append("\n---\n")
        md.append("*Generated by [SockMap](https://github.com/sockmap) 🧦*")
        
        doc["full"] = "\n".join(md)
        
        # Keep backward compatibility
        doc["markdown"] = doc["full"]
        
        return doc
        
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


def _generate_overview_section(stack) -> str:
    """Generate overview section"""
    md = []
    md.append("# 🧦 SockMap - Docker Stack Documentation")
    md.append(f"\n> Auto-generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md.append("")
    
    # Stats
    custom_nets = len([n for n in stack.networks if n.name not in ['bridge', 'host', 'none']])
    running = len([c for c in stack.containers if c.status.value == "running"])
    stopped = len(stack.containers) - running
    
    md.append("## 📊 Overview")
    md.append("")
    md.append("```")
    md.append("┌────────────────────────────────────────────────────────────┐")
    md.append("│                    Stack Statistics                        │")
    md.append("├────────────────────────────────────────────────────────────┤")
    md.append(f"│  📦 Containers:  {str(len(stack.containers)).ljust(5)} (🟢 {running} running, 🔴 {stopped} stopped)   │")
    md.append(f"│  🌐 Networks:    {str(custom_nets).ljust(5)} (custom networks)                    │")
    md.append(f"│  💾 Volumes:     {str(len(stack.volumes)).ljust(5)}                                      │")
    md.append("└────────────────────────────────────────────────────────────┘")
    md.append("```")
    md.append("")
    
    # Quick status table
    md.append("### Container Status Summary")
    md.append("")
    md.append("| Container | Image | Status | Category | Ports |")
    md.append("|-----------|-------|--------|----------|-------|")
    for c in sorted(stack.containers, key=lambda x: x.name):
        status_emoji = "🟢" if c.status.value == "running" else "🔴" if c.status.value == "exited" else "🟡"
        image_short = c.image.split(':')[0].split('/')[-1][:20]
        ports_str = ", ".join([f"{p.host_port}→{p.container_port}" for p in c.ports if p.host_port][:3]) or "-"
        md.append(f"| {c.name} | `{image_short}` | {status_emoji} {c.status.value} | {c.category.value} | {ports_str} |")
    md.append("")
    
    return "\n".join(md)


def _generate_architecture_section(stack) -> str:
    """Generate architecture section with ASCII diagrams"""
    md = []
    md.append("## 🏗️ Architecture")
    md.append("")
    
    # ASCII Architecture diagram
    arch_lines = _generate_architecture_ascii(stack.containers, stack.networks)
    md.extend(arch_lines)
    md.append("")
    
    # Network topology diagram
    md.append("### Network Topology")
    md.append("")
    md.append("```")
    net_lines = _generate_network_diagram(stack.containers, stack.networks)
    md.extend(net_lines)
    md.append("```")
    md.append("")
    
    # Connection flow
    md.append("### Connection Flow")
    md.append("")
    md.append("```")
    md.append("┌─────────────────────────────────────────────────────────┐")
    md.append("│                     Client Request                       │")
    md.append("└─────────────────────┬───────────────────────────────────┘")
    md.append("                      │")
    md.append("                      ▼")
    
    # Find reverse proxy
    proxy = next((c for c in stack.containers if c.category.value == "reverse_proxy"), None)
    if proxy:
        md.append("┌─────────────────────────────────────────────────────────┐")
        md.append(f"│  🔀 Reverse Proxy: {proxy.name:<37} │")
        ports = ", ".join([f":{p.host_port}" for p in proxy.ports if p.host_port][:3]) or "N/A"
        md.append(f"│     Listening on: {ports:<38} │")
        md.append("└─────────────────────┬───────────────────────────────────┘")
        md.append("                      │")
        md.append("                      ▼")
    
    # Find apps
    apps = [c for c in stack.containers if c.category.value in ["application", "backend", "frontend"]]
    if apps:
        md.append("┌─────────────────────────────────────────────────────────┐")
        md.append("│  📱 Applications                                        │")
        for app in apps[:5]:
            md.append(f"│     • {app.name:<50} │")
        if len(apps) > 5:
            md.append(f"│     ... and {len(apps)-5} more                                    │")
        md.append("└─────────────────────┬───────────────────────────────────┘")
        md.append("                      │")
        md.append("                      ▼")
    
    # Find databases
    dbs = [c for c in stack.containers if c.category.value in ["database", "cache"]]
    if dbs:
        md.append("┌─────────────────────────────────────────────────────────┐")
        md.append("│  🗄️  Data Layer                                         │")
        for db in dbs[:5]:
            md.append(f"│     • {db.name:<50} │")
        md.append("└─────────────────────────────────────────────────────────┘")
    
    md.append("```")
    md.append("")
    
    return "\n".join(md)


def _generate_containers_section(stack) -> str:
    """Generate detailed containers section"""
    md = []
    md.append("## 📦 Containers Detail")
    md.append("")
    
    for c in sorted(stack.containers, key=lambda x: x.name):
        status_emoji = "🟢" if c.status.value == "running" else "🔴" if c.status.value == "exited" else "🟡"
        
        md.append(f"### {status_emoji} {c.name}")
        md.append("")
        
        # Basic info table
        md.append("| Property | Value |")
        md.append("|----------|-------|")
        md.append(f"| **Image** | `{c.image}` |")
        md.append(f"| **ID** | `{c.short_id}` |")
        md.append(f"| **Status** | {c.status.value} |")
        md.append(f"| **Category** | {c.category.value} |")
        md.append(f"| **Created** | {c.created[:19] if c.created else 'N/A'} |")
        md.append("")
        
        # Ports
        if c.ports:
            md.append("#### 🔌 Port Mappings")
            md.append("")
            md.append("| Host | Container | Protocol |")
            md.append("|------|-----------|----------|")
            for p in c.ports:
                host = f"`{p.host_ip}:{p.host_port}`" if p.host_port else "N/A"
                md.append(f"| {host} | `{p.container_port}` | {p.protocol} |")
            md.append("")
        
        # Networks
        if c.networks:
            md.append("#### 🌐 Networks")
            md.append("")
            md.append("| Network | IP Address | Gateway |")
            md.append("|---------|------------|---------|")
            for n in c.networks:
                ip = f"`{n.ip_address}`" if n.ip_address else "N/A"
                gw = f"`{n.gateway}`" if n.gateway else "N/A"
                md.append(f"| {n.network_name} | {ip} | {gw} |")
            md.append("")
        
        # Volumes
        if c.volumes:
            md.append("#### 💾 Volume Mounts")
            md.append("")
            md.append("| Source | Destination | Mode |")
            md.append("|--------|-------------|------|")
            for v in c.volumes:
                src = v.source if len(v.source) <= 40 else "..." + v.source[-37:]
                md.append(f"| `{src}` | `{v.destination}` | {v.mode} |")
            md.append("")
        
        # Environment variables (filtered for safety)
        safe_envs = [e for e in c.env_vars if not any(s in e.upper() for s in ['PASSWORD', 'SECRET', 'KEY', 'TOKEN', 'CREDENTIAL'])]
        if safe_envs:
            md.append("#### ⚙️ Environment Variables")
            md.append("")
            md.append("```bash")
            for env in safe_envs[:15]:
                md.append(env)
            if len(safe_envs) > 15:
                md.append(f"# ... and {len(safe_envs) - 15} more variables")
            md.append("```")
            md.append("")
        
        # Dependencies
        if c.dependencies:
            md.append("#### 🔗 Dependencies")
            md.append("")
            for dep in c.dependencies:
                md.append(f"- → **{dep.target_name}** _{dep.type}_")
            md.append("")
        
        # Labels (useful ones)
        interesting_labels = {k: v for k, v in c.labels.items() if any(p in k for p in ['traefik', 'compose', 'maintainer', 'description', 'version'])}
        if interesting_labels:
            md.append("#### 🏷️ Labels")
            md.append("")
            md.append("```yaml")
            for k, v in list(interesting_labels.items())[:10]:
                md.append(f"{k}: {v[:60] if len(v) > 60 else v}")
            md.append("```")
            md.append("")
        
        md.append("---")
        md.append("")
    
    return "\n".join(md)


def _generate_networks_section(stack) -> str:
    """Generate networks section"""
    md = []
    md.append("## 🌐 Networks")
    md.append("")
    
    custom_nets = [n for n in stack.networks if n.name not in ['bridge', 'host', 'none']]
    
    if not custom_nets:
        md.append("_No custom networks found._")
        md.append("")
        return "\n".join(md)
    
    for n in custom_nets:
        md.append(f"### {n.name}")
        md.append("")
        md.append("| Property | Value |")
        md.append("|----------|-------|")
        md.append(f"| **ID** | `{n.short_id}` |")
        md.append(f"| **Driver** | {n.driver} |")
        md.append(f"| **Scope** | {n.scope} |")
        md.append(f"| **Internal** | {'Yes' if n.internal else 'No'} |")
        md.append("")
        
        # Containers in network
        if n.containers:
            md.append("**Connected Containers:**")
            md.append("")
            for cid in n.containers:
                c = next((c for c in stack.containers if c.id == cid), None)
                if c:
                    net_info = next((net for net in c.networks if net.network_name == n.name), None)
                    ip = net_info.ip_address if net_info and net_info.ip_address else "N/A"
                    md.append(f"- {c.name} (`{ip}`)")
            md.append("")
        
        md.append("---")
        md.append("")
    
    return "\n".join(md)


def _generate_volumes_section(stack) -> str:
    """Generate volumes section"""
    md = []
    md.append("## 💾 Volumes")
    md.append("")
    
    if not stack.volumes:
        md.append("_No volumes found._")
        md.append("")
        return "\n".join(md)
    
    md.append("| Volume | Driver | Mountpoint | Used By |")
    md.append("|--------|--------|------------|---------|")
    for v in stack.volumes:
        containers = ", ".join(v.containers) if v.containers else "_unused_"
        name = v.name if len(v.name) <= 25 else v.name[:22] + "..."
        mountpoint = v.mountpoint if len(v.mountpoint) <= 30 else "..." + v.mountpoint[-27:]
        md.append(f"| `{name}` | {v.driver} | `{mountpoint}` | {containers} |")
    md.append("")
    
    # Volume details
    md.append("### Volume Details")
    md.append("")
    
    for v in stack.volumes:
        if v.containers:
            md.append(f"#### {v.name if len(v.name) <= 30 else v.name[:27] + '...'}")
            md.append("")
            md.append(f"- **Full Name**: `{v.name}`")
            md.append(f"- **Driver**: {v.driver}")
            md.append(f"- **Mountpoint**: `{v.mountpoint}`")
            if v.containers:
                md.append(f"- **Used by**: {', '.join(v.containers)}")
            md.append("")
    
    return "\n".join(md)
