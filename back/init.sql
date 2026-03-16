CREATE TABLE IF NOT EXISTS hosts (
    id SERIAL PRIMARY KEY,
    ip INET UNIQUE NOT NULL,
    hostname VARCHAR(255),
    nickname VARCHAR(255),
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


CREATE TABLE IF NOT EXISTS connection_history (
    id SERIAL PRIMARY KEY,
    host_id INTEGER REFERENCES hosts(id) ON DELETE CASCADE,
    status VARCHAR(20),
    latency_ms FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS scan_history (
    id SERIAL PRIMARY KEY,
    schedule_id INTEGER REFERENCES scan_schedules(id) ON DELETE SET NULL,
    schedule_name VARCHAR(255),
    scan_type VARCHAR(50),
    action_type VARCHAR(50),
    targets_count INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'success',
    duration_seconds FLOAT,
    scan_results JSONB,
    shutdown_results JSONB,
    error_message TEXT,
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS admin_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    role VARCHAR(20) DEFAULT 'viewer',
    is_super_admin BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_admin_users_username ON admin_users(username);


CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    username VARCHAR(100),
    action VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    details JSONB,
    ip_address VARCHAR(45),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_username ON audit_log(username);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_log_category ON audit_log(category);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at);


CREATE INDEX idx_hosts_ip ON hosts(ip);
CREATE INDEX idx_hosts_status ON hosts(status);
CREATE INDEX idx_hosts_last_seen ON hosts(last_seen);
CREATE INDEX idx_ports_host_id ON ports(host_id);
CREATE INDEX idx_services_host_id ON services(host_id);
CREATE INDEX idx_vulnerabilities_host_id ON vulnerabilities(host_id);
CREATE INDEX idx_connection_history_host_id ON connection_history(host_id);
CREATE INDEX idx_scan_history_schedule_id ON scan_history(schedule_id);
CREATE INDEX idx_scan_history_executed_at ON scan_history(executed_at);


CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';


CREATE TRIGGER update_hosts_updated_at BEFORE UPDATE ON hosts
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


CREATE TRIGGER update_services_updated_at BEFORE UPDATE ON services
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();



DO $$ BEGIN
    ALTER TABLE fullscan_history ADD COLUMN IF NOT EXISTS user_id INTEGER;
    ALTER TABLE fullscan_history ADD COLUMN IF NOT EXISTS username VARCHAR(100);
EXCEPTION WHEN others THEN NULL;
END $$;


DO $$ BEGIN
    ALTER TABLE scan_schedules ADD COLUMN IF NOT EXISTS created_by VARCHAR(100);
    ALTER TABLE scan_schedules ADD COLUMN IF NOT EXISTS updated_by VARCHAR(100);
EXCEPTION WHEN others THEN NULL;
END $$;


DO $$ BEGIN
    ALTER TABLE admin_users ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'viewer';
EXCEPTION WHEN others THEN NULL;
END $$;


UPDATE admin_users SET role = 'admin' WHERE username = 'admin' AND (role IS NULL OR role = 'viewer');


DO $$ BEGIN
    ALTER TABLE admin_users ADD COLUMN IF NOT EXISTS is_super_admin BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN others THEN NULL;
END $$;

UPDATE admin_users SET is_super_admin = TRUE WHERE username = 'admin';


DO $$ BEGIN
    ALTER TABLE admin_users ADD COLUMN IF NOT EXISTS must_change_password BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN others THEN NULL;
END $$;


UPDATE admin_users SET role = 'mod' WHERE role = 'editor';
UPDATE admin_users SET role = 'op' WHERE role = 'operator';



CREATE TABLE IF NOT EXISTS subnets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    start_ip VARCHAR(45) NOT NULL,
    end_ip VARCHAR(45) NOT NULL,
    created_by VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS subnet_devices (
    id SERIAL PRIMARY KEY,
    subnet_id INTEGER NOT NULL REFERENCES subnets(id) ON DELETE CASCADE,
    ip VARCHAR(45) NOT NULL,
    label VARCHAR(255),
    device_type VARCHAR(50) DEFAULT 'pc',
    status VARCHAR(20) DEFAULT 'grey',
    last_scan_at TIMESTAMP WITH TIME ZONE,
    scan_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_subnet_devices_subnet_id ON subnet_devices(subnet_id);
CREATE INDEX IF NOT EXISTS idx_subnet_devices_ip ON subnet_devices(ip);



CREATE TABLE IF NOT EXISTS ssh_credentials (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    username VARCHAR(255) NOT NULL,
    password TEXT NOT NULL,
    created_by VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ssh_credentials_name ON ssh_credentials(name);


-- token_version para revocación de tokens
DO $$ BEGIN
    ALTER TABLE admin_users ADD COLUMN IF NOT EXISTS token_version INTEGER NOT NULL DEFAULT 0;
EXCEPTION WHEN others THEN NULL;
END $$;


-- Tabla de intentos de login para rate limiting persistente
CREATE TABLE IF NOT EXISTS login_attempts (
    id SERIAL PRIMARY KEY,
    ip_address VARCHAR(45) NOT NULL,
    username VARCHAR(100),
    attempted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_login_attempts_ip ON login_attempts(ip_address);
CREATE INDEX IF NOT EXISTS idx_login_attempts_at ON login_attempts(attempted_at);
