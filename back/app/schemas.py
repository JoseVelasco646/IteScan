from pydantic import BaseModel, field_validator
from typing import List, Optional
import ipaddress



class HostsRequest(BaseModel):
    hosts: List[str]
    host_timeout: int = 2
    concurrency: int = 50

    @field_validator('hosts')
    @classmethod
    def validate_hosts(cls, v):
        validated = []
        invalid_hosts = []
        for host in v:
            host = host.strip()
            if not host:
                continue
            try:
                ipaddress.ip_address(host)
                validated.append(host)
            except ValueError:
                invalid_hosts.append(host)
        if invalid_hosts:
            raise ValueError(f'IPs inválidas: {", ".join(invalid_hosts[:5])}')
        if not validated:
            raise ValueError('Al menos una IP válida es requerida')
        return validated


class NetworkRequest(BaseModel):
    cidr: str
    host_timeout: int = 2
    concurrency: int = 50

    @field_validator('cidr')
    @classmethod
    def validate_cidr(cls, v):
        try:
            ipaddress.ip_network(v, strict=False)
            return v
        except ValueError:
            raise ValueError(f'CIDR inválido: {v}. Formato esperado: 192.168.0.0/24')


class PortScanRequest(BaseModel):
    host: str
    ports: str = "1-1024"

    @field_validator('host')
    @classmethod
    def validate_host(cls, v):
        v = v.strip()
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError(f'IP inválida: {v}. Solo se aceptan direcciones IP válidas')


class ServiceScanRequest(BaseModel):
    host: str
    ports: str = "1-1024"

    @field_validator('host')
    @classmethod
    def validate_host(cls, v):
        v = v.strip()
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError(f'IP inválida: {v}. Solo se aceptan direcciones IP válidas')


class VulnScanRequest(BaseModel):
    host: str

    @field_validator('host')
    @classmethod
    def validate_host(cls, v):
        v = v.strip()
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError(f'IP inválida: {v}. Solo se aceptan direcciones IP válidas')


class VulnSegmentScanRequest(BaseModel):
    hosts: List[str]

    @field_validator('hosts')
    @classmethod
    def validate_hosts(cls, v):
        validated = []
        invalid_hosts = []
        for host in v:
            host = host.strip()
            try:
                ipaddress.ip_address(host)
                validated.append(host)
                continue
            except ValueError:
                pass
            try:
                ipaddress.ip_network(host, strict=False)
                validated.append(host)
                continue
            except ValueError:
                invalid_hosts.append(host)
        if invalid_hosts:
            raise ValueError(f'IPs/CIDRs inválidos: {", ".join(invalid_hosts[:5])}')
        if not validated:
            raise ValueError('Al menos una IP o CIDR válido es requerido')
        return validated


class OSRequest(BaseModel):
    host: str

    @field_validator('host')
    @classmethod
    def validate_host(cls, v):
        v = v.strip()
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError(f'IP inválida: {v}. Solo se aceptan direcciones IP válidas')


class OSSegmentRequest(BaseModel):
    hosts: List[str]
    host_timeout: int = 60
    concurrency: int = 50

    @field_validator('hosts')
    @classmethod
    def validate_hosts(cls, v):
        validated = []
        invalid_hosts = []
        for host in v:
            host = host.strip()
            try:
                ipaddress.ip_address(host)
                validated.append(host)
                continue
            except ValueError:
                pass
            try:
                ipaddress.ip_network(host, strict=False)
                validated.append(host)
                continue
            except ValueError:
                invalid_hosts.append(host)
        if invalid_hosts:
            raise ValueError(f'IPs/CIDRs inválidos: {", ".join(invalid_hosts[:5])}')
        if not validated:
            raise ValueError('Al menos una IP o CIDR válido es requerido')
        return validated


class MacScanRequest(BaseModel):
    cidr: str
    host_timeout: int = 8
    concurrency: int = 30

    @field_validator('cidr')
    @classmethod
    def validate_cidr(cls, v):
        try:
            ipaddress.ip_network(v, strict=False)
            return v
        except ValueError:
            raise ValueError(f'CIDR inválido: {v}')


