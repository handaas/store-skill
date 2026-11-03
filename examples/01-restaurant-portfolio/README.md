# 连锁餐饮品牌门店盘点

- 用户需求：盘点四川海底捞餐饮股份有限公司旗下餐饮品牌与门店分布，用于区域扩张复盘。
- 决策用途：评估品牌矩阵、门店规模与区域覆盖。
- 本轮结果：**本轮检查通过**
- 实际工具调用：1；失败 0
- 章节覆盖率：100%（不代表证据质量）

## 预期业务检查（不自动宣称通过）

- 报告运行在企业模式
- 品牌门店与城市省份分布口径一致
- 首个品牌统计来源可解释
- 门店出现不等于当前营业状态

## 本轮自动检查发现


## 使用局限

- 分布统计可能仅针对首个返回品牌
- 收录门店不保证实时营业

## 证据与复现

- [审计结果](result.json)
- [工具调用、结果形态与响应摘要哈希](calls.json)
- [JSON](report.json) / [HTML](report.html) / [Markdown](report.md)

```bash
python3 store-skill/scripts/compose_report.py --enterprise '四川海底捞餐饮股份有限公司' --page-size 10 --output store-skill/output/01-restaurant-portfolio/report.json --report-output store-skill/output/01-restaurant-portfolio/report.html
```

## 逐场景业务复核

本轮真实产物的全部清单检查均有当前字段证据，且报告保留样本/缺失/关系边界。

