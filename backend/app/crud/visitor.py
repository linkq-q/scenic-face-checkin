from sqlalchemy.orm import Session

from app.models.visitor import Visitor


def get_by_id(db: Session, visitor_id: int) -> Visitor | None:
    return db.get(Visitor, visitor_id)


def get_by_phone(db: Session, phone: str) -> Visitor | None:
    return db.query(Visitor).filter(Visitor.phone == phone).first()


def create(
    db: Session,
    name: str,
    phone: str,
    face_encoding: str | None = None,
    avatar_path: str | None = None,
) -> Visitor:
    visitor = Visitor(
        name=name,
        phone=phone,
        face_encoding=face_encoding,
        avatar_path=avatar_path,
    )
    db.add(visitor)
    db.commit()
    db.refresh(visitor)
    return visitor


def update_face(
    db: Session,
    visitor: Visitor,
    face_encoding: str,
    avatar_path: str,
) -> Visitor:
    visitor.face_encoding = face_encoding
    visitor.avatar_path = avatar_path
    db.commit()
    db.refresh(visitor)
    return visitor


def get_all_with_encoding(db: Session) -> list[Visitor]:
    """返回所有已注册人脸编码的游客（用于人脸比对）。"""
    return (
        db.query(Visitor)
        .filter(Visitor.face_encoding.isnot(None))
        .all()
    )
