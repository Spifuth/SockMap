import docker
import re
from docker.errors import DockerException
from typing import Optional
from .models import (
    ContainerInfo,
    ContainerStatus,
    ContainerCategory,
    ContainerDependency,
    PortMapping,
    VolumeMount,
    NetworkInfo,
    NetworkDetail,
    VolumeDetail,
    DockerStack,
    GraphData,
    GraphNode,
    GraphEdge,
)


# Patterns pour détecter le type de container
CATEGORY_PATTERNS = {
    ContainerCategory.REVERSE_PROXY: {
        "images": [
            "traefik", "nginx-proxy", "nginx/nginx", "jwilder/nginx-proxy",
            "caddy", "haproxy", "envoyproxy", "kong", "linuxserver/swag",
            "nginxproxymanager", "nginx-proxy-manager"
        ],
        "names": ["traefik", "nginx-proxy", "caddy", "haproxy", "proxy", "swag", "npm"],
        "labels": ["traefik.enable"],
        "ports": [80, 443, 8080, 8443],
    },
    ContainerCategory.SECURITY: {
        "images": [
            "authelia", "tinyauth", "keycloak", "authentik", "oauth2-proxy",
            "thomseddon/traefik-forward-auth", "vouch", "organizr",
            "lldap", "openldap", "freeipa", "crowdsec"
        ],
        "names": ["authelia", "tinyauth", "keycloak", "authentik", "auth", "ldap", "crowdsec"],
        "labels": [],
        "ports": [9091, 8080, 9000],
    },
    ContainerCategory.DATABASE: {
        "images": [
            "mysql", "mariadb", "postgres", "postgresql", "mongo", "mongodb",
            "redis", "memcached", "influxdb", "clickhouse", "cockroachdb",
            "timescaledb", "cassandra", "neo4j", "arangodb", "sqlite"
        ],
        "names": ["mysql", "mariadb", "postgres", "db", "database", "mongo", "redis"],
        "labels": [],
        "ports": [3306, 5432, 27017, 6379, 11211, 8086, 9000],
    },
    ContainerCategory.CACHE: {
        "images": ["redis", "memcached", "varnish", "squid"],
        "names": ["cache", "redis-cache", "varnish"],
        "labels": [],
        "ports": [6379, 11211],
    },
    ContainerCategory.MONITORING: {
        "images": [
            "prometheus", "grafana", "uptimekuma", "uptime-kuma", "netdata",
            "zabbix", "nagios", "datadog", "newrelic", "telegraf", "loki",
            "jaeger", "zipkin", "elasticsearch", "kibana", "graylog"
        ],
        "names": ["prometheus", "grafana", "uptime", "monitoring", "metrics", "loki"],
        "labels": [],
        "ports": [9090, 3000, 3001, 9100],
    },
    ContainerCategory.STORAGE: {
        "images": [
            "minio", "nextcloud", "seafile", "owncloud", "syncthing",
            "filebrowser", "photoprism", "immich"
        ],
        "names": ["minio", "nextcloud", "storage", "files", "photos"],
        "labels": [],
        "ports": [9000, 9001],
    },
    ContainerCategory.MESSAGING: {
        "images": [
            "rabbitmq", "kafka", "nats", "activemq", "mosquitto",
            "emqx", "pulsar"
        ],
        "names": ["rabbitmq", "kafka", "nats", "mqtt", "broker", "queue"],
        "labels": [],
        "ports": [5672, 9092, 4222, 1883],
    },
}

# Tier hiérarchique pour chaque catégorie (pour le positionnement vertical)
CATEGORY_TIERS = {
    ContainerCategory.REVERSE_PROXY: 0,  # Tout en haut - point d'entrée
    ContainerCategory.SECURITY: 1,       # Juste après le proxy
    ContainerCategory.FRONTEND: 2,       # Frontend apps
    ContainerCategory.BACKEND: 2,        # Backend apps (même niveau)
    ContainerCategory.APPLICATION: 2,    # Apps génériques
    ContainerCategory.CACHE: 3,          # Cache layer
    ContainerCategory.MESSAGING: 3,      # Message brokers
    ContainerCategory.DATABASE: 4,       # Databases en bas
    ContainerCategory.STORAGE: 4,        # Storage aussi en bas
    ContainerCategory.MONITORING: 5,     # Monitoring à part
    ContainerCategory.UNKNOWN: 2,        # Par défaut au milieu
}


