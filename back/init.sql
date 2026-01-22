-- Tabla principal de hosts
CREATE TABLE IF NOT EXISTS hosts (
    id SERIAL PRIMARY KEY,
    ip VARCHAR(45) UNIQUE NOT NULL,
    hostname VARCHAR(255),
    mac VARCHAR(17),
    vendor VARCHAR(255),
    os_name VARCHAR(255),
    os_accuracy INTEGER,
    status VARCHAR(20) DEFAULT 'unknown',
    latency_ms FLOAT,
    last_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de puertos
CREATE TABLE IF NOT EXISTS ports (
    id SERIAL PRIMARY KEY,
    host_id INTEGER REFERENCES hosts(id) ON DELETE CASCADE,
    port INTEGER NOT NULL,
    protocol VARCHAR(10),
    service VARCHAR(100),
    state VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(host_id, port, protocol)
);

-- Tabla de servicios
CREATE TABLE IF NOT EXISTS services (
    id SERIAL PRIMARY KEY,
    host_id INTEGER REFERENCES hosts(id) ON DELETE CASCADE,
    port INTEGER NOT NULL,
    protocol VARCHAR(10),
    service_name VARCHAR(100),
    product VARCHAR(255),
    version VARCHAR(100),
    extra_info TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(host_id, port, protocol)
);

-- Tabla de vulnerabilidades
CREATE TABLE IF NOT EXISTS vulnerabilities (
    id SERIAL PRIMARY KEY,
    host_id INTEGER REFERENCES hosts(id) ON DELETE CASCADE,
    port INTEGER,
    script_name VARCHAR(255),
    severity VARCHAR(20),
    description TEXT,
    output TEXT,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de historial de conexiones
CREATE TABLE IF NOT EXISTS connection_history (
    id SERIAL PRIMARY KEY,
    host_id INTEGER REFERENCES hosts(id) ON DELETE CASCADE,
    status VARCHAR(20),
    latency_ms FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para mejorar el rendimiento
CREATE INDEX idx_hosts_ip ON hosts(ip);
CREATE INDEX idx_hosts_status ON hosts(status);
CREATE INDEX idx_hosts_last_seen ON hosts(last_seen);
CREATE INDEX idx_ports_host_id ON ports(host_id);
CREATE INDEX idx_services_host_id ON services(host_id);
CREATE INDEX idx_vulnerabilities_host_id ON vulnerabilities(host_id);
CREATE INDEX idx_connection_history_host_id ON connection_history(host_id);

-- Función para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger para hosts
CREATE TRIGGER update_hosts_updated_at BEFORE UPDATE ON hosts
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger para services
CREATE TRIGGER update_services_updated_at BEFORE UPDATE ON services
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
