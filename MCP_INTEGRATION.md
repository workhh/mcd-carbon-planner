# MCP_INTEGRATION.md

## 接入的 MCP Server

| 项 | 值 |
|---|---|
| 服务方 | 麦当劳中国 |
| 接入地址 | `https://mcp.mcd.cn` |
| 传输协议 | Streamable HTTP |
| 鉴权方式 | 请求头 `Authorization: Bearer <MCP_TOKEN>` |
| 限流 | 600 次/分钟（客户端已内置 150ms 最小间隔节流） |

配置方式（WorkBuddy：专家·技能·连接器 → 连接器 → 自定义连接器 → 配置 MCP）：

```json
{
  "mcpServers": {
    "mcd-mcp": {
      "type": "streamablehttp",
      "url": "https://mcp.mcd.cn",
      "headers": {
        "Authorization": "Bearer YOUR_MCP_TOKEN"
      }
    }
  }
}
```

> Token 申请：open.mcd.cn 手机号登录 → 控制台 → 激活。
> **本项目不存储、不硬编码任何 Token**，运行时从环境变量 `MCD_MCP_TOKEN` 读取。

## 使用的 Tool 清单

| Tool | 用途 | 调用时机 |
|---|---|---|
| `query-meals` | 查询门店可售餐品（分类、餐品编码、标签） | 构建点餐候选池 |
| `list-nutrition-foods` | 餐品营养信息（能量、蛋白质、脂肪、碳水、钠、钙） | 填充 Meal 营养字段 |
| `query-meal-detail` | 餐品详情与套餐组成 | 套餐替换选项分析 |
| `calculate-price` | 商品价格计算（可含优惠券） | 方案定价与预算校验 |
| `query-store-coupons` | 当前门店可用优惠券 | 「券后再规划」模式 |
| `available-coupons` / `auto-bind-coupons` | 麦麦省领券 | 优惠叠加分析 |
| `order-list` | 历史订单 | 订单碳账单 |
| `query-nearby-stores` | 附近门店 | 定位默认门店 |
| `campaign-calendar` | 营销活动日历 | 活动期点餐提示 |

## 调用流程

### 流程 A：低碳点餐规划

```
用户约束（人数/预算/忌口/就餐方式）
   │
   ▼
query-meals ─────────► 候选池（餐品名、类别、编码）
   │
   ▼
list-nutrition-foods ─► 营养字段（kcal/蛋白/钠）
   │
   ▼
mcd_carbon.planner.plan_meal（本地约束求解）
   │
   ▼
方案输出（表格 + 碳评级 + 基准对比）
```

### 流程 B：家庭饮食碳账单

```
order-list（近 N 期历史订单）
   │
   ▼
映射为 OrderRecord（月份、餐品 category、数量）
   │
   ▼
mcd_carbon.report.build_report（本地计算）
   │
   ▼
碳账单（总碳排 / 碳强度 / Top 高碳单品 / 替换建议）
```

## 数据映射说明

MCP 返回的餐品编码到本地碳因子类别（`factors.MEAL_CARBON_KGCO2E` 的 key）的映射由 Skill 层完成：
先按餐品名称关键词匹配类别（牛肉/鸡肉/鱼肉/蛋/素食/小食/饮料），
无法匹配时使用 `default`（1.00 kgCO2e）并在输出中标注「估算口径：默认类」。

## 业务价值

1. **决策价值**：把「吃什么」从拍脑袋变成有约束（预算/热量/忌口）有目标（低碳）的求解问题；
2. **碳账价值**：麦当劳订单天然带餐品明细，是家庭饮食碳足迹最高频、最易得的数据源，本项目把它变成可持续跟踪的月度碳账单；
3. **场景差异**：现有参赛项目集中在「省钱/比价」与「营养查询」，碳足迹 × 家庭场景组合是空白切入点，且与企业 ESG/双碳咨询实务（本作者主业方向）同源。

## 演示降级

未配置 `MCD_MCP_TOKEN` 时，`mcp_client` 自动切换到演示模式：
`tools/list` 返回内置工具描述，`query-meals` / `list-nutrition-foods` 返回
`demo_data.DEMO_MENU`（12 个代表性餐品），完整功能链路不中断，
方便评审与用户零成本体验。演示模式下所有输出均标注「演示模式」。