class PortSegmentScanRequest(BaseModel):
    hosts: List[str]
    ports: str = "1-1024"
    host_timeout: int = 45
    concurrency: int = 50

    @field_validator('hosts')
    @classmethod
    def validate_hosts(cls, v):
        validated = []
        invalid_hosts = []
        for host in v:
            host = host.strip()
            try:
                ipaddress.ip_address(host)
                validated.append(host)
                continue
            except ValueError:
                pass
            try:
                ipaddress.ip_network(host, strict=False)
                validated.append(host)
                continue
            except ValueError:
                invalid_hosts.append(host)
        if invalid_hosts:
            raise ValueError(f'IPs/CIDRs inválidos: {", ".join(invalid_hosts[:5])}')
        if not validated:
            raise ValueError('Al menos una IP o CIDR válido es requerido')
        return validated


class ServiceSegmentScanRequest(BaseModel):
    hosts: List[str]
    ports: str = "1-1024"
    host_timeout: int = 120
    concurrency: int = 50

    @field_validator('hosts')
    @classmethod
    def validate_hosts(cls, v):
        validated = []
        invalid_hosts = []
        for host in v:
            host = host.strip()
            try:
                ipaddress.ip_address(host)
                validated.append(host)
                continue
            except ValueError:
                pass
            try:
                ipaddress.ip_network(host, strict=False)
                validated.append(host)
                continue
            except ValueError:
                invalid_hosts.append(host)
        if invalid_hosts:
            raise ValueError(f'IPs/CIDRs inválidos: {", ".join(invalid_hosts[:5])}')
        if not validated:
            raise ValueError('Al menos una IP o CIDR válido es requerido')
        return validated


class FullScanRequest(BaseModel):
    host: str
    save_to_db: bool = True
    host_timeout: int = 120

    @field_validator('host')
    @classmethod
    def validate_host(cls, v):
        v = v.strip()
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError(f'IP inválida: {v}. Solo se aceptan direcciones IP válidas')


class FullScanRangeRequest(BaseModel):
    hosts: List[str]
    save_to_db: bool = True
    host_timeout: int = 120
    concurrency: int = 20


class SavePingResultsRequest(BaseModel):
    results: List[dict]




class SSHShutdownRequest(BaseModel):
    host: str
    username: str
    password: Optional[str] = None
    key_file: Optional[str] = None
    sudo_password: Optional[str] = None
    os_type: str = "linux"

    @field_validator('host')
    @classmethod
    def validate_host(cls, v):
        v = v.strip()
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError(f'IP inválida: {v}. Se requiere una dirección IP válida')


class SSHRangeShutdownRequest(BaseModel):
    start_ip: str
    end_ip: str
    username: str
    password: Optional[str] = None
    key_file: Optional[str] = None
    sudo_password: Optional[str] = None
    os_type: str = "linux"

    @field_validator('start_ip', 'end_ip')
    @classmethod
    def validate_ip(cls, v):
        v = v.strip()
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError(f'IP inválida: {v}. Se requiere una dirección IP válida')




class IPRangeFilter(BaseModel):
    start_ip: str
    end_ip: str


class SubnetFilter(BaseModel):
    subnet: str


class DeleteHostRequest(BaseModel):
    ip: str


class DeleteHostsRequest(BaseModel):
    ips: List[str]


class UpdateNicknameRequest(BaseModel):
    ip: str
    nickname: str = ""




class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        if not any(c.isupper() for c in v):
            raise ValueError('La contraseña debe contener al menos una mayúscula')
        if not any(c.islower() for c in v):
            raise ValueError('La contraseña debe contener al menos una minúscula')
        if not any(c.isdigit() for c in v):
            raise ValueError('La contraseña debe contener al menos un número')
        return v


class CreateAdminRequest(BaseModel):
    username: str
    password: str
    display_name: Optional[str] = None
    role: str = "viewer"

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        if not any(c.isupper() for c in v):
            raise ValueError('La contraseña debe contener al menos una mayúscula')
        if not any(c.islower() for c in v):
            raise ValueError('La contraseña debe contener al menos una minúscula')
        if not any(c.isdigit() for c in v):
            raise ValueError('La contraseña debe contener al menos un número')
        return v


class UpdateAdminRequest(BaseModel):
    display_name: Optional[str] = None
    is_active: Optional[bool] = None
    new_password: Optional[str] = None
    role: Optional[str] = None




class FullScanHistorySave(BaseModel):
    scan_type: str  # 'single' o 'range'
    target: str
    hosts_scanned: int = 0
    hosts_active: int = 0
    total_ports: int = 0
    total_services: int = 0
    status: str = "success"
    duration_seconds: Optional[float] = None
    scan_results: Optional[list] = None
    error_message: Optional[str] = None
