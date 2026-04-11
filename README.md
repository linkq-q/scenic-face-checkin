# scenic-face-checkin

基于人脸识别的景区门票核销与游客流量统计系统。

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python 3.11 · FastAPI · SQLAlchemy 2 · face_recognition (Dlib) · OpenCV |
| 数据库 | MySQL 8 · utf8mb4 |
| 前端 | Vue 3 · Vite 5 · Element Plus · ECharts |

## 环境要求

- Python 3.11+
- Node.js 18+
- MySQL 8+
- CMake（编译 dlib 时需要，通常已预装）

## 安装步骤

### 1. 克隆仓库

```bash
git clone <repo-url>
cd scenic-face-checkin
```

### 2. 后端依赖

```bash
cd backend
pip install -r requirements.txt
```

> **注意**：`face-recognition-models` 在部分系统上因 setuptools 版本问题无法直接构建 wheel。
> 若遇到此问题，执行：
> ```bash
> pip download face-recognition-models==0.3.0 -d /tmp/frm/
> tar -xf /tmp/frm/face_recognition_models-0.3.0.tar.gz -C /tmp/
> cp -r /tmp/face_recognition_models-0.3.0/face_recognition_models \
>       $(python -c "import site; print(site.getsitepackages()[0])")/
> pip install face_recognition==1.3.0 --no-deps
> ```

### 3. 配置数据库

```bash
cp .env.example .env
# 编辑 .env，填入 MySQL 连接信息
```

`.env` 示例：

```dotenv
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=yourpassword
DB_NAME=scenic_face
```

### 4. 初始化数据库

```bash
# 在 backend/ 目录下执行
python init_db.py
```

输出示例：
```
[OK] 数据库 `scenic_face` 已就绪
[OK] 数据表创建完成：visitors, tickets, checkin_logs
[OK] 当前库中的表：['checkin_logs', 'tickets', 'visitors']
```

### 5. 前端依赖

```bash
cd ../frontend
npm install
```

## 启动

### 后端

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问 API 文档：<http://localhost:8000/docs>

### 前端

```bash
cd frontend
npm run dev
```

访问管理界面：<http://localhost:5173>

## 项目结构

```
scenic-face-checkin/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py          # 读取 .env 配置
│   │   │   ├── face_engine.py     # 人脸识别核心（extract/compare/match）
│   │   │   ├── matcher.py         # 内存编码缓存 + 批量匹配
│   │   │   └── storage.py         # 头像文件读写
│   │   ├── crud/                  # 数据库操作函数
│   │   ├── models/                # SQLAlchemy ORM 模型
│   │   ├── routers/               # FastAPI 路由
│   │   ├── schemas/               # Pydantic 请求/响应模型
│   │   ├── database.py            # 引擎、Session、Base
│   │   └── main.py                # FastAPI 入口
│   ├── storage/avatars/           # 游客头像存储目录（运行时创建）
│   ├── tests/
│   │   ├── fixtures/              # 测试用人脸编码 .npy 文件
│   │   ├── test_face_engine.py    # 人脸引擎单元测试
│   │   └── e2e_test.py            # 端到端集成测试
│   ├── .env.example
│   ├── init_db.py                 # 一键建库建表脚本
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── views/
    │   │   ├── RegisterView.vue   # 游客注册
    │   │   ├── TicketView.vue     # 门票管理
    │   │   ├── CheckinView.vue    # 入园核销
    │   │   └── StatsView.vue      # 客流统计
    │   ├── api/index.js           # axios 封装
    │   ├── router/index.js        # Vue Router
    │   └── App.vue                # 侧边栏布局
    ├── package.json
    └── vite.config.js
```

## API 接口速查

### 游客

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/visitors/register` | 注册游客（multipart：name, phone, face_image） |
| GET  | `/api/visitors/{id}` | 查询游客详情 |

### 门票

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/tickets` | 创建门票（JSON：visitor_id, scenic_name, visit_date） |
| GET  | `/api/tickets` | 查询门票列表（query: visitor_id?, date?, status?） |
| GET  | `/api/tickets/{id}` | 查询门票详情（含游客姓名） |

### 核销

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/checkin/verify` | 人脸核销（multipart：face_image, gate_id?, visit_date?） |

核销返回值：

```json
// 成功
{ "success": true, "visitor_name": "张三", "ticket_id": 1, "score": 0.87, "checked_at": "..." }

// 失败
{ "success": false, "reason": "no_face|no_match|no_valid_ticket|already_used" }
```

### 统计

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/stats/daily?date=YYYY-MM-DD` | 按小时统计指定日期核销量 |
| GET | `/api/stats/range?start=&end=` | 按日汇总区间核销量 |
| GET | `/api/stats/realtime` | 今日总量 / 近1小时 / 最后核销时间 |

### 静态资源

| 路径 | 说明 |
|------|------|
| `GET /storage/avatars/{visitor_id}.jpg` | 游客头像 |
| `GET /docs` | FastAPI Swagger 文档 |

## 运行测试

### 单元测试（无需数据库）

```bash
cd backend
python -m pytest tests/test_face_engine.py -v
```

### 端到端测试（需要 MySQL）

```bash
cd backend
python tests/e2e_test.py
```

> 端到端测试会向数据库写入真实数据（`E2E测试游客`），执行完毕后可在前端 StatsView 页面看到今日核销数据更新。
