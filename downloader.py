import os
import yt_dlp
from config import DOWNLOADS_DIR

os.makedirs(DOWNLOADS_DIR, exist_ok=True)

YDL_OPTS = {
    "format": "bestaudio/best",
    "outtmpl": f"{DOWNLOADS_DIR}/%(id)s.%(ext)s",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }
    ],
}


def search_and_download(query: str) -> dict:
    """
    Searches YouTube for the query and downloads the best match's audio.
    Returns: {"title": str, "path": str, "duration": int}
    """
    search_query = query if query.startswith("http") else f"ytsearch1:{query}"

    with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
        info = ydl.extract_info(search_query, download=True)

        # ytsearch wraps the result inside "entries"
        if "entries" in info:
            info = info["entries"][0]

        file_path = ydl.prepare_filename(info)
        # the extension changes after the mp3 postprocessing step
        file_path = os.path.splitext(file_path)[0] + ".mp3"

        return {
            "title": info.get("title", "Unknown"),
            "path": file_path,
            "duration": info.get("duration", 0),
        }
