"""麦碳算 McdCarbon - 麦当劳餐品碳足迹因子库.

量级估算说明：
    本模块中的因子为公开研究的量级参考值（kgCO2e/份或 kgCO2e/件），
    综合 IPCC 国家温室气体清单排放因子、食物生命周期评价（LCA）研究的
    公开区间中值，以及连锁快餐供应链的一般特征估算。
    所有数值仅供同一场景下的横向对比使用，不作为精确核算依据。
"""

from __future__ import annotations

# 餐品碳足迹：kgCO2e / 份（按标准单份出品）
# key 为餐品类别代码，planner 通过餐品的 category 字段匹配
MEAL_CARBON_KGCO2E: dict[str, float] = {
    # 牛肉类（反刍动物肠道发酵 + 饲料种植是主要排放源）
    "beef_burger": 3.20,
    "beef_combo_extra": 0.60,   # 牛肉汉堡套餐中额外的酱料/芝士增量
    # 猪肉类
    "pork_burger": 1.80,
    # 禽肉类
    "chicken_burger": 1.10,
    "chicken_nugget": 1.00,     # 麦乐鸡（4-6 块标准份）
    "chicken_wing": 1.30,
    # 鱼虾类
    "fish_burger": 1.30,
    "shrimp": 1.60,
    # 蛋奶素食类
    "egg_meal": 0.90,           # 麦满分系列
    "veggie_burger": 0.55,
    "salad": 0.35,
    # 主食小食
    "fries": 0.45,              # 中薯标准份
    "corn_cup": 0.25,
    "rice_bowl": 0.70,
    "soup": 0.30,
    # 饮料甜品
    "soft_drink": 0.22,         # 可乐/零度/雪碧等
    "milkshake": 0.75,
    "ice_cream": 0.60,
    "pie": 0.55,
    "coffee_black": 0.30,
    "coffee_milk": 0.55,
    "tea": 0.18,
    "water": 0.08,
    # 兜底
    "default": 1.00,
}

# 每件独立包装的碳足迹：kgCO2e / 件（纸盒、纸袋、塑料杯盖、吸管等）
PACKAGING_PER_ITEM_KGCO2E = 0.09

# 就餐方式附加碳足迹：kgCO2e / 单
# 堂食：门店能耗分摊到堂食订单（含清洁、翻台）
# 外带：包装用量略高于堂食
# 外送：在包装基础上叠加配送里程
DINE_IN_OVERHEAD_KGCO2E = 0.10
TAKEAWAY_OVERHEAD_KGCO2E = 0.14
DELIVERY_BASE_KGCO2E = 0.15
# 外送里程附加：kgCO2e / 公里（电动自行车估算值）
DELIVERY_PER_KM_KGCO2E = 0.028

# 门店平均配送半径（公里），用于外送单的默认里程估算
DEFAULT_DELIVERY_KM = 3.5


def meal_carbon(category: str, packaging_items: int = 1,
                overhead: str = "takeaway",
                delivery_km: float | None = None) -> float:
    """计算单份餐品的估算碳足迹（kgCO2e）。

    Args:
        category: 餐品类别代码，见 MEAL_CARBON_KGCO2E
        packaging_items: 该餐品的独立包装件数
        overhead: 就餐方式 "dine_in" / "takeaway" / "delivery"
        delivery_km: 外送里程，None 时按默认半径估算
    """
    base = MEAL_CARBON_KGCO2E.get(category, MEAL_CARBON_KGCO2E["default"])
    total = base + packaging_items * PACKAGING_PER_ITEM_KGCO2E

    if overhead == "dine_in":
        total += DINE_IN_OVERHEAD_KGCO2E
    elif overhead == "takeaway":
        total += TAKEAWAY_OVERHEAD_KGCO2E
    elif overhead == "delivery":
        km = delivery_km if delivery_km is not None else DEFAULT_DELIVERY_KM
        total += DELIVERY_BASE_KGCO2E + km * DELIVERY_PER_KM_KGCO2E
    return round(total, 3)


def carbon_grade(total_kgco2e: float, people: int = 1) -> tuple[str, str]:
    """按人均碳足迹给出评级与建议。

    参照量级：一顿快餐人均约 1.5-3.5 kgCO2e。
    """
    per_person = total_kgco2e / max(people, 1)
    if per_person <= 1.5:
        return "A（低碳）", "这顿的人均碳排控制得很好，保持当前搭配思路。"
    if per_person <= 2.5:
        return "B（中等）", "人均碳排中等，替换 1 份牛肉类为禽类可再降约 2 kgCO2e。"
    if per_person <= 4.0:
        return "C（偏高）", "人均碳排偏高，优先把主食换成禽类/鱼类/蛋类，小食把薯条换成玉米杯。"
    return "D（高碳）", "人均碳排偏高，建议重新搭配：主食去牛肉化 + 减少小食份数 + 优先减主食碳。"


__all__ = [
    "MEAL_CARBON_KGCO2E",
    "PACKAGING_PER_ITEM_KGCO2E",
    "DINE_IN_OVERHEAD_KGCO2E",
    "TAKEAWAY_OVERHEAD_KGCO2E",
    "DELIVERY_BASE_KGCO2E",
    "DELIVERY_PER_KM_KGCO2E",
    "DEFAULT_DELIVERY_KM",
    "meal_carbon",
    "carbon_grade",
]
