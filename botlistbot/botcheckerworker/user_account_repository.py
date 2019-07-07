import os
from pathlib import Path
from logzero import logger as log

from decouple import config
from minio import Minio

import appglobals

BUCKET_NAME = "useraccounts"

client = Minio(
    config('MINIO_URL'),
    access_key=config('MINIO_ACCESS_KEY'),
    secret_key=config('MINIO_SECRET_KEY'),
    secure=True)

if not client.bucket_exists(BUCKET_NAME):
    raise RuntimeError(f"Bucket {BUCKET_NAME} does not exist.")


def download_session(session_name: str, output_path: Path) -> str:
    session_name = session_name.replace(".session", "") + ".session"
    session = client.get_object(BUCKET_NAME, session_name)
    out_path = str(output_path / session_name)
    with open(out_path, 'wb') as file_data:
        for d in session.stream(32 * 1024):
            file_data.write(d)
    log.info(f"Downloaded session '{session_name}' to '{output_path}'.")
    return out_path


accounts_path = Path(appglobals.ROOT_DIR) / "accounts"
os.makedirs(accounts_path, exist_ok=True)
