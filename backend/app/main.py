from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import visitors, tickets, checkin, stats

_STORAGE_DIR = Path(__file__).resolve().parents[1] / "storage"
_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时预热人脸编码缓存
    from app.core.matcher import build_cache
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        build_cache(db)
    except Exception:
        # 数据库未就绪（如测试环境）时跳过，不阻断启动
        pass
    finally:
        db.close()
    yield


app = FastAPI(
    title="景区人脸核销系统",
    description="基于人脸识别的景区门票核销与游客流量统计系统",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS：允许 Vue 开发服务器跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务（头像存储目录）
app.mount("/storage", StaticFiles(directory=str(_STORAGE_DIR)), name="storage")

# 路由注册
app.include_router(visitors.router)
app.include_router(tickets.router)
app.include_router(checkin.router)
app.include_router(stats.router)


@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "message": "景区人脸核销系统运行中"}
