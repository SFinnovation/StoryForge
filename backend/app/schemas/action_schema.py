from pydantic import BaseModel, Field


class ActionRequest(BaseModel):
    """前端提交的玩家行动请求。"""

    action_text: str = Field(..., min_length=1, description="玩家输入的行动描述")


class ActionResponse(BaseModel):
    """后端调度完成后返回给前端的行动结果。"""

    check_result: dict = Field(..., description="骰子判定结果，如骰值、目标值、使用属性等")
    story_text: str = Field(..., description="AI 生成的后续剧情文本")
    new_clues: list[str] = Field(default_factory=list, description="本次行动新发现的线索列表")
    is_success: bool = Field(..., description="行动判定是否成功")
