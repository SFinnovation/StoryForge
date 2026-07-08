# -*- coding: utf-8 -*-
"""clue_pressure 剧情推进压力 (ai-module-design §5)

数据来源全部在 DB:
  turns_since_key_clue     <- game_sessions 字段 (state_committer 每轮维护)
  failed_checks_in_scene   <- ActionCheckRepo.count_failed_in_scene (当前场景)
  player_confusion_score   <- MVP 恒 0.0 (P1 由 LLM 评估)
"""
from dataclasses import dataclass

from sqlalchemy.orm import Session

from backend.app.models.models import GameSession
from backend.app.repositories import ActionCheckRepo, SessionRepo


@dataclass
class CluePressureResult:
    clue_pressure: float
    turns_since_key_clue: int
    failed_checks_in_scene: int
    current_scene: str | None

    @property
    def tier(self) -> str:
        """行为档位 (§5.3), 注入主 Agent 上下文供其调整暗示强度"""
        p = self.clue_pressure
        if p < 0.3:
            return "normal"        # 正常反馈, 不主动塞线索
        if p < 0.6:
            return "weak_hint"     # 环境暗示、弱线索
        if p < 0.8:
            return "strong_hint"   # 明显线索, 引导换方向
        return "push"              # 强推进, NPC 可主动提示


def calc_clue_pressure(
    turns_since_key_clue: int,
    failed_checks_in_scene: int,
    player_confusion_score: float = 0.0,
) -> float:
    """§5.2 公式原样实现"""
    return min(1.0, turns_since_key_clue * 0.15
               + failed_checks_in_scene * 0.1
               + player_confusion_score * 0.2)


class CluePressureService:
    def __init__(self, db: Session):
        self.sessions = SessionRepo(db)
        self.checks = ActionCheckRepo(db)

    def calculate(self, session_id: int) -> CluePressureResult:
        session = self.sessions.get(session_id)
        if session is None:
            raise ValueError(f"session {session_id} 不存在")
        scene = session.current_scene
        failed = self.checks.count_failed_in_scene(session_id, scene) if scene else 0
        pressure = calc_clue_pressure(session.turns_since_key_clue, failed)
        return CluePressureResult(
            clue_pressure=pressure,
            turns_since_key_clue=session.turns_since_key_clue,
            failed_checks_in_scene=failed,
            current_scene=scene,
        )


def calculate(db: Session, session: GameSession) -> dict:
    result = CluePressureService(db).calculate(session.id)
    session.clue_pressure = result.clue_pressure
    return {
        "clue_pressure": round(result.clue_pressure, 2),
        "turns_since_key_clue": result.turns_since_key_clue,
        "failed_checks_in_scene": result.failed_checks_in_scene,
        "current_scene": result.current_scene or "",
    }
