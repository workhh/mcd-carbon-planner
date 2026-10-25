# workbuddy.md — WorkBuddy 开发上下文记录

> 本文件记录本项目使用 **WorkBuddy** 从需求到交付的完整开发过程，供「麦当劳程序员创意开发大赛」WorkBuddy 专项奖励核验。
> 项目：麦碳算 McdCarbon · 家庭低碳点餐规划师（基于麦当劳中国 MCP 的 Skill）
> 开发日期：2026-10-25（1024 程序员节当天）
> 开发方式：需求描述、规则研究、架构决策、全部源代码、测试与文档均在 WorkBuddy 对话中由 AI 协作生成，无本地 IDE 参与。

---

## 第一阶段：需求确认（19:06）

**用户输入**：今天是程序员节，询问 WorkBuddy 是否有送积分活动。

**WorkBuddy 行动**：检索到两个活动——
1. 麦当劳 × WorkBuddy 程序员创意开发大赛（报名截止 10-25 23:59，前 100 名 + 3000 积分专项奖）；
2. WorkBuddy 1024 造物挑战。

**用户决策**：参加麦当劳大赛，要求"帮我完成这个任务"（从查规则到提交报名的全流程）。

## 第二阶段：规则研究（19:07–19:12）

通过 WebFetch 读取两个官方仓库：

- `M-China/mcd-developer-innovation-challenge`：拿到报名格式（Issue 正文四行式）、必交文件清单（README.md / CONTEST_DECLARATION.md / MCP_INTEGRATION.md / 源代码 / workbuddy.md）、排名规则（GitHub Star 数，10-26 00:00 定榜）、奖项设置。
- `M-China/mcd-mcp-server`：拿到接入方式（`https://mcp.mcd.cn`，Streamable HTTP，Bearer Token，限流 600 次/分钟）与 30 个 Tool 的完整清单（query-meals / list-nutrition-foods / calculate-price / order-list 等）。

**关键决策 1：项目创意选「碳足迹」而非「省钱/比价」**。
依据：榜单前三（611/512/491 stars）均为省钱比价方向，已红海；营养类已有多项目；而碳足迹 × 家庭场景组合空白，且与开发者主业（双碳/节能咨询）同源，有辨识度。

**关键决策 2：零第三方依赖 + 演示降级**。
理由：MCP Token 需开发者本人手机号申请，参赛项目必须做到"评审零成本体验"——未配置 Token 时自动切换内置演示菜单，全功能链路不中断。所有 Token 只走环境变量 `MCD_MCP_TOKEN`，符合官方参赛声明的信息安全条款。

## 第三阶段：核心实现（19:15–19:40）

按依赖顺序生成全部源代码（均在 WorkBuddy 对话中产出）：

1. `factors.py` — 碳因子库：餐品因子（牛肉 3.2 / 禽类 1.1 / 素食 0.35 kgCO2e 等）+ 包装 0.09/件 + 就餐方式附加（堂食/外带/外送含里程），附量级估算口径声明；
2. `mcp_client.py` — MCP 客户端：纯标准库实现 JSON-RPC over Streamable HTTP（initialize → tools/list → tools/call，SSE/JSON 双格式解析），150ms 节流，demo 模式降级；
3. `demo_data.py` — 12 个代表性餐品演示菜单；
4. `planner.py` — 约束求解：分层装盘；
5. `report.py` — 订单碳账单蒸馏；
6. `__main__.py` — CLI（demo / plan / report）；
7. `tests/test_planner.py` — 7 个测试用例。

## 第四阶段：测试与缺陷修复（19:40–19:50）

**测试结果：7/7 通过**（碳因子排序 / 预算约束 / 忌口 / 素食 / 减碳对比 / 报告构建 / 评级）。

**Bug 1（严重）：demo 输出出现「3 人聚餐 = 5 份中薯条 + 1 杯可乐」**。
根因：贪心按「饱腹度/碳^权重」排序，低碳小食（薯条）得分虚高，无结构约束。
修复：重构为**分层装盘**——主食层每人至少 1 份、热量缺口用主食补、配餐层每人最多 2 份、局部替换仅限同类互换。修复后 3 人方案 = 鸡肉/蛋主食 ×3 + 可乐，人均 2.01 kgCO2e，减碳 56%。

