from flask import Blueprint, request, jsonify
from app_utils import validate_payload, queue_task_wrapper
from services.authentication import authenticate
import subprocess
import requests
from tempfile import NamedTemporaryFile
import os
import logging
from urllib.parse import urlparse

v1_media_duration_bp = Blueprint("v1_media_duration_bp", __name__)
logger = logging.getLogger(__name__)

@v1_media_duration_bp.route("/v1/media/media-duration", methods=["POST"])
@authenticate
@validate_payload(
    {
        "type": "object",
        "properties": {
            "media_url": {"type": "string", "format": "uri"},
            "webhook_url": {"type": "string", "format": "uri"},
            "id": {"type": "string"}
        },
        "required": ["media_url"],
        "additionalProperties": False
    }
)
@queue_task_wrapper(bypass_queue=False)
def get_media_duration(job_id, data):
    media_url = data.get("media_url")
    webhook_url = data.get("webhook_url")
    id = data.get("id")

    logger.info(f"Job {job_id}: Received media duration request for {media_url}")

    try:
        response = requests.get(media_url)
        response.raise_for_status()

        # Extract file extension from URL
        parsed_url = urlparse(media_url)
        _, ext = os.path.splitext(parsed_url.path)
        if not ext:
            ext = ".mp3"  # fallback to .mp3 if no extension

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
                error_msg = result.stderr.strip()
                logger.error(f"Job {job_id}: ffprobe error - {error_msg}")
                return error_msg, "/v1/media/media-duration", 500

            duration = float(result.stdout.strip())
            logger.info(f"Job {job_id}: media duration is {duration} seconds")
            return round(duration, 2), "/v1/media/media-duration", 200

    except Exception as e:
        logger.exception(f"Job {job_id}: Exception - {str(e)}")
        return str(e), "/v1/media/media-duration", 500
