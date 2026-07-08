# 多人房间 E2E 测试方案

> 覆盖：前端 API 客户端 → 后端 REST/WS → SQLite 持久化 → 实时广播  
> 执行脚本：`python backend/scripts/e2e_multiplayer_api.py --spawn-server`

---

## 1. 测试目标

| 层级 | 验证点 |
|------|--------|
| **外部接入** | 通过 `httpx` + `websockets` 调用真实 HTTP/WS，不直接 import service |
| **REST** | 房间相关全部端点 + 鉴权依赖链（register → token → rooms） |
| **WebSocket** | 双客户端同房、事件广播、seq 去重、断线补消息 |
| **数据库** | `rooms` / `room_members` / `room_messages` / `room_actions` / `game_sessions` 落库一致 |
| **隐私** | `dm.ask` 默认仅提问者可见（REST 历史过滤 + WS 定向推送） |

---

## 2. 环境准备

```powershell
cd "E:\HuaweiMoveData\Users\congw\Desktop\go work\StoryForge"

# 一键自动化（推荐）：自动起服务 + 独立 sqlite + LLM mock
python backend/scripts/e2e_multiplayer_api.py --spawn-server --verbose

# 或对接已有后端
python backend/scripts/e2e_multiplayer_api.py --base-url http://127.0.0.1:8080
```

默认测试端口 `8876`（避免与开发服务 8765/8080 冲突）。

### 最近执行结果（37/37 通过）

```
REST：auth / worlds / characters / rooms 全端点
WS：snapshot / chat / ooc / typing / action / dm.ask / ping
DB：rooms / room_members / room_messages / room_actions / game_sessions
```

测试过程中发现并修复：**WebSocket 广播 `datetime` 无法 JSON 序列化**（`websocket_manager.py` 统一用 `send_text + isoformat`）。

前端（本机有 Node 时）：

```powershell
cd frontend
npm run dev
# 浏览器打开 Vite 地址，按 §6 手工走查
```

---

## 3. 接口矩阵（前端 `client.js` / `wsClient.js` ↔ 后端）

### 3.1 REST

| 前端调用 | 方法 | 路径 | 测试用例 ID |
|----------|------|------|-------------|
| `authApi.register` | POST | `/api/v1/auth/register` | T-AUTH-01 |
| `authApi.me` | GET | `/api/v1/auth/me` | T-AUTH-02 |
| `worldsApi.list` | GET | `/api/v1/worlds` | T-WORLD-01 |
| `charactersApi.create` | POST | `/api/v1/characters` | T-CHAR-01 |
| `charactersApi.list` | GET | `/api/v1/characters` | T-CHAR-02 |
| `roomsApi.create` | POST | `/api/v1/rooms` | T-ROOM-01 |
| `roomsApi.list({scope:'mine'})` | GET | `/api/v1/rooms?scope=mine` | T-ROOM-02 |
| `roomsApi.list({scope:'public'})` | GET | `/api/v1/rooms?scope=public` | T-ROOM-03 |
| `roomsApi.join` | POST | `/api/v1/rooms/join` | T-ROOM-04 |
| `roomsApi.get` | GET | `/api/v1/rooms/{id}` | T-ROOM-05 |
| `roomsApi.setCharacter` | POST | `/api/v1/rooms/{id}/character` | T-ROOM-06 |
| `roomsApi.setReady` | POST | `/api/v1/rooms/{id}/ready` | T-ROOM-07 |
| `roomsApi.start` | POST | `/api/v1/rooms/{id}/start` | T-ROOM-08 |
| `roomsApi.messages` | GET | `/api/v1/rooms/{id}/messages` | T-ROOM-09 |
| `roomsApi.chat` | POST | `/api/v1/rooms/{id}/chat` | T-ROOM-10 |
| `roomsApi.ooc` | POST | `/api/v1/rooms/{id}/ooc` | T-ROOM-11 |
| `roomsApi.ask` | POST | `/api/v1/rooms/{id}/ask` | T-ROOM-12 |
| `roomsApi.action` | POST | `/api/v1/rooms/{id}/action` | T-ROOM-13 |
| `roomsApi.leave` | POST | `/api/v1/rooms/{id}/leave` | T-ROOM-14 |
| `roomsApi.end` | POST | `/api/v1/rooms/{id}/end` | T-ROOM-15 |

