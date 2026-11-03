# 杭州药店拜访优先字段清单

- 用户需求：请检索杭州药店类门店，按实际店名、营业状态、商圈以及人均价格或排名整理人工拜访优先字段；不要判断药品许可或地址匹配。
- 决策用途：为医药渠道团队提供可人工排序的拜访字段清单。
- 本轮结果：**本轮检查通过**
- 实际工具调用：1；失败 0
- 章节覆盖率：100%（不代表证据质量）

## 预期业务检查（不自动宣称通过）

- offline_records 至少有两条实际返回记录
- 至少两条记录同时具备非空店铺名称、店铺分类和店铺状态
- 至少两条记录具备非空商圈，且人均价格或店铺排名至少一项非空
- 药店相关性必须由实际店铺分类字段支持，不能只依赖 category 参数
- 缺失价格必须保留缺失，不得补零或据此降低优先级

## 本轮自动检查发现


## 使用局限

- 不包含药品经营许可证核验
- 实际地址缺失时不能证明地区匹配
- 优先字段仅供人工排序，不能自动作准入决定

## 证据与复现

- [审计结果](result.json)
- [工具调用、结果形态与响应摘要哈希](calls.json)
- [JSON](report.json) / [HTML](report.html) / [Markdown](report.md)

```bash
python3 store-skill/scripts/compose_report.py --category '医疗健康,药店' --address '浙江省,杭州市' --page-size 10 --output store-skill/output/11-pharmacy-visit-priority/report.json --report-output store-skill/output/11-pharmacy-visit-priority/report.html
```

## 逐场景业务复核

本轮真实产物的全部清单检查均有当前字段证据，且报告保留样本/缺失/关系边界。

