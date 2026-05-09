from fastapi import FastAPI, Form, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import uvicorn
import os
import uuid
import time
import glob
import requests
import platform
import traceback
import subprocess

if platform.system() == "Windows":
    DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
else:
    DOWNLOAD_DIR = "/tmp/downloads"

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

def clear_old_files():
    patterns = [
        os.path.join(DOWNLOAD_DIR, "file_*"),
        "file_*.mp4",
        "file_*.mp3"
    ]
    for pattern in patterns:
        for f in glob.glob(pattern):
            try:
                os.remove(f)
            except:
                pass

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    clear_old_files()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/get_trending")
async def get_trending():
    ids = [
        "fbedbdcadebc7273fa7fcae3a7bec09c",
        "ac04fc8d0017f2f4090c8a2f7d177ccf",
        "7fd05a44ee06beb5ca93ef48c4e6d32a",
        "39d8cbcd75d46956d6b1468a99092a56",
        "3e6f641d551d32e5bd9503a8ab352748",
        "36d7548641b3dbacff83c23da170626d",
        "d2ef72b1f6da86c895f4600dd4641fc8",
        "41606614d91a06a0400ee7522a29a702",
        "28beaf4910d912d9a4ad37e218bb2b12",
        "b2e17e8c8bcb49b1eab878e9aace139a",
    ]
    
    ydl_opts = {
        'quiet': True,
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    
    videos = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for vid_id in ids:
            try:
                url = f"https://rutube.ru/video/{vid_id}/"
                info = ydl.extract_info(url, download=False)
                videos.append({
                    "title": (info.get("title") or "Видео")[:60],
                    "thumbnail": info.get("thumbnail", ""),
                    "url": url,
                })
            except:
                pass
    
    return {"videos": videos}

@app.post("/get_formats")
async def get_formats(url: str = Form(...)):
    try:
        ydl_opts = {
            'quiet': True,
            'nocheckcertificate': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            is_vk = any(site in url for site in ["vk.com", "vk.ru", "vkvideo.ru"])
            formats = []

            for f in info.get('formats', []):
                fid = f.get('format_id', '')
                height = f.get('height')
                if is_vk:
                    if fid.startswith('url') and height:
                        formats.append({"id": fid, "res": f"{height}p", "h": height})
                else:
                    vcodec = f.get('vcodec', 'none')
                    acodec = f.get('acodec', 'none')
                    if height and vcodec not in ('none', None) and height >= 144:
                        formats.append({"id": str(height), "res": f"{height}p", "h": height})

            if not formats:
                formats = [
                    {"id": "1080", "res": "1080p", "h": 1080},
                    {"id": "720",  "res": "720p",  "h": 720},
                    {"id": "480",  "res": "480p",  "h": 480},
                    {"id": "360",  "res": "360p",  "h": 360},
                ]

            unique_fmts = {f['res']: f for f in formats}.values()
            sorted_fmts = sorted(unique_fmts, key=lambda x: x['h'], reverse=True)

            return {
                "title": info.get('title'),
                "formats": sorted_fmts,
                "thumbnail": info.get('thumbnail')
            }
    except Exception as e:
        traceback.print_exc()
        return {"error": f"Ошибка парсинга: {str(e)}"}

@app.post("/download")
async def download_video(background_tasks: BackgroundTasks, url: str = Form(...), format_id: str = Form(...), mode: str = Form(...)):
    try:
        is_vk = any(site in url for site in ["vk.com", "vk.ru", "vkvideo.ru"])

        temp_id = uuid.uuid4().hex[:8]
        ext = "mp3" if mode == "audio" else "mp4"
        output_filename = f"file_{temp_id}.{ext}"
        full_path = os.path.join(DOWNLOAD_DIR, output_filename)

        ffmpeg_path = os.path.join(os.getcwd(), "ffmpeg.exe") if platform.system() == "Windows" else "ffmpeg"

        ydl_opts = {
            'outtmpl': full_path,
            'nopart': True,
            'nocheckcertificate': True,
            'quiet': False,
            'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            
        }

        if mode == "audio":
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })

        elif mode == "video_only":
            if is_vk or "rutube.ru" in url:
                ydl_opts.update({
                    'format': 'best' if "rutube.ru" in url else format_id,
                    'merge_output_format': 'mp4',
                })
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                found = glob.glob(os.path.join(DOWNLOAD_DIR, f"file_{temp_id}.*"))
                if not found:
                    return {"error": "Файл не скачался"}

                input_file = found[0]
                silent_file = os.path.join(DOWNLOAD_DIR, f"silent_{temp_id}.mp4")

                subprocess.run([
                    ffmpeg_path, '-i', input_file,
                    '-an', '-c:v', 'copy',
                    silent_file, '-y'
                ], check=True)

                os.remove(input_file)

                background_tasks.add_task(lambda f: (time.sleep(600), os.remove(f) if os.path.exists(f) else None), silent_file)
                return FileResponse(silent_file, filename=f"video_only_{temp_id}.mp4", media_type="video/mp4")
            else:
                ydl_opts.update({
                    'format': f'bestvideo[height<={format_id}]',
                    'postprocessor_args': ['-an', '-c:v', 'libx264', '-pix_fmt', 'yuv420p']
                })

        else:
            if is_vk:
                ydl_opts.update({
                    'format': format_id,
                    'merge_output_format': 'mp4',
                })
            elif "rutube.ru" in url:
                ydl_opts.update({
                    'format': 'best',
                    'merge_output_format': 'mp4',
                })
            else:
                ydl_opts.update({
                    'format': f'bestvideo[height<={format_id}]+bestaudio/best',
                    'merge_output_format': 'mp4',
                    'postprocessor_args': ['-c:v', 'libx264', '-c:a', 'aac', '-pix_fmt', 'yuv420p']
                })

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        actual_file = full_path
        if not os.path.exists(full_path):
            found = glob.glob(os.path.join(DOWNLOAD_DIR, f"file_{temp_id}.*"))
            if found:
                actual_file = found[0]
            else:
                return {"error": "Файл не создался. Проверьте наличие FFmpeg."}

        download_name = f"{mode}_{temp_id}.{ext}"

        background_tasks.add_task(lambda f: (time.sleep(600), os.remove(f) if os.path.exists(f) else None), actual_file)

        return FileResponse(
            actual_file,
            filename=download_name,
            media_type="audio/mpeg" if mode == "audio" else "video/mp4"
        )
    except Exception as e:
        traceback.print_exc()
        return {"error": f"Ошибка: {str(e)}"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
