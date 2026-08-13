# MCP 工具参考 — store-mcp-server

本 skill 连接的 MCP server：`handaas-mcp-server/store-mcp-server`（“店铺大数据”）。

> **重要**：本 skill 有**两种模式**：
> - **企业模式**（`--enterprise`）：`company_restaurant_branches` 入参为 `matchKeyword`（企业全称）+ `keywordType`；
>   `restaurant_branch_stats` 的 `matchKeyword` 是**品牌 id**（取自 `company_restaurant_branches` 返回的某个品牌的 `brandId`）。
> - **检索模式**（`--store-name` / `--brand` / `--category`）：`offline_store_search` 按门店检索条件查询。
> 当用户只给企业关键词时，先调模糊查询补全全称。

## 通用约定

- `keywordType` 枚举：`name`（企业名称）/ `nameId`（企业 id）/ `regNumber`（注册号）/ `socialCreditCode`（统一社会信用代码）。
- 分页：`pageIndex` 从 1 开始；`pageSize` 单页最多 50。
- 多选格式：`ooStoreBrandList` 用英文分号 `;` 分隔；`ooStoreCalClassification` 一/二级类目用英文逗号 `,`，多选用英文分号（如 `汽车服务,汽车俱乐部;汽车服务,汽车维修`）。

---

## 工具清单

### 1. `store_bigdata_company_restaurant_branches` — 餐饮品牌门店

用途：按企业主体返回旗下餐饮品牌列表，含品牌类别、起源地、门店数、商场店数、城市/省份分布（前 10）。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `matchKeyword` | string | 是 | 企业名称 / 注册号 / 统一社会信用代码 / 企业 id（无全称则先调 fuzzy_search） |
| `keywordType` | string | 否 | 主体类型：name / nameId / regNumber / socialCreditCode |

返回：`storeTotal`（门店总数）、`storeList`（品牌列表 list of {brandId, brandName, firstClassify, secondClassify, brandCradle, brandStoreNum, mallStoreNum, brandStoreCityStats, brandStoreProvinceStats}）。

product_id：`66f3d8bf64bd2be52d68a0e9`。

---

### 2. `store_bigdata_restaurant_branch_stats` — 餐饮门店分布统计

用途：按**品牌 id** 返回该品牌在各城市及省份的门店分布数量。`matchKeyword` 来自 `company_restaurant_branches` 返回的 `brandId`。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `matchKeyword` | string | 是 | **品牌 id**（字段来源：企业旗下餐饮品牌门店的 `brandId`） |
| `pageIndex` | int | 否 | 从 1 开始（默认 1） |
| `pageSize` | int | 否 | 单页最多 50 |

返回：`cityStatsTotal`（覆盖城市数）、`provinceStatsTotal`（覆盖省份数）、`cityStatsList`（城市分布 list of {city,count}）、`provinceStatsList`（省份分布 list of {province,count}）。

product_id：`66f3d8c064bd2be52d68a159`。

---

### 3. `store_bigdata_offline_store_search` — 线下门店检索

用途：按店铺名称 / 经营品牌 / 店铺分类 / 地区 / 状态 / 人均消费等条件检索线下门店。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `ooStoreName` | string | 否 | 店铺名称 |
| `ooStoreBrandList` | string | 否 | 经营品牌（多选用英文分号 `;` 分隔） |
| `ooStoreCalClassification` | string | 否 | 店铺分类（一/二级类目用英文逗号，多选用英文分号） |
| `address` | string | 否 | 地区（英文逗号分割，如 `广东省,广州市,天河公园`） |
| `ooStoreStatus` | string | 否 | 店铺状态：营业 / 尚未营业 / 暂停营业 / 歇业·关闭 / 关闭·下架（默认全部） |
| `ooStoreAddressValue` | string | 否 | 店铺地址 |
| `hasMobile` | string | 否 | 有无手机号：1 / 0 |
| `hasPhone` | int | 否 | 有无固话：1 / 0 |
| `ooMinStorePerCapitaConsumption` | float | 否 | 人均消费最小值 |
| `ooMaxStorePerCapitaConsumption` | float | 否 | 人均消费最大值 |
| `pageIndex` | int | 否 | 从 1 开始 |
| `pageSize` | int | 否 | 单页最多 50（默认 10） |

返回（list + `total`）：`ooStoreId`（店铺 id）、`ooStoreName`（店铺名称）、`ooStoreCalClassification`（店铺分类）、`ooStoreStatus`（店铺状态）、`ooStoreTradingArea`（商圈）、`ooStorePerCapitaConsumption`（人均价格）、`ooStoreRank`（店铺排名）、`hasContact` / `contactNumber` / `hasMobile` / `hasPhone`（联系方式字段）。

product_id：`66ed53be15858a879f40242f`。

---

### 4. `store_bigdata_fuzzy_search` — 关键词模糊查询企业

用途：根据企业名称 / 人名 / 品牌 / 产品等关键词模糊查询企业列表，用于补全企业全称（仅企业模式、且输入非全称时调用）。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `matchKeyword` | string | 是 | 匹配关键词 |
| `pageIndex` | int | 否 | 分页开始位置（默认 1） |
| `pageSize` | int | 否 | 单页最多 50 |

返回：`total` + 企业列表（`name`、`nameId`、`regCapitalValue`、`foundTime`、`operStatus`、`address`、`legalRepresentative`、`enterpriseType`、`catchReason` 等）。

product_id：`675cea1f0e009a9ea37edaa1`。

---

## 推荐调用顺序（报告编排）

### 企业模式
1. （若仅有关键词）`store_bigdata_fuzzy_search` → 取 `name` 作为全称。
2. `store_bigdata_company_restaurant_branches` → 旗下品牌列表 + 门店总数。
3. 取首个品牌的 `brandId` → `store_bigdata_restaurant_branch_stats` → 城市 / 省份分布统计。

### 检索模式
1. `store_bigdata_offline_store_search` → 按门店名称 / 品牌 / 分类 / 地区等检索明细。

> 企业模式通常调用 2-3 个工具；检索模式调用 1 个工具。
