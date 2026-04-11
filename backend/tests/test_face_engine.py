"""
人脸识别引擎单元测试。

测试说明
--------
① compare_face — 不同人的编码 → 返回 (False, score)
② compare_face — 同一人的编码 → 返回 (True, score > 0.55)
③ extract_encoding — 无人脸图片 → 返回 None，不抛异常

编码来源：
  tests/fixtures/enc_person_a1.npy  -- 人物 A，照片 1
  tests/fixtures/enc_person_a2.npy  -- 人物 A，照片 2（同人，微小扰动）
  tests/fixtures/enc_person_b1.npy  -- 人物 B（不同人）
  tests/fixtures/no_face.jpg        -- 纯色图，无人脸

Fixture 生成方式（已提前执行并提交）：
  rng_a = np.random.default_rng(42); enc_a1 = normalize(rng_a.random(128))
  enc_a2 = normalize(enc_a1 + rng_a.random(128) * 0.05)   # 同人，距离 ~0.17
  rng_b = np.random.default_rng(43); enc_b1 = normalize(rng_b.random(128))  # 距离 ~0.69
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pytest

# 确保从 backend/ 下能找到 app 包
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.face_engine import (
    compare_face,
    encoding_to_str,
    extract_encoding,
    find_match,
    str_to_encoding,
)

FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load(name: str) -> list[float]:
    """从 .npy fixture 加载编码向量。"""
    return np.load(FIXTURES / name).tolist()


# ---------------------------------------------------------------------------
# ① compare_face — 不同人，应返回 False
# ---------------------------------------------------------------------------

class TestCompareFaceDifferentPerson:
    """用人物 A、人物 B 的编码测试 compare_face，预期不匹配。"""

    def test_returns_false(self):
        enc_a = _load("enc_person_a1.npy")
        enc_b = _load("enc_person_b1.npy")
        is_match, score = compare_face(enc_a, enc_b)
        assert is_match is False, f"Expected no match between A and B, got score={score:.4f}"

    def test_score_is_low(self):
        enc_a = _load("enc_person_a1.npy")
        enc_b = _load("enc_person_b1.npy")
        _, score = compare_face(enc_a, enc_b)
        # 不同人距离大 → score 应远低于 0.55
        assert score < 0.55, f"Score too high for different people: {score:.4f}"

    def test_score_is_float(self):
        enc_a = _load("enc_person_a1.npy")
        enc_b = _load("enc_person_b1.npy")
        _, score = compare_face(enc_a, enc_b)
        assert isinstance(score, float)


# ---------------------------------------------------------------------------
# ② compare_face — 同一人，应返回 True 且 score > 0.55
# ---------------------------------------------------------------------------

class TestCompareFaceSamePerson:
    """用同一人的两张编码测试 compare_face，预期匹配且置信度高。"""

    def test_returns_true(self):
        enc_a1 = _load("enc_person_a1.npy")
        enc_a2 = _load("enc_person_a2.npy")
        is_match, score = compare_face(enc_a1, enc_a2)
        assert is_match is True, f"Expected match for same person, got score={score:.4f}"

    def test_score_above_threshold(self):
        enc_a1 = _load("enc_person_a1.npy")
        enc_a2 = _load("enc_person_a2.npy")
        _, score = compare_face(enc_a1, enc_a2)
        assert score > 0.55, f"Score too low for same person: {score:.4f}"

    def test_identical_encoding_perfect_score(self):
        enc = _load("enc_person_a1.npy")
        is_match, score = compare_face(enc, enc)
        assert is_match is True
        assert score > 0.99, f"Identical encodings should have score ~1.0, got {score:.4f}"


# ---------------------------------------------------------------------------
# ③ extract_encoding — 无人脸图片
# ---------------------------------------------------------------------------

class TestExtractEncodingNoFace:
    """对无人脸图片调用 extract_encoding，应返回 None 且不抛异常。"""

    def test_returns_none_for_no_face_image(self):
        no_face_path = str(FIXTURES / "no_face.jpg")
        assert os.path.exists(no_face_path), "Fixture no_face.jpg not found"
        result = extract_encoding(no_face_path)
        assert result is None

    def test_returns_none_for_nonexistent_file(self):
        result = extract_encoding("/tmp/does_not_exist_abc123.jpg")
        assert result is None

    def test_does_not_raise(self):
        """任何情况下都不应向外抛出异常。"""
        try:
            extract_encoding(str(FIXTURES / "no_face.jpg"))
            extract_encoding("/tmp/nonexistent.jpg")
        except Exception as exc:
            pytest.fail(f"extract_encoding raised an exception: {exc}")


# ---------------------------------------------------------------------------
# find_match — 综合测试
# ---------------------------------------------------------------------------

class TestFindMatch:
    def test_finds_correct_visitor(self):
        enc_a1 = _load("enc_person_a1.npy")
        enc_a2 = _load("enc_person_a2.npy")
        enc_b = _load("enc_person_b1.npy")

        candidates = [
            {"visitor_id": 1, "encoding": enc_a1},
            {"visitor_id": 2, "encoding": enc_b},
        ]
        result = find_match(enc_a2, candidates)
        assert result is not None
        assert result["visitor_id"] == 1
        assert result["score"] > 0.55

    def test_returns_none_when_no_match(self):
        enc_a = _load("enc_person_a1.npy")
        enc_b = _load("enc_person_b1.npy")
        # 候选列表里只有 B，但 unknown 是 A 的变体，距离仍然 > 0.45
        # 我们构造一个与 A 差距极大的 encoding
        enc_far = np.zeros(128)
        enc_far[0] = 1.0
        candidates = [{"visitor_id": 99, "encoding": enc_far.tolist()}]
        result = find_match(enc_b, candidates)
        assert result is None

    def test_empty_candidates(self):
        enc = _load("enc_person_a1.npy")
        result = find_match(enc, [])
        assert result is None


# ---------------------------------------------------------------------------
# encoding_to_str / str_to_encoding — 序列化往返
# ---------------------------------------------------------------------------

class TestEncodingSerialization:
    def test_roundtrip(self):
        enc = _load("enc_person_a1.npy")
        s = encoding_to_str(enc)
        assert isinstance(s, str)
        recovered = str_to_encoding(s)
        assert len(recovered) == 128
        assert all(abs(a - b) < 1e-9 for a, b in zip(enc, recovered))

    def test_output_is_valid_json(self):
        import json
        enc = _load("enc_person_a1.npy")
        s = encoding_to_str(enc)
        parsed = json.loads(s)
        assert isinstance(parsed, list)
        assert len(parsed) == 128
