---
name: store-report
description: "Use for generating a professional store big-data report (店铺大数据报告) from the HandaaS store MCP — covering 餐饮品牌门店、餐饮门店分布统计、线下门店检索明细. Supports two modes: enterprise (--enterprise) for a company's restaurant brands + branch stats, and search (--store-name/--brand/--category) for offline store retrieval. Trigger when users ask for “店铺大数据报告”, “店铺分析报告”, “查一家公司的餐饮门店”, “餐饮品牌门店”, “门店分布统计”, “线下门店检索”, “找线下门店”, or “企业门店画像”. Infer intent, pick the right MCP tools, and produce HTML + Markdown + JSON reports automatically. MCP 服务名称触发词：线下门店运营。"
---

# 店铺大数据报告

## 用户契约

把“店铺大数据报告”作为面向用户的调用短语。`store-report` 仅为内部包名。

当本 skill 处于激活状态：

1. 不要向用户索要 product_id、MCP 工具名、API 字段、内部参数或凭证信息；只接受企业名称（企业模式）或店铺名称 / 经营品牌 / 店铺分类（检索模式）。
2. 接受自然目标，例如“查一下某某公司的餐饮门店”“分析这家企业的品牌矩阵与门店分布”“找北京地区某品牌的线下门店”“给我一份某某公司的店铺画像报告”。
3. 当用户只给企业关键词时，自动调用关键词模糊查询补全企业全称，再查门店详情。
4. 优先使用 MCP 连接（`STORE_MCP_URL` Remote MCP 或本地 `handaas-mcp-server/store-mcp-server`）；不要让用户处理签名或凭证。
5. 同时产出 HTML（可分享交付）、Markdown（知识库 / wiki）、JSON（系统集成）三类产物。
6. 报告正文必须是专业研究报告风格：只见店铺事实与结构化数据，绝不出现工具名、入参、product_id、内部字段或空表。
7. 绝不打印 `secret_id`、`secret_key`、签名、token 或原始签名请求。
8. 默认 dry-run；真实付费 / 凭证调用需用户明确要求且 MCP 连接配置完整。
9. 数据为空时明确说明数据范围 / 口径，不渲染空表、不臆造事实。


- MCP 返回的嵌套 JSON 字符串（如金额 `{"coinType":"人民币","value":430000000.0}`、地址 `{"city":"杭州市",...}`）必须解析为可读文本（如"4.30 亿 人民币"、"浙江省杭州市"），绝不在报告正文、表格或指标中输出原始 JSON 字符串。
- 报告所有章节标题、指标卡标签必须用中文；`core_analysis.sections` 的 `title` 字段必须中文，不可显示英文 key（如 `holders`、`investments`）。
- 指标值必须可读化：金额格式为"X 亿/万 + 币种"，地址拼接省市区，比率显示百分号。详见 `references/report-output.md` 的「数据格式约束」。

## 付费调用纪律（先规划后查询）

每次真实调用均按接口/页计费，必须先规划再查询，不得默认全量拉取：

1. 每一次业务/工具调用、每一页都可能收费。想算 total / 页数不是无限制取全量的授权。
2. 调用前先推导：需要哪些结论、需要哪些数据维度、工具与参数计划、必要页数与最大调用预算。total 未知时，第一个必要的明细页同时完成 total 发现并直接作为报告数据，绝不为此多付一次（首屏响应必须复用，不重复拉取）。
3. 优先用统计 / 画像 / 聚合接口回答能回答的问题（企业模式优先 `store_bigdata_company_restaurant_branches` 的门店总数与城市/省份分布统计）；明细接口（`store_bigdata_offline_store_search`）仅取结论、图表、代表性记录或用户明确的全量/计数需求所需的行数。只有用户明确要全面报告时才跑全面管线，绝不因为工具存在就全部调用。
4. 在 schema 允许范围内用合理的大 pageSize（≤50），取得所需证据 / 样本即停，且不超出显式预算。更多调用必须有“缺失结论”的正当理由，不能只为填满章节。不得用样本分布冒充全量结论。
5. 复用当前任务 / 报告内的相同请求（含首屏规划数据）；不要为渲染重跑 compose/MCP，用已保存 JSON 本地重渲染。不自动重试、不重复拉取同一统计或明细、不并行独立拉取相同数据。任何补充查询必须先列缺口并复用已返回记录。
6. `total_pages` / `remaining_pages` 是按请求 pageSize 的估算；短而非空页面仍有剩余记录时在预算内继续。只有稳定有效的 total 等于实际扫描条数才算完整采集；错误、提前空页、重复页、total 变化/缺失、数量溢出均视为不完整。显式预算 / 样本停止即部分采集，绝不宣称全量。
7. 预算不足以支撑用户要求的关键结论时：先说明证据缺口与预计需要追加的调用数，再请求扩大授权（提高 `--max-pages`）；不静默降级结论，也不擅自扩大计费范围。

分页收集默认一次明细调用预算 `--max-pages 1`（仅 `store_bigdata_offline_store_search` 检索明细分页；企业模糊补全、品牌门店、分布统计不翻页）；明细接口的 total、实际取数、完整性披露写入报告 `data_source.pagination`，报告级去重统计写入 `data_source.call_usage`。

## MCP 服务入口

- MCP 服务当前名称：线下门店运营（连接仍使用原服务目录标识）。

