# 前端结构与交互逻辑

> 更新日期：2026-07-09  
> 本文记录当前 `frontend/` 的真实结构、页面职责、状态流转、REST 与 WebSocket 对接方式。

## 技术栈

- Vue 3 + `<script setup>`
- Vite
- 原生 `fetch`
- 浏览器 WebSocket
- 暂未引入 Vue Router / Pinia；页面切换由 `App.vue` 内部状态驱动。

## 目录结构

```text
frontend/
├─ index.html
├─ package.json
├─ vite.config.js
├─ public/dice/             # 1-20 点骰子视频
├─ 背景/
├─ 图标/
├─ 游戏种类/
└─ src/
   ├─ api/
   │  ├─ client.js          # REST API client
   │  └─ wsClient.js        # 房间 WebSocket client
   ├─ components/
   │  └─ AppNavbar.vue
   ├─ App.vue
   ├─ LoginRegister.vue
   ├─ HomePage.vue
   ├─ JoinRoomModal.vue
   ├─ ScriptPage.vue
   ├─ RolePage.vue
   ├─ GameRoomPage.vue
   ├─ EndingPage.vue
   ├─ ArchivePage.vue
   ├─ AdminPage.vue
   ├─ SettingsModal.vue
   ├─ global-back-button.css
   ├─ global-back-button.js
   ├─ main.js
   └─ style.css
```

## 页面职责

| 文件 | 职责 |
|---|---|
| `App.vue` | 应用壳层；维护登录态、当前用户、当前页面、房间 ID、结局数据；管理员自动进入后台。 |
| `LoginRegister.vue` | 登录、注册、游客进入；对接 `/auth/login`、`/auth/register`、`/auth/guest`。 |
| `HomePage.vue` | 大厅；读取世界观、角色、房间、会话；创建房间、加入房间、继续冒险、进入档案。 |
| `JoinRoomModal.vue` | 加入房间弹窗；支持房间码与公开房间选择。 |
| `ScriptPage.vue` | 世界观馆；保留视觉设计卡，并注入后端 `world_id`。 |
| `RolePage.vue` | 三阶段角色创建；基础设定、属性分配、技能选择，创建角色后进入房间流程。 |
| `GameRoomPage.vue` | 多人跑团主界面；建房/加入、成员列表、准备、开局、聊天、行动、DM 提问、骰点动画、右侧信息面板。 |
| `EndingPage.vue` | 本局结束后的结局/总结展示。 |
| `ArchivePage.vue` | 档案馆；读取历史会话并展示。 |
| `AdminPage.vue` | 管理员后台；统计卡、世界活跃度图表、世界观/模组管理、用户管理、会话记录。 |
| `SettingsModal.vue` | 设置与退出入口。 |

## 页面切换

`App.vue` 使用本地状态切换页面：

```text
LoginRegister
  -> App.vue
     -> home | script | role | room | ending | archive
     -> admin 用户直接渲染 AdminPage
```

页面别名：

| 别名 | 页面 |
|---|---|
| `大厅` / `home` | `HomePage` |
| `世界观` / `script` | `ScriptPage` |
| `角色` / `role` | `RolePage` |
| `房间` / `room` | `GameRoomPage` |
| `结局` / `ending` | `EndingPage` |
| `档案` / `archive` | `ArchivePage` |

## REST API 对接

`src/api/client.js` 负责：

- `API_BASE_URL` 默认 `/api/v1`
- token 存取：`storyforge_access_token`
- 当前用户存取：`storyforge_user`
- 统一解析 `{code, message, data}`
- 将 Pydantic 校验错误转成中文提示

主要 API 分组：

| 前端对象 | 后端接口 |
|---|---|
| `authApi` | `/auth/register`、`/auth/login`、`/auth/guest`、`/auth/me`、`/auth/logout` |
| `worldsApi` | `/worlds` |
| `charactersApi` | `/characters` |
| `roomsApi` | `/rooms`、`/rooms/join`、`/rooms/{id}/start`、`/rooms/{id}/action`、`/rooms/{id}/ask` 等 |
| `sessionsApi` | `/sessions`、`/sessions/{id}/messages`、`/sessions/{id}/report` |
| `adminApi` | `/admin/summary`、`/admin/worlds`、`/admin/users`、`/admin/sessions` |

## WebSocket 对接

`src/api/wsClient.js` 封装 `RoomSocket`：

- 地址：`/api/v1/ws/rooms/{room_id}?token=<access_token>`
- 自动重连：指数退避，最高约 15 秒
- 心跳：每 25 秒发送 `ping`
- `seq` 去重：防止重连或广播重复造成消息重复展示
- 断线补消息：重连后用 `roomsApi.messages(afterSeq=lastSeq)` 拉取漏收消息

客户端发送：

| 方法 | WebSocket type |
|---|---|
| `sendChat` | `chat.send` |
| `sendOoc` | `ooc.send` |
| `submitAction` | `action.submit` |
| `sendDmAsk` | `dm.ask` |
| `notifyTyping` | `typing.start` / `typing.stop` |

`GameRoomPage.vue` 对 `chat.message`、`ooc.message`、`action.received`、`dice.result`、`dm.narration`、`dm.guidance`、`state.updated`、`game.ended` 等事件进行 UI 更新。

## 多人房间页面

`GameRoomPage.vue` 是当前答辩演示的主页面，包含：

- 房间创建与加入。
- 房间码展示。
- 成员列表、角色头像、职业等级、在线/准备状态。
- 房主开局和结束。
- 中央消息流：群聊、场外、行动、骰点、AI 旁白、DM 建议。
- 玩家行动输入：触发后端 d20 判定和 AI DM 叙事。
- DM 提问输入：不推进剧情，默认私密回答。
- 右侧功能面板：房间进度、团队同步、线索/任务/行动摘要。
- d20 骰点视频动画：读取 `frontend/public/dice/{1-20}.mp4`。

## 管理员后台页面

管理员用户登录后，`App.vue` 根据 `currentUser.role === 'admin'` 直接渲染 `AdminPage.vue`。

`AdminPage.vue` 展示：

- 今日新增会话、实时活跃房间、累计历史会话、消息与行动、用户档案、世界观/模组统计。
- 世界活跃度图表，数据来自 `/api/v1/admin/summary` 的 `world_activity`。
- 世界观树：上架/停用世界观、创建/启用/停用模组。
- 用户列表：封禁/解封用户、查看该用户会话记录。
- 会话记录：按用户查看，并可强制归档。

这部分可用于满足验收要求中的“登录角色差异”“数据操作”“数据可视化来自后端”。

## 认证与角色差异

```text
普通用户 / 游客
  -> HomePage
  -> ScriptPage / RolePage
  -> GameRoomPage
  -> ArchivePage / EndingPage

管理员
  -> AdminPage
  -> 查看统计、管理世界观/模组、用户、会话
```

游客会清除 token 并依赖后端 demo user 兼容逻辑。正式用户 token 存在 localStorage 中，后续请求自动带 `Authorization: Bearer <token>`。

## 当前注意事项

- 仍未使用 Vue Router，答辩讲解时应说明这是 MVP 为降低复杂度采用的状态驱动导航。
- 多人房间要求满员、全员选角、全员准备后才能开局；演示前要保证房间人数设置与测试账号数量一致。
- `dm.ask` 默认 `visibility=self`，因此只有提问者能看到私密 DM 建议。
- 生产环境仍需标准 JWT/RBAC、多实例 WebSocket 扩展和更完整的错误提示策略。
