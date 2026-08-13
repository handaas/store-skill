# 报告输出 — 店铺大数据报告

本文件规定 `store-report` skill 产出的报告结构、质量底线与渲染工作流。所有产物遵循 `AGENTS.md` 的统一 JSON 骨架与本 skill 的领域裁剪。

## 默认展示模式

- HTML：可分享 / 可交付的可视化报告；独立本地文件，内嵌 CSS，无调试 / 内部段落。
- Markdown：知识库 / wiki / PRD / 后续手工编辑。
- JSON：系统集成或二次处理。

`compose_report.py` 通过 `--report-output <path>` 同时产出 HTML + Markdown；`--output <path>` 产出 JSON。`render_report.py` 可基于已有 JSON 重渲染。

## 两种模式

- **企业模式**（`--enterprise`）：分析对象为企业主体，覆盖旗下餐饮品牌门店 + 餐饮门店分布统计（按品牌 id）。
- **检索模式**（`--store-name` / `--brand` / `--category`）：分析对象为门店检索条件，覆盖线下门店检索明细。

## 报告结构（7 章）

1. **报告摘要**：分析对象（企业或门店检索条件）、数据覆盖范围、核心发现、关键指标卡。
2. **查询对象与口径**：模式、企业全称 / 检索条件、匹配方式、数据范围、产品、局限。
3. **数据总览**：旗下门店总数、品牌数量、覆盖城市数、覆盖省份、线下门店检索结果等指标卡（按模式填充）。
4. **核心分析**（店铺专属子章节，由 `core_analysis.sections` 驱动渲染）：
   - 餐饮品牌门店（表，企业模式）：品牌名称 / 一级类别 / 二级类别 / 起源地 / 门店数 / 商场店数。
   - 餐饮门店分布统计（表，企业模式）：地区类型 / 地区 / 门店数量。
   - 线下门店检索明细（表，两种模式均可）：店铺名称 / 店铺分类 / 店铺状态 / 商圈 / 人均价格 / 店铺排名。
5. **代表性记录**：关键门店 / 品牌记录 Top N。
6. **特征与洞察**：结构化解读（门店资产规模 / 品牌矩阵 / 地域覆盖 / 门店集中度），每条含 `feature` / `evidence` / `interpretation`。
7. **数据口径与来源**：MCP server、数据产品、生成时间、是否 dry-run、模式。

## 质量底线

- 报告脱离 Skill 上下文也可独立阅读；正文只见店铺事实与结构化数据。
- 绝不出现工具名、入参（如 `matchKeyword=...`）、product_id、内部字段名、空表、调试信息。
- HTML 采用研究报告视觉风格：A4 风、灰色顶部条纹、蓝色报告横幅、左侧目录 / 范围侧栏、深蓝章节标题、深蓝表头、浅蓝斑马行、打印友好分页。
- 数据为空时明确说明数据范围 / 口径（例如检索模式未命中、企业无餐饮品牌），不渲染空表、不臆造事实。
- 绝不打印 `secret_id` / `secret_key` / 签名 / token / 原始签名请求。
- 自动补全企业全称时，在报告口径中说明“由关键词模糊查询补全”。

### 数据格式约束（铁律）

以下约束适用于 compose_report.py 组装数据与 render_report.py 渲染输出的全过程：

1. **嵌套 JSON 字符串必须解析**：MCP 返回的某些字段（如 `regCapital`、`addressValue`、`subscriptionDetail`）可能是 JSON 字符串（例：`{"coinType":"人民币","value":430000000.0}`）。compose 层必须调用 `_unwrap_json_str()` / `_parse_reg_capital()` / `_flatten_addr()` 解析为可读文本（如"4.30 亿 人民币"、"浙江省杭州市滨江区..."）。绝不在报告正文、表格单元格或指标值中输出原始 JSON 字符串。

2. **section 标题必须用中文**：`core_analysis.sections` 数组中每个 section 的 `title` 字段必须使用中文（如"企业基本信息"、"对外投资"、"股东信息"）。`key` 字段用英文 snake_case 供程序索引，但 `title` 绝不可显示英文 key。即使缺少 sections 数组，渲染器回退逻辑也内置了 `_TITLE_MAP` 映射。

3. **指标值可读化**：所有 `metrics` 的 `value` 字段必须格式化为人类可读形式：
   - 金额：`10995210218.0` → `109.95 亿 人民币`（≥1 亿用亿，≥1 万用万）
   - 地址：嵌套 dict → 省+市+区拼接 或取 `value` 字段
   - 比率：`0.8858` → `88.58%`
   - 日期：保持 `yyyy-MM-dd` 格式
   - "-" 表示字段缺失（MCP 未返回）；`0` 表示真实为零

4. **企业画像指标提取**：有 fuzzy_search 的 skill 必须从返回的 record 中提取 `regCapitalValue` / `foundTime` / `operStatus` / `enterpriseType` / `legalRepresentative`，通过 `_enrich_metrics_with_profile()` 追加为指标卡。

5. **分布派生指标**：`_derive_core_metrics()` 从 core_analysis 各 section 计算分布指标（CR3 集中度、覆盖城市/平台/类目数、价格区间、正面占比等），确保指标总数 M ≥ 6。

## 工作流

```bash
# 1. 干跑 — 企业模式（不调真实 API）
python scripts/compose_report.py \
  --enterprise "示例餐饮管理有限公司" \
  --dry-run \
  --output output/store.json \
  --report-output output/store.html

# 2. 真实查询 — 企业模式（需 MCP 连接就绪）
python scripts/compose_report.py \
  --enterprise "示例餐饮管理有限公司" \
  --output output/store.json \
  --report-output output/store.html

# 3. 检索模式 — 按店铺名称 / 品牌 / 分类
python scripts/compose_report.py \
  --store-name "示例咖啡" --brand "示例" --category "餐饮,咖啡厅" \
  --output output/store_search.json \
  --report-output output/store_search.html

# 4. 重渲染已有 JSON
python scripts/render_report.py --input output/store.json --output output/store.html
python scripts/render_report.py --input output/store.json --output output/store.md
```

返回：JSON 路径、HTML 路径、Markdown 路径，以及模式与企业全称 / 检索条件映射、数据口径摘要。
