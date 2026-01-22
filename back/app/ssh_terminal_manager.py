import asyncio
import paramiko
from typing import Dict, Optional
import threading
import time
from fastapi import WebSocket


class SSHSession:
    
    def __init__(self, host: str, username: str, password: str, port: int = 22):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.client = None
        self.channel = None
        self.connected = False
        self.output_buffer = []
        self.lock = threading.Lock()
        
    def connect(self) -> bool:
        try:
            print(f"Attempting SSH connection to {self.host}:{self.port}")
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
                allow_agent=False
            )
            
            print(f"SSH connected, creating PTY...")
            self.channel = self.client.invoke_shell(
                term='xterm-256color',
                width=120,
                height=30
            )
            
            self.channel.setblocking(0)
            
            self.connected = True
            print(f"PTY created successfully for {self.host}")
            return True
            
        except Exception as e:
            print(f"Error connecting to {self.host}: {e}")
            self.connected = False
            return False
    
    def read_output(self, timeout: float = 0.1) -> str:
        """Lee el output disponible del canal SSH"""
        if not self.channel or not self.connected:
            return ""
        
        output = ""
        try:
            time.sleep(timeout)
            
            max_reads = 20  
            reads = 0
            empty_reads = 0
            
            while reads < max_reads and empty_reads < 5:
                if self.channel.recv_ready():
                    data = self.channel.recv(4096)
                    if data:
                        decoded = data.decode('utf-8', errors='ignore')
                        output += decoded
                        print(f"Read {len(data)} bytes from SSH")
                        reads += 1
                        empty_reads = 0  
                    else:
                        empty_reads += 1
                else:
                    empty_reads += 1
                    if empty_reads >= 5:
                        break
                    time.sleep(0.02)  
                
            if self.channel.recv_stderr_ready():
                data = self.channel.recv_stderr(4096)
                if data:
                    output += data.decode('utf-8', errors='ignore')
                    print(f"Read {len(data)} bytes from SSH stderr")
                
        except Exception as e:
            print(f"Error reading from {self.host}: {e}")
            
        return output
    
    def write_input(self, data: str):
        if not self.channel or not self.connected:
            print(f"Cannot write - channel not connected")
            return False
        
        try:
            print(f"Writing {len(data)} bytes to SSH: {data[:50]}")
            self.channel.send(data)
            return True
        except Exception as e:
            print(f" Error writing to {self.host}: {e}")
            return False
    
    def resize_pty(self, width: int, height: int):
        if self.channel and self.connected:
            try:
                self.channel.resize_pty(width=width, height=height)
            except Exception as e:
                print(f"Error resizing pty: {e}")
    
    def close(self):
        self.connected = False
        if self.channel:
            try:
                self.channel.close()
            except:
                pass
        if self.client:
            try:
                self.client.close()
            except:
                pass


class SSHTerminalManager:
    def __init__(self):
        self.sessions: Dict[str, SSHSession] = {}
        self.lock = threading.Lock()
    
    def create_session(self, session_id: str, host: str, username: str, password: str, port: int = 22) -> bool:
        with self.lock:
            if session_id in self.sessions:
                self.sessions[session_id].close()
                del self.sessions[session_id]
            
            session = SSHSession(host, username, password, port)
            if session.connect():
                self.sessions[session_id] = session
                return True
            return False
    
    def get_session(self, session_id: str) -> Optional[SSHSession]:
        with self.lock:
            return self.sessions.get(session_id)
    
    def close_session(self, session_id: str):
        with self.lock:
            if session_id in self.sessions:
                self.sessions[session_id].close()
                del self.sessions[session_id]
    
    def close_all(self):
        with self.lock:
            for session in self.sessions.values():
                session.close()
            self.sessions.clear()


ssh_manager = SSHTerminalManager()
