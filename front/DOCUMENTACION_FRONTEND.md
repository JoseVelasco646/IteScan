# Documentación Técnica del Frontend
## Network Scanner - Sistema de Escaneo y Monitoreo de Red

**Residencia Profesional**  
**Tecnología:** Vue.js 3 (Composition API)  
**Autor:** Manuel  
**Fecha:** Diciembre 2025

---

## 📋 Índice

1. [Descripción General](#descripción-general)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Tecnologías Utilizadas](#tecnologías-utilizadas)
4. [Estructura del Proyecto](#estructura-del-proyecto)
5. [Componentes Principales](#componentes-principales)
6. [Composables (Lógica Reutilizable)](#composables-lógica-reutilizable)
7. [Servicios y API](#servicios-y-api)
8. [Flujos de Trabajo](#flujos-de-trabajo)
9. [Comunicación en Tiempo Real](#comunicación-en-tiempo-real)
10. [Guía de Desarrollo](#guía-de-desarrollo)
11. [Despliegue](#despliegue)

---

## 1. Descripción General

Network Scanner es una aplicación web moderna desarrollada con Vue.js 3 que permite escanear, monitorear y administrar redes de computadoras. La aplicación proporciona funcionalidades avanzadas de escaneo de red incluyendo:

- **Escaneo ICMP/TCP Ping**: Detección de hosts activos en la red
- **Escaneo de Puertos**: Identificación de puertos abiertos (TCP/UDP)
- **Detección de Servicios**: Identificación de servicios y versiones
- **Detección de Sistema Operativo**: Fingerprinting de OS mediante nmap
- **Escaneo de MAC/Vendor**: Identificación de direcciones MAC y fabricantes
- **Escaneos Programados**: Automatización de tareas de escaneo
- **Administración SSH**: Apagado y reinicio remoto de equipos
- **Visualización de Datos**: Tablas interactivas, exportación a Excel/PDF/PNG

### Características Principales

✅ **Interfaz Reactiva**: Actualización en tiempo real mediante WebSockets  
✅ **Multi-Host Support**: Escaneo simultáneo de múltiples hosts  
✅ **CIDR Expansion**: Soporte para notación CIDR (192.168.0.0/24)  
✅ **Progress Tracking**: Barras de progreso en tiempo real  
✅ **Scan Cancellation**: Cancelación de escaneos en ejecución  
✅ **Responsive Design**: Interfaz adaptable a diferentes dispositivos  
✅ **Exportación de Datos**: Excel, PDF, PNG  
✅ **Compatibilidad Multi-Plataforma**: Windows y Linux  

---

## 2. Arquitectura del Sistema

### Patrón de Arquitectura

La aplicación sigue el patrón **MVVM (Model-View-ViewModel)** implementado a través de:

- **Models**: Representados por los datos de la API (responses)
- **Views**: Componentes Vue (.vue files)
- **ViewModels**: Composables que manejan la lógica de negocio

### Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│                    User Interface                       │
│  (Components: FullScan, PingScanner, HostsTable, etc.)  │
└─────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────┐
│                   Composables Layer                      │
│  useScanState | useScanProgress | useWebSocket | useToast│
└─────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────┐
│                     API Service                          │
│              (scanner.js - Axios HTTP Client)            │
└─────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────┐
│                  Backend FastAPI                         │
│         REST API + WebSocket (Real-time updates)         │
└─────────────────────────────────────────────────────────┘
```

### Comunicación de Datos

1. **HTTP REST**: Peticiones/respuestas síncronas (Axios)
2. **WebSocket**: Actualizaciones en tiempo real (progreso de escaneos)
3. **Event Bus**: Comunicación entre componentes (via composables)

---

## 3. Tecnologías Utilizadas

### Core Framework
- **Vue.js 3.5.25**: Framework JavaScript progresivo
- **Composition API**: Sistema de composición reactiva
- **Vue Router 4.6.3**: Enrutamiento SPA

### Librerías UI/UX
- **Tailwind CSS 3.4.19**: Framework de utilidades CSS
- **Lucide Vue Next 0.562.0**: Iconos SVG modernos
- **Vue Toastification 2.0.0**: Notificaciones toast

### Comunicación y Datos
- **Axios 1.13.2**: Cliente HTTP para API REST
- **WebSocket API Nativa**: Comunicación bidireccional en tiempo real

### Exportación de Datos
- **ExcelJS 4.4.0**: Generación de archivos Excel (.xlsx)
- **jsPDF 3.0.4**: Generación de archivos PDF
- **jsPDF-AutoTable 5.0.2**: Tablas para PDF
- **html2canvas 1.4.1**: Captura de HTML a imagen PNG

### Herramientas de Desarrollo
- **Vite 7.2.4**: Build tool y dev server
- **ESLint 9.39.1**: Linter JavaScript
- **Prettier 3.6.2**: Formateador de código
- **PostCSS 8.5.6**: Procesador CSS

---

## 4. Estructura del Proyecto

```
network-scanner-frontend/
├── public/                      # Archivos estáticos
├── src/
│   ├── api/
│   │   └── scanner.js          # Cliente API (Axios)
│   │
│   ├── assets/
│   │   └── main.css            # Estilos globales
│   │
│   ├── components/             # Componentes Vue
│   │   ├── FullScan.vue        # Escaneo completo de host
│   │   ├── HostsTable.vue      # Tabla de hosts escaneados
│   │   ├── MacScanner.vue      # Escaneo de direcciones MAC
│   │   ├── OSDetection.vue     # Detección de sistema operativo
│   │   ├── PingScanner.vue     # Escaneo ICMP/TCP ping
│   │   ├── PortScanner.vue     # Escaneo de puertos
│   │   ├── ScanProgress.vue    # Barra de progreso
│   │   ├── ScanScheduler.vue   # Programación de escaneos
│   │   ├── ServiceScanner.vue  # Detección de servicios
│   │   ├── SkeletonLoader.vue  # Componente de carga
│   │   └── VulnerabilityScanner.vue  # Escaneo de vulnerabilidades
│   │
│   ├── composables/            # Lógica reutilizable
│   │   ├── useScanProgress.js  # Gestión de progreso de escaneos
│   │   ├── useScanState.js     # Estado global de escaneos
│   │   ├── useToast.js         # Sistema de notificaciones
│   │   └── useWebSocket.js     # Cliente WebSocket
│   │
│   ├── router/
│   │   └── index.js            # Configuración de rutas
│   │
│   ├── views/
│   │   └── Dashboard.vue       # Vista principal
│   │
│   ├── App.vue                 # Componente raíz
│   ├── main.js                 # Punto de entrada
│   └── index.css               # Estilos Tailwind
│
├── eslint.config.js            # Configuración ESLint
├── jsconfig.json               # Configuración JavaScript
├── package.json                # Dependencias NPM
├── postcss.config.js           # Configuración PostCSS
├── tailwind.config.js          # Configuración Tailwind
├── vite.config.js              # Configuración Vite
└── index.html                  # HTML principal
```

---

## 5. Componentes Principales

### 5.1 FullScan.vue

**Propósito**: Realiza escaneo completo de un host (ping, puertos, servicios, OS, MAC).

**Características**:
- Escaneo individual o por rango de IPs
- Persistencia en base de datos
- Barra de progreso por etapas (ping, MAC, puertos, servicios, OS)
- Cancelación de escaneos en progreso

**Props**: Ninguna

**Emisiones**:
- Ninguna (actualización vía WebSocket)

**Datos Reactivos**:
```javascript
{
  host: '',              // IP individual
  startIP: '',           // IP inicio (rango)
  endIP: '',             // IP fin (rango)
  scanType: 'single',    // 'single' | 'range'
  results: [],           // Resultados de escaneos
  scanCompleted: false,  // Estado de completado
  currentScanId: null    // ID del escaneo activo
}
```

**Métodos Principales**:
- `scanSingle()`: Escanea un host individual
- `scanRange()`: Escanea un rango de IPs
- `handleScan()`: Orquesta el tipo de escaneo
- `cancelScan()`: Cancela el escaneo activo

---

### 5.2 PingScanner.vue

**Propósito**: Escaneo ICMP/TCP ping para detección rápida de hosts.

**Características**:
- Soporte para múltiples hosts (separados por comas)
- Expansión automática de CIDR (192.168.0.0/24)
- Detección automática de método (ICMP o TCP)
- Resolución de hostname
- Cancelación de escaneos

**Datos Reactivos**:
```javascript
{
  hosts: '',             // Lista de hosts (ej: "192.168.0.1, 192.168.0.2")
  results: [],           // Array de resultados
  activeHosts: 0,        // Contador de hosts activos
  inactiveHosts: 0       // Contador de hosts inactivos
}
```

**Estructura de Resultado**:
```javascript
{
  host: "192.168.0.10",
  hostname: "PC-ADMIN",
  status: "up",          // "up" | "down"
  latency_ms: 2.45,
  method: "icmp"         // "icmp" | "tcp"
}
```

---

### 5.3 PortScanner.vue

**Propósito**: Escaneo de puertos TCP/UDP en hosts.

**Características**:
- Escaneo de puertos personalizados (ej: "80,443,3306")
- Rangos de puertos (ej: "1-1024")
- Multi-host support
- Detección de servicios en puertos abiertos

**Datos Reactivos**:
```javascript
{
  hosts: '',             // Lista de hosts
  ports: '1-1024',       // Puertos a escanear
  results: []            // Resultados por host
}
```

**Estructura de Resultado**:
```javascript
{
  host: "192.168.0.10",
  ports: [
    {
      port: 80,
      protocol: "tcp",
      state: "open",
      service: "http"
    }
  ]
}
```

---

### 5.4 OSDetection.vue

**Propósito**: Detección de sistema operativo mediante fingerprinting.

**Características**:
- Detección basada en nmap -O
- Precisión porcentual
- Información de CPE (Common Platform Enumeration)
- Multi-host support con progreso individual

**Datos Reactivos**:
```javascript
{
  hosts: '',             // Lista de hosts
  results: []            // Resultados de detección
}
```

**Estructura de Resultado**:
```javascript
{
  host: "192.168.0.10",
  os: {
    name: "Microsoft Windows 10",
    accuracy: 95,
    cpe: "cpe:/o:microsoft:windows_10"
  }
}
```

---

### 5.5 MacScanner.vue

**Propósito**: Escaneo de direcciones MAC y fabricantes (solo LAN).

**Características**:
- Escaneo de red completa (CIDR)
- Identificación de fabricante (vendor)
- Resolución de hostname
- Ejecución paralela con semáforos

**Datos Reactivos**:
```javascript
{
  network: '192.168.0.0/24',  // CIDR notation
  devices: []                  // Dispositivos encontrados
}
```

**Estructura de Resultado**:
```javascript
{
  ip: "192.168.0.50",
  hostname: "Laptop-Maria",
  mac: "AA:BB:CC:DD:EE:FF",
  vendor: "Intel Corporate"
}
```

---

### 5.6 ServiceScanner.vue

**Propósito**: Detección de servicios y versiones en puertos abiertos.

**Características**:
- Escaneo con nmap -sV
- Información de producto y versión
- Datos adicionales (extrainfo)

**Estructura de Resultado**:
```javascript
{
  host: "192.168.0.10",
  services: [
    {
      port: 80,
      protocol: "tcp",
      service: "http",
      product: "Apache httpd",
      version: "2.4.54",
      extra: "(Ubuntu)"
    }
  ]
}
```

---

### 5.7 HostsTable.vue

**Propósito**: Visualización y gestión de hosts escaneados en la base de datos.

**Características Principales**:

**Visualización**:
- Tabla interactiva con paginación
- Búsqueda y filtrado en tiempo real
- Ordenamiento por columnas
- Estadísticas (total hosts, activos, inactivos)
- Skeleton loader durante carga

**Gestión de Hosts**:
- Eliminación individual y masiva
- Actualización de estado (activo/inactivo)
- Visualización de detalles (modal)
- Selección múltiple (checkboxes)

**Exportación**:
- Excel (.xlsx) con formato profesional
- PDF con tabla automática
- PNG (captura de pantalla)

**Administración SSH**:
- Apagado remoto de equipos seleccionados
- Reinicio remoto
- Ejecución de comandos personalizados

**Datos Reactivos**:
```javascript
{
  hosts: [],              // Lista de hosts de la DB
  selectedHosts: [],      // Hosts seleccionados
  searchQuery: '',        // Término de búsqueda
  currentPage: 1,         // Página actual
  itemsPerPage: 10,       // Items por página
  statistics: {           // Estadísticas
    total: 0,
    active: 0,
    inactive: 0
  }
}
```

**Métodos de Exportación**:
- `exportarExcel()`: Genera archivo .xlsx con ExcelJS
- `exportarPDF()`: Genera PDF con jsPDF-AutoTable
- `exportarPNG()`: Captura HTML con html2canvas

---

### 5.8 ScanScheduler.vue

**Propósito**: Programación y gestión de escaneos automáticos.

**Características**:

**Programación**:
- Frecuencias: Horaria, Diaria, Semanal, Mensual
- Tipos de escaneo: Ping, Puertos, Servicios, OS, MAC, Full
- Tipos de acción: Escaneo, Apagado, Ambos
- Targets: IP individual, rango, subnet (CIDR), lista de hosts

**Gestión**:
- Activar/Desactivar schedules
- Editar configuración
- Eliminar schedules
- Ejecutar manualmente
- Ver resultados de ejecuciones previas

**Administración SSH**:
- Apagado programado después de escaneo
- Credenciales SSH guardadas (username/password)
- Targets de apagado personalizados

**Datos Reactivos**:
```javascript
{
  schedules: [],          // Lista de schedules
  showScheduleModal: false,
  editingSchedule: null,
  formData: {
    name: '',
    scan_type: 'ping',
    action_type: 'scan',
    frequency: 'daily',
    time: '00:00',
    day_of_week: null,
    day_of_month: null,
    target_subnet: '',
    target_range: '',
    target_hosts: '',
    shutdown_after_scan: false,
    shutdown_targets: '',
    ssh_username: '',
    ssh_password: ''
  }
}
```

**Estructura de Schedule**:
```javascript
{
  id: 1,
  name: "Escaneo Diario Red Principal",
  scan_type: "full",
  action_type: "both",
  frequency: "daily",
  time: "02:00",
  enabled: true,
  target_subnet: "192.168.0.0/24",
  shutdown_after_scan: true,
  last_run: "2025-12-24T02:00:00",
  next_run: "2025-12-25T02:00:00"
}
```

---

### 5.9 ScanProgress.vue

**Propósito**: Componente reutilizable de barra de progreso.

**Props**:
```javascript
{
  scanId: String,           // ID único del escaneo
  scanType: String,         // Tipo de escaneo
  showProgress: Boolean,    // Mostrar/ocultar barra
  title: String            // Título personalizado
}
```

**Características**:
- Actualización en tiempo real vía WebSocket
- Información de progreso: X/Y hosts (Z%)
- Host actual siendo escaneado
- Animación suave de progreso

---

### 5.10 SkeletonLoader.vue

**Propósito**: Componente de carga tipo skeleton screen.

**Props**:
```javascript
{
  rows: Number,            // Número de filas skeleton
  columns: Number          // Número de columnas
}
```

**Uso**: Mejora UX durante carga de datos (ej: tabla de hosts).

---

## 6. Composables (Lógica Reutilizable)

### 6.1 useScanState.js

**Propósito**: Gestión global del estado de escaneos activos.

**Estado Compartido**:
```javascript
{
  activeScans: Set,        // Set de IDs de escaneos activos
  scanningState: Boolean   // true si hay algún escaneo activo
}
```

**Métodos Exportados**:

```javascript
// Iniciar un escaneo
startScan(scanId: string) => void

// Finalizar un escaneo
endScan(scanId: string) => void

// Verificar si un scan está activo
isScanActive(scanId: string) => boolean

// Verificar si hay algún scan activo
isAnyScanning() => boolean
```

**Caso de Uso**:
```javascript
import { useScanState } from '@/composables/useScanState'

const { startScan, endScan, isAnyScanning } = useScanState()

const handleScan = async () => {
  const scanId = `ping-${Date.now()}`
  startScan(scanId)
  
  try {
    await scannerAPI.pingHosts(hosts)
  } finally {
    endScan(scanId)
  }
}
```

---

### 6.2 useScanProgress.js

**Propósito**: Gestión de barras de progreso en tiempo real vía WebSocket.

**Estado Reactivo**:
```javascript
{
  progressData: ref({}),        // Datos de progreso por scanId
  cancelledScanIds: Set         // IDs de scans cancelados
}
```

**Estructura de progressData**:
```javascript
{
  [scanId]: {
    active: true,
    progress: 45.5,
    total: 100,
    completed: 45,
    status: 'scanning',
    current_host: '192.168.0.45',
    scan_type: 'ping'
  }
}
```

**Métodos Exportados**:

```javascript
// Obtener datos de progreso de un scan
getProgressData(scanId: string) => Object | null

// Verificar si un scan está activo
isScanActive(scanId: string) => boolean

// Cancelar el scan actual
cancelCurrentScan() => void

// Limpiar datos de progreso
clearProgress(scanId: string) => void
```

**Integración con WebSocket**:
```javascript
// Escucha eventos 'scan_progress' del WebSocket
ws.on('scan_progress', (data) => {
  const { scan_id, progress, status, completed, total } = data
  
  if (cancelledScanIds.has(scan_id)) {
    return // Ignorar mensajes de scans cancelados
  }
  
  progressData.value[scan_id] = {
    active: status !== 'completed' && status !== 'cancelled',
    progress: progress || 0,
    total: total || 0,
    completed: completed || 0,
    status,
    current_host: data.current_host,
    scan_type: data.scan_type
  }
})
```

**Cancelación de Scans**:
```javascript
// Envía mensaje de cancelación vía WebSocket
cancelCurrentScan() {
  if (currentScanId.value) {
    ws.send({
      type: 'cancel_scan',
      scan_id: currentScanId.value
    })
    
    cancelledScanIds.add(currentScanId.value)
    progressData.value[currentScanId.value].active = false
  }
}
```

---

### 6.3 useWebSocket.js

**Propósito**: Cliente WebSocket reutilizable con reconexión automática.

**Configuración**:
```javascript
const WS_URL = 'ws://localhost:8000/ws'
const MAX_RECONNECT_ATTEMPTS = 5
const RECONNECT_INTERVAL = 3000  // 3 segundos
const PING_INTERVAL = 30000      // 30 segundos
```

**Estado Reactivo**:
```javascript
{
  ws: ref(null),                 // Instancia WebSocket
  connected: ref(false),         // Estado de conexión
  reconnectAttempts: ref(0),     // Intentos de reconexión
  listeners: Map                 // Mapa de event listeners
}
```

**Métodos Exportados**:

```javascript
// Conectar al WebSocket
connect() => void

// Desconectar
disconnect() => void

// Registrar listener para un tipo de evento
on(eventType: string, callback: Function) => void

// Remover listener
off(eventType: string, callback: Function) => void

// Enviar mensaje al servidor
send(message: string | Object) => void
```

**Sistema de Eventos**:
```javascript
// Escuchar eventos específicos
ws.on('scan_progress', (data) => {
  console.log('Progreso:', data.progress)
})

// Escuchar todos los eventos
ws.on('*', ({ type, data }) => {
  console.log(`Evento ${type}:`, data)
})
```

**Reconexión Automática**:
```javascript
ws.onclose = (event) => {
  connected.value = false
  
  // Intentar reconectar si no se alcanzó el máximo
  if (reconnectAttempts.value < MAX_RECONNECT_ATTEMPTS) {
    reconnectTimeout.value = setTimeout(() => {
      reconnectAttempts.value++
      connect()
    }, RECONNECT_INTERVAL)
  }
}
```

**Keep-Alive (Ping/Pong)**:
```javascript
// Enviar ping cada 30 segundos para mantener viva la conexión
pingInterval.value = setInterval(() => {
  if (ws.value?.readyState === WebSocket.OPEN) {
    ws.value.send('ping')
  }
}, 30000)

// El servidor responde con 'pong' (ignorado automáticamente)
```

---

### 6.4 useToast.js

**Propósito**: Sistema de notificaciones toast centralizado.

**Configuración**:
```javascript
{
  position: 'top-right',
  timeout: 3000,
  closeOnClick: true,
  pauseOnFocusLoss: true,
  pauseOnHover: true,
  draggable: true,
  draggablePercent: 0.6,
  showCloseButtonOnHover: false,
  hideProgressBar: false,
  closeButton: 'button',
  icon: true,
  rtl: false
}
```

**Métodos Exportados**:

```javascript
// Notificación de éxito
toast.success(message: string, options?: Object) => void

// Notificación de error
toast.error(message: string, options?: Object) => void

// Notificación de advertencia
toast.warning(message: string, options?: Object) => void

// Notificación informativa
toast.info(message: string, options?: Object) => void
```

**Casos de Uso**:
```javascript
import { useToast } from '@/composables/useToast'

const toast = useToast()

// Éxito
toast.success('Escaneo completado exitosamente')

// Error
toast.error('No se pudo conectar al servidor')

// Advertencia
toast.warning('Algunos hosts no respondieron')

// Info
toast.info('Iniciando escaneo de red...')

// Con opciones personalizadas
toast.success('Operación exitosa', {
  timeout: 5000,
  position: 'bottom-center'
})
```

---

## 7. Servicios y API

### 7.1 scanner.js - Cliente API

**Ubicación**: `src/api/scanner.js`

**Propósito**: Centralización de todas las peticiones HTTP al backend.

**Configuración Base**:
```javascript
import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 600000,  // 10 minutos para escaneos largos
  headers: {
    'Content-Type': 'application/json'
  }
})
```

**Métodos de API**:

#### Escaneos

```javascript
// Ping múltiples hosts
pingHosts(hosts: string[], signal?: AbortSignal)
  => Promise<{ results: Array }>

// Escaneo completo de host
fullHostScan(host: string, includeVulns?: boolean)
  => Promise<Object>

// Escaneo de puertos
scanPorts(hosts: string[], ports?: string)
  => Promise<Array>

// Detección de servicios
scanServices(hosts: string[], ports?: string)
  => Promise<Array>

// Detección de OS
detectOS(hosts: string[])
  => Promise<Array>

// Escaneo de MAC (CIDR)
scanMAC(network: string)
  => Promise<{ devices: Array }>

// Escaneo de vulnerabilidades
scanVulnerabilities(host: string)
  => Promise<Object>
```

#### Base de Datos

```javascript
// Obtener todos los hosts
getAllHosts()
  => Promise<Array>

// Obtener host por IP
getHost(ip: string)
  => Promise<Object>

// Eliminar host
deleteHost(ip: string)
  => Promise<void>

// Obtener estadísticas
getStatistics()
  => Promise<{ total, active, inactive }>
```

#### Schedules

```javascript
// Listar schedules
getSchedules()
  => Promise<Array>

// Crear schedule
createSchedule(scheduleData: Object)
  => Promise<Object>

// Actualizar schedule
updateSchedule(id: number, scheduleData: Object)
  => Promise<Object>

// Eliminar schedule
deleteSchedule(id: number)
  => Promise<void>

// Activar/Desactivar schedule
toggleSchedule(id: number)
  => Promise<Object>

// Ejecutar schedule manualmente
runScheduleNow(id: number)
  => Promise<Object>

// Obtener resultados de schedule
getScheduleResults(id: number)
  => Promise<Object>
```

#### SSH Operations

```javascript
// Apagar host vía SSH
shutdownHost(data: {
  host: string,
  username: string,
  password: string,
  key_file?: string
})
  => Promise<Object>

// Reiniciar host vía SSH
rebootHost(data: {
  host: string,
  username: string,
  password: string,
  key_file?: string
})
  => Promise<Object>

// Apagar rango de IPs
shutdownRange(data: {
  start_ip: string,
  end_ip: string,
  username: string,
  password: string,
  key_file?: string
})
  => Promise<{ results: Array }>

// Ejecutar comando SSH
executeCommand(data: {
  host: string,
  command: string,
  username: string,
  password: string,
  key_file?: string
})
  => Promise<{ output: string }>

// Probar conexión SSH
testSSH(data: {
  host: string,
  username: string,
  password: string,
  key_file?: string
})
  => Promise<{ success: boolean }>
```

**Manejo de Errores**:
```javascript
try {
  const hosts = await scannerAPI.getAllHosts()
} catch (error) {
  if (error.response) {
    // Error del servidor (4xx, 5xx)
    console.error('Server error:', error.response.data)
  } else if (error.request) {
    // No se recibió respuesta
    console.error('No response from server')
  } else {
    // Error en la configuración
    console.error('Request error:', error.message)
  }
}
```

**Cancelación de Requests**:
```javascript
const abortController = new AbortController()

scannerAPI.pingHosts(hosts, abortController.signal)

// Cancelar después de 5 segundos
setTimeout(() => {
  abortController.abort()
}, 5000)
```

---

## 8. Flujos de Trabajo

### 8.1 Flujo de Escaneo Completo (Full Scan)

```
┌─────────────────────┐
│  Usuario ingresa IP │
└──────────┬──────────┘
           ↓
┌─────────────────────────────┐
│ Click "Escanear" button     │
│ - Genera scanId único       │
│ - startScan(scanId)         │
└──────────┬──────────────────┘
           ↓
┌─────────────────────────────────────┐
│ API Request: fullHostScan(host)     │
│ - Backend inicia escaneo            │
│ - Emite eventos WebSocket           │
└──────────┬──────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ WebSocket Events (tiempo real)      │
│                                      │
│ 1. status: "scanning", stage: "mac" │
│    progress: 20%                     │
│                                      │
│ 2. status: "scanning", stage: "ports"│
│    progress: 40%                     │
│                                      │
│ 3. status: "scanning", stage: "services"│
│    progress: 60%                     │
│                                      │
│ 4. status: "scanning", stage: "os"  │
│    progress: 80%                     │
│                                      │
│ 5. status: "completed"               │
│    progress: 100%                    │
└──────────┬──────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ API Response recibida                │
│ - Host guardado en DB                │
│ - results actualizado                │
└──────────┬──────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ UI Actualizada                       │
│ - Mostrar resultados                 │
│ - endScan(scanId)                    │
│ - Toast de éxito                     │
└─────────────────────────────────────┘
```

### 8.2 Flujo de Progreso con WebSocket

```
┌─────────────────┐      ┌──────────────┐      ┌─────────────┐
│   Component     │      │  Composable  │      │  WebSocket  │
│  (PingScanner)  │      │(useScanProgress)│    │   Server    │
└────────┬────────┘      └──────┬───────┘      └──────┬──────┘
         │                      │                      │
         │ 1. startScan(id)     │                      │
         ├─────────────────────>│                      │
         │                      │                      │
         │ 2. API call          │                      │
         ├──────────────────────┼─────────────────────>│
         │                      │                      │
         │                      │ 3. Progress Event    │
         │                      │<─────────────────────┤
         │                      │                      │
         │                      │ 4. Update progressData│
         │                      │                      │
         │ 5. Re-render (reactive)                     │
         │<─────────────────────┤                      │
         │                      │                      │
         │                      │ 6. Completed Event   │
         │                      │<─────────────────────┤
         │                      │                      │
         │ 7. endScan(id)       │                      │
         ├─────────────────────>│                      │
         │                      │                      │
```

### 8.3 Flujo de Cancelación de Scan

```
┌──────────────────┐
│ Usuario presiona │
│ botón "Cancelar" │
└────────┬─────────┘
         ↓
┌────────────────────────────┐
│ cancelCurrentScan()        │
│ - Obtiene scanId activo    │
└────────┬───────────────────┘
         ↓
┌────────────────────────────────┐
│ WebSocket send:                │
│ {                              │
│   type: 'cancel_scan',         │
│   scan_id: scanId              │
│ }                              │
└────────┬───────────────────────┘
         ↓
┌────────────────────────────────┐
│ Backend recibe cancelación     │
│ - Agrega scanId a cancelled_scans│
│ - Detiene ejecución de loops   │
└────────┬───────────────────────┘
         ↓
┌────────────────────────────────┐
│ Frontend actualiza UI          │
│ - progressData[id].active = false│
│ - Agrega a cancelledScanIds    │
│ - Ignora mensajes futuros      │
└────────────────────────────────┘
```

### 8.4 Flujo de Schedule Execution

```
┌─────────────────────────┐
│ Usuario crea Schedule   │
│ - Frecuencia: Diaria    │
│ - Hora: 02:00           │
│ - Tipo: Full Scan       │
└──────────┬──────────────┘
           ↓
┌──────────────────────────────┐
│ POST /api/schedules          │
│ - Guarda en DB               │
│ - Calcula next_run           │
└──────────┬───────────────────┘
           ↓
┌──────────────────────────────────┐
│ Backend Scheduler Service        │
│ (Corre cada 60 segundos)         │
│                                   │
│ while (running):                  │
│   now = datetime.now()            │
│   for schedule in schedules:      │
│     if schedule.next_run <= now:  │
│       execute_scheduled_scan()    │
└──────────┬────────────────────────┘
           ↓
┌──────────────────────────────────┐
│ Ejecución del Scan               │
│ - Ejecuta scan según tipo        │
│ - Guarda resultados en cache     │
│ - Actualiza last_run, next_run   │
└──────────┬────────────────────────┘
           ↓
┌──────────────────────────────────┐
│ WebSocket Notification           │
│ {                                 │
│   type: 'schedule_update',        │
│   action: 'executed',             │
│   schedule: {...}                 │
│ }                                 │
└──────────┬────────────────────────┘
           ↓
┌──────────────────────────────────┐
│ Frontend actualiza UI             │
│ - Actualiza lista de schedules    │
│ - Muestra toast de éxito          │
└───────────────────────────────────┘
```

---

## 9. Comunicación en Tiempo Real

### 9.1 Eventos WebSocket

El sistema utiliza WebSocket para comunicación bidireccional en tiempo real.

**URL de Conexión**: `ws://localhost:8000/ws`

#### Mensajes del Cliente → Servidor

**1. Cancelación de Scan**
```json
{
  "type": "cancel_scan",
  "scan_id": "ping-1735123456789"
}
```

**2. Keep-Alive Ping**
```
"ping"
```

#### Mensajes del Servidor → Cliente

**1. Progreso de Scan**
```json
{
  "type": "scan_progress",
  "data": {
    "scan_id": "ping-1735123456789",
    "scan_type": "ping",
    "status": "scanning",
    "total": 100,
    "completed": 45,
    "progress": 45.5,
    "current_host": "192.168.0.45",
    "result": {
      "host": "192.168.0.45",
      "status": "up",
      "latency_ms": 2.3
    }
  }
}
```

**Estados Posibles**:
- `started`: Scan iniciado
- `scanning`: En progreso
- `completed`: Finalizado exitosamente
- `cancelled`: Cancelado por el usuario
- `error`: Error durante ejecución

**2. Actualización de Schedule**
```json
{
  "type": "schedule_update",
  "data": {
    "action": "executed",
    "schedule": {
      "id": 5,
      "name": "Escaneo Nocturno",
      "last_run": "2025-12-25T02:00:00",
      "next_run": "2025-12-26T02:00:00"
    }
  }
}
```

**Acciones Posibles**:
- `created`: Schedule creado
- `updated`: Schedule actualizado
- `deleted`: Schedule eliminado
- `executed`: Schedule ejecutado

**3. Actualización de Host**
```json
{
  "type": "host_update",
  "data": {
    "ip": "192.168.0.10",
    "hostname": "PC-Admin",
    "status": "active",
    "last_seen": "2025-12-25T10:30:00Z"
  }
}
```

**4. Keep-Alive Pong**
```
"pong"
```

### 9.2 Manejo de Reconexión

El composable `useWebSocket` implementa reconexión automática:

```javascript
// Configuración
MAX_RECONNECT_ATTEMPTS = 5
RECONNECT_INTERVAL = 3000  // 3 segundos

// Lógica de reconexión
ws.onclose = () => {
  connected.value = false
  
  if (reconnectAttempts.value < MAX_RECONNECT_ATTEMPTS) {
    setTimeout(() => {
      reconnectAttempts.value++
      connect()  // Reintentar conexión
    }, RECONNECT_INTERVAL)
  }
}

ws.onopen = () => {
  connected.value = true
  reconnectAttempts.value = 0  // Resetear contador
}
```

---

## 10. Guía de Desarrollo

### 10.1 Requisitos del Sistema

**Node.js**: v20.19.0 o v22.12.0+  
**NPM**: v10.0.0+  
**Sistema Operativo**: Windows, Linux, macOS

### 10.2 Instalación

```bash
# Clonar repositorio
cd network-scanner-frontend

# Instalar dependencias
npm install

# Configurar variables de entorno (opcional)
cp .env.example .env
```

### 10.3 Comandos Disponibles

```bash
# Desarrollo (Hot-reload)
npm run dev
# Servidor disponible en: http://localhost:5173

# Build de producción
npm run build
# Output en: dist/

# Preview de build
npm run preview

# Linting (ESLint)
npm run lint

# Formateo de código (Prettier)
npm run format
```

### 10.4 Estructura de un Componente Vue

**Plantilla Estándar**:
```vue
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useScanState } from '@/composables/useScanState'
import { useToast } from '@/composables/useToast'
import scannerAPI from '@/api/scanner'

// Estado reactivo
const data = ref(null)
const loading = ref(false)

// Composables
const { startScan, endScan } = useScanState()
const toast = useToast()

// Computed properties
const isValid = computed(() => data.value?.length > 0)

// Métodos
const handleAction = async () => {
  loading.value = true
  try {
    const result = await scannerAPI.someMethod()
    toast.success('Operación exitosa')
  } catch (err) {
    toast.error('Error en la operación')
  } finally {
    loading.value = false
  }
}

// Lifecycle hooks
onMounted(() => {
  // Código de inicialización
})
</script>

<template>
  <div class="container">
    <!-- Template HTML con Tailwind CSS -->
  </div>
</template>

<style scoped>
/* Estilos específicos del componente */
</style>
```

### 10.5 Convenciones de Código

**Nomenclatura**:
- Componentes: PascalCase (`FullScan.vue`)
- Composables: camelCase con prefijo `use` (`useScanState.js`)
- Variables: camelCase (`currentHost`)
- Constantes: UPPER_SNAKE_CASE (`MAX_RETRIES`)

**Estructura de Archivos**:
- Un componente por archivo
- Composables agrupados por funcionalidad
- Servicios centralizados en `/api`

**Imports**:
```javascript
// 1. Vue core
import { ref, computed } from 'vue'

// 2. Librerías externas
import axios from 'axios'

// 3. Composables
import { useScanState } from '@/composables/useScanState'

// 4. Componentes
import ScanProgress from '@/components/ScanProgress.vue'

// 5. Utilidades/API
import scannerAPI from '@/api/scanner'
```

### 10.6 Buenas Prácticas

**1. Manejo de Estado**
```javascript
// ✅ Correcto: Usar composables para estado compartido
const { activeScans } = useScanState()

// ❌ Incorrecto: Estado global sin estructura
window.scans = []
```

**2. Manejo de Errores**
```javascript
// ✅ Correcto: Try-catch con notificación al usuario
try {
  await scannerAPI.scanHost(ip)
  toast.success('Scan completado')
} catch (err) {
  toast.error('Error en el scan')
}

// ❌ Incorrecto: Silenciar errores
await scannerAPI.scanHost(ip).catch(() => {})
```

**3. Limpieza de Recursos**
```javascript
// ✅ Correcto: Limpiar en onUnmounted
import { onUnmounted } from 'vue'

const interval = setInterval(() => {}, 1000)

onUnmounted(() => {
  clearInterval(interval)
})

// ❌ Incorrecto: No limpiar timers/listeners
```

**4. Reactividad**
```javascript
// ✅ Correcto: Usar ref/reactive
const hosts = ref([])
hosts.value.push(newHost)

// ❌ Incorrecto: Mutar sin reactividad
let hosts = []
hosts.push(newHost)  // No reactivo
```

### 10.7 Testing (Guía Futura)

```javascript
// Ejemplo de test unitario (Vitest)
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import PingScanner from '@/components/PingScanner.vue'

describe('PingScanner', () => {
  it('renders correctly', () => {
    const wrapper = mount(PingScanner)
    expect(wrapper.find('input').exists()).toBe(true)
  })
  
  it('validates IP format', async () => {
    const wrapper = mount(PingScanner)
    await wrapper.find('input').setValue('invalid')
    expect(wrapper.vm.isValidIP).toBe(false)
  })
})
```

---

## 11. Despliegue

### 11.1 Build de Producción

```bash
# Generar build optimizado
npm run build

# Output:
# dist/
# ├── assets/
# │   ├── index-[hash].js      # JavaScript minificado
# │   └── index-[hash].css     # CSS minificado
# └── index.html               # HTML principal
```

**Optimizaciones automáticas**:
- Minificación de JS/CSS
- Tree-shaking (eliminación de código no usado)
- Code splitting (división de bundles)
- Asset hashing (caché eficiente)

### 11.2 Variables de Entorno

Crear archivo `.env.production`:
```bash
VITE_API_BASE_URL=https://api.example.com
VITE_WS_URL=wss://api.example.com/ws
```

Acceso en código:
```javascript
const API_URL = import.meta.env.VITE_API_BASE_URL
```

### 11.3 Servidor Web

**Opción 1: Nginx**
```nginx
server {
    listen 80;
    server_name example.com;
    root /var/www/network-scanner/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Caché para assets
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

**Opción 2: Apache**
```apache
<VirtualHost *:80>
    ServerName example.com
    DocumentRoot /var/www/network-scanner/dist

    <Directory /var/www/network-scanner/dist>
        RewriteEngine On
        RewriteBase /
        RewriteRule ^index\.html$ - [L]
        RewriteCond %{REQUEST_FILENAME} !-f
        RewriteCond %{REQUEST_FILENAME} !-d
        RewriteRule . /index.html [L]
    </Directory>
</VirtualHost>
```

**Opción 3: Node.js (Express)**
```javascript
import express from 'express'
import path from 'path'

const app = express()
const PORT = 3000

app.use(express.static('dist'))

app.get('*', (req, res) => {
  res.sendFile(path.resolve('dist', 'index.html'))
})

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`)
})
```

### 11.4 Docker

**Dockerfile**:
```dockerfile
# Build stage
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**docker-compose.yml**:
```yaml
version: '3.8'
services:
  frontend:
    build: .
    ports:
      - "80:80"
    environment:
      - VITE_API_BASE_URL=http://backend:8000
    depends_on:
      - backend
```

### 11.5 Verificación de Build

```bash
# Probar build localmente
npm run build
npm run preview

# Análisis de bundle
npx vite-bundle-visualizer
```

---

## 📊 Métricas del Proyecto

- **Componentes**: 11 componentes Vue
- **Composables**: 4 composables reutilizables
- **Rutas**: 1 ruta principal (Dashboard)
- **Dependencias**: 10 dependencias de producción
- **Tamaño del Bundle** (aprox.): ~300KB gzipped
- **Compatibilidad**: Navegadores modernos (ES2020+)

---

## 🔐 Seguridad

### Consideraciones Implementadas

1. **CORS**: Configurado en el backend para restringir orígenes
2. **Input Validation**: Validación de IPs y rangos en el frontend
3. **XSS Prevention**: Vue escapa automáticamente el HTML
4. **Credenciales SSH**: Se envían solo vía HTTPS en producción

### Recomendaciones para Producción

- Implementar autenticación (JWT/OAuth)
- Usar HTTPS para todas las comunicaciones
- Implementar rate limiting en el backend
- Sanitizar inputs antes de enviar al servidor
- Implementar CSP (Content Security Policy)

---

## 🚀 Mejoras Futuras

1. **Autenticación y Autorización**
   - Login con JWT
   - Roles de usuario (Admin, Viewer)
   - Permisos granulares

2. **Visualizaciones Avanzadas**
   - Gráficos de estadísticas (Chart.js/D3.js)
   - Mapa de red visual
   - Timeline de eventos

3. **Notificaciones**
   - Notificaciones push (Web Push API)
   - Email alerts para eventos críticos

4. **Testing**
   - Unit tests (Vitest)
   - E2E tests (Playwright/Cypress)
   - Coverage > 80%

5. **Performance**
   - Lazy loading de componentes
   - Virtual scrolling para tablas grandes
   - Service Workers para PWA

6. **Internacionalización**
   - Soporte multi-idioma (i18n)
   - Formato de fechas/números localizados

---

## 📚 Referencias

- [Vue.js Documentation](https://vuejs.org/)
- [Vue Router](https://router.vuejs.org/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Axios Documentation](https://axios-http.com/)
- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [Vite Documentation](https://vitejs.dev/)

---

## 📝 Licencia

Este proyecto fue desarrollado como parte de una Residencia Profesional.

---

## ✍️ Autor

**Manuel**  
Residencia Profesional - Diciembre 2025  
Network Scanner System - Frontend Documentation

---

**Última actualización**: 25 de Diciembre de 2025
