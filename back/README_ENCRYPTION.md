# Encriptación Automática de Contraseñas SSH

Las contraseñas SSH en los escaneos programados se encriptan automáticamente al guardar y se desencriptan al leer.

## ⚠️ Seguridad Importante

**Las contraseñas NUNCA se envían al frontend:**
- ❌ No se incluyen en respuestas de API (GET, POST, PUT)
- ❌ No se envían por WebSocket
- ✅ Solo se almacenan encriptadas en la base de datos
- ✅ Solo se desencriptan internamente para conexiones SSH

## Configuración

Agrega la clave de encriptación en tu archivo `.env`:

```bash
# Generar clave única
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Agregar al .env
ENCRYPTION_KEY=tu_clave_generada_aqui
```

## Uso

Las contraseñas se manejan automáticamente:

```python
# Al guardar - se encripta automáticamente
schedule.ssh_password = "mi_contraseña"
db.add(schedule)
db.commit()

# Al leer internamente - se desencripta automáticamente  
password = schedule.ssh_password  # Solo disponible en backend

# Al enviar al frontend - se excluye automáticamente
return schedule  # ssh_password no se incluye en JSON
```

**Nota:** Guarda tu `ENCRYPTION_KEY` de forma segura. No la compartas ni la subas a repositorios públicos.
