"""麦碳算 McdCarbon - 麦当劳家庭低碳点餐规划师.

基于麦当劳中国 MCP（https://mcp.mcd.cn）的 Skill：
- plan_meal:    人数/预算/忌口约束下的低碳套餐规划
- build_report: 历史订单碳账单蒸馏
"""

from .factors import (
    MEAL_CARBON_KGCO2E, meal_carbon, carbon_grade,
    PACKAGING_PER_ITEM_KGCO2E, DINE_IN_OVERHEAD_KGCO2E,
    TAKEAWAY_OVERHEAD_KGCO2E, DELIVERY_BASE_KGCO2E,
    DELIVERY_PER_KM_KGCO2E, DEFAULT_DELIVERY_KM,
)
from .mcp_client import McdMcpClient, McpTool, McpError, MCP_ENDPOINT, TOKEN_ENV
from .planner import (
    Meal, Constraints, PlanItem, PlanResult, plan_meal, format_plan,
    DEFAULT_MIN_KCAL_PER_PERSON, BASELINE_COMBO,
)
from .report import OrderRecord, OrderCarbonReport, build_report, format_report
from .demo_data import DEMO_MENU, DEMO_TOOLS

__version__ = "1.0.0"

__all__ = [
    "MEAL_CARBON_KGCO2E", "meal_carbon", "carbon_grade",
    "PACKAGING_PER_ITEM_KGCO2E", "DINE_IN_OVERHEAD_KGCO2E",
    "TAKEAWAY_OVERHEAD_KGCO2E", "DELIVERY_BASE_KGCO2E",
    "DELIVERY_PER_KM_KGCO2E", "DEFAULT_DELIVERY_KM",
    "McdMcpClient", "McpTool", "McpError", "MCP_ENDPOINT", "TOKEN_ENV",
    "Meal", "Constraints", "PlanItem", "PlanResult",
    "plan_meal", "format_plan", "DEFAULT_MIN_KCAL_PER_PERSON",
    "BASELINE_COMBO",
    "OrderRecord", "OrderCarbonReport", "build_report", "format_report",
    "DEMO_MENU", "DEMO_TOOLS",
]
