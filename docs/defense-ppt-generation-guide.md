# StoryForge 答辩 PPT 生成指导

> 用途：把本文直接交给其他 AI，让它按要求生成答辩 PPT。  
> 项目：StoryForge（灵境档案）AI 跑团互动与推理系统。  
> 建议页数：14-16 页。  
> 风格：深色奇幻档案感，金色/琥珀色点缀，画面要多用真实系统截图/界面占位，不要做纯文字报告。

## 一、必须遵守的答辩要求

PPT 必须覆盖并按以下顺序组织：

1. 项目背景与真实需求
2. 小组分工
3. 系统功能演示
4. 数据流展示
5. 特色技术展示
6. Vibe Coding 关键迭代过程
7. 项目不足与后续优化方向

验收必须展示的内容：

| 内容 | PPT 中的呈现方式 |
|---|---|
| 项目运行 | 放本地启动命令、前后端地址、运行页面截图。 |
| 登录角色 | 普通用户进入玩家大厅，管理员进入后台，展示功能差异。 |
| 数据操作 | 展示建房/加入、世界观/模组新增或停用、用户封禁/解封、会话归档。 |
| 数据可视化 | 展示管理员统计卡、世界活跃度图表，并标注数据来自后端 `/api/v1/admin/summary`。 |
| 特色技术 | 至少讲 1 项核心技术，建议讲“AI DM 多 Agent + 后端 d20 判定 + WebSocket 实时同步”。 |
| 真实需求 | 说明解决 DM 稀缺、线上跑团协同难、记录分散、规则判定不透明等问题。 |
| Vibe 日志 | 讲清至少 1 次关键迭代，例如“从单人会话扩展到多人房间实时协作”。 |
| 代码理解 | 用架构图、数据流图和关键文件路径说明核心逻辑，不要只展示效果图。 |

项目不涉及硬件、摄像头、传感器或外部设备，不需要硬件采集链路。若必须回应硬件项，说明“本项目为纯 Web 软件系统，无硬件输入；系统数据来自用户操作、后端数据库与 AI 服务”。

## 二、项目一句话定位

StoryForge 是一个支持多人房间实时交流、角色协作行动、AI DM 叙事推进、后端 d20 规则判定、跑团日志持久化与管理员数据可视化的 Web 跑团平台。

## 三、推荐 PPT 结构

### 1. 封面

标题：StoryForge 灵境档案  
副标题：AI 跑团互动与推理系统  
画面建议：使用项目前端深色奇幻界面截图或登录/大厅截图作为背景。  
备注：写小组名、成员、日期。

### 2. 项目背景与真实需求

核心文案：

- 传统 TRPG/跑团依赖主持人 DM，组织成本高。
- 多人线上跑团常见问题：信息分散、规则判定不透明、历史记录难追踪。
- 新手玩家不熟悉规则，需要系统提示和低门槛引导。
- 管理者需要查看活跃房间、用户、会话和内容状态。

画面建议：用“痛点 -> 系统能力”双栏图。

### 3. 项目目标与用户角色

展示三类角色：

| 角色 | 需求 | 系统能力 |
|---|---|---|
| 普通玩家 | 加入房间、创建角色、提交行动、看 AI 旁白。 | 玩家大厅、角色创建、多人房间。 |
| 房主 | 组织房间、开局、结束本局。 | 房间码、准备状态、开局/结束控制。 |
| 管理员 | 维护内容、查看数据、管理用户和会话。 | 管理员后台与数据可视化。 |

### 4. 小组分工

用表格展示。可按真实成员姓名替换“成员 A/B/C/D”。

| 成员 | 主要职责 | 对应模块 |
|---|---|---|
| 成员 A | 后端架构、数据库、REST API | `backend/app/api/v1/`、`models.py`、`services/` |
| 成员 B | AI DM 流水线、规则判定、Prompt | `backend/app/ai/`、`action_service.py`、`rule_service.py` |
| 成员 C | 前端页面、多人房间交互、WebSocket 客户端 | `frontend/src/*.vue`、`wsClient.js` |
| 成员 D | 管理员后台、测试验证、答辩材料 | `AdminPage.vue`、`admin.py`、`backend/scripts/`、`docs/` |

备注：答辩时每位成员至少能解释一个核心文件或流程。

### 5. 系统总体架构

用架构图展示：

```text
Vue 前端
  -> REST API / WebSocket
FastAPI 后端
  -> Services / AI Orchestrator / Repositories
SQLite 数据库
  -> 用户、角色、房间、会话、消息、行动、报告
D&D 规则 JSON
  -> rule_service 后端判定
```

必须标注关键文件：

