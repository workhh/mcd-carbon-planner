---
name: mcd-carbon-planner
description: 麦碳算·家庭低碳点餐规划师。当用户要「点麦当劳/规划一家人的麦当劳餐/看看这顿麦当劳多少碳/家庭饮食碳账单/麦当劳历史订单分析」时使用。基于麦当劳中国 MCP（query-meals、list-nutrition-foods、calculate-price、order-list 等）获取实时菜单与营养数据，结合本地碳因子库做约束求解，输出低碳套餐方案与订单碳账单。
---

# 麦碳算 · 家庭低碳点餐规划师

基于麦当劳中国 MCP 的 Skill：把「一家人今天吃什么」变成一次低碳、控预算、看得懂碳排的点餐决策。

## 何时触发

- 「帮我规划一下今天一家三口的麦当劳」
- 「这顿麦当劳碳排多少 / 帮我算算减碳」
- 「分析我最近的麦当劳订单，给我饮食碳账单」
- 「预算 100 块，4 个人吃，别太碳」

## 前置条件

需要麦当劳中国 MCP Token（申请方式见 MCP_INTEGRATION.md）。
未配置 Token 时自动进入演示模式：使用内置示例菜单，功能完整可体验。
Token 通过环境变量 `MCD_MCP_TOKEN` 提供，**严禁写入任何文件或对话输出**。

## 工作流

1. **收集约束**（一次问清，别逐条追问）：
   - 人数、总预算（可「不限」）
   - 忌口/偏好：不吃牛肉、不吃鸡肉、素食
   - 就餐方式：堂食 / 外带 / 外送（外送问配送距离，默认 3.5km）
   - 减碳意愿：carbon_priority 0（省钱优先）— 1（减碳优先），默认 0.6
2. **取实时菜单**：调用 MCP `query-meals`（门店可售餐品）+ `list-nutrition-foods`（营养数据）构建候选池；候选池字段对齐 `planner.Meal`。
3. **求解**：`python -m mcd_carbon plan`（stdin 传 JSON：meals + constraints），返回结构化方案。
4. **输出**：把 `format_plan` 的结果直接呈现给用户，附一句碳评级白话解释。
5. **可选延伸**：
   - 查优惠：`query-store-coupons` / `available-coupons`，把券后价作为预算约束重跑一次；
   - 订单碳账单：`order-list` 拉历史订单 → `python -m mcd_carbon report`；
   - 下单：仅在用户明确说「就点这个」时调用 `create-order`，下单前必须复述订单明细与金额。

## 输出规范

- 方案用表格呈现：餐品 / 数量 / 单价 / 小计 / 热量 / 碳足迹；
- 必须给出：合计金额、人均碳足迹、碳评级、与经典牛肉套餐基准的减碳对比；
- 必须附口径声明：碳足迹为量级估算，餐品价格以实时菜单为准。

## 红线

- 不编造营养数据：MCP 没返回的字段留空或标注「未提供」；
- 不泄露 Token：输出、日志、示例文件中一律用 `YOUR_MCP_TOKEN` 占位；
- 不替用户直接付款：`create-order` 返回支付链接后交给用户自行确认支付。

## 项目结构

```
mcd_carbon/
├── factors.py      # 碳因子库（量级估算，含口径说明）
├── mcp_client.py   # 麦当劳 MCP 客户端（纯标准库，含演示降级）
├── planner.py      # 分层装盘约束求解
├── report.py       # 历史订单碳账单
├── demo_data.py    # 演示菜单
└── __main__.py     # CLI：demo / plan / report
```