**Bug 2（中）：1 人食不限预算时把 7 个配餐全堆上（7.07 kgCO2e，D 级）**。
修复：配餐层加「每人最多 2 份」配额。修复后 = 2 主食 + 可乐 + 玉米杯，人均 3.55，减碳 22%。

**Bug 3（轻）：碳评级建议文案与方案内容矛盾**（方案无牛肉却提示"牛肉占比偏高"）。修复：文案改为中性表述。

## 第五阶段：文档与工程化（19:50–20:00）

- `CONTEST_DECLARATION.md`：官方模板原文下载（curl 遇 SSL 错误，改用 WebFetch 通道获取），内容未改一字；
- `README.md` / `MCP_INTEGRATION.md` / `SKILL.md`：面向用户 / 面向评审 / 面向 Agent 三层文档；
- `examples/demo_output.md`：`python -m mcd_carbon demo` 真实运行输出；
- 本地 `git init` + 提交（commit: feat: 麦碳算）。

## 第六阶段：发布与报名（20:01–20:33，实际过程）

1. 用户（GitHub 账号 workhh）生成 fine-grained PAT 交由 WorkBuddy 使用：验证凭据、读取用户名；
2. 通过 REST API（POST /user/repos）创建公开仓库 `workhh/mcd-carbon-planner`；
3. `git push` 遇 TLS 阻断（schannel 握手失败、代理 CONNECT 502）。诊断确认：github.com 主站链路被阻断，而 api.github.com 可达 → 改走 **Git Data API**（blobs → tree → commit → ref）单次提交 16 个文件，提交历史干净（Initial commit + feat commit）；
4. 报名 Issue 经 API 首次提交遇 403：fine-grained token 的仓库访问范围不覆盖第三方组织仓库（GitHub 平台硬限制，非配置问题）；
5. 用户改用手机端网页登录 GitHub（电脑端 github.com 主站同被阻断），按官方模板手工提交报名 Issue。**#1399 于北京时间 20:32:48 创建成功（Open），处于报名窗口内（截止 23:59）**，等待官方机器人异步校验。

报名 Issue（#1399）正文：

```
【参赛申请】
项目名称：麦碳算 McdCarbon · 家庭低碳点餐规划师
项目地址：https://github.com/workhh/mcd-carbon-planner
项目简介：基于麦当劳中国MCP的家庭低碳点餐规划Skill：调用 query-meals 与
list-nutrition-foods 获取实时菜单与营养数据，结合本地碳因子库做分层装盘约束求解
（支持人数/预算/忌口/人均钠上限/减碳权重），输出带碳足迹表格、碳评级与经典牛肉套餐
基准减碳对比的点餐方案；支持 order-list 历史订单蒸馏为家庭饮食月度碳账单并给出替换建议。
纯标准库零第三方依赖，未配置Token时自动进入演示模式可完整体验，含7个测试用例，
仓库含官方要求全部文件（README.md、CONTEST_DECLARATION.md、MCP_INTEGRATION.md、
源代码、workbuddy.md）。
```

## 交付清单核对（官方报名条件）

| 条件 | 状态 |
|---|---|
| README.md（介绍/安装/示例/目标用户） | ✓ |
| CONTEST_DECLARATION.md（官方原文未改） | ✓ |
| MCP_INTEGRATION.md（Server/Tool/流程/业务价值） | ✓ |
| 源代码（mcd_carbon/ + tests/，7 用例通过） | ✓ |
| workbuddy.md（本文件） | ✓ |
| 公开 Public 仓库 | ✓ workhh/mcd-carbon-planner |
| 项目创建时间在 2025-12-25 至 2026-10-25 23:59 | ✓ 2026-10-25 |
| 按标准格式发布报名 Issue | ✓ #1399 |

## 开发环境

- WorkBuddy（Agent 模式，Windows）
- Python 3.10+，零第三方依赖
- 全程未使用本地 IDE，源代码、测试、文档均由 WorkBuddy 对话生成
