import random
from typing import TypedDict


class ActionCheckResult(TypedDict):
    dice_roll: int
    final_value: int
    is_success: bool


def roll_action_check(
    attribute_modifier: int,
    dc: int,
    skill_bonus: int = 0,
) -> ActionCheckResult:
    """
    执行 DND 风格的 d20 行动检定。

    掷骰结果加上属性修正与技能加值，与难度等级 (DC) 比较以判定成败。
    """
    dice_roll = random.randint(1, 20)
    final_value = dice_roll + attribute_modifier + skill_bonus
    is_success = final_value >= dc

    return {
        "dice_roll": dice_roll,
        "final_value": final_value,
        "is_success": is_success,
    }



"""
# ---------------------------------------------------------
# 以下为本地快速测试代码，正式环境中不会被执行
# ---------------------------------------------------------
if __name__ == "__main__":
    print("=== 开始测试 d20 判定系统 ===")
    
    # 模拟场景 1：普通潜行 (属性加成高，难度中等)
    print("\n[场景 1] 盗贼尝试潜行绕过守卫 (DC 14, 敏捷修正 +4)")
    result1 = roll_action_check(attribute_modifier=4, skill_bonus=0, dc=14)
    print(f"掷骰结果: {result1['dice_roll']}, 最终数值: {result1['final_value']}, 是否成功: {result1['is_success']}")
    
    # 模拟场景 2：战士用力推开巨石 (属性加成一般，难度极高)
    print("\n[场景 2] 战士尝试推开巨石 (DC 20, 力量修正 +2)")
    result2 = roll_action_check(attribute_modifier=2, skill_bonus=0, dc=20)
    print(f"掷骰结果: {result2['dice_roll']}, 最终数值: {result2['final_value']}, 是否成功: {result2['is_success']}")
    
    # 模拟场景 3：法师解读古老符文 (带有技能加成)
    print("\n[场景 3] 法师解读古老符文 (DC 15, 智力修正 +3, 奥秘技能加成 +2)")
    result3 = roll_action_check(attribute_modifier=3, skill_bonus=2, dc=15)
    print(f"掷骰结果: {result3['dice_roll']}, 最终数值: {result3['final_value']}, 是否成功: {result3['is_success']}")
"""