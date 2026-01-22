import asyncio
import paramiko
from typing import List, Dict
import ipaddress
import socket
from datetime import datetime, timezone



def shutdown_host_ssh_sync(
    host: str,
    username: str,
    password: str = None,
    key_file: str = None,
    port: int = 22,
    timeout: int = 10,
) -> Dict:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        if key_file:
            client.connect(
                host,
                port=port,
                username=username,
                key_filename=key_file,
                timeout=timeout,
                banner_timeout=timeout
            )
        else:
            client.connect(
                host,
                port=port,
                username=username,
                password=password,
                timeout=timeout,
                banner_timeout=timeout
            )

        attempts = [
            ("shutdown /s /t 0", "Windows shutdown"),
            ('powershell -Command "Stop-Computer -Force"', "PowerShell Stop-Computer"),
        ]

        for cmd, note in attempts:
            try:
                stdin, stdout, stderr = client.exec_command(cmd, timeout=15)

                try:
                    exit_code = stdout.channel.recv_exit_status()
                except Exception:
                    exit_code = None

                now_iso = datetime.now(timezone.utc).isoformat()
                client.close()

                return {
                    "host": host,
                    "success": True,
                    "message": f"Shutdown command sent ({note})",
                    "exit_code": exit_code,
                    "os_type": "windows",
                    "timestamp": now_iso
                }

            except Exception:
                continue

        client.close()
        return {
            "host": host,
            "success": False,
            "message": "No se pudo ejecutar el apagado en Windows",
            "exit_code": -1,
            "os_type": "windows"
        }

    except paramiko.AuthenticationException as e:
        return {
            "host": host,
            "success": False,
            "message": "Error de autenticación SSH",
            "error": str(e),
            "exit_code": -1
        }
    except socket.timeout:
        return {
            "host": host,
            "success": False,
            "message": "Timeout de conexión SSH",
            "exit_code": -1
        }
    except Exception as e:
        return {
            "host": host,
            "success": False,
            "message": "Error inesperado",
            "error": str(e),
            "exit_code": -1
        }
    finally:
        try:
            client.close()
        except:
            pass


async def shutdown_host_ssh(
    host: str,
    username: str,
    password: str = None,
    key_file: str = None,
) -> Dict:
    return await asyncio.to_thread(
        shutdown_host_ssh_sync,
        host,
        username,
        password,
        key_file
    )



async def shutdown_multiple_hosts(
    hosts: List[str],
    username: str,
    password: str = None,
    key_file: str = None,
) -> List[Dict]:
    tasks = [
        shutdown_host_ssh(host, username, password, key_file)
        for host in hosts
    ]
    return await asyncio.gather(*tasks)


def expand_ip_range(start_ip: str, end_ip: str) -> List[str]:
    try:
        start = int(ipaddress.IPv4Address(start_ip))
        end = int(ipaddress.IPv4Address(end_ip))
        return [str(ipaddress.IPv4Address(i)) for i in range(start, end + 1)]
    except Exception:
        return []


async def shutdown_ip_range(
    start_ip: str,
    end_ip: str,
    username: str,
    password: str = None,
    key_file: str = None,
) -> List[Dict]:
    hosts = expand_ip_range(start_ip, end_ip)
    return await shutdown_multiple_hosts(hosts, username, password, key_file)



def execute_command_ssh_sync(
    host: str,
    command: str,
    username: str,
    password: str = None,
    key_file: str = None,
    port: int = 22,
    timeout: int = 30
) -> Dict:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        if key_file:
            ssh.connect(host, port, username, key_filename=key_file, timeout=timeout, banner_timeout=timeout)
        else:
            ssh.connect(host, port, username, password=password, timeout=timeout, banner_timeout=timeout)

        stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
        exit_code = stdout.channel.recv_exit_status()
        
        stdout_text = stdout.read().decode(errors="ignore").strip()
        stderr_text = stderr.read().decode(errors="ignore").strip()

        return {
            "host": host,
            "success": exit_code == 0,
            "stdout": stdout_text,
            "stderr": stderr_text,
            "exit_code": exit_code
        }

    except paramiko.AuthenticationException as e:
        return {
            "host": host,
            "success": False,
            "stdout": "",
            "stderr": f"Authentication failed: {str(e)}",
            "exit_code": -1,
            "error": "authentication_failed"
        }
    except paramiko.SSHException as e:
        return {
            "host": host,
            "success": False,
            "stdout": "",
            "stderr": f"SSH error: {str(e)}",
            "exit_code": -1,
            "error": "ssh_error"
        }
    except socket.timeout:
        return {
            "host": host,
            "success": False,
            "stdout": "",
            "stderr": "Connection timeout",
            "exit_code": -1,
            "error": "timeout"
        }
    except Exception as e:
        return {
            "host": host,
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "exit_code": -1,
            "error": "unknown_error"
        }
    finally:
        try:
            ssh.close()
        except:
            pass


async def execute_command_ssh(
    host: str,
    command: str,
    username: str,
    password: str = None,
    key_file: str = None
) -> Dict:
    return await asyncio.to_thread(
        execute_command_ssh_sync,
        host,
        command,
        username,
        password,
        key_file
    )



async def reboot_host_ssh(
    host: str,
    username: str,
    password: str = None,
    key_file: str = None,
) -> Dict:
    return await execute_command_ssh(
        host,
        'shutdown /r /t 0',
        username,
        password,
        key_file
    )



def test_ssh_connection(
    host: str,
    username: str,
    password: str = None,
    key_file: str = None,
    port: int = 22
) -> Dict:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        if key_file:
            ssh.connect(host, port, username, key_filename=key_file, timeout=5)
        else:
            ssh.connect(host, port, username, password, timeout=5)

        return {
            "host": host,
            "success": True,
            "message": "SSH connection successful"
        }

    except Exception as e:
        return {
            "host": host,
            "success": False,
            "message": str(e)
        }
    finally:
        try:
            ssh.close()
        except:
            pass
