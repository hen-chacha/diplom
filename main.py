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
    videos = [
        {"title": "Проблема Вольво оказалась слишком банальной", "thumbnail": "https://pic.rtbcdn.ru/video/2026-05-08/48/34/48349de84176b8c658697a7ed42685d3.jpg", "url": "https://rutube.ru/video/fbedbdcadebc7273fa7fcae3a7bec09c/"},
        {"title": "КАБРИО ЛЕТО. Дороже = лучше? BMW M8, Mercedes", "thumbnail": "https://pic.rtbcdn.ru/video/2026-05-07/f9/97/f9975888741688c242e948269ec21020.jpg", "url": "https://rutube.ru/video/ac04fc8d0017f2f4090c8a2f7d177ccf/"},
        {"title": "«Молокозавод» победил: Инженерное решение", "thumbnail": "https://pic.rtbcdn.ru/video/2026-05-08/c5/91/c591b490553f2af1d1af2fb0acc4304a.jpg", "url": "https://rutube.ru/video/7fd05a44ee06beb5ca93ef48c4e6d32a/"},
        {"title": "Привезли мебель для дачи", "thumbnail": "https://pic.rtbcdn.ru/video/2026-05-07/97/ed/97ed1d307c78d3d9a930e189b578b769.jpg", "url": "https://rutube.ru/video/39d8cbcd75d46956d6b1468a99092a56/"},
        {"title": "Rezvani Vengeance - бронированный внедорожник", "thumbnail": "https://pic.rtbcdn.ru/video/2026-05-05/d0/d7/d0d77060d83a6c4591b574bc0d7a1a32.jpg", "url": "https://rutube.ru/video/3e6f641d551d32e5bd9503a8ab352748/"},
        {"title": "Жизнь на пенсии. Смотрела спортивные соревнования", "thumbnail": "https://pic.rtbcdn.ru/video/2026-05-08/8e/b9/8eb9b39addb15c8b02a3ee270944c935.jpg", "url": "https://rutube.ru/video/36d7548641b3dbacff83c23da170626d/"},
        {"title": "Покупаем саженцы и рассаду. Начинаем высадку", "thumbnail": "https://pic.rtbcdn.ru/video/2026-05-08/4d/bf/4dbfa99cd0fc049d0062a19d5eecd711.jpg", "url": "https://rutube.ru/video/d2ef72b1f6da86c895f4600dd4641fc8/"},
        {"title": "Приехали дети и внуки. Неожиданная помощь", "thumbnail": "https://pic.rtbcdn.ru/video/2026-05-08/d3/01/d3015e571b0296df4968586934708555.jpg", "url": "https://rutube.ru/video/41606614d91a06a0400ee7522a29a702/"},
        {"title": "Volonaut Airbike — ховербайк на реактивной тяге", "thumbnail": "https://pic.rtbcdn.ru/video/2026-05-05/03/e2/03e2c35dbb76c51eb9dcc4790986bf81.jpg", "url": "https://rutube.ru/video/28beaf4910d912d9a4ad37e218bb2b12/"},
        {"title": "Здоровая спина. Как убрать боль в пояснице", "thumbnail": "https://pic.rtbcdn.ru/video/2026-05-06/1c/bb/1cbb13b10853fdf35e4fb3ebe2a7cf66.jpg", "url": "https://rutube.ru/video/b2e17e8c8bcb49b1eab878e9aace139a/"},
    ]
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
                vcodec = f.get('vcodec', 'none')
                if height and vcodec not in ('none', None):
                    res_label = f"{height}p"
                    formats.append({"id": fid, "res": res_label, "h": height})

            if not formats:
                for f in info.get('formats', []):
                    if f.get('acodec') != 'none':
                        formats.append({"id": f.get('format_id', 'bestaudio'), "res": "Audio", "h": 0})

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
        print("--- Проверка FFmpeg перед загрузкой ---")
        os.system("ffmpeg -version")
        is_vk = any(site in url for site in ["vk.com", "vk.ru", "vkvideo.ru"])
        is_rutube = "rutube.ru" in url

        temp_id = uuid.uuid4().hex[:8]
        outtmpl = os.path.join(DOWNLOAD_DIR, f"file_{temp_id}.%(ext)s")

        ydl_opts = {
            'outtmpl': outtmpl,
            'nopart': True,
            'nocheckcertificate': True,
            'quiet': False,
            'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'referer': url,
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
            if is_vk or is_rutube:
                ydl_opts.update({
                    'format': 'best' if is_rutube else format_id,
                    'postprocessor_args': ['-an'],
                })
            else:
                ydl_opts.update({
                    'format': f'bestvideo[height<={format_id}]',
                    'postprocessor_args': ['-an'],
                })

        else:  # Full video
            if is_vk:
                ydl_opts.update({
                    'format': f"{format_id}+bestaudio/best",
                    'merge_output_format': 'mp4',
                    'postprocessor_args': ['-c:v', 'copy', '-c:a', 'aac']
                })
            elif is_rutube:
                ydl_opts.update({
                    'format': 'best',
                    'merge_output_format': 'mp4'
                })
            else:
                ydl_opts.update({
                    'format': f'bestvideo[height<={format_id}]+bestaudio/best',
                    'merge_output_format': 'mp4',
                    'postprocessor_args': ['-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k']
                })

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        found_files = glob.glob(os.path.join(DOWNLOAD_DIR, f"file_{temp_id}.*"))
        actual_files = [f for f in found_files if not f.endswith(('.part', '.ytdl'))]

        if not actual_files:
            return {"error": "Сервер не смог создать файл. Попробуйте другое качество."}

        final_file = actual_files[0]

        if final_file.endswith(".mp3"):
            m_type = "audio/mpeg"
        else:
            m_type = "video/mp4"

        download_name = f"{mode}_{temp_id}{os.path.splitext(final_file)[1]}"

        background_tasks.add_task(lambda f: (time.sleep(600), os.remove(f) if os.path.exists(f) else None), final_file)

        return FileResponse(
            final_file,
            filename=download_name,
            media_type=m_type
        )

    except Exception as e:
        traceback.print_exc()
        return {"error": f"Ошибка сервера: {str(e)}"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
