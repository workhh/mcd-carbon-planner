"""麦碳算测试套件：运行 python -m pytest tests/ 或 python tests/test_planner.py"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcd_carbon import (
    Meal, Constraints, plan_meal, format_plan,
    meal_carbon, carbon_grade, build_report, OrderRecord,
    format_report, DEMO_MENU,
)


def meals_from_demo():
    return [
        Meal(name=m["name"], category=m["category"], price=m["price"],
             kcal=m["kcal"], protein=m["protein"], sodium=m["sodium"],
             satiety=m["satiety"], packaging_items=m["packaging_items"],
             tags=m["tags"])
        for m in DEMO_MENU
    ]


def test_meal_carbon_ordering():
    """牛肉类碳足迹应显著高于禽类和素食类."""
    beef = meal_carbon("beef_burger")
    chicken = meal_carbon("chicken_burger")
    corn = meal_carbon("corn_cup")
    assert beef > chicken > corn > 0
    # 外送应高于堂食（含配送里程与包装附加）
    assert meal_carbon("beef_burger", overhead="delivery") > \
        meal_carbon("beef_burger", overhead="dine_in")


def test_plan_respects_budget():
    meals = meals_from_demo()
    c = Constraints(people=2, budget=80.0, carbon_priority=0.8)
    result = plan_meal(meals, c)
    assert result.total_price <= 80.0
    assert result.total_kcal >= 550 * 2


def test_plan_respects_no_beef():
    meals = meals_from_demo()
    c = Constraints(people=1, carbon_priority=1.0, no_beef=True)
    result = plan_meal(meals, c)
    for item in result.items:
        assert "beef" not in item.meal.tags, f"含牛肉: {item.meal.name}"


def test_plan_vegetarian():
    meals = meals_from_demo()
    c = Constraints(people=1, vegetarian=True, carbon_priority=0.7)
    result = plan_meal(meals, c)
    for item in result.items:
        assert item.meal.category not in (
            "beef_burger", "pork_burger", "chicken_burger",
            "chicken_nugget", "fish_burger", "shrimp")


def test_plan_reduces_carbon_vs_baseline():
    """减碳模式下总碳应低于牛肉套餐基准."""
    meals = meals_from_demo()
    c = Constraints(people=2, carbon_priority=1.0)
    result = plan_meal(meals, c)
    assert result.total_carbon < result.baseline_carbon()
    assert result.carbon_saved_vs_baseline() > 0


def test_report_build():
    orders = [
        OrderRecord("2026-09", [("巨无霸", "beef_burger", 1),
                                ("中薯条", "fries", 1),
                                ("可口可乐（中）", "soft_drink", 1)]),
        OrderRecord("2026-10", [("麦辣鸡腿堡", "chicken_burger", 2)]),
    ]
    rep = build_report(orders, price_lookup={"巨无霸": 26.5})
    assert rep.order_count == 2
    assert rep.total_carbon > 0
    assert "beef_burger" in rep.by_category
    assert any("牛肉" in s for s in rep.suggestions)
    assert rep.carbon_intensity >= 0


def test_carbon_grade():
    grade, advice = carbon_grade(2.0, 1)
    assert grade.startswith("A") or grade.startswith("B")


def _run_all():
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {t.__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} 通过")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run_all())
