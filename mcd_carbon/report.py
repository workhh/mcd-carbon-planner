"""历史订单碳账单：把 order-list 蒸馏成家庭饮食碳报告."""

from __future__ import annotations

from dataclasses import dataclass, field

from .factors import meal_carbon, MEAL_CARBON_KGCO2E

# 减碳替换建议表：高碳品类 → 低碳替代（kgCO2e/份）
SWAP_SUGGESTIONS = [
    ("beef_burger", "chicken_burger", "牛肉汉堡", "鸡肉汉堡"),
    ("beef_burger", "fish_burger", "牛肉汉堡", "麦香鱼"),
    ("fries", "corn_cup", "薯条", "玉米杯"),
    ("pork_burger", "egg_meal", "猪柳汉堡", "吉士蛋麦满分"),
    ("milkshake", "coffee_black", "奶昔", "美式咖啡"),
]


@dataclass
class OrderRecord:
    """一条历史订单（可来自 MCP order-list，或演示数据）."""
    date: str                          # YYYY-MM
    items: list[tuple[str, str, int]]  # (餐品名, category, 数量)
    overhead: str = "takeaway"
    delivery_km: float | None = None


@dataclass
class OrderCarbonReport:
    period: str = ""
    order_count: int = 0
    total_spend: float = 0.0
    total_carbon: float = 0.0
    by_category: dict[str, float] = field(default_factory=dict)
    top_carbon_items: list[tuple[str, float]] = field(default_factory=list)
    monthly: dict[str, float] = field(default_factory=dict)
    suggestions: list[str] = field(default_factory=list)

    @property
    def carbon_intensity(self) -> float:
        """碳强度：kgCO2e / 百元."""
        if self.total_spend <= 0:
            return 0.0
        return round(self.total_carbon / self.total_spend * 100, 3)

    def to_dict(self) -> dict:
        return {
            "统计周期": self.period,
            "订单数": self.order_count,
            "总支出（元）": round(self.total_spend, 2),
            "总碳足迹（kgCO2e）": round(self.total_carbon, 2),
            "碳强度（kgCO2e/百元）": self.carbon_intensity,
            "类别碳排占比": {
                k: f"{v / self.total_carbon * 100:.0f}%"
                for k, v in sorted(self.by_category.items(),
                                   key=lambda kv: -kv[1])
            } if self.total_carbon else {},
            "月度碳排（kgCO2e）": {k: round(v, 2)
                                   for k, v in self.monthly.items()},
            "减碳建议": self.suggestions,
        }


def build_report(orders: list[OrderRecord],
                 price_lookup: dict[str, float] | None = None) -> OrderCarbonReport:
    """汇总订单列表，生成碳账单."""
    rep = OrderCarbonReport()
    price_lookup = price_lookup or {}
    item_carbon: dict[str, float] = {}

    for o in orders:
        rep.order_count += 1
        rep.period = rep.period or o.date
        month = o.date
        rep.monthly.setdefault(month, 0.0)
        for name, category, qty in o.items:
            carbon = meal_carbon(category, 1, o.overhead, o.delivery_km) * qty
            rep.total_carbon += carbon
            rep.by_category[category] = (rep.by_category.get(category, 0.0)
                                         + carbon)
            rep.monthly[month] = rep.monthly[month] + carbon
            item_carbon[name] = item_carbon.get(name, 0.0) + carbon
            rep.total_spend += price_lookup.get(name, 0.0) * qty

    rep.top_carbon_items = sorted(item_carbon.items(),
                                  key=lambda kv: -kv[1])[:5]

    # 生成替换建议：找出实际消费过的高碳类别，给低碳替代
    for high, low, high_name, low_name in SWAP_SUGGESTIONS:
        if high in rep.by_category:
            delta = (MEAL_CARBON_KGCO2E[high]
                     - MEAL_CARBON_KGCO2E[low])
            rep.suggestions.append(
                f"把「{high_name}」换成「{low_name}」，"
                f"每份约减 {delta:.1f} kgCO2e")
    if not rep.suggestions:
        rep.suggestions.append("当前搭配已较低碳，继续保持。")
    return rep


def format_report(rep: OrderCarbonReport) -> str:
    d = rep.to_dict()
    lines = ["## 麦碳算 · 家庭饮食碳账单", ""]
    lines.append(f"统计周期：{d['统计周期']} ｜ 订单数：{d['订单数']}")
    lines.append("")
    lines.append(f"- 总支出：¥{d['总支出（元）']:.1f}"
                 f"（需提供价格表才能统计，未提供则显示 0）")
    lines.append(f"- 总碳足迹：**{d['总碳足迹（kgCO2e）']:.2f} kgCO2e**")
    lines.append(f"- 碳强度：{d['碳强度（kgCO2e/百元）']:.2f} kgCO2e/百元")
    lines.append("")
    if d["类别碳排占比"]:
        lines.append("**碳排来源（按类别）**：")
        for k, v in d["类别碳排占比"].items():
            lines.append(f"- {k}: {v}")
        lines.append("")
    if rep.top_carbon_items:
        lines.append("**Top 高碳单品**：")
        for name, carbon in rep.top_carbon_items:
            lines.append(f"- {name}: {carbon:.2f} kgCO2e")
        lines.append("")
    lines.append("**减碳建议**：")
    for s in d["减碳建议"]:
        lines.append(f"- {s}")
    lines.append("")
    lines.append("> 碳足迹为量级估算，仅供家庭饮食决策参考。")
    return "\n".join(lines)
