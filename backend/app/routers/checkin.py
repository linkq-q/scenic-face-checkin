import tempfile
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.core.face_engine import extract_encoding
from app.core.matcher import get_match
from app.crud import checkin as checkin_crud
from app.crud import ticket as ticket_crud
from app.database import get_db

router = APIRouter(prefix="/api/checkin", tags=["checkin"])


@router.post("/verify")
async def verify_checkin(
    face_image: UploadFile = File(...),
    gate_id: str | None = Form(default=None),
    visit_date: date = Form(default_factory=date.today),
    db: Session = Depends(get_db),
):
    # 1. 读取图片并提取人脸向量
    image_bytes = await face_image.read()
    suffix = Path(face_image.filename or "upload.jpg").suffix or ".jpg"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(image_bytes)
        tmp_path = tmp.name

    try:
        encoding = extract_encoding(tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    if encoding is None:
        return {"success": False, "reason": "no_face"}

    # 2. 从缓存中找最佳匹配游客
    match = get_match(encoding, db)
    if match is None:
        return {"success": False, "reason": "no_match"}

    visitor_id: int = match["visitor_id"]
    score: float = match["score"]

    # 3. 检查门票状态
    unused_ticket = checkin_crud.get_unused_ticket(db, visitor_id, visit_date)

    if unused_ticket is None:
        # 判断是已核销还是根本没票
        if checkin_crud.has_used_ticket(db, visitor_id, visit_date):
            return {"success": False, "reason": "already_used"}
        return {"success": False, "reason": "no_valid_ticket"}

    # 4. 核销：将门票改为 used
    ticket_crud.update_status(db, unused_ticket, "used")

    # 5. 写 checkin_logs
    log = checkin_crud.create_log(
        db,
        ticket_id=unused_ticket.id,
        visitor_id=visitor_id,
        gate_id=gate_id,
        match_score=score,
    )

    # 6. 查游客姓名
    from app.crud import visitor as visitor_crud
    visitor = visitor_crud.get_by_id(db, visitor_id)

    return {
        "success": True,
        "visitor_name": visitor.name if visitor else "未知",
        "ticket_id": unused_ticket.id,
        "score": round(score, 4),
        "checked_at": log.checked_at.isoformat(),
    }