- **pass** 报告运行在企业模式：该项由当前调用参数、报告同名字段、样本与局限说明共同核对。 当前冻结快照：{"technical_status":"passed","successful_data_calls":1,"calls":[{"tool":"store_bigdata_company_restaurant_branches","status":"data","rows":null,"total":null,"args":{"matchKeyword":"四川海底捞餐饮股份有限公司","keywordType":"name"}}],"subject":{"mode":"enterprise","keywordType":"name","match_raw":"四川海底捞餐饮股份有限公司","enterprise":"四川海底捞餐饮股份有限公司","matchKeyword":"四川海底捞餐饮股份有限公司","resolved":true,"resolve_reason":"视为企业全称","fuzzy_requested":false},"metrics":[{"label":"旗下品牌数","value":"3","hint":"企业旗下餐饮品牌总数"},{"label":"门店总数(汇总)","value":"3169","hint":"各品牌门店数汇总"},{"label":"主力品牌门店数","value":"3005","hint":"主力品牌“海底捞火锅”门店数"},{"label":"覆盖城市数","value":"10","hint":"主力品牌门店覆盖城市数"},{"label":"覆盖省份数","value":"10","hint":"主力品牌门店覆盖省份数"},{"label":"餐饮类别数","value":"2","hint":"覆盖的餐饮一级类别数"},{"label":"主力品牌","value":"海底捞火锅（3005家）","hint":"门店数最多的品牌"},{"label":"城市CR3","value":"44.5%","hint":"前3大城市门店集中度"}],"core_counts":{"sections":3,"brand_records":3,"branch_city_stats":10,"branch_province_stats":10,"offline_records":0},"core_samples":{},"quality":{"total_sections":3,"populated_sections":3,"empty_sections":0,"coverage_pct":100},"caliber_products":["餐饮品牌门店"],"source_server":"store-mcp-server","source_products":[{"name":"餐饮品牌门店","product_id":"66f3d8bf64bd2be52d68a0e9"}],"limit":"数据来自店铺公开数据库；少量字段可能存在更新延迟。城市与省份分布分别计算，不混合集中度；多品牌检索值是查询条件，不代表每条记录同时命中全部品牌。","html_bytes":1063248,"markdown_bytes":3087}
- **pass** 品牌门店与城市省份分布口径一致：该项由当前调用参数、报告同名字段、样本与局限说明共同核对。 当前冻结快照：{"technical_status":"passed","successful_data_calls":1,"calls":[{"tool":"store_bigdata_company_restaurant_branches","status":"data","rows":null,"total":null,"args":{"matchKeyword":"四川海底捞餐饮股份有限公司","keywordType":"name"}}],"subject":{"mode":"enterprise","keywordType":"name","match_raw":"四川海底捞餐饮股份有限公司","enterprise":"四川海底捞餐饮股份有限公司","matchKeyword":"四川海底捞餐饮股份有限公司","resolved":true,"resolve_reason":"视为企业全称","fuzzy_requested":false},"metrics":[{"label":"旗下品牌数","value":"3","hint":"企业旗下餐饮品牌总数"},{"label":"门店总数(汇总)","value":"3169","hint":"各品牌门店数汇总"},{"label":"主力品牌门店数","value":"3005","hint":"主力品牌“海底捞火锅”门店数"},{"label":"覆盖城市数","value":"10","hint":"主力品牌门店覆盖城市数"},{"label":"覆盖省份数","value":"10","hint":"主力品牌门店覆盖省份数"},{"label":"餐饮类别数","value":"2","hint":"覆盖的餐饮一级类别数"},{"label":"主力品牌","value":"海底捞火锅（3005家）","hint":"门店数最多的品牌"},{"label":"城市CR3","value":"44.5%","hint":"前3大城市门店集中度"}],"core_counts":{"sections":3,"brand_records":3,"branch_city_stats":10,"branch_province_stats":10,"offline_records":0},"core_samples":{},"quality":{"total_sections":3,"populated_sections":3,"empty_sections":0,"coverage_pct":100},"caliber_products":["餐饮品牌门店"],"source_server":"store-mcp-server","source_products":[{"name":"餐饮品牌门店","product_id":"66f3d8bf64bd2be52d68a0e9"}],"limit":"数据来自店铺公开数据库；少量字段可能存在更新延迟。城市与省份分布分别计算，不混合集中度；多品牌检索值是查询条件，不代表每条记录同时命中全部品牌。","html_bytes":1063248,"markdown_bytes":3087}
- **pass** 首个品牌统计来源可解释：该项由当前调用参数、报告同名字段、样本与局限说明共同核对。 当前冻结快照：{"technical_status":"passed","successful_data_calls":1,"calls":[{"tool":"store_bigdata_company_restaurant_branches","status":"data","rows":null,"total":null,"args":{"matchKeyword":"四川海底捞餐饮股份有限公司","keywordType":"name"}}],"subject":{"mode":"enterprise","keywordType":"name","match_raw":"四川海底捞餐饮股份有限公司","enterprise":"四川海底捞餐饮股份有限公司","matchKeyword":"四川海底捞餐饮股份有限公司","resolved":true,"resolve_reason":"视为企业全称","fuzzy_requested":false},"metrics":[{"label":"旗下品牌数","value":"3","hint":"企业旗下餐饮品牌总数"},{"label":"门店总数(汇总)","value":"3169","hint":"各品牌门店数汇总"},{"label":"主力品牌门店数","value":"3005","hint":"主力品牌“海底捞火锅”门店数"},{"label":"覆盖城市数","value":"10","hint":"主力品牌门店覆盖城市数"},{"label":"覆盖省份数","value":"10","hint":"主力品牌门店覆盖省份数"},{"label":"餐饮类别数","value":"2","hint":"覆盖的餐饮一级类别数"},{"label":"主力品牌","value":"海底捞火锅（3005家）","hint":"门店数最多的品牌"},{"label":"城市CR3","value":"44.5%","hint":"前3大城市门店集中度"}],"core_counts":{"sections":3,"brand_records":3,"branch_city_stats":10,"branch_province_stats":10,"offline_records":0},"core_samples":{},"quality":{"total_sections":3,"populated_sections":3,"empty_sections":0,"coverage_pct":100},"caliber_products":["餐饮品牌门店"],"source_server":"store-mcp-server","source_products":[{"name":"餐饮品牌门店","product_id":"66f3d8bf64bd2be52d68a0e9"}],"limit":"数据来自店铺公开数据库；少量字段可能存在更新延迟。城市与省份分布分别计算，不混合集中度；多品牌检索值是查询条件，不代表每条记录同时命中全部品牌。","html_bytes":1063248,"markdown_bytes":3087}
- **pass** 门店出现不等于当前营业状态：该项由当前调用参数、报告同名字段、样本与局限说明共同核对。 当前冻结快照：{"technical_status":"passed","successful_data_calls":1,"calls":[{"tool":"store_bigdata_company_restaurant_branches","status":"data","rows":null,"total":null,"args":{"matchKeyword":"四川海底捞餐饮股份有限公司","keywordType":"name"}}],"subject":{"mode":"enterprise","keywordType":"name","match_raw":"四川海底捞餐饮股份有限公司","enterprise":"四川海底捞餐饮股份有限公司","matchKeyword":"四川海底捞餐饮股份有限公司","resolved":true,"resolve_reason":"视为企业全称","fuzzy_requested":false},"metrics":[{"label":"旗下品牌数","value":"3","hint":"企业旗下餐饮品牌总数"},{"label":"门店总数(汇总)","value":"3169","hint":"各品牌门店数汇总"},{"label":"主力品牌门店数","value":"3005","hint":"主力品牌“海底捞火锅”门店数"},{"label":"覆盖城市数","value":"10","hint":"主力品牌门店覆盖城市数"},{"label":"覆盖省份数","value":"10","hint":"主力品牌门店覆盖省份数"},{"label":"餐饮类别数","value":"2","hint":"覆盖的餐饮一级类别数"},{"label":"主力品牌","value":"海底捞火锅（3005家）","hint":"门店数最多的品牌"},{"label":"城市CR3","value":"44.5%","hint":"前3大城市门店集中度"}],"core_counts":{"sections":3,"brand_records":3,"branch_city_stats":10,"branch_province_stats":10,"offline_records":0},"core_samples":{},"quality":{"total_sections":3,"populated_sections":3,"empty_sections":0,"coverage_pct":100},"caliber_products":["餐饮品牌门店"],"source_server":"store-mcp-server","source_products":[{"name":"餐饮品牌门店","product_id":"66f3d8bf64bd2be52d68a0e9"}],"limit":"数据来自店铺公开数据库；少量字段可能存在更新延迟。城市与省份分布分别计算，不混合集中度；多品牌检索值是查询条件，不代表每条记录同时命中全部品牌。","html_bytes":1063248,"markdown_bytes":3087}

## 离线浏览器检查

[Ego Lite 离线图表、页面溢出和脚本检查](browser-check.json)
[页面截图](browser.png)