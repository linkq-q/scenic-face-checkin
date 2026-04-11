from fastapi import FastAPI

app = FastAPI(
    title="景区人脸核销系统",
    description="基于人脸识别的景区门票核销与游客流量统计系统",
    version="0.1.0",
)


@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "message": "景区人脸核销系统运行中"}