### 3.2 WebSocket

| 前端 `RoomSocket` | 方向 | 事件 type | 测试用例 ID |
|-------------------|------|-----------|-------------|
| 连接 | C→S | `?token=` 鉴权 | T-WS-01 |
| — | S→C | `room.snapshot` | T-WS-02 |
| `sendChat` | C→S | `chat.send` | T-WS-03 |
| — | S→C | `chat.message` | T-WS-04 |
| `sendOoc` | C→S | `ooc.send` | T-WS-05 |
| — | S→C | `ooc.message` | T-WS-06 |
| `notifyTyping` | C→S | `typing.start` / `typing.stop` | T-WS-07 |
| `submitAction` | C→S | `action.submit` | T-WS-08 |
| — | S→C | `action.accepted` / `dice.*` / `dm.narration` | T-WS-09 |
| `sendDmAsk` | C→S | `dm.ask` | T-WS-10 |
| — | S→C | `dm.guidance`（仅提问者） | T-WS-11 |
| `ping` | C→S | `ping` → `pong` | T-WS-12 |
| 重连补消息 | REST | `GET messages?after_seq=` | T-WS-13 |

---

## 4. 自动化场景（脚本顺序）

```text
Phase A · 基建
  注册 Host / Guest → me → 拉 worlds → 各建角色

Phase B · 房间生命周期（REST）
  Host 创建 public 房间 → mine/public 列表可见
  Guest join → get 详情 → 选角 → ready
  Host start → 房间 status=playing，game_sessions 有记录

Phase C · 双客户端实时（WS）
  Host WS + Guest WS 连接，收 room.snapshot
  Guest 发 chat.send → 双方收 chat.message
  Host 发 ooc.send → 双方收 ooc.message
  Guest typing.start → Host 收到（不含自己）
  Host action.submit → 双方收 action/dice/narration 链路

Phase D · DM 问答与隐私
  Guest dm.ask → Guest 收 guidance，Host 不收私密消息
  GET messages 分页：Guest 有 guidance，Host 过滤后无

Phase E · 幂等与补消息
  重复 client_msg_id action → duplicate
  after_seq 拉取增量消息

Phase F · 房主转让与结束
  Host leave → owner 转让给 Guest
  新 Host end → status=finished
```

---

## 5. 数据库断言

| 表 | 断言 |
|----|------|
| `rooms` | `status` 状态机 waiting→playing→finished；`owner_id` 转让后变更 |
| `room_members` | 加入后 2 人；host 离开后 role/owner 正确 |
| `room_messages` | `seq` 单调递增；含 chat/ooc/action/dice/narration/guidance |
| `room_actions` | `status=done`；`client_msg_id` 幂等 |
| `game_sessions` | `mode=multiplayer`，`room_id` 关联正确 |
| `messages` | 叙事日志有开局/行动旁白（单人管线镜像） |

---

## 6. 前端手工走查（双浏览器）

1. 账号 A / B 分别登录 `HomePage`
2. A 创建公开房间 → 进入 `GameRoomPage`
3. B 加入房间码 → 准备 → A 开始游戏
4. 双方看到开局旁白、`ai.thinking`、骰子、叙事
5. B 使用「问 DM」→ 仅 B 看到紫色建议
6. 聊天 / OOC / 打字状态互相同步
7. A 刷新页面 → 历史消息恢复（`after_seq`）
8. A 离开房间 → B 升为房主

---

## 7. 通过标准

- 自动化脚本 **0 failed**
- 所有 REST 返回 `code=0`（或预期 4xx 负例）
- WS 双端关键事件 **≥1 次收到**
- DB 断言全部通过
- 手工走查 §6 无阻塞缺陷
