import paramiko
import threading
import time
from typing import Dict, Optional


class SSHSession:

    def __init__(self, host: str, username: str, password: str, port: int = 22):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.client: Optional[paramiko.SSHClient] = None
        self.channel: Optional[paramiko.Channel] = None
        self.connected = False

    def connect(self, cols: int = 120, rows: int = 30) -> bool:
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=10,
                banner_timeout=10,
                look_for_keys=False,
                allow_agent=False,
            )
            self.channel = self.client.invoke_shell(
                term="xterm-256color",
                width=cols,
                height=rows,
            )
            self.channel.setblocking(0)
            self.channel.settimeout(0.0)
            self.connected = True
            return True
        except Exception:
            self.connected = False
            return False

    def read(self) -> bytes:
        if not self.channel or not self.connected:
            return b""
        chunks = []
        try:
            while self.channel.recv_ready():
                chunk = self.channel.recv(16384)
                if chunk:
                    chunks.append(chunk)
                else:
                    break
            while self.channel.recv_stderr_ready():
                chunk = self.channel.recv_stderr(16384)
                if chunk:
                    chunks.append(chunk)
                else:
                    break
        except Exception:
            pass
        return b"".join(chunks)

    def write(self, data: bytes) -> bool:
        if not self.channel or not self.connected:
            return False
        try:
            self.channel.sendall(data)
            return True
        except Exception:
            self.connected = False
            return False

    def resize(self, cols: int, rows: int):
        if self.channel and self.connected:
            try:
                self.channel.resize_pty(width=cols, height=rows)
            except Exception:
                pass

    def is_alive(self) -> bool:
        if not self.channel or not self.connected:
            return False
        if self.channel.closed or self.channel.exit_status_ready():
            self.connected = False
            return False
        transport = self.client.get_transport() if self.client else None
        if not transport or not transport.is_active():
            self.connected = False
            return False
        return True

    def close(self):
        self.connected = False
        if self.channel:
            try:
                self.channel.close()
            except Exception:
                pass
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass


class SSHTerminalManager:

    def __init__(self):
        self.sessions: Dict[str, SSHSession] = {}
        self.lock = threading.Lock()

    def create_session(
        self, session_id: str, host: str, username: str, password: str,
        port: int = 22, cols: int = 120, rows: int = 30,
    ) -> bool:
        with self.lock:
            if session_id in self.sessions:
                self.sessions[session_id].close()
                del self.sessions[session_id]
            session = SSHSession(host, username, password, port)
            if session.connect(cols, rows):
                self.sessions[session_id] = session
                return True
            return False

    def get_session(self, session_id: str) -> Optional[SSHSession]:
        return self.sessions.get(session_id)

    def close_session(self, session_id: str):
        with self.lock:
            session = self.sessions.pop(session_id, None)
            if session:
                session.close()

    def close_all(self):
        with self.lock:
            for session in self.sessions.values():
                session.close()
            self.sessions.clear()


ssh_manager = SSHTerminalManager()
