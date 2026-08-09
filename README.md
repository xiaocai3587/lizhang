# 礼账 Lizhang v2

> 一套面向中国式人情往来的个人礼账管理系统 —— 记录谁给我随了礼、我给谁随了礼、什么时候该回礼、回多少。

中国式人情社会里，婚丧嫁娶、满月升学，礼金往来错综复杂。本系统把"账本"和"关系图谱"结合在一起，让每一笔礼金都有迹可循，让该回的礼不会被遗忘。

---

## 目录

- [核心特性](#核心特性)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [Docker 一键部署](#docker-一键部署)
- [数据模型](#数据模型)
- [功能详解与使用案例](#功能详解与使用案例)
- [API 参考](#api-参考)
- [常见问题](#常见问题)
- [许可](#许可)

---

## 核心特性

| 模块 | 能力 |
|------|------|
| 📊 仪表盘 | 统计概览、最近事件、回礼建议、月度趋势、往来 TOP 榜 |
| 👥 人物管理 | 三大分组（自家 / 老婆家 / 朋友），支持小名、称谓、出生年、礼金状态 |
| 🎁 礼金往来 | 一笔礼金可拆分多个随礼人 / 多个收礼人，支持共同随礼 |
| 📅 事件管理 | 按 received（收礼）/ given（出礼）分类记录红白事 |
| 🌳 家族图谱 | 自动推算称谓（爸妈/姑舅/堂表/侄甥…），按父系母系分左右可视化 |
| 💡 回礼建议 | 基于"对方最近一次礼金 × (1+3%)^年数"算法，只显示净欠 > 0 的人 |
| 📥 数据导入导出 | CSV 四表互导，支持备份与迁移 |
| 🎨 主题 | 亮色 / 暗色主题切换 |

---

## 技术栈

**后端**
- Python 3.10+
- FastAPI 0.110+（异步 Web 框架）
- SQLAlchemy 2.0+（ORM）
- SQLite（开箱即用，零配置）
- Pydantic v2（数据校验）
- Pandas（CSV 处理）

**前端**
- Vue 3.5+（Composition API + `<script setup>`）
- TypeScript 5.6+
- Element Plus 2.8+（UI 组件库）
- Vite 5.4+（构建工具）
- Vue Router 4 + Pinia 2（路由与状态）
- @antv/g6 5.0（关系图谱渲染）

**部署**
- Docker + Docker Compose
- Nginx（前端静态资源 + API 反代）

---

## 项目结构

```
lizhang-v2/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── config.py            # 配置（DATABASE_URL / CORS）
│   │   ├── database.py          # SQLAlchemy 引擎与建表
│   │   ├── models.py            # 5 张表 ORM 定义
│   │   ├── schemas.py           # Pydantic 模型
│   │   ├── routers/
│   │   │   ├── persons.py       # 人物 CRUD + 统计
│   │   │   ├── events.py        # 事件 CRUD
│   │   │   ├── gifts.py         # 礼金 CRUD
│   │   │   ├── relations.py     # 关系 CRUD
│   │   │   ├── graph.py         # 家族/朋友图谱数据
│   │   │   ├── stats.py         # 仪表盘 + 回礼建议
│   │   │   └── data.py          # CSV 导入导出
│   │   └── services/
│   │       ├── kinship.py       # 称谓推算引擎（核心算法）
│   │       ├── suggestion.py    # 回礼建议算法
│   │       ├── family_tree.py   # 家族树构建
│   │       ├── friend_graph.py  # 朋友图谱构建
│   │       └── csv_io.py        # CSV 读写
│   ├── data/                    # SQLite 数据库（.gitignore 忽略）
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── views/               # 9 个页面（仪表盘/人物/事件/礼金/图谱/设置）
│   │   ├── components/graph/    # FamilyTree / FriendGraph 组件
│   │   ├── api/                 # axios 封装
│   │   ├── stores/              # Pinia 状态
│   │   ├── types/               # TypeScript 类型
│   │   ├── utils/format.ts      # 格式化工具
│   │   └── styles/              # CSS 变量 + 全局样式
│   ├── Dockerfile
│   ├── nginx.conf
│   └── vite.config.ts
└── docker-compose.yml
```

---

## 快速开始

### 环境要求

- Python ≥ 3.10
- Node.js ≥ 18
- npm ≥ 9

### 1. 启动后端

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -r requirements.txt

# 启动（开发模式，热重载）
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

后端启动后：
- API 服务：http://localhost:8000
- 交互文档（Swagger）：http://localhost:8000/docs
- 首次启动自动建库建表（`backend/data/lizhang.db`）

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端访问：http://localhost:5173

> Vite 已配置代理，`/api` 请求自动转发到 `http://localhost:8000`，前后端联调零配置。

### 3. 开始使用

1. 进入【人物】页面，新建"我"和"老婆"两个账号（勾选"是我"标记本人）
2. 添加父母、岳父母、亲戚朋友
3. 进入【事件】页面，新建事件（如"我和XX结婚"，角色选"收礼"）
4. 在事件详情里逐笔录入礼金
5. 回到【仪表盘】，查看统计与回礼建议

---

## Docker 一键部署

最简单的部署方式，适合 NAS / 云服务器：

```bash
git clone https://github.com/xiaocai3587/lizhang.git
cd lizhang
docker-compose up -d --build
```

启动后：
- 前端：http://your-server-ip
- 后端 API：http://your-server-ip:8000（仅用于调试，生产可关闭）

数据持久化在 Docker volume `lizhang-data` 中，升级镜像不丢数据。

---

## 数据模型

系统共 5 张表，关系如下：

```
┌──────────┐       ┌──────────┐
│  Person  │◀──────│ Relation │（亲子/配偶/兄弟姐妹）
│  人物    │       │  关系    │
└────┬─────┘       └──────────┘
     │
     │ 1:N
     ▼
┌──────────────┐       ┌────────┐
│GiftParticipant│──────▶│  Gift  │──▶┌────────┐
│ 礼金参与者    │ role  │ 礼金   │   │ Event  │
│(giver/receiver)│      │        │   │ 事件   │
└──────────────┘       └────────┘   └────────┘
```

| 表 | 关键字段 | 说明 |
|----|---------|------|
| `persons` | `name` / `nickname` / `group` / `is_self` / `title` / `gift_status` | 礼金状态：`normal`/`excluded`（已平账/不来往） |
| `relations` | `from_id` / `to_id` / `type` | `parent_child` / `spouse` / `sibling` |
| `events` | `title` / `date` / `role` | `role`: `received`（收礼）/ `given`（出礼） |
| `gifts` | `amount` / `is_shared` / `event_id` | 一笔礼金关联一个事件 |
| `gift_participants` | `gift_id` / `person_id` / `role` | `role`: `giver`（随礼人）/ `receiver`（收礼人） |

**设计要点**：一笔礼金通过 `gift_participants` 关联多个随礼人和多个收礼人，完美支持"老张+老李共同随 1000 元给小明+小红"这种联合随礼场景。

---

## 功能详解与使用案例

### 案例 1：结婚收礼 + 回礼提醒

**场景**：2026 年 5 月 2 日我和王伟男结婚，多个亲戚朋友随礼，3 年后其中一个亲戚的孩子结婚，我该回多少？

**操作步骤**：

1. **录入事件**：进入【事件】→ 新建
   - 标题：`我和王伟男结婚`
   - 日期：`2026-05-02`
   - 角色：`收礼`（received）

2. **录入礼金**：在事件详情页逐笔添加
   ```
   随礼人：张三          金额：¥500   共同：否
   随礼人：李四+王五     金额：¥1000  共同：是   备注：两人合伙
   随礼人：大姑          金额：¥1000
   ```
   > 共同随礼时，`is_shared=true`，随礼人列表勾选多人，系统会自动拆分到每个人头上

3. **3 年后回礼**：进入【仪表盘】→ 回礼建议
   - 系统自动列出张三，建议金额 = `500 × (1+3%)^3 ≈ ¥546.36`
   - 如果张三在这 3 年间也办过事并且你随过礼，系统会扣减"已回礼"，只显示净欠部分

### 案例 2：家族称谓自动推算

**场景**：我建好了完整家族关系网，想看每个亲戚的正确称谓（大姑/二舅/表哥/外甥女…）。

**操作步骤**：

1. **建立关系链**：在【人物详情】页 → 添加关系
   ```
   我 → 父亲（亲子，父亲是甲方）
   我 → 母亲（亲子，母亲是甲方）
   父亲 → 大姑（兄弟姐妹）
   大姑 → 表妹（亲子，大姑是甲方）
   ```

2. **查看图谱**：进入【图谱】→ 家族树
   - 系统自动从"我"出发 BFS 遍历
   - 父系亲属显示在左侧，母系亲属显示在右侧
   - 每个节点显示两行：`正式名（小名）` + `称谓`
   - 称谓规则：
     - 父亲的姐妹 → `大姑`/`二姑`/`小姑`（按出生年排序）
     - 母亲的兄弟 → `大舅`/`二舅`/`小舅`
     - 兄弟的孩子（男性中间人）→ `侄子`/`侄女`
     - 姐妹的孩子（女性中间人）→ `外甥`/`外甥女`
     - 同辈按出生年区分 `哥/弟`、`姐/妹`

3. **手动覆盖**：如果推算不准，在【人物编辑】里手动填写 `title` 字段，系统优先使用手动值

### 案例 3：标记"已平账/不来往"

**场景**：某个远房亲戚去年办喜事我回了礼，双方两清了，不想再看到他的回礼建议。

**操作步骤**：

1. 进入该亲戚的【人物详情】页
2. 点击右上角橙色按钮【标记平账/不来往】
3. 确认后该人物被标记为 `excluded`
4. 该人物立即从【仪表盘 - 回礼建议】列表中消失
5. 想恢复？再次点击绿色按钮【恢复往来】即可

### 案例 4：联合随礼的记录

**场景**：朋友老张和老李合伙给小明随了 1000 元，怎么记录才能同时记到两人账上？

**操作步骤**：

1. 新建事件"小明结婚"（角色：收礼）
2. 添加一笔礼金：
   - 金额：`1000`
   - 共同随礼：`是`
   - 随礼人：勾选 `老张` + `老李`
   - 收礼人：勾选 `小明`
3. 系统自动给老张和老李各记一笔 1000 元往来（不是各 500，因为对外是一笔 1000）

### 案例 5：数据备份与迁移

**场景**：换电脑了，怎么把礼账数据搬过去？

**操作步骤**：

1. 在旧电脑的【设置】页 → 点击【导出 CSV】
2. 下载到 `lizhang_export.zip`，内含 4 个 CSV：
   - `persons.csv`
   - `relations.csv`
   - `events.csv`
   - `gifts.csv`
3. 在新电脑部署好系统后，进入【设置】→【导入 CSV】
4. 上传这 4 个文件，系统自动按依赖顺序导入

> 也可直接复制 `backend/data/lizhang.db` 文件到新机器，效果一样。

---

## API 参考

完整交互文档见 `http://localhost:8000/docs`（Swagger UI），以下为主要接口：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/persons` | 列出人物（支持 `search` / `group` 过滤） |
| POST | `/api/persons` | 新建人物 |
| GET | `/api/persons/{id}` | 获取人物详情 |
| PUT | `/api/persons/{id}` | 更新人物（含礼金状态切换） |
| DELETE | `/api/persons/{id}` | 删除人物（级联删除关系和参与记录） |
| GET | `/api/persons/{id}/stats` | 该人物收/送礼金统计 |
| GET | `/api/events` | 列出事件 |
| POST | `/api/events` | 新建事件 |
| GET | `/api/gifts` | 列出礼金（支持 `person_id` / `event_id` 过滤） |
| POST | `/api/gifts` | 新建礼金（含参与者） |
| GET | `/api/relations?person_id={id}` | 列出某人的关系 |
| POST | `/api/relations` | 新建关系 |
| DELETE | `/api/relations/{id}` | 删除关系 |
| GET | `/api/graph/family` | 家族树图谱数据 |
| GET | `/api/graph/friends` | 朋友关系图谱数据 |
| GET | `/api/stats/dashboard` | 仪表盘汇总统计 |
| GET | `/api/stats/suggestions` | 回礼建议列表 |
| POST | `/api/data/export` | 导出 CSV zip |
| POST | `/api/data/import` | 导入 CSV |

---

## 常见问题

**Q：数据存在哪里？会丢吗？**
A：默认使用 SQLite，数据库文件在 `backend/data/lizhang.db`。建议定期通过【设置 - 导出 CSV】备份。Docker 部署时数据在 `lizhang-data` volume 中，升级镜像不丢。

**Q：回礼建议的金额怎么算的？**
A：`建议金额 = 对方最近一次礼金 × (1 + 3%)^年数`，年数从最近一次随礼日算起。仅显示"净欠 > 0"的人（对方给我随的总额 > 我已回给对方的总额）。

**Q：为什么有的亲戚称谓推算不准？**
A：称谓推算依赖完整的关系链和出生年。建议：①补全兄弟姐妹的出生年（用于区分哥/弟、姐/妹）；②关系链要打通到共同祖先（如堂表亲需通过祖父母连接）；③不准时可在人物编辑里手动填 `title` 字段覆盖。

**Q：能多人共用一个账本吗？**
A：当前为单用户本地部署。多用户需自行改造鉴权层（FastAPI 加 OAuth2），数据模型已预留 `is_self` 字段支持"我"的身份切换。

**Q：支持手机端吗？**
A：界面做了响应式适配，平板/手机可正常浏览。原生 App 暂未提供，可用 PWA 方案包装。

---

## 许可

本项目仅供个人学习与使用。如需二次开发或商用，请联系作者。
