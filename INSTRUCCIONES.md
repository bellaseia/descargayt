# Cómo subir a Ionos — Paso a paso

## Lo que necesitas
- Una cuenta en Ionos con hosting que soporte **Python** (Deploy Now o VPS)
- Los archivos de esta carpeta

---

## Opción A — Ionos Deploy Now (la más fácil)

1. Ve a ionos.es → Deploy Now → "Nuevo proyecto"
2. Conecta con GitHub:
   - Crea una cuenta gratuita en github.com
   - Sube esta carpeta como repositorio nuevo
   - En GitHub.com: botón "+" → "New repository" → arrastra los archivos
3. En Ionos Deploy Now selecciona ese repositorio
4. Ionos detecta automáticamente que es Python con Flask
5. En la configuración pon:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn app:app --workers 2 --timeout 300`
6. Pulsa Deploy → en unos minutos tienes la URL

---

## Opción B — Ionos VPS (si ya tienes un VPS)

Conéctate por SSH y ejecuta estos comandos:

```bash
# Instalar dependencias del sistema
sudo apt update
sudo apt install python3-pip ffmpeg -y

# Subir los archivos (o clonar desde GitHub)
cd /var/www
# Copia los archivos aquí

# Instalar dependencias Python
pip3 install -r requirements.txt

# Arrancar la app (en segundo plano)
gunicorn app:app --workers 2 --timeout 300 --bind 0.0.0.0:8000 --daemon
```

Luego configura Nginx para apuntar el dominio al puerto 8000.

---

## Estructura de archivos

```
/
├── app.py              ← backend principal
├── requirements.txt    ← librerías Python
├── Procfile            ← instrucción de arranque
└── templates/
    └── index.html      ← la página web
```

---

## Notas

- Los vídeos se borran automáticamente del servidor tras 1 hora
- El sobrino solo necesita abrir la URL y pegar el enlace de YouTube
- Si un vídeo no descarga, prueba con otra URL (algunos vídeos tienen restricciones)
