#!/usr/bin/env python3
"""Compositor de video REAL para el QA de SIPRE.

Toma:
  - qa_workspace/frames/ : screenshots del navegador capturados durante
    la sesión (cada ~400ms desde el thread grabador de qa_demo.py)
  - qa_workspace/frames_log.json : timestamp relativo (t) de cada frame
  - qa_workspace/audios/*.aiff + say_log.json : narración con timestamps

Genera qa_workspace/qa_video.mp4:
  - Video a FPS constante mostrando los frames en su timestamp real
  - Audio maestro con todas las narraciones puestas en su timestamp de
    disparo (con silencios entre ellas)
"""
import os, sys, json, subprocess, tempfile, shutil, math
PROJ = "/Users/jorgebinkio/Documents/corpofuturo/willy/Presupuesto"
WS = os.path.join(PROJ, "qa_workspace")
FRAMES_LOG = os.path.join(WS, "frames_log.json")
SAY_LOG    = os.path.join(WS, "say_log.json")
OUT = os.path.join(WS, "qa_video.mp4")

if not os.path.isfile(FRAMES_LOG):
    print("Falta frames_log.json. Ejecutá qa_demo.py primero.")
    sys.exit(1)

with open(FRAMES_LOG) as f: frames = json.load(f)
with open(SAY_LOG) as f: says = json.load(f)
frames = [x for x in frames if os.path.isfile(x["path"])]
says = [x for x in says if os.path.isfile(x.get("aiff", ""))]
print(f"Frames: {len(frames)}  Says: {len(says)}")
if not frames:
    print("Sin frames.")
    sys.exit(1)

# Duración total = último timestamp + 2s de colchón
duracion = frames[-1]["t"] + 2.0
print(f"Duración total: {duracion:.1f}s")

# FPS constante para el video
FPS = int(os.environ.get("FPS", "10"))

tmpdir = tempfile.mkdtemp(prefix="qa_video_")
try:
    # ── 1) Video: renderizar cada frame a FPS constante, repitiendo el
    #    último frame disponible cuando no hay uno nuevo ────────────────
    print("Fase 1: montaje del video (concat demuxer)…")
    # Uso el concat demuxer con file+duration entre frames.
    # Duración de cada frame = diferencia con el siguiente (o 0.5s por default).
    listf = os.path.join(tmpdir, "frames_list.txt")
    with open(listf, "w") as f:
        for i, fr in enumerate(frames):
            nxt = frames[i+1]["t"] if i+1 < len(frames) else fr["t"] + 1.0
            dur = max(0.05, nxt - fr["t"])
            f.write(f"file '{fr['path']}'\n")
            f.write(f"duration {dur:.3f}\n")
        # Repetir último frame para cerrar
        f.write(f"file '{frames[-1]['path']}'\n")

    video_only = os.path.join(tmpdir, "video_only.mp4")
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", listf,
        "-vf", f"scale=1600:1000:force_original_aspect_ratio=decrease,pad=1600:1000:(ow-iw)/2:(oh-ih)/2:color=white,fps={FPS}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "24",
        "-r", str(FPS),
        video_only,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        print("video concat error:", r.stderr[-500:])
        sys.exit(1)
    print(f"  video_only.mp4 listo ({os.path.getsize(video_only)/1024/1024:.1f} MB)")

    # ── 2) Audio maestro: pego cada AIFF en su timestamp t ────────────
    print("Fase 2: audio maestro con timestamps…")
    # Estrategia: uso ffmpeg concat con silencios entre narraciones.
    audio_list = os.path.join(tmpdir, "audio_list.txt")
    audio_parts = []
    cursor = 0.0
    for i, s in enumerate(says):
        gap = max(0.0, s["t"] - cursor)
        if gap > 0.03:
            sil = os.path.join(tmpdir, f"sil_{i:04d}.aiff")
            subprocess.run([
                "ffmpeg", "-y", "-loglevel", "error",
                "-f", "lavfi", "-i", f"anullsrc=r=22050:cl=mono",
                "-t", f"{gap:.2f}",
                sil,
            ], capture_output=True, text=True, timeout=60)
            audio_parts.append(sil)
        audio_parts.append(s["aiff"])
        # Obtener duración del AIFF
        try:
            out = subprocess.run([
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", s["aiff"],
            ], capture_output=True, text=True, timeout=10).stdout.strip()
            aiff_dur = float(out)
        except Exception:
            aiff_dur = 3.0
        cursor = s["t"] + aiff_dur

    # Colchón final para alcanzar duración del video
    if cursor < duracion:
        sil = os.path.join(tmpdir, "sil_end.aiff")
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "lavfi", "-i", "anullsrc=r=22050:cl=mono",
            "-t", f"{duracion - cursor:.2f}",
            sil,
        ], capture_output=True, text=True, timeout=60)
        audio_parts.append(sil)

    with open(audio_list, "w") as f:
        for p in audio_parts:
            f.write(f"file '{p}'\n")

    audio_only = os.path.join(tmpdir, "audio_only.m4a")
    r = subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", audio_list,
        "-c:a", "aac", "-b:a", "128k", "-ar", "22050",
        audio_only,
    ], capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        print("audio concat error:", r.stderr[-500:])
        sys.exit(1)
    print(f"  audio_only.m4a listo ({os.path.getsize(audio_only)/1024:.1f} KB)")

    # ── 3) Mux final ───────────────────────────────────────────────────
    print("Fase 3: mux final…")
    r = subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", video_only,
        "-i", audio_only,
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        OUT,
    ], capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        print("mux error:", r.stderr[-500:])
        sys.exit(1)
    size_mb = os.path.getsize(OUT) / 1024 / 1024
    print(f"\n✅ Video final: {OUT}")
    print(f"   tamaño: {size_mb:.1f} MB · frames video: {len(frames)} · duración: {duracion:.1f}s")
finally:
    try: shutil.rmtree(tmpdir)
    except Exception: pass
