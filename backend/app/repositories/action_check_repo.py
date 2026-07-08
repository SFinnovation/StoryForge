# -*- coding: utf-8 -*-
"""ActionCheckRepo (ai-module-design §11.1)

- create: state_committer 写入顺序第 2 步 (检定记录, 数据来自 rule_service 非 LLM)
- count_failed_in_scene: clue_pressure 公式的 failed_checks_in_scene 项 (§5.2)
"""
from backend.app.models.models import ActionCheck
from backend.app.repositories.base import BaseRepo


class ActionCheckRepo(BaseRepo):

    def create(
        self,
        session_id: int,
        action_text: str,
        *,
        message_id: int | None = None,
        scene: str | None = None,
        check_type: str | None = None,
        skill_key: str | None = None,
        attribute_used: str | None = None,
        dc: int | None = None,
        dice_roll: int | None = None,
        ability_modifier: int | None = None,
        skill_bonus: int = 0,
        final_value: int | None = None,
        is_success: bool | None = None,
        result_text: str | None = None,
    ) -> ActionCheck:
        check = ActionCheck(
            session_id=session_id, message_id=message_id, scene=scene,
            action_text=action_text, check_type=check_type,
            skill_key=skill_key, attribute_used=attribute_used,
            dc=dc, dice_roll=dice_roll,
            ability_modifier=ability_modifier, skill_bonus=skill_bonus,
            final_value=final_value,
            is_success=None if is_success is None else int(is_success),
            result_text=result_text,
        )
        self.db.add(check)
        self.db.flush()
        return check

    def count_failed_in_scene(self, session_id: int, scene: str) -> int:
        return (
            self.db.query(ActionCheck)
            .filter_by(session_id=session_id, scene=scene, is_success=0)
            .count()
        )

    def list_by_session(self, session_id: int) -> list[ActionCheck]:
        """summary_agent 聚合检定历史用"""
        return (
            self.db.query(ActionCheck)
            .filter_by(session_id=session_id)
            .order_by(ActionCheck.id.asc())
            .all()
        )
