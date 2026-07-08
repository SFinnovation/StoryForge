# -*- coding: utf-8 -*-
"""ReportRepo — 结局报告写入 (implementation §6.2: 结束时写 reports 表)

reports 与 session 一对一 (uq_reports_session), create 做幂等: 已存在则更新。
"""
import json

from ..db.models import Report
from .base import BaseRepo

VALID_ENDING = ("good", "normal", "bad", "open")


class ReportRepo(BaseRepo):

    def get_by_session(self, session_id: int) -> Report | None:
        return self.db.query(Report).filter_by(session_id=session_id).first()

    def upsert(
        self,
        session_id: int,
        *,
        title: str | None = None,
        story_summary: str | None = None,
        key_choices: list | None = None,
        clues: list | None = None,
        ending_type: str | None = None,
        character_growth: str | None = None,
        ai_suggestion: str | None = None,
    ) -> Report:
        if ending_type is not None and ending_type not in VALID_ENDING:
            raise ValueError(f"非法 ending_type: {ending_type}")
        report = self.get_by_session(session_id)
        if report is None:
            report = Report(session_id=session_id)
            self.db.add(report)
        report.title = title
        report.story_summary = story_summary
        report.key_choices_json = json.dumps(key_choices or [], ensure_ascii=False)
        report.clues_json = json.dumps(clues or [], ensure_ascii=False)
        report.ending_type = ending_type
        report.character_growth = character_growth
        report.ai_suggestion = ai_suggestion
        self.db.flush()
        return report
