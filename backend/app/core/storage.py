"""
图片文件读写工具。

约定：游客头像统一存储到 backend/storage/avatars/{visitor_id}.jpg
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import cv2
import numpy as np

# 默认存储根目录：backend/storage/
_DEFAULT_STORAGE_ROOT = Path(__file__).resolve().parents[2] / "storage"


def get_avatar_path(visitor_id: int, storage_root: Path | None = None) -> Path:
    """返回游客头像的完整文件路径（不保证文件存在）。"""
    root = storage_root or _DEFAULT_STORAGE_ROOT
    return root / "avatars" / f"{visitor_id}.jpg"


def save_avatar(
    visitor_id: int,
    source_path: str,
    storage_root: Path | None = None,
) -> str:
    """
    将 source_path 的图片复制/转存为游客头像。

    Args:
        visitor_id:   游客 ID，决定存储文件名。
        source_path:  原始图片路径。
        storage_root: 自定义存储根目录，默认为 backend/storage/。

    Returns:
        保存后的文件路径字符串。
    """
    dest = get_avatar_path(visitor_id, storage_root)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, dest)
    return str(dest)


def save_avatar_from_bytes(
    visitor_id: int,
    image_bytes: bytes,
    storage_root: Path | None = None,
) -> str:
    """
    将内存中的图片字节流保存为游客头像（JPEG 格式）。

    Args:
        visitor_id:   游客 ID。
        image_bytes:  图片二进制内容。
        storage_root: 自定义存储根目录。

    Returns:
        保存后的文件路径字符串。
    """
    dest = get_avatar_path(visitor_id, storage_root)
    dest.parent.mkdir(parents=True, exist_ok=True)

    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Cannot decode image bytes")
    cv2.imwrite(str(dest), img, [cv2.IMWRITE_JPEG_QUALITY, 95])
    return str(dest)


def avatar_exists(visitor_id: int, storage_root: Path | None = None) -> bool:
    """检查游客头像文件是否存在。"""
    return get_avatar_path(visitor_id, storage_root).exists()


def delete_avatar(visitor_id: int, storage_root: Path | None = None) -> bool:
    """删除游客头像文件，返回是否成功删除。"""
    path = get_avatar_path(visitor_id, storage_root)
    if path.exists():
        os.remove(path)
        return True
    return False
