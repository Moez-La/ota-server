from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import FileResponse
import os

app = FastAPI(title="OTA Server")

CURRENT_VERSION = "3.0.0"
API_KEY = "moez-ota-secret-key-2026"
FIRMWARE_PATH = "firmware/gateway-update.swu"

def check_api_key(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

@app.get("/")
def root():
    return {"service": "OTA Server", "status": "running"}

@app.get("/version")
def get_version(x_api_key: str = Header(None)):
    check_api_key(x_api_key)
    return {
        "version": CURRENT_VERSION,
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

@app.get("/health")
def health():
    return {"status": "ok"}
