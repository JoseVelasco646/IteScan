# IteScan 🛡️

**Enterprise Network Scanner & Monitoring Platform**

A full-stack web application for network scanning, device monitoring, vulnerability detection, and remote SSH access. Built with modern technologies and enterprise-grade security features.

[![Python](https://img.shields.io/badge/Python-3.8+-3776ab?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.5+-4FC08D?logo=vue.js&logoColor=white)](https://vuejs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)

---

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Architecture](#-architecture)
- [Security Features](#-security-features)
- [Key Achievements](#-key-achievements)

---

## ✨ Features

### Network Scanning & Discovery
- 🔍 **Comprehensive Network Scanning** - Discover all hosts on your network with OS detection
- 📡 **Port & Service Detection** - Identify open ports, running services, and versions
- 🎯 **Vulnerability Scanning** - Integrated NSE scripts for security assessment
- 📊 **Real-time Monitoring** - Track device status and latency continuously

### Device Management
- 🏢 **Subnet Management** - Organize and monitor multiple network segments
- 🖥️ **Device Profiles** - Store and manage device information with custom labels
- 📍 **Connection History** - Track device status changes over time
- 🔄 **Scheduled Scans** - Automate network scans at custom intervals

### Remote Access & Control
- 🔐 **SSH Terminal** - Built-in terminal for remote device access
- 🗝️ **Credential Management** - Securely store and manage SSH credentials
- 💻 **Interactive Shell** - Real-time command execution with full terminal emulation
- 📝 **SSH History** - Track all remote access activities

### Reporting & Export
- 📄 **PDF Reports** - Generate detailed scan reports in PDF format
- 📊 **Excel Export** - Export scan data and history to Excel
- 📈 **Scan History** - Complete audit trail of all scan operations
- 📋 **Custom Reports** - Create customized reports with relevant data

### Administration & Security
- 👥 **Role-Based Access Control** - Admin, Moderator, Operator, Viewer roles
- 🔐 **JWT Authentication** - Secure token-based authentication
- 📋 **Audit Logging** - Complete audit trail of all user actions
- 🛡️ **Rate Limiting** - Protection against brute force attacks
- 🔑 **Password Security** - Bcrypt hashing with JWT token versioning

---

## 🛠️ Tech Stack

### Backend
| Technology | Purpose |
|------------|---------|
| **FastAPI** | High-performance async web framework |
| **Python 3.8+** | Core language |
| **PostgreSQL 15** | Relational database |
| **SQLAlchemy** | ORM for database operations |
| **Pydantic** | Data validation and serialization |
| **PyJWT** | JWT token generation and validation |
| **APScheduler** | Scheduled task execution |
| **asyncssh** | SSH client and server operations |
| **python-nmap** | Network scanning integration |
| **Uvicorn** | ASGI server |

### Frontend
| Technology | Purpose |
|------------|---------|
| **Vue 3** | Progressive JavaScript framework |
| **Vite** | Next-generation frontend build tool |
| **Tailwind CSS** | Utility-first CSS framework |
| **Axios** | HTTP client |
| **xterm.js** | Terminal emulator component |
| **jsPDF & ExcelJS** | Report generation |
| **Lucide Vue** | Icon library |

### Infrastructure
| Technology | Purpose |
|------------|---------|
| **Docker** | Containerization |
| **Docker Compose** | Multi-container orchestration |
| **Nginx** | Reverse proxy and web server |
| **Linux** | Host operating system |

---

## 📁 Project Structure

```
IteScan/
├── front/                          # Vue 3 Frontend
│   ├── src/
│   │   ├── components/            # Reusable Vue components
│   │   ├── views/                 # Page components
│   │   ├── services/              # API integration
│   │   ├── router/                # Vue Router configuration
│   │   └── App.vue                # Root component
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
│
├── back/                           # FastAPI Backend
│   ├── app/
│   │   ├── main.py               # FastAPI application entry point
│   │   ├── models.py             # SQLAlchemy ORM models
│   │   ├── schemas.py            # Pydantic request/response schemas
│   │   ├── database.py           # Database configuration
│   │   ├── auth.py               # JWT authentication logic
│   │   ├── crud.py               # Create, Read, Update, Delete operations
│   │   ├── routers/              # API endpoint groups
│   │   ├── scanners/             # Network scanning modules
│   │   ├── ssh_operations.py     # SSH client operations
│   │   ├── scheduler_service.py  # Task scheduling logic
│   │   ├── websocket_manager.py  # Real-time WebSocket connections
│   │   └── utils.py              # Utility functions
│   ├── init.sql                  # Database schema initialization
│   ├── requirements.txt          # Python dependencies
│   ├── Dockerfile
│   └── nginx.conf               # Nginx configuration
│
├── docker-compose.yml           # Docker Compose orchestration
├── .env                         # Environment variables
└── assets/                      # Project assets and documentation
```

---

## 📦 Prerequisites

- **Docker** & **Docker Compose** (recommended for easy setup)
- **Python 3.8+** (if running without Docker)
- **Node.js 20+** (if running frontend without Docker)
- **PostgreSQL 15+** (if running without Docker)
- **Linux/Unix** environment (macOS or Linux recommended for Nmap)

---

## 🚀 Installation

### Option 1: Docker Compose (Recommended)

The easiest way to get started is using Docker Compose, which sets up the entire stack automatically.

```bash
# Clone the repository
git clone https://github.com/JoseVelasco646/IteScan.git
cd IteScan

# Create environment file
cp .env.example .env

# Start all services
docker-compose up -d

# Wait for services to be healthy (check logs)
docker-compose logs -f
```

**Services will be available at:**
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

### Option 2: Manual Installation

#### Backend Setup

```bash
cd back

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure database
# Update DATABASE_URL in .env file

# Run database migrations
python -m alembic upgrade head

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```bash
cd front

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

---

## 📖 Usage

### Web Interface

1. **Access the Application**
   - Open `http://localhost:3000` in your browser
   - Default credentials: `admin` / (check docker logs for initial password)

2. **Scan Networks**
   - Navigate to "Network Scanner"
   - Enter subnet range (e.g., 192.168.1.0/24)
   - Start scan and monitor progress in real-time

3. **View Results**
   - Browse discovered hosts and their details
   - Click on a host to see open ports and services
   - View vulnerability assessments

4. **Remote Access**
   - Select a host and click "SSH Terminal"
   - Choose or create SSH credentials
   - Execute commands remotely in the integrated terminal

5. **Generate Reports**
   - Use the Reports section to export scan data
   - Generate PDF or Excel reports with custom filters
   - Download and share results

### API Examples

#### Authentication
```bash
# Login
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'

# Response includes JWT token
```

#### Scan Networks
```bash
# Start a network scan
curl -X POST "http://localhost:8000/api/scans/start" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"target":"192.168.1.0/24","scan_type":"full"}'
```

---

## 📚 API Documentation

Complete interactive API documentation is available at:

```
http://localhost:8000/docs              # Swagger UI
http://localhost:8000/redoc             # ReDoc
```

### Main API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | User authentication |
| POST | `/api/auth/logout` | User logout |
| GET | `/api/hosts` | List all discovered hosts |
| POST | `/api/scans/start` | Start a new network scan |
| GET | `/api/scans/history` | Get scan history |
| POST | `/api/ssh/connect` | Establish SSH connection |
| WS | `/api/ws/scan` | WebSocket for real-time scan updates |

---

## 🏗️ Architecture

### Application Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Vue 3)                        │
│  ├─ Dashboard          ├─ Network Scanner   ├─ Reports      │
│  └─ SSH Terminal       └─ Device Management                 │
└─────────────────────────────────────────────────────────────┘
                            ↓ HTTP/WebSocket
┌─────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                       │
│  ├─ Auth Service       ├─ Scan Service     ├─ SSH Manager   │
│  ├─ Schedule Service   └─ Report Generator                  │
└─────────────────────────────────────────────────────────────┘
                            ↓ SQL
┌─────────────────────────────────────────────────────────────┐
│               Database (PostgreSQL)                          │
│  ├─ Hosts              ├─ Ports            ├─ Audit Log    │
│  ├─ Services           ├─ Vulnerabilities  └─ SSH Creds    │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Scan Initiation**: User starts scan via UI → Backend receives request
2. **Network Scanning**: Backend runs Nmap → Collects host and service data
3. **Data Processing**: Results parsed and stored in PostgreSQL
4. **Real-time Updates**: WebSocket streams progress to frontend
5. **Persistence**: All data saved with audit logging
6. **Report Generation**: Data formatted and exported as needed

---

## 🔒 Security Features

### Authentication & Authorization
- ✅ JWT-based stateless authentication
- ✅ Role-Based Access Control (RBAC) with 4 user roles
- ✅ Bcrypt password hashing
- ✅ Token versioning for instant logout capability
- ✅ CORS protection

### Data Protection
- ✅ Encrypted SSH credential storage
- ✅ HTTPS support (via Nginx reverse proxy)
- ✅ SQL injection prevention (ORM + Pydantic validation)
- ✅ Rate limiting on login attempts

### Audit & Compliance
- ✅ Complete audit logging of all user actions
- ✅ Detailed scan history with execution metadata
- ✅ IP tracking for security events
- ✅ Timestamp tracking for all database operations

### Infrastructure Security
- ✅ Network isolation via Docker networks
- ✅ Principle of least privilege for containers
- ✅ Health checks for all services
- ✅ Volume isolation for sensitive data

---

## 🎯 Key Achievements

### Technical Highlights
- 🚀 **Async-First Architecture** - Built with async/await for high performance
- 🔄 **Real-time Updates** - WebSocket integration for live scan progress
- 📊 **Complex Database Schema** - 12+ tables with relationships and triggers
- 🔐 **Enterprise Security** - Multi-layer authentication and audit logging
- 🐳 **Docker Optimization** - Production-ready containerization
- 📱 **Responsive UI** - Works seamlessly on desktop and tablet

### Code Quality
- Clean architecture with separation of concerns
- Comprehensive error handling and validation
- Type hints throughout the codebase
- RESTful API design principles
- Modular and maintainable code structure

### Performance Considerations
- Optimized database queries with proper indexing
- Async operations for I/O-bound tasks
- Efficient frontend bundling with Vite
- Connection pooling for database
- Request caching strategies

---

## 🔄 Development Workflow

### Running Tests
```bash
# Backend tests
cd back
pytest

# Frontend tests
cd front
npm run test
```

### Code Formatting
```bash
# Backend
cd back
black app/
flake8 app/

# Frontend
cd front
npm run lint
npm run format
```

### Building for Production
```bash
# With Docker
docker-compose -f docker-compose.prod.yml up -d

# Manual build
cd front && npm run build
cd back && pip install -r requirements.txt
```

---

## 📞 Support & Documentation

- **API Documentation**: `http://localhost:8000/docs`
- **Issues**: Report issues on GitHub
- **Contributing**: Pull requests welcome

---

## 📄 License

This project is open source and available under the MIT License.

---

## 👨‍💻 Author

**Jose Velasco** - Full Stack Developer

- GitHub: [@JoseVelasco646](https://github.com/JoseVelasco646)
- LinkedIn: [Profile](https://linkedin.com)

---

## 🙏 Acknowledgments

- FastAPI community for excellent documentation
- Vue.js team for a amazing framework
- Nmap project for network scanning capabilities
- PostgreSQL for reliable database engine

---

**Made with ❤️ for network security and monitoring**