def _format_volume_label(name: str) -> str:
    """Format volume name for display - truncate long hashes"""
    # If it looks like a hash (64 hex chars), truncate it
    if len(name) == 64 and all(c in '0123456789abcdef' for c in name.lower()):
        return f"{name[:8]}..."
    # Also handle shorter hashes or very long names
    if len(name) > 20:
        return f"{name[:16]}..."
    return name


class DockerClient:
    """Client for interacting with Docker socket"""

    def __init__(self, socket_path: str = "unix://var/run/docker.sock"):
        self.socket_path = socket_path
        self._client: Optional[docker.DockerClient] = None

    @property
    def client(self) -> docker.DockerClient:
        if self._client is None:
            try:
                self._client = docker.DockerClient(base_url=self.socket_path)
            except DockerException as e:
                raise ConnectionError(f"Cannot connect to Docker socket: {e}")
        return self._client

    def ping(self) -> bool:
        """Check if Docker daemon is accessible"""
        try:
            return self.client.ping()
        except Exception:
            return False

    def get_containers(self, all: bool = True) -> list[ContainerInfo]:
        """Get all containers with detailed information"""
        containers = []
        for container in self.client.containers.list(all=all):
            try:
                container.reload()  # Get fresh data
                info = self._parse_container(container)
                containers.append(info)
            except Exception as e:
                print(f"Error parsing container {container.id}: {e}")
        return containers

    def _parse_container(self, container) -> ContainerInfo:
        """Parse a Docker container into ContainerInfo model"""
        attrs = container.attrs

        # Parse ports
        ports = []
        port_bindings = attrs.get("HostConfig", {}).get("PortBindings") or {}
        for container_port, bindings in port_bindings.items():
            port_num, protocol = container_port.split("/")
            if bindings:
                for binding in bindings:
                    ports.append(
                        PortMapping(
                            container_port=int(port_num),
                            host_port=int(binding["HostPort"]) if binding["HostPort"] else None,
                            protocol=protocol,
                            host_ip=binding.get("HostIp", "0.0.0.0"),
                        )
                    )
            else:
                ports.append(
                    PortMapping(container_port=int(port_num), protocol=protocol)
                )

        # Parse volumes/mounts
        volumes = []
        mounts = attrs.get("Mounts") or []
        for mount in mounts:
            volumes.append(
                VolumeMount(
                    source=mount.get("Source", ""),
                    destination=mount.get("Destination", ""),
                    mode=mount.get("Mode", "rw"),
                    type=mount.get("Type", "bind"),
                )
            )

        # Parse networks
        networks = []
        network_settings = attrs.get("NetworkSettings", {}).get("Networks") or {}
        for net_name, net_config in network_settings.items():
            networks.append(
                NetworkInfo(
                    network_id=net_config.get("NetworkID", ""),
                    network_name=net_name,
                    ip_address=net_config.get("IPAddress"),
                    gateway=net_config.get("Gateway"),
                    mac_address=net_config.get("MacAddress"),
                )
            )

        # Parse status
        status_str = attrs.get("State", {}).get("Status", "unknown").lower()
        try:
            status = ContainerStatus(status_str)
        except ValueError:
            status = ContainerStatus.CREATED

        # Detect category
        image = attrs.get("Config", {}).get("Image", "unknown")
        labels = attrs.get("Config", {}).get("Labels") or {}
        category = self._detect_category(container.name, image, labels, ports)

        # Detect dependencies
        env_vars = attrs.get("Config", {}).get("Env") or []
        dependencies = self._detect_dependencies(container.name, labels, env_vars, networks)

        return ContainerInfo(
            id=container.id,
            short_id=container.short_id,
            name=container.name,
            image=image,
            status=status,
            category=category,
            created=attrs.get("Created", ""),
            ports=ports,
            volumes=volumes,
            networks=networks,
            labels=labels,
            env_vars=env_vars,
            dependencies=dependencies,
        )

    def _detect_category(
        self, name: str, image: str, labels: dict, ports: list[PortMapping]
    ) -> ContainerCategory:
        """Détecte la catégorie d'un container basé sur son image, nom et labels"""
        name_lower = name.lower()
        image_lower = image.lower()
        port_numbers = [p.container_port for p in ports]

        for category, patterns in CATEGORY_PATTERNS.items():
            # Check image patterns
            for img_pattern in patterns["images"]:
                if img_pattern in image_lower:
                    return category

            # Check name patterns
            for name_pattern in patterns["names"]:
                if name_pattern in name_lower:
                    return category

            # Check labels
            for label_pattern in patterns["labels"]:
                if label_pattern in labels:
                    return category

        # Fallback: try to guess from common patterns
        if any(p in image_lower for p in ["frontend", "react", "vue", "angular", "svelte"]):
            return ContainerCategory.FRONTEND
        if any(p in image_lower for p in ["api", "backend", "server", "service"]):
            return ContainerCategory.BACKEND

        return ContainerCategory.APPLICATION

    def _detect_dependencies(
        self,
        container_name: str,
        labels: dict,
        env_vars: list[str],
        networks: list[NetworkInfo],
    ) -> list[ContainerDependency]:
        """Détecte les dépendances d'un container"""
        dependencies = []
        seen = set()

        # 1. Docker Compose depends_on (from labels)
        depends_on = labels.get("com.docker.compose.depends_on", "")
        if depends_on:
            for dep in depends_on.split(","):
                dep_name = dep.strip().split(":")[0]  # Remove condition like :service_started
                if dep_name and dep_name not in seen:
                    dependencies.append(
                        ContainerDependency(target_name=dep_name, type="depends_on")
                    )
                    seen.add(dep_name)

        # 2. Traefik routing labels (container routes to another)
        for key, value in labels.items():
            # traefik.http.routers.*.rule
            if "traefik" in key.lower() and "rule" in key.lower():
                # Extract Host from rule like "Host(`app.example.com`)"
                pass  # Just mark as reverse proxy target
            # traefik.http.services.*.loadbalancer.server.port
            if "loadbalancer" in key.lower() and "server" in key.lower():
                pass

        # 3. Environment variables referencing other containers
        # Common patterns: DB_HOST=mysql, REDIS_HOST=redis, etc.
        host_patterns = [
            r"(\w+)_HOST=(\w+)",
            r"(\w+)_SERVER=(\w+)",
            r"(\w+)_URL=(?:https?://)?(\w+)(?::\d+)?",
            r"DATABASE_URL=(?:\w+://)?(?:\w+:\w+@)?(\w+)(?::\d+)?",
            r"REDIS_URL=(?:redis://)?(\w+)(?::\d+)?",
        ]

        for env in env_vars:
            for pattern in host_patterns:
                match = re.search(pattern, env, re.IGNORECASE)
                if match:
                    # Get the last group (the hostname)
                    potential_host = match.groups()[-1]
                    # Filter out common non-container values
                    if potential_host.lower() not in [
                        "localhost", "127.0.0.1", "0.0.0.0", "host", 
                        container_name.lower(), "true", "false"
                    ] and potential_host not in seen:
                        dependencies.append(
                            ContainerDependency(
                                target_name=potential_host, type="env_reference"
                            )
                        )
                        seen.add(potential_host)

        # 4. Links (legacy Docker links)
        # These show up in /etc/hosts inside container

        # 5. Network aliases - containers on same network can reference each other
        # We'll handle this in graph building

        return dependencies

    def get_networks(self) -> list[NetworkDetail]:
        """Get all Docker networks"""
        networks = []
        for network in self.client.networks.list():
            try:
                network.reload()
                attrs = network.attrs
                containers = list(attrs.get("Containers", {}).keys())
                networks.append(
                    NetworkDetail(
                        id=network.id,
                        short_id=network.short_id,
                        name=network.name,
                        driver=attrs.get("Driver", "unknown"),
                        scope=attrs.get("Scope", "local"),
                        internal=attrs.get("Internal", False),
                        containers=containers,
                    )
                )
            except Exception as e:
                print(f"Error parsing network {network.id}: {e}")
        return networks

    def get_volumes(self) -> list[VolumeDetail]:
        """Get all Docker volumes with container usage"""
        volumes = []
        containers = self.client.containers.list(all=True)

        # Build volume to container mapping
        volume_containers: dict[str, list[str]] = {}
        for container in containers:
            for mount in container.attrs.get("Mounts", []):
                if mount.get("Type") == "volume":
                    vol_name = mount.get("Name", "")
                    if vol_name not in volume_containers:
                        volume_containers[vol_name] = []
                    volume_containers[vol_name].append(container.name)

        for volume in self.client.volumes.list():
            try:
                attrs = volume.attrs
                volumes.append(
                    VolumeDetail(
                        name=volume.name,
                        driver=attrs.get("Driver", "local"),
                        mountpoint=attrs.get("Mountpoint", ""),
                        labels=attrs.get("Labels") or {},
                        containers=volume_containers.get(volume.name, []),
                    )
                )
            except Exception as e:
                print(f"Error parsing volume {volume.name}: {e}")
        return volumes

    def get_stack(self) -> DockerStack:
        """Get complete Docker stack information"""
        return DockerStack(
            containers=self.get_containers(),
            networks=self.get_networks(),
            volumes=self.get_volumes(),
        )

    def get_graph_data(self) -> GraphData:
        """Generate graph data from Docker stack with hierarchical positioning"""
        stack = self.get_stack()
        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []

        # Build name to container mapping for dependency resolution
        name_to_container: dict[str, ContainerInfo] = {}
        for container in stack.containers:
            name_to_container[container.name.lower()] = container
            # Also map by service name (without project prefix)
            # e.g., "myproject_redis_1" -> "redis"
            parts = container.name.split("_")
            if len(parts) >= 2:
                name_to_container[parts[-2].lower()] = container

        # Add container nodes with category and tier
        for container in stack.containers:
            tier = CATEGORY_TIERS.get(container.category, 2)
            nodes.append(
                GraphNode(
                    id=f"container_{container.short_id}",
                    label=container.name,
                    type="container",
                    category=container.category.value,
                    status=container.status.value,
                    tier=tier,
                    metadata={
                        "image": container.image,
                        "ports": [p.model_dump() for p in container.ports],
                        "ip_addresses": [n.ip_address for n in container.networks if n.ip_address],
                        "category": container.category.value,
                        "dependencies": [d.target_name for d in container.dependencies],
                    },
                )
            )

            # Add dependency edges
            for dep in container.dependencies:
                target_container = name_to_container.get(dep.target_name.lower())
                if target_container:
                    edges.append(
                        GraphEdge(
                            source=f"container_{container.short_id}",
                            target=f"container_{target_container.short_id}",
                            type="dependency",
                            label=dep.type,
                        )
                    )

        # Add network nodes and edges
        for network in stack.networks:
            if network.name not in ["bridge", "host", "none"]:  # Skip default networks
                nodes.append(
                    GraphNode(
                        id=f"network_{network.short_id}",
                        label=network.name,
                        type="network",
                        tier=6,  # Networks at the bottom
                        metadata={
                            "driver": network.driver,
                            "scope": network.scope,
                        },
                    )
                )

            # Connect containers to networks
            for container_id in network.containers:
                short_id = container_id[:12]
                edges.append(
                    GraphEdge(
                        source=f"container_{short_id}",
                        target=f"network_{network.short_id}",
                        type="network_connection",
                        label=network.name,
                    )
                )

        # Add volume nodes and edges
        for volume in stack.volumes:
            if volume.containers:  # Only show volumes that are in use
                nodes.append(
                    GraphNode(
                        id=f"volume_{volume.name}",
                        label=_format_volume_label(volume.name),
                        type="volume",
                        tier=7,  # Volumes at the very bottom
                        metadata={
                            "driver": volume.driver,
                            "mountpoint": volume.mountpoint,
                            "full_name": volume.name,  # Keep full name in metadata
                        },
                    )
                )

                # Connect containers to volumes
                for container_name in volume.containers:
                    # Find container by name
                    for container in stack.containers:
                        if container.name == container_name:
                            edges.append(
                                GraphEdge(
                                    source=f"container_{container.short_id}",
                                    target=f"volume_{volume.name}",
                                    type="volume_mount",
                                )
                            )
                            break

        return GraphData(nodes=nodes, edges=edges)


# Singleton instance
docker_client = DockerClient()
