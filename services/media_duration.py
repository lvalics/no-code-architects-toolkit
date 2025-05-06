import requests
import subprocess
from tempfile import NamedTemporaryFile
import os
from urllib.parse import urlparse

def get_media_duration_from_url(media_url):
    response = requests.get(media_url)
    response.raise_for_status()
    parsed_url = urlparse(media_url)
    _, ext = os.path.splitext(parsed_url.path)
    if not ext:
        ext = ".mp3"
    with NamedTemporaryFile(suffix=ext) as tmp:
        tmp.write(response.content)
        tmp.flush()
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            tmp.name
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(result.stderr.strip())
        duration = float(result.stdout.strip())
        return round(duration, 2)
