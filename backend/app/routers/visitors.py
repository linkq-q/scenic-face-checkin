import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, Form, File
from sqlalchemy.orm import Session

from app import crud
from app.core.face_engine import encoding_to_str, extract_encoding
from app.core.matcher import push_to_cache
from app.core.storage import save_avatar_from_bytes
from app.database import get_db
from app.schemas.visitor import VisitorDetail, VisitorRegisterResponse

router = APIRouter(prefix="/api/visitors", tags=["visitors"])


@router.post("/register", response_model=VisitorRegisterResponse, status_code=201)
async def register_visitor(
    request: Request,
    name: str = Form(...),
    phone: str = Form(...),
    face_image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # 检查手机号是否已注册
    if crud.visitor.get_by_phone(db, phone):
        raise HTTPException(status_code=409, detail="该手机号已注册")

    # 读取图片字节
    image_bytes = await face_image.read()

    # 写临时文件以便 face_recognition 读取
    suffix = Path(face_image.filename or "upload.jpg").suffix or ".jpg"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(image_bytes)
        tmp_path = tmp.name

    try:
        encoding = extract_encoding(tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    if encoding is None:
        raise HTTPException(
            status_code=422,
            detail="未在上传图片中检测到人脸，请上传清晰的正面照片",
        )

    # 先创建游客记录以获取 visitor_id
    visitor = crud.visitor.create(db, name=name, phone=phone)

    # 保存头像并更新编码
    avatar_path = save_avatar_from_bytes(visitor.id, image_bytes)
    crud.visitor.update_face(
        db, visitor, encoding_to_str(encoding), avatar_path
    )

    # 实时更新内存缓存，让新游客立即可被识别
    push_to_cache(visitor.id, encoding)

    return VisitorRegisterResponse(
        visitor_id=visitor.id,
        name=visitor.name,
        message="注册成功",
    )


@router.get("/{visitor_id}", response_model=VisitorDetail)
def get_visitor(visitor_id: int, request: Request, db: Session = Depends(get_db)):
    visitor = crud.visitor.get_by_id(db, visitor_id)
    if visitor is None:
        raise HTTPException(status_code=404, detail="游客不存在")

    avatar_url: str | None = None
    if visitor.avatar_path:
        avatar_url = str(request.base_url) + f"static/avatars/{visitor.id}.jpg"

    return VisitorDetail(
        id=visitor.id,
        name=visitor.name,
        phone=visitor.phone,
        avatar_url=avatar_url,
        created_at=visitor.created_at,
    )
