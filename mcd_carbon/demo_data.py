"""演示数据：无 MCP Token 时的内置示例菜单.

价格为麦当劳公开菜单的量级参考（单点价，非优惠价），
营养数据为同类快餐产品的常见量级。
真实场景下请通过 MCP query-meals / list-nutrition-foods 获取实时数据。
"""

from __future__ import annotations

from .mcp_client import McpTool

DEMO_TOOLS = [
    McpTool("query-meals", "查询当前可售卖的餐品列表"),
    McpTool("query-meal-detail", "查询餐品详情"),
    McpTool("list-nutrition-foods", "餐品营养信息列表"),
    McpTool("calculate-price", "商品价格计算"),
    McpTool("query-store-coupons", "查询当前门店可用优惠券"),
    McpTool("available-coupons", "麦麦省券列表查询"),
    McpTool("order-list", "查询历史订单"),
    McpTool("query-my-account", "我的积分查询"),
    McpTool("campaign-calendar", "活动日历查询"),
]

DEMO_MENU = [
    {
        "name": "巨无霸", "category": "beef_burger", "price": 26.5,
        "kcal": 530, "protein": 27.0, "sodium": 1020, "satiety": 0.95,
        "packaging_items": 2, "tags": ["beef", "main"],
    },
    {
        "name": "麦辣鸡腿堡", "category": "chicken_burger", "price": 22.0,
        "kcal": 490, "protein": 24.0, "sodium": 980, "satiety": 0.90,
        "packaging_items": 2, "tags": ["chicken", "main"],
    },
    {
        "name": "板烧鸡腿堡", "category": "chicken_burger", "price": 23.0,
        "kcal": 470, "protein": 26.0, "sodium": 890, "satiety": 0.90,
        "packaging_items": 2, "tags": ["chicken", "main"],
    },
    {
        "name": "麦香鱼", "category": "fish_burger", "price": 21.0,
        "kcal": 380, "protein": 17.0, "sodium": 760, "satiety": 0.75,
        "packaging_items": 2, "tags": ["fish", "main"],
    },
    {
        "name": "猪柳蛋麦满分", "category": "pork_burger", "price": 19.5,
        "kcal": 430, "protein": 21.0, "sodium": 870, "satiety": 0.85,
        "packaging_items": 3, "tags": ["pork", "main", "breakfast"],
    },
    {
        "name": "吉士蛋麦满分", "category": "egg_meal", "price": 15.0,
        "kcal": 320, "protein": 15.0, "sodium": 620, "satiety": 0.65,
        "packaging_items": 3, "tags": ["egg", "main", "breakfast", "veggie_ok"],
    },
    {
        "name": "麦乐鸡（4块）", "category": "chicken_nugget", "price": 12.0,
        "kcal": 230, "protein": 12.0, "sodium": 540, "satiety": 0.45,
        "packaging_items": 1, "tags": ["chicken", "snack"],
    },
    {
        "name": "中薯条", "category": "fries", "price": 13.5,
        "kcal": 320, "protein": 3.5, "sodium": 210, "satiety": 0.50,
        "packaging_items": 1, "tags": ["side", "veggie"],
    },
    {
        "name": "玉米杯（小）", "category": "corn_cup", "price": 8.5,
        "kcal": 130, "protein": 3.0, "sodium": 60, "satiety": 0.35,
        "packaging_items": 1, "tags": ["side", "veggie"],
    },
    {
        "name": "可口可乐（中）", "category": "soft_drink", "price": 10.5,
        "kcal": 170, "protein": 0.0, "sodium": 15, "satiety": 0.20,
        "packaging_items": 1, "tags": ["drink", "veggie"],
    },
    {
        "name": "圆筒冰淇淋", "category": "ice_cream", "price": 6.5,
        "kcal": 150, "protein": 3.5, "sodium": 55, "satiety": 0.15,
        "packaging_items": 1, "tags": ["dessert", "veggie"],
    },
    {
        "name": "苹果派", "category": "pie", "price": 9.0,
        "kcal": 240, "protein": 2.0, "sodium": 180, "satiety": 0.25,
        "packaging_items": 1, "tags": ["dessert", "veggie"],
    },
]
