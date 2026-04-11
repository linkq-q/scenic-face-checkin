from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers import visitors, tickets

app = FastAPI(
    title="景区人脸核销系统",
    description="基于人脸识别的景区门票核销与游客流量统计系统",
    version="0.1.0",
)

# 静态文件：头像图片
_STORAGE_DIR = Path(__file__).resolve().parents[1] / "storage"
_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_STORAGE_DIR)), name="static")

# 路由注册
app.include_router(visitors.router)
app.include_router(tickets.router)


@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "message": "景区人脸核销系统运行中"}