- `frontend/src/GameRoomPage.vue`
- `frontend/src/api/client.js`
- `frontend/src/api/wsClient.js`
- `backend/app/api/v1/rooms.py`
- `backend/app/api/v1/ws_rooms.py`
- `backend/app/services/room_action_service.py`
- `backend/app/services/action_service.py`
- `backend/app/api/v1/admin.py`
- `backend/app/models/models.py`

### 6. 系统功能演示一：项目运行与登录角色

放运行命令：

```powershell
uvicorn backend.app.main:app --reload --port 8000
cd frontend
npm run dev
```

放地址：

- 前端：http://localhost:5173
- 后端：http://localhost:8000/docs

展示截图：

- 登录/注册页
- 普通用户大厅
- 管理员后台

讲解重点：普通用户和管理员登录后进入不同功能界面。

### 7. 系统功能演示二：多人房间跑团

展示流程截图或动线图：

```text
创建房间 -> 输入房间码加入 -> 选择角色 -> 全员准备 -> 房主开局
```

展示 `GameRoomPage`：

- 房间码
- 成员列表
- 在线/准备状态
- 开局按钮
- 中央消息流
- 右侧功能面板

### 8. 系统功能演示三：AI DM、行动与骰点

演示脚本：

1. 玩家发送群聊。
2. 玩家提交行动：“我调查大厅钟摆后方是否有机关。”
3. 前端显示 AI 正在思考。
4. 后端返回骰点结果。
5. 前端播放 d20 视频动画。
6. AI DM 推进剧情并写入消息流。

讲解重点：

- AI 不是直接决定成败。
- 行动先由 AI 解析，再由后端规则服务做 d20 判定。
- 结果会落库并通过 WebSocket 广播给房间成员。

### 9. 系统功能演示四：数据操作与管理员后台

展示管理员后台：

- 统计卡片
- 世界活跃度图表
- 世界观/模组树
- 用户列表
- 会话记录

必须展示至少一个数据操作：

- 新增世界观或模组
- 启用/停用世界观或模组
- 封禁/解封用户
- 强制归档会话

标注后端接口：

- `GET /api/v1/admin/summary`
- `POST /api/v1/admin/worlds`
- `POST /api/v1/admin/users/{id}/ban`
- `POST /api/v1/admin/sessions/{id}/dissolve`

### 10. 数据流展示一：玩家行动数据流

建议画成流程图：

```text
GameRoomPage
  -> wsClient action.submit
  -> ws_rooms.py
  -> room_action_service.py
  -> action_service.run_action_pipeline
  -> ActionParserAgent
  -> rule_service d20 判定
  -> NarrativeAgent + CriticAgent
  -> state_committer 写数据库
  -> room_messages 写事件流
  -> WebSocket 广播
  -> 前端消息流 / 骰点动画 / 统计更新
```

旁边放关键数据表：

- `room_actions`
- `room_messages`
- `game_sessions`
- `messages`
- `action_checks`
- `facts`
- `ai_reviews`

### 11. 数据流展示二：管理后台可视化数据流

建议画成“数据库 -> 后端聚合 -> 图表”的图：

```text
users / rooms / room_messages / room_actions / game_sessions / worlds
  -> backend/app/api/v1/admin.py
  -> GET /api/v1/admin/summary
  -> AdminPage.vue
  -> 统计卡片 + 世界活跃度图表
```

强调：图表数据来自后端真实聚合，不是前端写死。

### 12. 特色技术展示

推荐标题：AI DM 多 Agent 与后端规则判定结合

核心讲解：

- `OpeningAgent`：生成开场。
- `ActionParserAgent`：理解玩家行动，推断技能和 DC。
- `rule_service`：执行 d20 掷骰、属性修正、熟练加值和成功判断。
- `NarrativeAgent`：根据判定结果生成剧情。
- `CriticAgent + RevisionLoop`：审核 AI 输出，减少不合理叙事。
- `GuidanceAgent`：回答玩家提问，不推进剧情。

突出价值：

- 成败透明。
- AI 负责叙事，后端负责规则。
- 便于本地 fallback 演示和真实模型切换。

### 13. Vibe Coding 关键迭代过程

建议做成时间线：

| 迭代 | 问题 | 改动 | 结果 |
|---|---|---|---|
| 1. 单人闭环 | 先跑通 AI 开局、行动、总结。 | 实现 `/sessions/start`、`/sessions/{id}/action`、`StateCommitter`。 | 有基础可演示流程。 |
| 2. 前后端联调 | 前端不再只是静态页面。 | 接入 `client.js`、登录、世界观、角色、会话接口。 | 用户可从页面触发后端流程。 |
| 3. 多人房间 | 单人模式不满足协作跑团。 | 新增 `rooms`、`room_members`、`room_messages`、WebSocket。 | 多玩家实时聊天和共同行动。 |
| 4. 管理后台 | 验收要求数据操作与可视化。 | 新增 `/admin/summary`、`AdminPage.vue`、世界观/用户/会话管理。 | 可展示后端统计和数据管理。 |
| 5. 稳定性验证 | 现场演示需要稳定。 | 新增 `test_room_flow.py`、`e2e_multiplayer_api.py`、fallback AI。 | 无外部 AI Key 也能跑通闭环。 |

