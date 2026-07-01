from fastapi import FastAPI, HTTPException, Header, UploadFile, File
from fastapi.responses import FileResponse
from packaging import version as pkg_version
import os
import shutil

app = FastAPI(title="OTA Server")

CURRENT_VERSION = "3.0.0"
API_KEY = "moez-ota-secret-key-2026"
FIRMWARE_PATH = "firmware/gateway-update.swu"
UPLOAD_KEY = "moez-upload-secret-2026"

os.makedirs("firmware", exist_ok=True)

def check_api_key(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

@app.get("/")
def root():
    return {"service": "OTA Server", "status": "running"}

@app.get("/health")
def health():
    firmware_exists = os.path.exists(FIRMWARE_PATH)
    return {"status": "ok", "firmware_available": firmware_exists}

@app.get("/version")
def get_version(
    x_api_key: str = Header(None),
    x_current_version: str = Header(None)
):
    check_api_key(x_api_key)

    if x_current_version:
        try:
            current = pkg_version.parse(x_current_version)
            available = pkg_version.parse(CURRENT_VERSION)

            if available < current:
                raise HTTPException(
                    status_code=409,
                    detail=f"Anti-rollback: available {CURRENT_VERSION} older than installed {x_current_version}"
                )
            if available == current:
                return {
                    "version": CURRENT_VERSION,
                    "update_available": False,
                    "message": "Already up to date"
                }
        except HTTPException:
            raise

    return {
        "version": CURRENT_VERSION,
        "update_available": True,
        "filename": "gateway-update.swu"
    }

@app.get("/firmware")
def download_firmware(x_api_key: str = Header(None)):
    check_api_key(x_api_key)
    if not os.path.exists(FIRMWARE_PATH):
        raise HTTPException(status_code=404, detail="Firmware not found")
    return FileResponse(
        FIRMWARE_PATH,
        media_type="application/octet-stream",
        filename="gateway-update.swu"
    )

@app.post("/upload")
async def upload_firmware(
    file: UploadFile = File(...),
    x_upload_key: str = Header(None)
):
    if x_upload_key != UPLOAD_KEY:
        raise HTTPException(status_code=401, detail="Invalid upload key")
    os.makedirs("firmware", exist_ok=True)
    with open(FIRMWARE_PATH, "wb") as f:
        shutil.copyfileobj(file.file, f)
    size = os.path.getsize(FIRMWARE_PATH)
    return {"status": "uploaded", "size_mb": round(size/1024/1024, 2)}