- 上游 MCP 项目：`handaas-mcp-server/store-mcp-server`（位于 `HANDAAS_MCP_SERVER_ROOT` 或本仓库同级目录）。
- Remote MCP：设置环境变量 `STORE_MCP_URL`（streamable-http），可选 `STORE_MCP_TOKEN`。
- 本地 MCP：设置 `HANDAAS_MCP_SERVER_ROOT` 指向 `handaas-mcp-server` 仓库根目录；该 server 自己的 `.env` 提供 `INTEGRATOR_ID` / `SECRET_ID` / `SECRET_KEY`。
- 首次真实查询前，运行 `scripts/mcp_client.py ping` 与 `scripts/mcp_client.py list-tools` 验证连通。

## 按需加载 references

- 不清楚该 MCP 有哪些工具、参数、返回字段、何时调用：`references/mcp-tools-reference.md`。
- 报告结构、章节、质量底线、渲染工作流：`references/report-output.md`。

## 意图路由

| 用户意图 | 内部工作流 |
| --- | --- |
| 查一家公司的餐饮品牌门店与分布 | 企业模式：`compose_report.py --enterprise ...` |
| 门店分布统计（按品牌 id） | 企业模式自动取首个品牌 `brandId` 调 `restaurant_branch_stats` |
| 按店铺名称 / 品牌 / 分类 / 地区检索线下门店 | 检索模式：`compose_report.py --store-name/--brand/--category [--address] ...` |
| 只给企业关键词（不是全称） | 先 `store_bigdata_fuzzy_search` 补全全称，再查详情（企业模式） |
| 只要 JSON / 只要 HTML / 只要 Markdown | 用 `--output`（JSON）或 `--report-output`（HTML+MD），或 `render_report.py` 重渲染 |
| 连接 / 工具不存在 / 传参错误 | `mcp_client.py ping` / `list-tools` 排查；报脱敏后的缺失项 |

## Golden path for 店铺大数据报告

1. **选择模式**：若用户提供企业主体 → 企业模式；若用户提供店铺名称 / 品牌 / 分类 → 检索模式。
2. **企业模式**：若输入含“公司/集团/有限/院/厂/中心/事务所/合作社/合伙”等后缀视为全称；否则调 `store_bigdata_fuzzy_search` 取首个命中。
   - 调 `store_bigdata_company_restaurant_branches`（matchKeyword=企业全称）→ 旗下品牌列表 + 门店总数。
   - 取首个品牌的 `brandId` → 调 `store_bigdata_restaurant_branch_stats`（matchKeyword=品牌 id）→ 城市 / 省份分布。
3. **检索模式**：调 `store_bigdata_offline_store_search`（ooStoreName / ooStoreBrandList / ooStoreCalClassification / address）→ 线下门店检索明细（分页，默认 1 页预算；按 total 驱动、在 `--max-pages` 预算内翻页，超出预算在报告中披露未纳入条数）。
4. **组装统一报告**：核心分析含餐饮品牌门店（表）、餐饮门店分布统计（表）、线下门店检索明细（表）。
5. **渲染三件套**：`compose_report.py --enterprise ... | --store-name ... --output ... --report-output ...` 直接产出 JSON + HTML + Markdown。
6. **返回路径**：返回 JSON、HTML、Markdown 文件路径，以及模式与企业全称 / 检索条件映射、数据口径。

## 脚本速查

```bash
# 校验连接配置（脱敏）
python scripts/validate_config.py --allow-placeholders

# 连通性自测
python scripts/mcp_client.py ping
python scripts/mcp_client.py list-tools

# 干跑 — 企业模式（不调真实 API）
python scripts/compose_report.py \
  --enterprise "示例餐饮管理有限公司" \
  --dry-run \
  --output output/store.json \
  --report-output output/store.html

# 真实查询 — 企业模式（需 MCP 连接就绪）
python scripts/compose_report.py \
  --enterprise "示例餐饮管理有限公司" \
  --output output/store.json \
  --report-output output/store.html

# 检索模式 — 按店铺名称 / 品牌 / 分类 / 地区
python scripts/compose_report.py \
  --store-name "示例咖啡" --brand "示例" --category "餐饮,咖啡厅" --address "广东省,广州市" \
  --output output/store_search.json \
  --report-output output/store_search.html

# 检索模式 — 明细分页预算（默认 --max-pages 1，按 total 驱动翻页）
python scripts/compose_report.py \
  --store-name "示例咖啡" --page-size 50 --max-pages 2 \
  --output output/store_search.json \
  --report-output output/store_search.html

# 手动调单个工具
python scripts/mcp_client.py call-tool \
  --tool store_bigdata_company_restaurant_branches \
  --arguments-json '{"matchKeyword": "示例餐饮管理有限公司", "keywordType": "name"}'

# 重渲染已有 JSON
python scripts/render_report.py --input output/store.json --output output/store.html
python scripts/render_report.py --input output/store.json --output output/store.md
```

## 输出字段

- `subject`：模式（enterprise / search）、企业全称（企业模式）/ 门店检索条件（检索模式）、是否自动补全。
- `abstract` / `summary`：封面摘要与详细摘要。
- `metrics`：旗下门店总数、品牌数量、覆盖城市数、覆盖省份、线下门店检索结果（按模式填充）。
- `caliber`：匹配对象、匹配方式、数据范围、产品、局限。
- `core_analysis`：餐饮品牌门店（表）、餐饮门店分布统计（表）、线下门店检索明细（表）。
- `representative_records`：代表性门店 / 品牌记录。
- `insights`：结构化解读（门店资产规模 / 品牌矩阵 / 地域覆盖 / 门店集中度）。
- `data_source`：MCP server、数据产品、生成时间、是否 dry-run、模式、明细分页披露（pagination）与调用去重统计（call_usage）。

若 API 调用失败，明确报出缺失的配置 / 缺失的工具 / MCP 错误 / 参数校验错误 / 上游网络错误，给出 dry-run 命令或配置步骤，绝不暴露密钥。
