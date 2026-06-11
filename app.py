"""
Descargador YouTube - Para hosting Ionos (PHP/Python)
Requiere Python 3.10+ y yt-dlp instalado en el servidor
"""

import os, re, uuid, threading, time
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory

try:
    import yt_dlp
except ImportError:
    raise SystemExit("Instala yt-dlp: pip install yt-dlp")

app = Flask(__name__)

DOWNLOAD_DIR = Path(__file__).parent / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)

# Borrar archivos de más de 1 hora automáticamente
def limpiar_viejos():
    while True:
        time.sleep(600)
        ahora = time.time()
        for f in DOWNLOAD_DIR.glob("*"):
            if ahora - f.stat().st_mtime > 3600:
                try: f.unlink()
                except: pass

threading.Thread(target=limpiar_viejos, daemon=True).start()

# Estado en memoria: { job_id: {...} }
jobs = {}
lock = threading.Lock()


def hacer_descarga(job_id, url, modo):
    plantilla = str(DOWNLOAD_DIR / f"{job_id}_%(title)s.%(ext)s")

    def hook(d):
        with lock:
            if d["status"] == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                if total:
                    pct = round(d["downloaded_bytes"] / total * 100, 1)
                    jobs[job_id]["pct"] = pct
                    v = d.get("speed")
                    jobs[job_id]["vel"] = f"{v/1024/1024:.1f} MB/s" if v else ""
            elif d["status"] == "finished":
                jobs[job_id]["pct"] = 99
                jobs[job_id]["fase"] = "procesando"

    opts = {
        "outtmpl": plantilla,
        "progress_hooks": [hook],
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        # Simular navegador para evitar bloqueos de bot
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            )
        },
        "extractor_args": {"youtube": {"player_client": ["web", "android"]}},
        "socket_timeout": 30,
    }

    if modo == "mp3":
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
    elif modo == "720":
        opts["format"] = "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[height<=720]"
        opts["merge_output_format"] = "mp4"
    elif modo == "1080":
        opts["format"] = "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best[height<=1080]"
        opts["merge_output_format"] = "mp4"
    else:  # best
        opts["format"] = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
        opts["merge_output_format"] = "mp4"

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)

        archivos = sorted(DOWNLOAD_DIR.glob(f"{job_id}_*"), key=lambda f: f.stat().st_mtime)
        if not archivos:
            raise FileNotFoundError("Archivo no encontrado tras la descarga")

        archivo = archivos[-1]
        with lock:
            jobs[job_id].update({
                "fase": "done",
                "pct": 100,
                "archivo": archivo.name,
                "titulo": info.get("title", archivo.stem),
                "duracion": info.get("duration_string", ""),
                "miniatura": info.get("thumbnail", ""),
            })
    except Exception as e:
        with lock:
            jobs[job_id]["fase"] = "error"
            jobs[job_id]["error"] = str(e)[:500]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/start", methods=["POST"])
def start():
    data = request.get_json(silent=True) or {}
    url  = (data.get("url") or "").strip()
    modo = data.get("modo", "best")

    if not url or "youtube.com" not in url and "youtu.be" not in url:
        return jsonify({"ok": False, "error": "URL de YouTube no válida"}), 400

    jid = uuid.uuid4().hex
    with lock:
        jobs[jid] = {"fase": "descargando", "pct": 0, "vel": ""}

    threading.Thread(target=hacer_descarga, args=(jid, url, modo), daemon=True).start()
    return jsonify({"ok": True, "job": jid})


@app.route("/api/estado/<jid>")
def estado(jid):
    with lock:
        j = dict(jobs.get(jid, {}))
    if not j:
        return jsonify({"fase": "error", "error": "Job no encontrado"}), 404
    return jsonify(j)


@app.route("/api/archivo/<nombre>")
def archivo(nombre):
    nombre = Path(nombre).name  # seguridad
    return send_from_directory(DOWNLOAD_DIR, nombre, as_attachment=True)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
