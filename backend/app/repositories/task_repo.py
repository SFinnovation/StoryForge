# -*- coding: utf-8 -*-
"""TaskRepo (ai-module-design §11.1)

- update_batch: state_committer 写入顺序第 7 步 (narrative 输出的 task_updates)
- create:       开局主任务 (commit_opening) / 剧情新任务
- list_by_session: context_builder / 前端任务面板
"""
from backend.app.models.models import Task
from backend.app.repositories.base import BaseRepo

VALID_STATUS = ("todo", "doing", "done", "failed")


class TaskRepo(BaseRepo):

    def list_by_session(self, session_id: int, status: str | None = None) -> list[Task]:
        q = self.db.query(Task).filter_by(session_id=session_id)
        if status:
            q = q.filter_by(status=status)
        return q.order_by(Task.id.asc()).all()

    def create(
        self, session_id: int, title: str,
        description: str | None = None, status: str = "todo",
    ) -> Task:
        if status not in VALID_STATUS:
            raise ValueError(f"非法任务状态: {status}")
        task = Task(session_id=session_id, title=title,
                    description=description, status=status)
        self.db.add(task)
        self.db.flush()
        return task

    def update_batch(self, session_id: int, updates: list[dict]) -> list[Task]:
        """批量更新任务状态; 匹配不到已有任务且带 create=True 时新建。

        updates 元素:
          {"task_id": int, "status": "done"}                      # 按 id 更新
          {"title": "活捉克仑可", "status": "doing"}                # 按 title 更新
          {"title": "新任务", "status": "todo", "create": True,
           "description": "..."}                                   # 新建
        返回受影响的 Task 列表。
        """
        touched: list[Task] = []
        for u in updates:
            status = u.get("status")
            if status not in VALID_STATUS:
                continue
            task: Task | None = None
            if u.get("task_id"):
                task = self.db.get(Task, u["task_id"])
                if task is not None and task.session_id != session_id:
                    task = None  # 防跨会话改写
            elif u.get("title"):
                task = (
                    self.db.query(Task)
                    .filter_by(session_id=session_id, title=u["title"])
                    .first()
                )
            if task is not None:
                task.status = status
                if u.get("description"):
                    task.description = u["description"]
                touched.append(task)
            elif u.get("create") and u.get("title"):
                touched.append(self.create(
                    session_id, u["title"], u.get("description"), status))
        if touched:
            self.db.flush()
        return touched
