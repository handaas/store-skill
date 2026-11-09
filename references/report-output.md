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
   - 线下门店检索明细（表，两种模式均可）：店铺名称 / 上游实际品牌 / 店铺分类 / 店铺状态 / 上游实际地区与地址 / 商圈 / 人均价格 / 店铺排名。查询条件与实际返回字段分开；上游未返回实际品牌或地址时明确“无法逐条验证”。
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

## AI 审校交付门禁（草稿 → final）

`compose_*` 正常生成与 `--dry-run` 只产出草稿：JSON 标记 `data_source.semantic_review.status=pending`，同名 HTML/Markdown 带“数据草稿（待AI语义审校）”提示，不能交付。`apply_content_review`/`organize_report` 是确定性整理，不是 AI 审校。

```bash
python scripts/review_report.py --input output/draft.json --request output/review-request.json
# 当前 AI 阅读请求中的 report 后写 output/ai-review.json
python scripts/review_report.py --input output/draft.json --review output/ai-review.json \
  --output output/final/report.json --report-output output/final/report.html
```

请求含 `source_sha256`、`report`、`visible_section_keys`、`instructions`、`response_fields`；响应：

```json
{
  "source_sha256": "<与请求一致>",
  "summary": [{"text": "逐句摘要", "sources": ["/core_analysis/..."], "kind": "fact"}],
  "normalizations": [{"sources": ["/core_analysis/..."], "category": "类别", "normalized": "规范表达", "evidence": "原文摘录", "reason": "理由"}],
  "insights": [{"feature": "特征", "evidence": "证据摘录", "interpretation": "解读", "sources": ["/metrics/0"]}]
}
```

- `source_sha256` 必须与请求一致；不一致须重新请求，不能沿用旧判断。
- `sources` 使用 JSON Pointer，只能指向本报告实际存在的 `/subject/…`、`/core_analysis/…`、`/metrics/…`、`/caliber/…`、`/data_source/…`、`/analysis_request/…`；`/core_analysis/sections`、`/data_source/semantic_review` 与旧 `abstract`/`summary`/`insights` 不是事实依据。
- 每项至少一个来源且不能重复路径；同一来源可支持多项判断；不能借其他企业、案例、记录或常识补本记录。
- `summary` 写 3–5 句有信息量的逐句摘要，`kind` 只能是 `fact`/`interpretation`/`limitation`；无数据依据只能写 `limitation`。`normalizations` 是独立视图，原文不改写；`evidence` 必填，由当前 AI 选择简洁可读的原文摘录作为“原文依据”列，并由同项 `sources` 支撑，完整原值仍保留在 draft/request 与来源 SHA 记录中；必须保留否定、最高、至少、至多、试用期、转正后、仅限、部分、疑似、待定、已失效等限定；不同主体、互斥金额或比例不能合并；没有实际归类需要时可为空；`insights` 的 `feature`、`evidence`、`interpretation` 都须由同一 `sources` 支撑；`evidence` 是实际 AI 写的简洁可读证据摘录，保留来源数字、单位与限定。
- 所有文本（含 `normalized`、`category`、`reason`、`evidence`、洞察）中的数字必须逐字出现在所引 values 中，不新造派生数字、不改精度；需要派生指标先在脚本计算再引用。
- 只使用本次数据，不调用 MCP/外部模型 API/新增查询。应用后 `status=reviewed` 并记录来源 SHA-256、原 `generated_at`、审校时间与判断证据；原查询时间和原件不变。`summary` 写入 `abstract`/`summary`/`executive_summary`，`normalizations` 写入 `core_analysis.ai_normalization`（独立表格），`insights` 写入 `insights`；原始字段不改写。

**展示与交付**：空板块连标题和目录一起隐藏，但只能影响展示，不能从 `quality_report` 分母抹去未覆盖维度或提高覆盖率；真实 `0`/`False` 保留，缺失/未查询不等于 0；失败只写口径限制，不推断“无风险”。AI 标准化/摘要是解释视图，不新增数据来源或覆盖率。核对最终 JSON/HTML/Markdown 后才交付；请求文件、草稿或手工润色件不算完成。

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

## 内容审校（离线）

对已有 `report.json` 复核而不调用 MCP：`python scripts/store_content_review.py --input <report.json> --out-dir <dir>`；纯函数 `store_content_review.apply_content_review(report)`。审校顺序：

1. 主体/条件：检索模式把店铺分类、地区等条件分别标注，不拼成企业名；标题不再用逗号串条件。
2. 汇总：`门店总数(汇总)` 是品牌级字段相加、未去重，不称实体门店总数。
3. 地区：城市/省份是 Top 统计行，指标改为 `已返回城市数/省份数`，CR3 只在返回样本内计算，并披露合计门店/主力品牌门店覆盖比例。
4. 明细：排名、人均价格格式化；实际品牌/地区/地址全空时隐藏空列，同值验证列合并为说明；人均价格在非餐饮场景标注语义可能不适用。
5. 状态：营业/关闭下架只统计当前样本，不推全量在营率；删除无证据的经营质量结论。
6. 空结果：无核心明细且 `tool_errors` 为空时保留“本次查询未返回有效核心数据…”摘要，不改成有数据叙述，也不把成功空结果写进 `tool_errors`；显式 `0` 指标仍按 `0` 展示。

交付前按最终 `sections` 与实际 body 刷新 `data_source.quality_report`（`0` 计为已填充；`coverage_pct` 仅为章节填充率）；保留原 `generated_at`。

CLI 会拒绝 `--out-dir` 的 `report.json` 解析为 `--input` 的调用；输出目标应位于本 skill 的 `output/content-quality-review/`，不得覆盖 `examples/` 或 `test-records/`。

审校复核：完整保留有来源的摘要句子及采集层“数据缺口／主体解析受阻”提示；重审不得引用 `/core_analysis/ai_normalization` 等既有 AI 视图作为原始证据。HTML 与 Markdown 应使用一致的样本数量、趋势顺序及数据列，单元格中的竖线和换行不得破坏表格结构。
