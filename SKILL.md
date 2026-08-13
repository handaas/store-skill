---
name: store-report
description: Use for generating a professional store big-data report (店铺大数据报告) from the HandaaS store MCP — covering 餐饮品牌门店、餐饮门店分布统计、线下门店检索明细. Supports two modes: enterprise (--enterprise) for a company's restaurant brands + branch stats, and search (--store-name/--brand/--category) for offline store retrieval. Trigger when users ask for “店铺大数据报告”, “店铺分析报告”, “查一家公司的餐饮门店”, “餐饮品牌门店”, “门店分布统计”, “线下门店检索”, “找线下门店”, or “企业门店画像”. Infer intent, pick the right MCP tools, and produce HTML + Markdown + JSON reports automatically.
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

## MCP 服务入口

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
3. **检索模式**：调 `store_bigdata_offline_store_search`（ooStoreName / ooStoreBrandList / ooStoreCalClassification / address）→ 线下门店检索明细。
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
- `data_source`：MCP server、数据产品、生成时间、是否 dry-run、模式。

若 API 调用失败，明确报出缺失的配置 / 缺失的工具 / MCP 错误 / 参数校验错误 / 上游网络错误，给出 dry-run 命令或配置步骤，绝不暴露密钥。
