# 🧦 SockMap

**Auto-wiki your Docker stack** - A visual documentation tool that reads your Docker socket and automatically generates interactive graphs showing containers, networks, volumes, and their relationships.

![SockMap](https://img.shields.io/badge/version-0.1.0-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## ✨ Features

- 🔍 **Auto-discovery**: Automatically reads Docker socket to discover your stack
- 🗺️ **Interactive Graph**: Visual representation of containers, networks, and volumes
- 📊 **Container Details**: Shows IP addresses, ports, environment variables
- 💾 **Volume Mapping**: Displays volume mounts and bindings
- 🔗 **Network Topology**: Visualizes network connections between containers
- 🔄 **Real-time Updates**: Live refresh of container states

## 🚀 Quick Start

### Using Docker Compose (Recommended)

```bash
docker compose up -d
```

Then open http://localhost:8080 in your browser.

### Development Setup

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Browser (Vue.js)                      │
│                   Interactive D3 Graph                   │
└─────────────────────┬───────────────────────────────────┘
                      │ HTTP/WebSocket
┌─────────────────────▼───────────────────────────────────┐
│                  FastAPI Backend                         │
│              Docker Socket Reader                        │
└─────────────────────┬───────────────────────────────────┘
                      │ /var/run/docker.sock
┌─────────────────────▼───────────────────────────────────┐
│                   Docker Daemon                          │
└─────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
SockMap/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI application
│   │   ├── docker_client.py # Docker socket interface
│   │   ├── models.py        # Pydantic models
│   │   └── routers/
│   │       └── docker.py    # Docker API routes
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # Vue components
│   │   ├── composables/     # Vue composables
│   │   └── App.vue
│   └── package.json
└── docker-compose.yml
```

## 🔒 Security Note

SockMap requires access to the Docker socket (`/var/run/docker.sock`). This is read-only access but still grants visibility into your Docker environment. Use with caution in production environments.

## 📝 License

MIT License - See [LICENSE](LICENSE) for details.
