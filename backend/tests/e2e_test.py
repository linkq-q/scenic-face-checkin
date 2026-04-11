"""
端到端测试脚本。

运行方式
--------
    cd backend
    python tests/e2e_test.py

前置条件
--------
- MySQL 已启动，scenic_face 数据库已通过 init_db.py 建表
- backend/.env 中 DB_* 配置正确

测试流程
--------
1. 注册一个游客（mocked 人脸提取，使用 fixtures/enc_person_a1.npy）
2. 为该游客创建今日门票
3. 用相同编码调用核销接口，断言 success=True
4. 再次核销同一张票，断言 reason=already_used
5. 查询今日统计，断言 total_checkins >= 1

说明：人脸提取（extract_encoding）使用 mock，其他全部走真实 DB。
若需测试真实人脸识别，提供真实照片替换 ENCODING_A 并去掉 mock。
"""

from __future__ import annotations

import io
import sys
import time
from datetime import date
from pathlib import Path
from unittest.mock import patch

import numpy as np
from PIL import Image

# 将 backend/ 加入 sys.path，使 app 包可导入
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# ── 测试固件 ────────────────────────────────────────────────────────────────
_FIXTURE_DIR = Path(__file__).parent / "fixtures"
ENCODING_A: list[float] = np.load(_FIXTURE_DIR / "enc_person_a1.npy").tolist()

TODAY: str = date.today().isoformat()
# 每次运行使用唯一手机号，避免重复注册冲突
TEST_PHONE: str = f"138{int(time.time()) % 100_000_000:08d}"


def _make_jpeg_bytes() -> bytes:
    """生成一张纯色 JPEG（作为 face_image 字段上传，实际检测已 mock）。"""
    buf = io.BytesIO()
    Image.new("RGB", (200, 200), (200, 170, 140)).save(buf, "JPEG")
    buf.seek(0)
    return buf.read()


def _reset_matcher_cache() -> None:
    """清空模块级人脸编码缓存，确保测试隔离。"""
    import app.core.matcher as _m
    _m._cache = []
    _m._cache_loaded = False


def _check_db() -> None:
    """检查数据库连通性，失败则打印提示并退出。"""
    try:
        from sqlalchemy import text
        from app.database import engine
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        print(f"\n[ERROR] 数据库连接失败: {exc}")
        print("请确认 MySQL 已启动并已执行 python init_db.py\n")
        sys.exit(1)


# ── 断言辅助 ────────────────────────────────────────────────────────────────
def _assert(cond: bool, msg: str) -> None:
    if not cond:
        print(f"\n[FAIL] {msg}")
        sys.exit(1)


# ── 主测试流程 ───────────────────────────────────────────────────────────────
def run() -> None:
    print("=" * 60)
    print("景区人脸核销系统 — 端到端测试")
    print(f"日期: {TODAY}    测试手机号: {TEST_PHONE}")
    print("=" * 60)

    # 0. 数据库连通性
    _check_db()
    print("[OK] 0. 数据库连接成功")

    _reset_matcher_cache()
    image_bytes = _make_jpeg_bytes()

    with (
        patch("app.routers.visitors.extract_encoding", return_value=ENCODING_A),
        patch("app.routers.checkin.extract_encoding", return_value=ENCODING_A),
    ):
        from fastapi.testclient import TestClient
        from app.main import app

        with TestClient(app) as client:

            # 1. 游客注册 ───────────────────────────────────────────────────���
            resp = client.post(
                "/api/visitors/register",
                data={"name": "E2E测试游客", "phone": TEST_PHONE},
                files={"face_image": ("test.jpg", image_bytes, "image/jpeg")},
            )
            _assert(resp.status_code == 201, f"注册应返回 201，实际 {resp.status_code}: {resp.text}")
            body = resp.json()
            visitor_id: int = body["visitor_id"]
            _assert(body["name"] == "E2E测试游客", f"姓名不符: {body}")
            print(f"[OK] 1. 游客注册成功  visitor_id={visitor_id}")

            # 2. 创建今日门票 ─────────────────────────────────────────────────
            resp = client.post(
                "/api/tickets",
                json={
                    "visitor_id": visitor_id,
                    "scenic_name": "E2E测试景区",
                    "visit_date": TODAY,
                },
            )
            _assert(resp.status_code == 201, f"创建门票应返回 201，实际 {resp.status_code}: {resp.text}")
            body = resp.json()
            ticket_id: int = body["ticket_id"]
            _assert(body["status"] == "unused", f"新票状态应为 unused: {body}")
            print(f"[OK] 2. 门票创建成功  ticket_id={ticket_id}")

            # 3. 首次核销 → success=True ──────────────────────────────────────
            resp = client.post(
                "/api/checkin/verify",
                data={"gate_id": "GATE-E2E"},
                files={"face_image": ("test.jpg", image_bytes, "image/jpeg")},
            )
            _assert(resp.status_code == 200, f"核销应返回 200，实际 {resp.status_code}: {resp.text}")
            body = resp.json()
            _assert(body.get("success") is True, f"首次核销应 success=True: {body}")
            _assert(body["visitor_name"] == "E2E测试游客", f"游客姓名不符: {body}")
            _assert(body["ticket_id"] == ticket_id, f"票 ID 不符: {body}")
            _assert(body["score"] > 0.5, f"匹配度过低: {body}")
            print(
                f"[OK] 3. 核销成功  visitor={body['visitor_name']}"
                f"  ticket={body['ticket_id']}  score={body['score']}"
            )

            # 4. 重复核销 → reason=already_used ──────────────────────────────
            resp = client.post(
                "/api/checkin/verify",
                files={"face_image": ("test.jpg", image_bytes, "image/jpeg")},
            )
            _assert(resp.status_code == 200, f"重复核销应返回 200，实际 {resp.status_code}: {resp.text}")
            body = resp.json()
            _assert(body.get("success") is False, f"重复核销应 success=False: {body}")
            _assert(
                body.get("reason") == "already_used",
                f"应返回 already_used，实际: {body}",
            )
            print(f"[OK] 4. 重复核销正确拒绝  reason={body['reason']}")

            # 5. 今日统计 → total_checkins >= 1 ──────────────────────────────
            resp = client.get(f"/api/stats/daily?date={TODAY}")
            _assert(resp.status_code == 200, f"统计接口应返回 200，实际 {resp.status_code}: {resp.text}")
            body = resp.json()
            _assert(
                body["total_checkins"] >= 1,
                f"today total_checkins 应 >= 1，实际: {body}",
            )
            _assert(isinstance(body["by_hour"], list), f"by_hour 应为列表: {body}")
            print(
                f"[OK] 5. 今日统计正确  total_checkins={body['total_checkins']}"
                f"  by_hour 条数={len(body['by_hour'])}"
            )

    print()
    print("=" * 60)
    print("全部断言通过 ✓")
    print("=" * 60)


if __name__ == "__main__":
    run()