- **pass** offline_records 至少有两条实际返回记录：offline_records为10/100；方回春堂和北京同仁堂浙江国医馆均有名称、‘医疗健康、药店’分类、营业状态、非空商圈、人均价格及排名；无价格记录保持‘-’，未补零。 当前冻结快照：{"technical_status":"passed","successful_data_calls":1,"calls":[{"tool":"store_bigdata_offline_store_search","status":"data","rows":10,"total":100,"args":{"pageIndex":1,"pageSize":10,"ooStoreCalClassification":"医疗健康,药店","address":"浙江省,杭州市"}}],"subject":{"mode":"search","keywordType":"name","match_raw":"医疗健康,药店","enterprise":"","matchKeyword":"医疗健康,药店","store_name":"","brand":"","category":"医疗健康,药店","address":"浙江省,杭州市","address_value":""},"metrics":[{"label":"线下门店检索结果","value":"100","hint":"本次线下门店检索命中条数"}],"core_counts":{"sections":1,"brand_records":0,"branch_city_stats":0,"branch_province_stats":0,"offline_records":10},"core_samples":{"offline_records":[{"店铺名称":"方回春堂(拱宸桥馆)","店铺分类":"医疗健康、药店","店铺状态":"营业","商圈":"拱宸桥/上塘","人均价格":"288.0","店铺排名":"16103.0","实际品牌":"-","实际地区":"-","实际地址":"-","查询品牌条件":"-","查询地区条件":"浙江省,杭州市","查询地址条件":"-","品牌匹配验证":"未设置品牌条件","地址匹配验证":"上游未返回实际地区/地址，无法逐条验证地区条件"},{"店铺名称":"禧元堂燕窝(余杭店)","店铺分类":"医疗健康、药店","店铺状态":"关闭/下架","商圈":"临平","人均价格":"-","店铺排名":"15062.0","实际品牌":"-","实际地区":"-","实际地址":"-","查询品牌条件":"-","查询地区条件":"浙江省,杭州市","查询地址条件":"-","品牌匹配验证":"未设置品牌条件","地址匹配验证":"上游未返回实际地区/地址，无法逐条验证地区条件"}]},"quality":{"total_sections":1,"populated_sections":1,"empty_sections":0,"coverage_pct":100},"caliber_products":["线下门店检索"],"source_server":"store-mcp-server","source_products":[{"name":"线下门店检索","product_id":"66ed53be15858a879f40242f"}],"limit":"数据来自店铺公开数据库；少量字段可能存在更新延迟。城市与省份分布分别计算，不混合集中度；多品牌检索值是查询条件，不代表每条记录同时命中全部品牌。","html_bytes":1059945,"markdown_bytes":4520}
- **pass** 至少两条记录同时具备非空店铺名称、店铺分类和店铺状态：offline_records为10/100；方回春堂和北京同仁堂浙江国医馆均有名称、‘医疗健康、药店’分类、营业状态、非空商圈、人均价格及排名；无价格记录保持‘-’，未补零。 当前冻结快照：{"technical_status":"passed","successful_data_calls":1,"calls":[{"tool":"store_bigdata_offline_store_search","status":"data","rows":10,"total":100,"args":{"pageIndex":1,"pageSize":10,"ooStoreCalClassification":"医疗健康,药店","address":"浙江省,杭州市"}}],"subject":{"mode":"search","keywordType":"name","match_raw":"医疗健康,药店","enterprise":"","matchKeyword":"医疗健康,药店","store_name":"","brand":"","category":"医疗健康,药店","address":"浙江省,杭州市","address_value":""},"metrics":[{"label":"线下门店检索结果","value":"100","hint":"本次线下门店检索命中条数"}],"core_counts":{"sections":1,"brand_records":0,"branch_city_stats":0,"branch_province_stats":0,"offline_records":10},"core_samples":{"offline_records":[{"店铺名称":"方回春堂(拱宸桥馆)","店铺分类":"医疗健康、药店","店铺状态":"营业","商圈":"拱宸桥/上塘","人均价格":"288.0","店铺排名":"16103.0","实际品牌":"-","实际地区":"-","实际地址":"-","查询品牌条件":"-","查询地区条件":"浙江省,杭州市","查询地址条件":"-","品牌匹配验证":"未设置品牌条件","地址匹配验证":"上游未返回实际地区/地址，无法逐条验证地区条件"},{"店铺名称":"禧元堂燕窝(余杭店)","店铺分类":"医疗健康、药店","店铺状态":"关闭/下架","商圈":"临平","人均价格":"-","店铺排名":"15062.0","实际品牌":"-","实际地区":"-","实际地址":"-","查询品牌条件":"-","查询地区条件":"浙江省,杭州市","查询地址条件":"-","品牌匹配验证":"未设置品牌条件","地址匹配验证":"上游未返回实际地区/地址，无法逐条验证地区条件"}]},"quality":{"total_sections":1,"populated_sections":1,"empty_sections":0,"coverage_pct":100},"caliber_products":["线下门店检索"],"source_server":"store-mcp-server","source_products":[{"name":"线下门店检索","product_id":"66ed53be15858a879f40242f"}],"limit":"数据来自店铺公开数据库；少量字段可能存在更新延迟。城市与省份分布分别计算，不混合集中度；多品牌检索值是查询条件，不代表每条记录同时命中全部品牌。","html_bytes":1059945,"markdown_bytes":4520}
- **pass** 至少两条记录具备非空商圈，且人均价格或店铺排名至少一项非空：offline_records为10/100；方回春堂和北京同仁堂浙江国医馆均有名称、‘医疗健康、药店’分类、营业状态、非空商圈、人均价格及排名；无价格记录保持‘-’，未补零。 当前冻结快照：{"technical_status":"passed","successful_data_calls":1,"calls":[{"tool":"store_bigdata_offline_store_search","status":"data","rows":10,"total":100,"args":{"pageIndex":1,"pageSize":10,"ooStoreCalClassification":"医疗健康,药店","address":"浙江省,杭州市"}}],"subject":{"mode":"search","keywordType":"name","match_raw":"医疗健康,药店","enterprise":"","matchKeyword":"医疗健康,药店","store_name":"","brand":"","category":"医疗健康,药店","address":"浙江省,杭州市","address_value":""},"metrics":[{"label":"线下门店检索结果","value":"100","hint":"本次线下门店检索命中条数"}],"core_counts":{"sections":1,"brand_records":0,"branch_city_stats":0,"branch_province_stats":0,"offline_records":10},"core_samples":{"offline_records":[{"店铺名称":"方回春堂(拱宸桥馆)","店铺分类":"医疗健康、药店","店铺状态":"营业","商圈":"拱宸桥/上塘","人均价格":"288.0","店铺排名":"16103.0","实际品牌":"-","实际地区":"-","实际地址":"-","查询品牌条件":"-","查询地区条件":"浙江省,杭州市","查询地址条件":"-","品牌匹配验证":"未设置品牌条件","地址匹配验证":"上游未返回实际地区/地址，无法逐条验证地区条件"},{"店铺名称":"禧元堂燕窝(余杭店)","店铺分类":"医疗健康、药店","店铺状态":"关闭/下架","商圈":"临平","人均价格":"-","店铺排名":"15062.0","实际品牌":"-","实际地区":"-","实际地址":"-","查询品牌条件":"-","查询地区条件":"浙江省,杭州市","查询地址条件":"-","品牌匹配验证":"未设置品牌条件","地址匹配验证":"上游未返回实际地区/地址，无法逐条验证地区条件"}]},"quality":{"total_sections":1,"populated_sections":1,"empty_sections":0,"coverage_pct":100},"caliber_products":["线下门店检索"],"source_server":"store-mcp-server","source_products":[{"name":"线下门店检索","product_id":"66ed53be15858a879f40242f"}],"limit":"数据来自店铺公开数据库；少量字段可能存在更新延迟。城市与省份分布分别计算，不混合集中度；多品牌检索值是查询条件，不代表每条记录同时命中全部品牌。","html_bytes":1059945,"markdown_bytes":4520}
- **pass** 药店相关性必须由实际店铺分类字段支持，不能只依赖 category 参数：offline_records为10/100；方回春堂和北京同仁堂浙江国医馆均有名称、‘医疗健康、药店’分类、营业状态、非空商圈、人均价格及排名；无价格记录保持‘-’，未补零。 当前冻结快照：{"technical_status":"passed","successful_data_calls":1,"calls":[{"tool":"store_bigdata_offline_store_search","status":"data","rows":10,"total":100,"args":{"pageIndex":1,"pageSize":10,"ooStoreCalClassification":"医疗健康,药店","address":"浙江省,杭州市"}}],"subject":{"mode":"search","keywordType":"name","match_raw":"医疗健康,药店","enterprise":"","matchKeyword":"医疗健康,药店","store_name":"","brand":"","category":"医疗健康,药店","address":"浙江省,杭州市","address_value":""},"metrics":[{"label":"线下门店检索结果","value":"100","hint":"本次线下门店检索命中条数"}],"core_counts":{"sections":1,"brand_records":0,"branch_city_stats":0,"branch_province_stats":0,"offline_records":10},"core_samples":{"offline_records":[{"店铺名称":"方回春堂(拱宸桥馆)","店铺分类":"医疗健康、药店","店铺状态":"营业","商圈":"拱宸桥/上塘","人均价格":"288.0","店铺排名":"16103.0","实际品牌":"-","实际地区":"-","实际地址":"-","查询品牌条件":"-","查询地区条件":"浙江省,杭州市","查询地址条件":"-","品牌匹配验证":"未设置品牌条件","地址匹配验证":"上游未返回实际地区/地址，无法逐条验证地区条件"},{"店铺名称":"禧元堂燕窝(余杭店)","店铺分类":"医疗健康、药店","店铺状态":"关闭/下架","商圈":"临平","人均价格":"-","店铺排名":"15062.0","实际品牌":"-","实际地区":"-","实际地址":"-","查询品牌条件":"-","查询地区条件":"浙江省,杭州市","查询地址条件":"-","品牌匹配验证":"未设置品牌条件","地址匹配验证":"上游未返回实际地区/地址，无法逐条验证地区条件"}]},"quality":{"total_sections":1,"populated_sections":1,"empty_sections":0,"coverage_pct":100},"caliber_products":["线下门店检索"],"source_server":"store-mcp-server","source_products":[{"name":"线下门店检索","product_id":"66ed53be15858a879f40242f"}],"limit":"数据来自店铺公开数据库；少量字段可能存在更新延迟。城市与省份分布分别计算，不混合集中度；多品牌检索值是查询条件，不代表每条记录同时命中全部品牌。","html_bytes":1059945,"markdown_bytes":4520}
- **pass** 缺失价格必须保留缺失，不得补零或据此降低优先级：offline_records为10/100；方回春堂和北京同仁堂浙江国医馆均有名称、‘医疗健康、药店’分类、营业状态、非空商圈、人均价格及排名；无价格记录保持‘-’，未补零。 当前冻结快照：{"technical_status":"passed","successful_data_calls":1,"calls":[{"tool":"store_bigdata_offline_store_search","status":"data","rows":10,"total":100,"args":{"pageIndex":1,"pageSize":10,"ooStoreCalClassification":"医疗健康,药店","address":"浙江省,杭州市"}}],"subject":{"mode":"search","keywordType":"name","match_raw":"医疗健康,药店","enterprise":"","matchKeyword":"医疗健康,药店","store_name":"","brand":"","category":"医疗健康,药店","address":"浙江省,杭州市","address_value":""},"metrics":[{"label":"线下门店检索结果","value":"100","hint":"本次线下门店检索命中条数"}],"core_counts":{"sections":1,"brand_records":0,"branch_city_stats":0,"branch_province_stats":0,"offline_records":10},"core_samples":{"offline_records":[{"店铺名称":"方回春堂(拱宸桥馆)","店铺分类":"医疗健康、药店","店铺状态":"营业","商圈":"拱宸桥/上塘","人均价格":"288.0","店铺排名":"16103.0","实际品牌":"-","实际地区":"-","实际地址":"-","查询品牌条件":"-","查询地区条件":"浙江省,杭州市","查询地址条件":"-","品牌匹配验证":"未设置品牌条件","地址匹配验证":"上游未返回实际地区/地址，无法逐条验证地区条件"},{"店铺名称":"禧元堂燕窝(余杭店)","店铺分类":"医疗健康、药店","店铺状态":"关闭/下架","商圈":"临平","人均价格":"-","店铺排名":"15062.0","实际品牌":"-","实际地区":"-","实际地址":"-","查询品牌条件":"-","查询地区条件":"浙江省,杭州市","查询地址条件":"-","品牌匹配验证":"未设置品牌条件","地址匹配验证":"上游未返回实际地区/地址，无法逐条验证地区条件"}]},"quality":{"total_sections":1,"populated_sections":1,"empty_sections":0,"coverage_pct":100},"caliber_products":["线下门店检索"],"source_server":"store-mcp-server","source_products":[{"name":"线下门店检索","product_id":"66ed53be15858a879f40242f"}],"limit":"数据来自店铺公开数据库；少量字段可能存在更新延迟。城市与省份分布分别计算，不混合集中度；多品牌检索值是查询条件，不代表每条记录同时命中全部品牌。","html_bytes":1059945,"markdown_bytes":4520}

## 离线浏览器检查

[Ego Lite 离线图表、页面溢出和脚本检查](browser-check.json)