export const SSH_QUICK_COMMANDS = [
  { label: 'hostname', command: 'hostname' },
  { label: 'uptime', command: 'uptime' },
  { label: 'df -h', command: 'df -h' },
  { label: 'free -m', command: 'free -m' },
  { label: 'who', command: 'who' },
  { label: 'ps aux', command: 'ps aux | head -20' },
  { label: 'netstat', command: 'netstat -tuln | head -20' },
  { label: 'ip addr', command: 'ip addr show' },
]
