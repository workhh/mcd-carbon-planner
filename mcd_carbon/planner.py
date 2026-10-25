"""家庭低碳点餐规划器：约束求解 + 碳足迹对比.

求解思路（启发式，非全局最优，README 中已声明）：
1. 按忌口/素食约束过滤候选池
2. 以「饱腹度 / 碳足迹^碳优先权重」为得分贪心装盘，满足人均热量下限
3. 局部替换优化：在预算内尝试 swap，朝更低总碳 / 更优价格迭代
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .factors import meal_carbon, carbon_grade

# 快餐场景下的人均热量下限（kcal），一顿正餐的保守饱腹需求
DEFAULT_MIN_KCAL_PER_PERSON = 550

# 基准餐：经典牛肉汉堡套餐（牛肉汉堡 + 中薯 + 可乐），用于减碳对比
BASELINE_COMBO = ("beef_burger", "fries", "soft_drink")


@dataclass
class Meal:
    """一份餐品（可来自 MCP query-meals / list-nutrition-foods，或演示数据）."""
    name: str
    category: str                     # 碳因子类别代码，见 factors.MEAL_CARBON_KGCO2E
    price: float                      # 单点价格（元）
    kcal: float                       # 能量（kcal）
    protein: float = 0.0              # 蛋白质（g）
    sodium: float = 0.0               # 钠（mg）
    satiety: float = 0.5              # 饱腹度 0-1（用于装盘）
    packaging_items: int = 1          # 独立包装件数
    tags: list[str] = field(default_factory=list)  # 如 ["beef"] ["veggie"]

    def carbon(self, overhead: str = "takeaway",
               delivery_km: float | None = None) -> float:
        return meal_carbon(self.category, self.packaging_items,
                           overhead, delivery_km)

    @property
    def carbon_per_kcal(self) -> float:
        """每千卡碳排（gCO2e/kcal），越低越优."""
        if self.kcal <= 0:
            return float("inf")
        return self.carbon() * 1000 / self.kcal


@dataclass
class Constraints:
    people: int = 1
    budget: float | None = None       # 总预算（元），None 为不限
    no_beef: bool = False
    no_chicken: bool = False
    vegetarian: bool = False
    max_sodium_per_person: float | None = None   # mg
    min_kcal_per_person: float = DEFAULT_MIN_KCAL_PER_PERSON
    overhead: str = "takeaway"        # dine_in / takeaway / delivery
    delivery_km: float | None = None
    carbon_priority: float = 0.6      # 0=只看省钱，1=只看减碳


@dataclass
class PlanItem:
    meal: Meal
    quantity: int

    @property
    def price(self) -> float:
        return self.meal.price * self.quantity

    @property
    def kcal(self) -> float:
        return self.meal.kcal * self.quantity

    @property
    def carbon(self) -> float:
        return self.meal.carbon() * self.quantity


@dataclass
class PlanResult:
    items: list[PlanItem]
    constraints: Constraints

    @property
    def total_price(self) -> float:
        return round(sum(i.price for i in self.items), 2)

    @property
    def total_kcal(self) -> float:
        return round(sum(i.kcal for i in self.items), 1)

    @property
    def total_carbon(self) -> float:
        return round(sum(i.carbon for i in self.items), 3)

    @property
    def total_protein(self) -> float:
        return round(sum(i.meal.protein * i.quantity for i in self.items), 1)

    @property
    def per_person_carbon(self) -> float:
        return round(self.total_carbon / max(self.constraints.people, 1), 3)

    def baseline_carbon(self) -> float:
        """基准牛肉汉堡套餐（按同人数）的估算碳足迹."""
        per_combo = sum(meal_carbon(c) for c in BASELINE_COMBO)
        return round(per_combo * self.constraints.people, 3)

    def carbon_saved_vs_baseline(self) -> float:
        return round(max(0.0, self.baseline_carbon() - self.total_carbon), 3)

    def summary(self) -> dict:
        grade, advice = carbon_grade(self.total_carbon,
                                     self.constraints.people)
        baseline = self.baseline_carbon()
        saved = self.carbon_saved_vs_baseline()
        return {
            "总价（元）": self.total_price,
            "总热量（kcal）": self.total_kcal,
            "总蛋白（g）": self.total_protein,
            "总碳足迹（kgCO2e）": self.total_carbon,
            "人均碳足迹（kgCO2e）": self.per_person_carbon,
            "碳评级": grade,
            "建议": advice,
            "基准牛肉套餐碳排（kgCO2e）": baseline,
            "较基准减碳（kgCO2e）": saved,
            "减碳比例": f"{saved / baseline * 100:.0f}%" if baseline else "—",
            "明细": [
                {"餐品": i.meal.name, "数量": i.quantity,
                 "单价（元）": i.meal.price, "小计（元）": i.price,
                 "热量（kcal）": i.kcal,
                 "碳足迹（kgCO2e）": i.carbon}
                for i in self.items
            ],
        }


def _passes(meal: Meal, c: Constraints) -> bool:
    if c.no_beef and "beef" in meal.tags:
        return False
    if c.no_chicken and "chicken" in meal.tags:
        return False
    if c.vegetarian and "veggie" not in meal.tags and meal.category in (
            "beef_burger", "pork_burger", "chicken_burger",
            "chicken_nugget", "fish_burger", "shrimp"):
        return False
    return True


def _kcal_ok(items: list[PlanItem], c: Constraints) -> bool:
    total = sum(i.kcal for i in items)
    return total >= c.min_kcal_per_person * c.people


def _budget_ok(items: list[PlanItem], c: Constraints) -> bool:
    if c.budget is None:
        return True
    return sum(i.price for i in items) <= c.budget


def _sodium_ok(items: list[PlanItem], c: Constraints) -> bool:
    if c.max_sodium_per_person is None:
        return True
    total = sum(i.meal.sodium * i.quantity for i in items)
    return total <= c.max_sodium_per_person * c.people


def _score(m: Meal, w: float) -> float:
    """性价比得分：饱腹度优先，碳足迹按权重惩罚."""
    return m.satiety / max(m.carbon(), 1e-6) ** w


def plan_meal(meals: list[Meal], c: Constraints,
              max_swap_rounds: int = 200) -> PlanResult:
    """主入口：给定候选餐品与约束，返回低碳点餐方案.

    分层装盘策略（避免「5 份薯条当饭」这类结构失衡）：
    1. 主食层：每人至少 1 份主食，热量缺口优先用主食补齐
    2. 配餐饮料层：每类每人限 1 份，按性价比补足体验
    3. 局部替换优化：仅同类互换，朝更低总碳迭代
    """
    pool = [m for m in meals if _passes(m, c)]
    if not pool:
        raise ValueError("约束过严，候选池为空——请放宽忌口或预算")

    w = max(0.0, min(1.0, c.carbon_priority))
    mains = sorted((m for m in pool if "main" in m.tags),
                   key=lambda m: -_score(m, w))
    others = sorted((m for m in pool if "main" not in m.tags),
                    key=lambda m: -_score(m, w))
    if not mains:
        # 候选池无主食时降级：取饱腹度最高的前 N 份充当主食
        mains = sorted(pool, key=lambda m: -m.satiety)[:c.people]
        others = [m for m in pool if m not in mains]

    items: list[PlanItem] = [PlanItem(m, 1) for m in mains[:c.people]]

    # 1) 热量缺口：在预算内追加主食份数
    guard = 0
    while not _kcal_ok(items, c) and guard < 50:
        guard += 1
        grown = False
        for it in items:
            if it.meal in mains[:c.people]:
                trial = PlanItem(it.meal, it.quantity + 1)
                new_items = [trial if x is it else x for x in items]
                if _budget_ok(new_items, c):
                    items = new_items
                    grown = True
                    break
        if not grown:
            break

    # 2) 配餐饮料层：每人最多 2 份配餐（一杯饮料 + 一份小食的典型结构）
    side_quota = c.people * 2
    for m in others:
        if side_quota <= 0:
            break
        trial = items + [PlanItem(m, 1)]
        if _budget_ok(trial, c) and _sodium_ok(trial, c):
            items = trial
            side_quota -= 1

    # 3) 局部替换优化：仅同类互换
    chosen = {i.meal.name for i in items}
    for _ in range(max_swap_rounds):
        improved = False
        for cand in pool:
            if cand.name in chosen:
                continue
            for idx, cur in enumerate(items):
                cur_is_main = "main" in cur.meal.tags
                cand_is_main = "main" in cand.tags
                if cur_is_main != cand_is_main:
                    continue
                trial = list(items)
                trial[idx] = PlanItem(cand, cur.quantity)
                if not (_budget_ok(trial, c) and _kcal_ok(trial, c)
                        and _sodium_ok(trial, c)):
                    continue
                d_carbon = (sum(i.carbon for i in trial)
                            - sum(i.carbon for i in items))
                d_price = (sum(i.price for i in trial)
                           - sum(i.price for i in items))
                if d_carbon < -1e-9 or (abs(d_carbon) <= 1e-9
                                        and d_price < -0.01):
                    items = trial
                    chosen = {i.meal.name for i in items}
                    improved = True
                    break
            if improved:
                break
        if not improved:
            break

    # 4) 合并同品多项
    merged: dict[str, PlanItem] = {}
    for i in items:
        if i.meal.name in merged:
            merged[i.meal.name].quantity += i.quantity
        else:
            merged[i.meal.name] = PlanItem(i.meal, i.quantity)

    return PlanResult(items=list(merged.values()), constraints=c)


def format_plan(result: PlanResult) -> str:
    """人类可读的点餐方案报告."""
    s = result.summary()
    lines = ["## 麦碳算 · 家庭低碳点餐方案", ""]
    lines.append(f"用餐人数：{result.constraints.people} 人"
                 f" | 预算：{'不限' if result.constraints.budget is None else str(result.constraints.budget) + ' 元'}"
                 f" | 就餐方式：{result.constraints.overhead}")
    lines.append("")
    lines.append("| 餐品 | 数量 | 单价 | 小计 | 热量 | 碳足迹 |")
    lines.append("|---|---|---|---|---|---|")
    for d in s["明细"]:
        lines.append(
            f"| {d['餐品']} | {d['数量']} | ¥{d['单价（元）']:.1f} "
            f"| ¥{d['小计（元）']:.1f} | {d['热量（kcal）']:.0f} kcal "
            f"| {d['碳足迹（kgCO2e）']:.2f} kgCO2e |")
    lines += [
        "",
        f"**合计：¥{s['总价（元）']:.1f} ｜ {s['总热量（kcal）']:.0f} kcal "
        f"｜ 蛋白 {s['总蛋白（g）']:.0f}g ｜ "
        f"总碳足迹 {s['总碳足迹（kgCO2e）']:.2f} kgCO2e "
        f"（人均 {s['人均碳足迹（kgCO2e）']:.2f}）**",
        "",
        f"碳评级：**{s['碳评级']}** —— {s['建议']}",
        "",
        f"对比经典牛肉套餐（同 {result.constraints.people} 人）基准碳排 "
        f"{s['基准牛肉套餐碳排（kgCO2e）']:.2f} kgCO2e，"
        f"本方案减碳 {s['较基准减碳（kgCO2e）']:.2f} kgCO2e（{s['减碳比例']}）。",
        "",
        "> 碳足迹为量级估算（公开 LCA 研究区间中值 + 包装/能耗模型），"
        "仅供横向对比；餐品与价格以麦当劳实时菜单为准。",
    ]
    return "\n".join(lines)
