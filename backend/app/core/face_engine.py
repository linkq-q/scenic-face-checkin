"""
人脸识别引擎。

提供以下功能：
- extract_encoding  从图片文件中提取 128 维人脸特征向量
- compare_face      比对两个向量是否属于同一人
- find_match        在候选列表里找出最相似的游客
- encoding_to_str   向量 → JSON 字符串（存库序列化）
- str_to_encoding   JSON 字符串 → 向量（读库反序列化）
"""

from __future__ import annotations

import json
import logging

import face_recognition
import numpy as np

logger = logging.getLogger(__name__)


def extract_encoding(image_path: str) -> list[float] | None:
    """
    读取图片，检测第一张人脸并返回 128 维特征向量。

    Args:
        image_path: 图片文件的绝对/相对路径（支持 jpg、png 等格式）。

    Returns:
        128 个 float 组成的列表；若图片中未检测到人脸则返回 None。
    """
    try:
        image = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(image)
        if not encodings:
            logger.debug("No face detected in %s", image_path)
            return None
        return encodings[0].tolist()
    except Exception:
        logger.exception("Failed to extract encoding from %s", image_path)
        return None


def compare_face(
    known_encoding: list[float],
    unknown_encoding: list[float],
    tolerance: float = 0.45,
) -> tuple[bool, float]:
    """
    比对两个 128 维向量是否属于同一人。

    Args:
        known_encoding:   已知人脸的特征向量。
        unknown_encoding: 待识别人脸的特征向量。
        tolerance:        欧式距离阈值，默认 0.45（严格模式）。

    Returns:
        (is_match, score) — score = 1 - distance，越高越相似。
    """
    known_np = np.array(known_encoding)
    unknown_np = np.array(unknown_encoding)

    distance: float = float(face_recognition.face_distance([known_np], unknown_np)[0])
    is_match: bool = distance <= tolerance
    score: float = round(1.0 - distance, 6)
    return is_match, score


def find_match(
    unknown_encoding: list[float],
    candidates: list[dict],
) -> dict | None:
    """
    在候选列表中找出与 unknown_encoding 最相似的一条记录。

    Args:
        unknown_encoding: 待识别人脸的 128 维向量。
        candidates: 候选列表，每条格式为
                    {"visitor_id": int, "encoding": list[float]}

    Returns:
        匹配成功时返回 {"visitor_id": int, "score": float}；
        无匹配时返回 None。
    """
    if not candidates:
        return None

    known_encodings = [np.array(c["encoding"]) for c in candidates]
    unknown_np = np.array(unknown_encoding)

    distances = face_recognition.face_distance(known_encodings, unknown_np)
    best_idx = int(np.argmin(distances))
    best_distance = float(distances[best_idx])

    # 使用与 compare_face 相同的阈值
    if best_distance > 0.45:
        return None

    return {
        "visitor_id": candidates[best_idx]["visitor_id"],
        "score": round(1.0 - best_distance, 6),
    }


def encoding_to_str(encoding: list[float]) -> str:
    """将 128 维向量序列化为 JSON 字符串，用于存入数据库。"""
    return json.dumps(encoding)


def str_to_encoding(s: str) -> list[float]:
    """将数据库中存储的 JSON 字符串反序列化为向量列表。"""
    return json.loads(s)
