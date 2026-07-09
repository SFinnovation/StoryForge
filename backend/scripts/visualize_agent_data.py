from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "storyforge.db"
DEFAULT_OUT = ROOT / "docs" / "agent_data_visualization.html"


AGENT_TABLES = [
    "worlds",
    "adventure_modules",
    "world_modules",
    "rulebook_packs",
    "rooms",
    "game_sessions",
    "messages",
    "room_messages",
    "facts",
    "npc_profiles",
    "clues",
    "tasks",
    "ai_reviews",
]


def rows(con: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    return [dict(row) for row in con.execute(sql, params).fetchall()]


def scalar(con: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> Any:
    return con.execute(sql, params).fetchone()[0]


def short(value: Any, length: int = 180) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if len(text) <= length:
        return text
    return text[: length - 1] + "..."


def parse_json(value: Any) -> Any:
    if value in (None, ""):
        return None
    try:
        return json.loads(str(value))
    except json.JSONDecodeError:
        return value


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def status_class(value: Any) -> str:
    text = str(value or "").lower()
    if text in {"playing", "active", "approved", "ok", "done"}:
        return "ok"
    if text in {"waiting", "pending", "open"}:
        return "warn"
    if text in {"archived", "failed", "error", "blocked"}:
        return "bad"
    return "muted"


def h(value: Any) -> str:
    return escape("" if value is None else str(value))


def badge(label: Any, css: str | None = None) -> str:
    return f'<span class="badge {css or status_class(label)}">{h(label)}</span>'


def table(title: str, items: list[dict[str, Any]], columns: list[tuple[str, str]], empty: str = "No rows") -> str:
    if not items:
        return f"""
        <section class="panel">
          <h2>{h(title)}</h2>
          <div class="empty">{h(empty)}</div>
        </section>
        """
    head = "".join(f"<th>{h(label)}</th>" for _, label in columns)
    body = []
    for item in items:
        cells = []
        for key, _ in columns:
            value = item.get(key)
            if key.endswith("_json"):
                parsed = parse_json(value)
                cells.append(
                    f"<td><details><summary>{h(short(parsed, 80))}</summary><pre>{h(jdump(parsed))}</pre></details></td>"
                )
            elif key in {"status", "room_status", "session_status", "sender_role", "sender_type", "message_type"}:
                cells.append(f"<td>{badge(value)}</td>")
            else:
                cells.append(f"<td>{h(short(value))}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    return f"""
    <section class="panel">
      <h2>{h(title)}</h2>
      <div class="table-wrap">
        <table>
          <thead><tr>{head}</tr></thead>
          <tbody>{''.join(body)}</tbody>
        </table>
      </div>
    </section>
    """


def text_card(title: str, value: Any, foot: str = "") -> str:
    return f"""
    <article class="card">
      <div class="card-title">{h(title)}</div>
      <pre>{h(short(value, 1200))}</pre>
      {f'<p class="foot">{h(foot)}</p>' if foot else ''}
    </article>
    """


def collect(db_path: Path) -> dict[str, Any]:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    counts = {name: scalar(con, f"SELECT COUNT(*) FROM {name}") for name in AGENT_TABLES}
    room_chain = rows(
        con,
        """
        SELECT
          r.id AS room_id,
          r.title AS room_title,
          r.room_code,
          r.status AS room_status,
          r.max_players,
          r.world_id,
          r.current_session_id,
          w.name AS world_name,
          w.type AS world_type,
          w.adventure_module_id,
          w.rulebook_pack_id,
          w.opening_prompt,
          w.description AS world_description,
          s.id AS session_id,
          s.status AS session_status,
          s.mode,
          c.id AS character_id,
          c.name AS character_name,
          c.class_id,
          c.background_id,
          c.motivation
        FROM rooms r
        LEFT JOIN worlds w ON w.id = r.world_id
        LEFT JOIN game_sessions s ON s.id = r.current_session_id
        LEFT JOIN characters c ON c.id = s.character_id
        ORDER BY r.id
        """,
    )
    active = next((room for room in room_chain if room.get("room_status") == "playing"), None)
    if active is None:
        active = next((room for room in reversed(room_chain) if room.get("session_id")), room_chain[-1] if room_chain else None)
    room_id = active.get("room_id") if active else None
    session_id = active.get("session_id") if active else None

    session_filter = (session_id,) if session_id else (-1,)
    room_filter = (room_id,) if room_id else (-1,)
    data = {
        "db_path": str(db_path),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "counts": counts,
        "room_chain": room_chain,
        "active": active,
        "modules": {
            "adventure_modules": rows(con, "SELECT id, title, source_filename, status, opening_prompt, created_at FROM adventure_modules ORDER BY id"),
            "world_modules": rows(con, "SELECT id, world_id, name, description, is_enabled, created_at FROM world_modules ORDER BY id"),
            "rulebook_packs": rows(con, "SELECT id, title, source_filename, status, core_rules_summary, created_at FROM rulebook_packs ORDER BY id"),
        },
        "messages": rows(
            con,
            """
            SELECT id, session_id, sender_type, sender_name, message_type, content, tokens_used, latency_ms, created_at
            FROM messages
            WHERE session_id = ?
            ORDER BY id
            """,
            session_filter,
        ),
        "room_messages": rows(
            con,
            """
            SELECT id, room_id, session_id, seq, sender_role, sender_name, message_type, content, payload_json, created_at
            FROM room_messages
            WHERE room_id = ?
            ORDER BY seq, id
            """,
            room_filter,
        ),
        "tasks": rows(con, "SELECT id, session_id, title, description, status, created_at, updated_at FROM tasks WHERE session_id = ? ORDER BY id", session_filter),
        "facts": rows(con, "SELECT id, session_id, fact_type, content, visibility_json, importance, status, created_at FROM facts WHERE session_id = ? ORDER BY id", session_filter),
        "npc_profiles": rows(con, "SELECT id, session_id, npc_id, name, personality, speaking_style, related_scene, is_visible, alertness, created_at FROM npc_profiles WHERE session_id = ? ORDER BY id", session_filter),
        "clues": rows(con, "SELECT id, session_id, title, content, source_scene, importance, discovered_at FROM clues WHERE session_id = ? ORDER BY id", session_filter),
        "ai_reviews": rows(
            con,
            """
            SELECT id, session_id, message_id, approved, overall_score, scores_json, fatal_errors_json,
                   revision_instructions_json, revision_count, used_fallback, tokens_used, latency_ms, created_at
            FROM ai_reviews
            WHERE session_id = ?
            ORDER BY id
            """,
            session_filter,
        ),
    }
    con.close()
    return data


def render(data: dict[str, Any]) -> str:
    counts = data["counts"]
    active = data.get("active") or {}
    module_empty = counts["adventure_modules"] == 0 and counts["world_modules"] == 0 and counts["rulebook_packs"] == 0
    module_state = "Module tables are empty" if module_empty else "Module data exists"
    source_warning = (
        "The selected room has no adventure_module_id; OpeningAgent is using the world's generic opening_prompt."
        if not active.get("adventure_module_id")
        else "The selected room is linked to an adventure module."
    )
    opening_messages = [m for m in data["messages"] if str(m.get("sender_type", "")).lower() in {"ai", "dm", "assistant"}]
    opening_room_messages = [m for m in data["room_messages"] if m.get("sender_role") == "ai_dm"]
    first_agent_text = opening_room_messages[0]["content"] if opening_room_messages else (opening_messages[0]["content"] if opening_messages else "")

    stats = "".join(
        f"""
        <article class="stat">
          <strong>{h(value)}</strong>
          <span>{h(key)}</span>
        </article>
        """
        for key, value in counts.items()
    )

    modules = data["modules"]
    module_tables = (
        table("adventure_modules", modules["adventure_modules"], [("id", "ID"), ("title", "Title"), ("source_filename", "Source"), ("status", "Status"), ("opening_prompt", "Opening Prompt"), ("created_at", "Created")], "Empty: no imported adventure module is available to OpeningAgent.")
        + table("world_modules", modules["world_modules"], [("id", "ID"), ("world_id", "World"), ("name", "Name"), ("description", "Description"), ("is_enabled", "Enabled"), ("created_at", "Created")], "Empty: no world-specific module rows.")
        + table("rulebook_packs", modules["rulebook_packs"], [("id", "ID"), ("title", "Title"), ("source_filename", "Source"), ("status", "Status"), ("core_rules_summary", "Rules Summary"), ("created_at", "Created")], "Empty: no imported rulebook pack.")
    )

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>StoryForge Agent DB Visualization</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f6f7f9;
      --panel: #ffffff;
      --text: #1f2933;
      --muted: #697386;
      --line: #d8dee8;
      --ok: #12805c;
      --warn: #ad5700;
      --bad: #b42318;
      --blue: #2458b3;
      --ink: #111827;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, "Segoe UI", "Microsoft YaHei", sans-serif;
      color: var(--text);
      background: var(--bg);
      line-height: 1.45;
    }}
    header {{
      padding: 28px 32px 20px;
      background: #ffffff;
      border-bottom: 1px solid var(--line);
    }}
    h1, h2, h3, p {{ margin: 0; }}
    h1 {{ font-size: 24px; letter-spacing: 0; }}
    h2 {{ font-size: 17px; margin-bottom: 14px; }}
    h3 {{ font-size: 14px; color: var(--muted); margin-bottom: 8px; }}
    main {{ padding: 24px 32px 40px; max-width: 1500px; margin: 0 auto; }}
    .sub {{ color: var(--muted); margin-top: 8px; }}
    .grid {{ display: grid; gap: 16px; }}
    .stats {{ grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); margin: 18px 0 0; }}
    .stat, .panel, .card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
    }}
    .stat {{ padding: 12px 14px; min-height: 74px; }}
    .stat strong {{ display: block; font-size: 24px; color: var(--ink); }}
    .stat span {{ display: block; margin-top: 4px; color: var(--muted); font-size: 12px; }}
    .panel {{ padding: 18px; margin-bottom: 16px; overflow: hidden; }}
    .cards {{ grid-template-columns: repeat(auto-fit, minmax(290px, 1fr)); }}
    .card {{ padding: 14px; min-height: 132px; }}
    .card-title {{ color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .04em; margin-bottom: 8px; }}
    .foot {{ margin-top: 10px; color: var(--muted); font-size: 12px; }}
    pre {{
      white-space: pre-wrap;
      word-break: break-word;
      margin: 0;
      font-family: "Cascadia Mono", Consolas, monospace;
      font-size: 12px;
    }}
    .flow {{
      display: grid;
      grid-template-columns: minmax(170px, 1fr) 32px minmax(170px, 1fr) 32px minmax(170px, 1fr) 32px minmax(170px, 1fr);
      align-items: stretch;
      gap: 8px;
    }}
    .node {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      background: #fbfcfe;
      min-height: 126px;
    }}
    .node strong {{ display: block; font-size: 15px; margin-bottom: 8px; }}
    .node code {{ font-size: 12px; color: var(--blue); }}
    .arrow {{ align-self: center; color: var(--muted); text-align: center; font-size: 24px; }}
    .alert {{
      padding: 12px 14px;
      border: 1px solid #ffd6a8;
      background: #fff8ef;
      color: #7a3f00;
      border-radius: 8px;
      margin: 16px 0;
    }}
    .table-wrap {{ overflow-x: auto; border: 1px solid var(--line); border-radius: 8px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 12px; background: #fff; }}
    th, td {{ padding: 10px 12px; border-bottom: 1px solid var(--line); vertical-align: top; text-align: left; }}
    th {{ background: #f1f4f8; color: #334155; font-weight: 700; position: sticky; top: 0; }}
    tr:last-child td {{ border-bottom: 0; }}
    details summary {{ cursor: pointer; color: var(--blue); max-width: 420px; }}
    details pre {{ margin-top: 8px; background: #f6f8fb; padding: 10px; border-radius: 6px; }}
    .badge {{
      display: inline-flex;
      align-items: center;
      min-height: 22px;
      padding: 2px 8px;
      border-radius: 999px;
      border: 1px solid var(--line);
      background: #f7f9fc;
      color: var(--muted);
      font-size: 12px;
      white-space: nowrap;
    }}
    .badge.ok {{ color: var(--ok); background: #ecfdf5; border-color: #a7f3d0; }}
    .badge.warn {{ color: var(--warn); background: #fff7ed; border-color: #fed7aa; }}
    .badge.bad {{ color: var(--bad); background: #fef3f2; border-color: #fecaca; }}
    .empty {{ color: var(--muted); padding: 18px; border: 1px dashed var(--line); border-radius: 8px; background: #fbfcfe; }}
    @media (max-width: 920px) {{
      header, main {{ padding-left: 18px; padding-right: 18px; }}
      .flow {{ grid-template-columns: 1fr; }}
      .arrow {{ transform: rotate(90deg); }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>StoryForge Agent DB Visualization</h1>
    <p class="sub">DB: {h(data["db_path"])} · Generated: {h(data["generated_at"])}</p>
    <div class="grid stats">{stats}</div>
  </header>
  <main>
    <section class="panel">
      <h2>Source Chain</h2>
      <div class="flow">
        <div class="node">
          <strong>Room</strong>
          <code>id={h(active.get("room_id"))} / {h(active.get("room_code"))}</code>
          <p>{h(active.get("room_title"))}</p>
          <p>{badge(active.get("room_status"))}</p>
        </div>
        <div class="arrow">→</div>
        <div class="node">
          <strong>World</strong>
          <code>world_id={h(active.get("world_id"))}</code>
          <p>{h(active.get("world_name"))}</p>
          <p>{h(active.get("world_description"))}</p>
        </div>
        <div class="arrow">→</div>
        <div class="node">
          <strong>Adventure Module</strong>
          <code>adventure_module_id={h(active.get("adventure_module_id"))}</code>
          <p>{h(module_state)}</p>
          <p>{badge("missing", "bad") if not active.get("adventure_module_id") else badge("linked", "ok")}</p>
        </div>
        <div class="arrow">→</div>
        <div class="node">
          <strong>OpeningAgent Input</strong>
          <code>session_id={h(active.get("session_id"))}</code>
          <p>{h(active.get("opening_prompt"))}</p>
        </div>
      </div>
      <div class="alert">{h(source_warning)}</div>
    </section>

    <section class="panel">
      <h2>Agent Snapshot</h2>
      <div class="grid cards">
        {text_card("First AI Room Message", first_agent_text or "No AI room message found")}
        {text_card("Character", jdump({k: active.get(k) for k in ["character_id", "character_name", "class_id", "background_id", "motivation"]}))}
        {text_card("World Opening Prompt", active.get("opening_prompt") or "")}
      </div>
    </section>

    {table("Room -> World -> Session", data["room_chain"], [("room_id", "Room ID"), ("room_title", "Title"), ("room_code", "Code"), ("room_status", "Room Status"), ("max_players", "Max"), ("world_id", "World ID"), ("world_name", "World"), ("adventure_module_id", "Module ID"), ("current_session_id", "Current Session"), ("character_name", "Character"), ("opening_prompt", "Opening Prompt")])}
    {module_tables}
    {table("messages: session narrative log", data["messages"], [("id", "ID"), ("session_id", "Session"), ("sender_type", "Sender"), ("sender_name", "Name"), ("message_type", "Type"), ("content", "Content"), ("tokens_used", "Tokens"), ("latency_ms", "Latency"), ("created_at", "Created")])}
    {table("room_messages: realtime room event stream", data["room_messages"], [("seq", "Seq"), ("id", "ID"), ("session_id", "Session"), ("sender_role", "Role"), ("sender_name", "Name"), ("message_type", "Type"), ("content", "Content"), ("payload_json", "Payload JSON"), ("created_at", "Created")])}
    {table("tasks", data["tasks"], [("id", "ID"), ("session_id", "Session"), ("title", "Title"), ("description", "Description"), ("status", "Status"), ("created_at", "Created"), ("updated_at", "Updated")])}
    {table("facts", data["facts"], [("id", "ID"), ("session_id", "Session"), ("fact_type", "Type"), ("content", "Content"), ("visibility_json", "Visibility"), ("importance", "Importance"), ("status", "Status"), ("created_at", "Created")])}
    {table("npc_profiles", data["npc_profiles"], [("id", "ID"), ("session_id", "Session"), ("npc_id", "NPC ID"), ("name", "Name"), ("personality", "Personality"), ("speaking_style", "Style"), ("related_scene", "Scene"), ("is_visible", "Visible"), ("alertness", "Alertness"), ("created_at", "Created")])}
    {table("clues", data["clues"], [("id", "ID"), ("session_id", "Session"), ("title", "Title"), ("content", "Content"), ("source_scene", "Scene"), ("importance", "Importance"), ("discovered_at", "Discovered")])}
    {table("ai_reviews", data["ai_reviews"], [("id", "ID"), ("session_id", "Session"), ("message_id", "Message"), ("approved", "Approved"), ("overall_score", "Score"), ("scores_json", "Scores"), ("fatal_errors_json", "Fatal Errors"), ("revision_instructions_json", "Revisions"), ("revision_count", "Revision Count"), ("used_fallback", "Fallback"), ("tokens_used", "Tokens"), ("latency_ms", "Latency"), ("created_at", "Created")])}
  </main>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a read-only StoryForge agent DB visualization.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="Path to SQLite database")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Path to output HTML report")
    args = parser.parse_args()

    db_path = args.db.resolve()
    if not db_path.exists():
        raise SystemExit(f"Database not found: {db_path}")

    report = render(collect(db_path))
    out_path = args.out.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    print(out_path)


if __name__ == "__main__":
    main()
