from pydantic import BaseModel, Field


class ActionRequest(BaseModel):
    action_text: str = Field(..., min_length=1, description="玩家输入的行动描述")
