"""CLI 入口：python -m mcd_carbon [demo|plan|report]

- demo:  无 Token 演示模式，用内置示例菜单跑通全流程
- plan:  点餐规划（从 stdin 读 JSON 约束，或交互参数）
- report:订单碳账单（从 stdin 读 JSON 订单列表）
"""

from __future__ import annotations

import json
import sys

from . import (
    DEMO_MENU, plan_meal, format_plan, build_report, format_report,
    Meal, Constraints, OrderRecord, McdMcpClient, TOKEN_ENV,
)


def _demo_meals():
    return [
        Meal(name=m["name"], category=m["category"], price=m["price"],
             kcal=m["kcal"], protein=m["protein"], sodium=m["sodium"],
             satiety=m["satiety"], packaging_items=m["packaging_items"],
             tags=m["tags"])
        for m in DEMO_MENU
    ]


def _cmd_demo():
    print("=== 演示模式（未检测到 MCP Token，使用内置示例菜单）===\n")

    # 场景 1：三口之家周末聚餐，预算 100，减碳优先
    c = Constraints(people=3, budget=100.0, carbon_priority=0.8)
    r1 = plan_meal(_demo_meals(), c)
    print(format_plan(r1))

    # 场景 2：一人食，不吃牛肉
    c2 = Constraints(people=1, carbon_priority=0.9, no_beef=True)
    r2 = plan_meal(_demo_meals(), c2)
    print("\n\n" + format_plan(r2))

    # 场景 3：历史订单碳账单
    orders = [
        OrderRecord("2026-09", [("巨无霸", "beef_burger", 2),
                                ("中薯条", "fries", 2),
                                ("可口可乐（中）", "soft_drink", 2)],
                    overhead="delivery", delivery_km=4.0),
        OrderRecord("2026-10", [("麦辣鸡腿堡", "chicken_burger", 3),
                                ("麦乐鸡（4块）", "chicken_nugget", 2)]),
    ]
    prices = {m["name"]: m["price"] for m in DEMO_MENU}
    rep = build_report(orders, price_lookup=prices)
    print("\n\n" + format_report(rep))


def _cmd_plan():
    payload = json.load(sys.stdin)
    c = Constraints(**payload.get("constraints", {}))
    meals = [Meal(**m) for m in payload["meals"]]
    print(format_plan(plan_meal(meals, c)))


def _cmd_report():
    payload = json.load(sys.stdin)
    orders = [OrderRecord(**o) for o in payload["orders"]]
    prices = payload.get("prices", {})
    print(format_report(build_report(orders, price_lookup=prices)))


def main(argv=None):
    argv = argv or sys.argv[1:]
    cmd = argv[0] if argv else "demo"
    if cmd == "demo":
        _cmd_demo()
    elif cmd == "plan":
        _cmd_plan()
    elif cmd == "report":
        _cmd_report()
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