备注：这一页要体现“通过 AI 辅助开发进行多轮需求澄清、实现、验证和修正”，不要写成简单流水账。

### 14. 项目不足

必须坦诚但不要削弱项目价值：

- 当前 WebSocket 连接池和房间锁是单进程内存实现，多实例部署需要 Redis Pub/Sub 与分布式锁。
- 认证是自定义 Bearer token，生产环境应升级为标准 JWT、刷新 token 和完整 RBAC。
- D&D 角色规则仍是 MVP，复杂种族、27 点购、完整职业成长还需扩展。
- PDF 导出和更完整战报可视化仍可继续完善。
- 真实模型调用受网络和 API Key 影响，现场演示提供 fallback 保证稳定。

### 15. 后续优化方向

建议写：

- 接入标准 JWT/RBAC 与更细粒度权限。
- Redis 支撑多实例 WebSocket 与房间行动队列。
- 完善 D&D 5e 规则、COC 规则和更多世界观模组。
- 增强战报页：图表、行动贡献、线索路径、角色成长。
- 管理后台增加操作日志前端展示和更强筛选。
- 引入 CI，自动运行后端验证、前端构建和端到端测试。

### 16. 总结页

三句话：

1. StoryForge 把“AI 叙事、规则判定、多人协作、数据管理”整合成一个可运行 Web 系统。
2. 项目已能完成从登录、建房、开局、行动、骰点、AI 旁白到后台数据可视化的完整演示。
3. 后续将从生产级权限、多实例实时通信、规则完整度和战报可视化继续优化。

## 四、答辩现场演示脚本

建议 6-8 分钟：

1. 打开前端和后端文档页，证明项目可运行。
2. 普通用户 A 登录，进入大厅。
3. 普通用户 B 在另一个浏览器登录。
4. A 创建 2 人房间，B 输入房间码加入。
5. 两人选角色并准备，A 开局。
6. 展示 AI DM 开场同步到两端。
7. A 提交行动，展示骰点动画和 AI 旁白。
8. B 使用 DM 提问，展示私密建议。
9. 管理员登录，展示统计卡、世界活跃图表、用户/世界观/会话管理。

## 五、PPT 视觉要求

- 主色：深色背景、金色/琥珀色高亮，贴合项目 UI。
- 每页不超过 5 个主 bullet。
- 关键流程必须用图，不要堆代码。
- 功能演示页优先放真实截图，占页面 60% 以上。
- 技术页用“文件路径 + 流程箭头 + 数据表”表达代码理解。
- 不要使用与项目无关的硬件、摄像头、IoT 图标。

## 六、可直接引用的关键文件路径

前端：

- `frontend/src/App.vue`
- `frontend/src/LoginRegister.vue`
- `frontend/src/HomePage.vue`
- `frontend/src/RolePage.vue`
- `frontend/src/GameRoomPage.vue`
- `frontend/src/AdminPage.vue`
- `frontend/src/api/client.js`
- `frontend/src/api/wsClient.js`

后端：

- `backend/app/main.py`
- `backend/app/api/v1/router.py`
- `backend/app/api/v1/rooms.py`
- `backend/app/api/v1/ws_rooms.py`
- `backend/app/api/v1/admin.py`
- `backend/app/services/room_service.py`
- `backend/app/services/room_action_service.py`
- `backend/app/services/guidance_service.py`
- `backend/app/services/action_service.py`
- `backend/app/services/rule_service.py`
- `backend/app/services/state_committer.py`
- `backend/app/models/models.py`

验证：

- `backend/scripts/test_room_flow.py`
- `backend/scripts/e2e_multiplayer_api.py`
- `backend/scripts/test_admin_api.py`
- `backend/scripts/test_frontend_contract.py`

## 七、生成 PPT 时不要犯的错误

- 不要把系统说成“纯聊天机器人”；它有后端规则判定和数据库持久化。
- 不要说数据可视化是静态图片；管理后台统计来自后端聚合接口。
- 不要只讲 AI；必须讲登录角色、数据操作、数据流和代码理解。
- 不要声称已经支持生产级集群部署；当前 WebSocket 是单进程版本。
- 不要加入硬件采集流程；本项目没有硬件。
