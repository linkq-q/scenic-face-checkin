"""
编码缓存与批量匹配层。

策略：
- 模块级变量 _cache 在首次使用时从 DB 加载（惰性初始化）。
- 注册新游客后，调用 push_to_cache 追加条目，无需重建整个缓存。
- 缓存仅存 visitor_id + encoding（list[float]），不存其他字段。
"""

from __future__ import annotations

import logging
import threading

from sqlalchemy.orm import Session

from app.core.face_engine import find_match, str_to_encoding

logger = logging.getLogger(__name__)

# 模块级缓存，线程安全写入
_cache: list[dict] = []   # [{visitor_id: int, encoding: list[float]}]
_cache_lock = threading.Lock()
_cache_loaded = False


def build_cache(db: Session) -> None:
    """从数据库全量加载人脸编码，覆盖现有缓存。"""
    global _cache, _cache_loaded
    from app.crud.visitor import get_all_with_encoding

    visitors = get_all_with_encoding(db)
    new_cache = []
    for v in visitors:
        try:
            enc = str_to_encoding(v.face_encoding)
            new_cache.append({"visitor_id": v.id, "encoding": enc})
        except Exception:
            logger.warning("Failed to parse encoding for visitor %d", v.id)

    with _cache_lock:
        _cache = new_cache
        _cache_loaded = True

    logger.info("[matcher] cache built: %d visitors loaded", len(_cache))
    if len(_cache) == 0:
        logger.warning("[matcher] cache is empty — no visitors with face_encoding found in DB")


def push_to_cache(visitor_id: int, encoding: list[float]) -> None:
    """注册新游客后追加/更新缓存，不影响已有条目。"""
    with _cache_lock:
        # 若已存在则覆盖（重新注册场景）
        for entry in _cache:
            if entry["visitor_id"] == visitor_id:
                entry["encoding"] = encoding
                return
        _cache.append({"visitor_id": visitor_id, "encoding": encoding})


def get_match(
    unknown_encoding: list[float],
    db: Session,
) -> dict | None:
    """
    在缓存中为 unknown_encoding 寻找最佳匹配。

    首次调用时若缓存为空，自动从 DB 初始化。

    Returns:
        {"visitor_id": int, "score": float} 或 None。
    """
    global _cache_loaded
    if not _cache_loaded:
        build_cache(db)

    with _cache_lock:
        snapshot = list(_cache)

    return find_match(unknown_encoding, snapshot)
