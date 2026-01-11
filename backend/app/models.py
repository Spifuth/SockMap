from pydantic import BaseModel
from typing import Optional
from enum import Enum


class ContainerStatus(str, Enum):
    RUNNING = "running"
    PAUSED = "paused"
    EXITED = "exited"
    RESTARTING = "restarting"
    DEAD = "dead"
    CREATED = "created"


class ContainerCategory(str, Enum):
    """Catégories de containers pour le positionnement dans le graphe"""
    REVERSE_PROXY = "reverse_proxy"      # Traefik, Nginx Proxy Manager, Caddy, HAProxy
    SECURITY = "security"                 # Authelia, TinyAuth, Keycloak, Authentik
    DATABASE = "database"                 # MySQL, PostgreSQL, MongoDB, Redis, MariaDB
    CACHE = "cache"                       # Redis, Memcached, Varnish
    MONITORING = "monitoring"             # Prometheus, Grafana, Uptime Kuma
    STORAGE = "storage"                   # MinIO, NextCloud, Seafile
    MESSAGING = "messaging"               # RabbitMQ, Kafka, NATS
    APPLICATION = "application"           # Apps génériques
    FRONTEND = "frontend"                 # Apps frontend (React, Vue, etc.)
    BACKEND = "backend"                   # APIs, services backend
    UNKNOWN = "unknown"


class PortMapping(BaseModel):
    container_port: int
    host_port: Optional[int] = None
    protocol: str = "tcp"
    host_ip: str = "0.0.0.0"


class VolumeMount(BaseModel):
    source: str
    destination: str
    mode: str = "rw"
    type: str  # bind, volume, tmpfs


class NetworkInfo(BaseModel):
    network_id: str
    network_name: str
    ip_address: Optional[str] = None
    gateway: Optional[str] = None
    mac_address: Optional[str] = None


class ContainerDependency(BaseModel):
    """Dépendance entre containers"""
    target_name: str              # Nom du container cible
    target_id: Optional[str] = None
    type: str                     # depends_on, links, network_alias, env_reference


class ContainerInfo(BaseModel):
    id: str
    short_id: str
    name: str
    image: str
    status: ContainerStatus
    category: ContainerCategory = ContainerCategory.UNKNOWN
    created: str
    ports: list[PortMapping] = []
    volumes: list[VolumeMount] = []
    networks: list[NetworkInfo] = []
    labels: dict[str, str] = {}
    env_vars: list[str] = []
    dependencies: list[ContainerDependency] = []
    dependents: list[str] = []  # Containers qui dépendent de celui-ci


class NetworkDetail(BaseModel):
    id: str
    short_id: str
    name: str
    driver: str
    scope: str
    internal: bool
    containers: list[str] = []  # Container IDs


class VolumeDetail(BaseModel):
    name: str
    driver: str
    mountpoint: str
    labels: dict[str, str] = {}
    containers: list[str] = []  # Container names using this volume


class DockerStack(BaseModel):
    """Complete Docker stack information for graph generation"""
    containers: list[ContainerInfo]
    networks: list[NetworkDetail]
    volumes: list[VolumeDetail]


class GraphNode(BaseModel):
    id: str
    label: str
    type: str  # container, network, volume
    category: Optional[str] = None  # Pour les containers: reverse_proxy, security, etc.
    status: Optional[str] = None
    tier: int = 0  # Niveau hiérarchique (0=proxy, 1=security, 2=app, 3=db, etc.)
    metadata: dict = {}


class GraphEdge(BaseModel):
    source: str
    target: str
    type: str  # network_connection, volume_mount, dependency
    label: Optional[str] = None


class GraphData(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
