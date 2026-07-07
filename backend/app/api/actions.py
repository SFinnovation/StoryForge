from fastapi import APIRouter

from app.schemas.action_schema import ActionRequest, ActionResponse
from app.services.dice_service import roll_action_check

router = APIRouter(prefix="/sessions", tags=["actions"])


@router.post("/{session_id}/action", response_model=ActionResponse)
def submit_action(session_id: str, payload: ActionRequest) -> ActionResponse:
    """玩家行动调度入口：编排角色状态、AI 判定、掷骰与剧情生成。"""
    _ = session_id

    # 第一步：Mock 获取当前角色状态 (假设属性修正为 +3)
    attribute_modifier = 3

    # 第二步：Mock 调用 AI 判断行动 (假设判定为潜行，DC 为 15)
    action_type = "潜行"
    dc = 15

    # 第三步：真实调用 dice_service 掷骰
    dice_result = roll_action_check(attribute_modifier=attribute_modifier, dc=dc)
    is_success = dice_result["is_success"]

    # 第四步：Mock 调用 AI 生成剧情 (根据掷骰成败返回描述文本)
    if is_success:
        story_text = (
            f"你决定「{payload.action_text}」。"
            "你成功潜入阴影之中，守卫丝毫没有察觉你的踪迹。"
        )
        new_clues = ["守卫换岗的规律"]
    else:
        story_text = (
            f"你决定「{payload.action_text}」。"
            "脚下不慎踩断枯枝，守卫立刻警觉地朝你的方向看来。"
        )
        new_clues = []

    check_result = {
        "dice_roll": dice_result["dice_roll"],
        "final_value": dice_result["final_value"],
        "dc": dc,
        "attribute_modifier": attribute_modifier,
        "action_type": action_type,
    }

    # 第五步：构造 ActionResponse 并返回
    return ActionResponse(
        check_result=check_result,
        story_text=story_text,
        new_clues=new_clues,
        is_success=is_success,
    )
