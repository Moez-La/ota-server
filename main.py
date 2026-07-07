from fastapi import FastAPI, HTTPException, Header, UploadFile, File
from fastapi.responses import FileResponse
from packaging import version as pkg_version
import os, shutil, re

app = FastAPI(title="OTA Server")

API_KEY = os.getenv("API_KEY")
FIRMWARE_PATH = "firmware/gateway-update.swu"
UPLOAD_KEY = os.getenv("UPLOAD_KEY")

os.makedirs("firmware", exist_ok=True)

def get_version_from_swu():
    """Lit la version depuis sw-description dans le .swu (Python pur)"""
    try:
        with open(FIRMWARE_PATH, 'rb') as f:
            content = f.read(16384)  # Premiers 16KB suffisent
        text = content.decode('latin-1', errors='ignore')
        match = re.search(r'version\s*=\s*"([^"]+)"', text)
        if match:
            return match.group(1)
    except:
        pass
    return "0.0.0"

def check_api_key(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

@app.get("/")
def root():
    return {"service": "OTA Server", "status": "running"}

@app.get("/health")
def health():
    firmware_exists = os.path.exists(FIRMWARE_PATH)
    version = get_version_from_swu() if firmware_exists else "none"
    return {
        "status": "ok",
        "firmware_available": firmware_exists,
        "firmware_version": version
    }

@app.get("/version")
def get_version(
    x_api_key: str = Header(None),
    x_current_version: str = Header(None)
):
    check_api_key(x_api_key)

    available = get_version_from_swu()

    if x_current_version:
        try:
            current = pkg_version.parse(x_current_version)
            avail = pkg_version.parse(available)

            if avail < current:
                raise HTTPException(
                    status_code=409,
                    detail=f"Anti-rollback: available {available} older than installed {x_current_version}"
                )
            if avail == current:
                return {
                    "version": available,
                    "update_available": False,
                    "message": "Already up to date"
                }
        except HTTPException:
            raise

    return {
        "version": available,
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
    version = get_version_from_swu()
    return {
        "status": "uploaded",
        "size_mb": round(size/1024/1024, 2),
        "version": version
    }
