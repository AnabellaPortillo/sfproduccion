# LabCore LIS — Guía de instalación

## Opción 1 — Docker (recomendado para red del laboratorio)

Solo necesitás instalar Docker Desktop una vez.
Los usuarios acceden desde cualquier navegador en la red.

### Instalar Docker
- **Windows**: https://www.docker.com/products/docker-desktop  
- **Mac**: https://www.docker.com/products/docker-desktop  
- **Linux**: `sudo apt install docker.io docker-compose`

### Iniciar LabCore
```bash
# En la carpeta del proyecto:
docker compose up -d
```

Listo. Abrir en el navegador: **http://localhost:8000**  
Desde otras PCs de la red: **http://IP-DEL-SERVIDOR:8000**

Para encontrar la IP del servidor: `ipconfig` (Windows) o `ip a` (Linux).

### Comandos útiles
```bash
docker compose up -d        # iniciar
docker compose down         # detener
docker compose logs -f      # ver errores
docker compose restart      # reiniciar
```

La base de datos se guarda automáticamente aunque apagues el servidor.

---

## Opción 2 — Python directo (una sola PC)

Si querés correrlo en una sola computadora sin Docker:

### Instalar Python
Descargar Python 3.11+ desde https://www.python.org/downloads/  
(tildar "Add Python to PATH" durante la instalación)

### Iniciar LabCore
```bash
# En la carpeta del proyecto:
pip install -r requirements.txt
python seed.py
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Abrir en el navegador: **http://localhost:8000**

---

## Usuarios por defecto

| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `admin123` | Administrador |
| `supervisor` | `super123` | Supervisor |
| `tecnico1` | `tec123` | Técnico |
| `recepcion` | `rec123` | Recepción |
