# store-skill：已验收示例

本目录只展示 **4 个完全通过的真实正向场景**（最低要求4例）。

每例均为真实、非空、非缓存调用；技术检查、独立业务检查和离线浏览器检查全部通过。报告保持原实测字节，不把空数据、报错处理或仅生成页面计作通过。

| 场景 | 真实使用需求 | 报告 |
|---|---|---|
| [连锁餐饮品牌门店盘点](01-restaurant-portfolio/README.md) | 盘点四川海底捞餐饮股份有限公司旗下餐饮品牌与门店分布，用于区域扩张复盘。 | [HTML](01-restaurant-portfolio/report.html) / [MD](01-restaurant-portfolio/report.md) / [JSON](01-restaurant-portfolio/report.json) |
| [广州汽车维修营业状态初筛](09-auto-service-status-shortlist/README.md) | 请检索广州汽车服务/汽车维修门店，依据实际店名、分类和门店状态区分可继续核验与已关闭/下架样本；不要验证地址或维修资质。 | [HTML](09-auto-service-status-shortlist/report.html) / [MD](09-auto-service-status-shortlist/report.md) / [JSON](09-auto-service-status-shortlist/report.json) |
| [成都海底捞门店经营字段快照](10-hotpot-local-operation-snapshot/README.md) | 请检索成都名称包含海底捞的门店样本，展示实际店名与状态，并从商圈、人均价格、排名中至少提供两项可用字段，用于观察本地样本差异；不核验地址或品牌归属。 | [HTML](10-hotpot-local-operation-snapshot/report.html) / [MD](10-hotpot-local-operation-snapshot/report.md) / [JSON](10-hotpot-local-operation-snapshot/report.json) |
| [杭州药店拜访优先字段清单](11-pharmacy-visit-priority/README.md) | 请检索杭州药店类门店，按实际店名、营业状态、商圈以及人均价格或排名整理人工拜访优先字段；不要判断药品许可或地址匹配。 | [HTML](11-pharmacy-visit-priority/report.html) / [MD](11-pharmacy-visit-priority/report.md) / [JSON](11-pharmacy-visit-priority/report.json) |

- [逐例验收结果](results.json) · [业务复核](review.json) · [证据摘要](evidence-index.json)
- [完整测试记录](../test-records/live-replaced-20261027/README.md)仅用于审计，不属于可展示示例。
- 当前数据与结论限于原查询时点及公开样本；覆盖率不代表准确率或低风险。
