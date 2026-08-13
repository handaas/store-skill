#!/usr/bin/env python3
"""Compose a store big-data report by orchestrating the store MCP.

Calls the upstream store-mcp-server tools and assembles a structured JSON
payload rendered into a professional HTML / Markdown report. Supports
``--dry-run`` which returns a well-formed skeleton from the bundled sample data
WITHOUT contacting the MCP.

The store report has TWO modes:

- **Enterprise mode** (``--enterprise``): query a company's restaurant brands
  (`company_restaurant_branches`) and, for the top brand, its branch stats
  (`restaurant_branch_stats`, which takes a *brand id* as `matchKeyword`).
- **Search mode** (``--store-name`` / ``--brand`` / ``--category``): query
  offline stores directly via `offline_store_search`.

This file never prints secrets; MCP credentials live in the server's own .env.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys
from typing import Any, Dict, List, Mapping, Optional

from common import REPORT_BANNER, REPORT_TYPE, json_dumps, load_json_file, print_json
import mcp_client
from render_report import render_html, render_markdown, html_to_pdf

SAMPLE_PATH = pathlib.Path(__file__).resolve().parent.parent / "assets" / "report.example.json"

# Store MCP tools.
T_FUZZY = "store_bigdata_fuzzy_search"
T_BRANCHES = "store_bigdata_company_restaurant_branches"
T_OFFLINE_SEARCH = "store_bigdata_offline_store_search"
T_BRANCH_STATS = "store_bigdata_restaurant_branch_stats"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _is_api_error(value: Any) -> bool:
    """Detect MCP API error responses (not empty data, but actual failures like 405)."""
    if value is None:
        return False
    if isinstance(value, str):
        return any(s in value for s in ("接口调用失败", "查询失败", "状态码：4", "状态码：5"))
    if isinstance(value, dict):
        for v in value.values():
            if isinstance(v, str) and any(s in v for s in ("接口调用失败", "查询失败", "状态码：4", "状态码：5")):
                return True
    return False

def _first_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        if _is_api_error(value):
            return []
        # Treat upstream empty responses ({"text": "查询数据为空"}) and internal
        # skip markers ({"_error": "未指定..."}) as empty so tables don't render
        # a phantom all-"-" row.
        if set(value.keys()) <= {"text", "error", "code", "_error"} and not any(
            isinstance(value.get(k), list) for k in ("resultList", "storeList", "list", "items", "data")
        ):
            return []
        for key in ("resultList", "storeList", "list", "items", "data"):
            if isinstance(value.get(key), list):
                return value[key]
    if value in (None, "", {}):
        return []
    return [value]


def _first_record(value: Any) -> Dict[str, Any]:
    for record in _first_list(value):
        if isinstance(record, dict):
            return record
    if isinstance(value, dict):
        return value
    return {}


def _text(value: Any, limit: int = 0) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        t = json.dumps(value, ensure_ascii=False)
    else:
        t = str(value)
    t = " ".join(t.split())
    if limit and len(t) > limit:
        return t[: limit - 1].rstrip() + "…"
    return t


def _int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_call(tool: str, arguments: Dict[str, Any]) -> Any:
    try:
        result = mcp_client.call_tool(tool, arguments)
        if _is_api_error(result):
            return {"_error": "API错误"}
        return result
    except Exception as exc:
        return {"_error": str(exc)}


def _safe_total(payload: Any, *keys: str) -> Any:
    if isinstance(payload, dict):
        for key in keys:
            if payload.get(key) is not None:
                return payload.get(key)
        return payload.get("total")
    return None


# --------------------------------------------------------------------------- #
# Resolution
# --------------------------------------------------------------------------- #

def resolve_enterprise_name(raw: str) -> Dict[str, Any]:
    raw = (raw or "").strip()
    if not raw:
        return {"keyword": "", "enterprise": "", "resolved": False, "reason": "关键词为空"}
    if any(suffix in raw for suffix in ("公司", "集团", "有限", "院", "厂", "中心", "事务所", "合作社", "合伙")):
        return {"keyword": raw, "enterprise": raw, "resolved": True, "reason": "视为企业全称"}
    fuzzy = _safe_call(T_FUZZY, {"matchKeyword": raw, "pageSize": 1})
    record = _first_record(fuzzy)
    name = str(record.get("name") or "").strip()
    if name:
        return {"keyword": raw, "enterprise": name, "resolved": True, "reason": "由关键词模糊查询补全", "fuzzy_total": _int(_safe_total(fuzzy)), "record": record}
    return {"keyword": raw, "enterprise": raw, "resolved": False, "reason": "模糊查询未命中企业全称，按关键词直查"}


# --------------------------------------------------------------------------- #
# Enterprise profile helpers (from fuzzy_search record)
# --------------------------------------------------------------------------- #

def _extract_profile(record: Dict[str, Any]) -> Dict[str, Any]:
    """Extract enterprise profile fields from a fuzzy_search record."""
    return {
        "name": _text(record.get("name")),
        "reg_capital": record.get("regCapitalValue"),
        "reg_capital_coin": _text(record.get("regCapitalCoinType")),
        "annual_turnover": _text(record.get("annualTurnover")),
        "oper_status": _text(record.get("operStatus")),
        "enterprise_type": _text(record.get("enterpriseType")),
        "found_time": _text(record.get("foundTime")),
        "legal_rep": _text(record.get("legalRepresentative")),
        "address": _text(record.get("address")),
        "homepage": _text(record.get("homepage")),
    }


def _format_capital(val: Any, coin: str = "") -> str:
    """Format capital value: 10995210218.0 -> '109.95 亿'."""
    try:
        v = float(val)
        if v >= 1e8:
            s = f"{v / 1e8:.2f} 亿"
        elif v >= 1e4:
            s = f"{v / 1e4:.2f} 万"
        else:
            s = f"{v:.0f}"
        if coin:
            s += f" {coin}"
        return s
    except (TypeError, ValueError):
        return _text(val) if val else "-"


def _enrich_metrics_with_profile(metrics: List[Dict[str, Any]], record: Any) -> List[Dict[str, Any]]:
    """Append enterprise profile metrics from a fuzzy_search record."""
    if not isinstance(record, dict):
        return metrics
    _prof = _extract_profile(record)
    if _prof.get("reg_capital") and _prof["reg_capital"] not in ("-", "", None):
        metrics.append({"label": "注册资本", "value": _format_capital(_prof["reg_capital"], _prof.get("reg_capital_coin", "")), "hint": "工商登记注册资本"})
    if _prof.get("found_time") and _prof["found_time"] != "-":
        metrics.append({"label": "成立时间", "value": _prof["found_time"], "hint": "工商登记成立日期"})
    if _prof.get("oper_status") and _prof["oper_status"] != "-":
        metrics.append({"label": "经营状态", "value": _prof["oper_status"], "hint": "工商登记经营状态"})
    if _prof.get("enterprise_type") and _prof["enterprise_type"] != "-":
        metrics.append({"label": "企业类型", "value": _prof["enterprise_type"], "hint": "工商登记企业类型"})
    if _prof.get("legal_rep") and _prof["legal_rep"] != "-":
        metrics.append({"label": "法定代表人", "value": _prof["legal_rep"], "hint": "工商登记法定代表人"})
    return metrics


def _derive_core_metrics(metrics: List[Dict[str, Any]], core: Mapping[str, Any]) -> List[Dict[str, Any]]:
    """Derive additional metrics from core analysis sections."""
    brands = core.get("brand_records", []) if isinstance(core, dict) else []
    branches = core.get("branch_stats", []) if isinstance(core, dict) else []
    if isinstance(brands, list) and brands:
        categories = set(str(r.get("一级类别", "")) for r in brands if r.get("一级类别"))
        if categories:
            metrics.append({"label": "餐饮类别数", "value": str(len(categories)), "hint": "覆盖的餐饮一级类别数"})
        try:
            def _cnt(r):
                v = str(r.get("门店数", "0")).replace(",", "")
                return int(v) if v.isdigit() else 0
            top_brand = max(brands, key=_cnt)
            if top_brand.get("品牌名称"):
                cnt = _cnt(top_brand)
                metrics.append({"label": "主力品牌", "value": f"{top_brand['品牌名称']}（{cnt}家）", "hint": "门店数最多的品牌"})
        except (ValueError, TypeError):
            pass
    if isinstance(branches, list) and branches:
        try:
            nums = [int(str(r.get("门店数量", "0")).replace(",", "")) for r in branches if str(r.get("门店数量", "0")).replace(",", "").isdigit()]
            total = sum(nums)
            if total > 0:
                top3 = sum(sorted(nums, reverse=True)[:3])
                metrics.append({"label": "城市CR3", "value": f"{top3/total*100:.1f}%", "hint": "前3大城市门店集中度"})
        except (ValueError, TypeError):
            pass
    return metrics


# --------------------------------------------------------------------------- #
# Section builders
# --------------------------------------------------------------------------- #

def build_subject(mode: str, raw: str, resolved: Mapping[str, Any], keyword_type: str, filters: Mapping[str, Any]) -> Dict[str, Any]:
    subject: Dict[str, Any] = {
        "mode": mode,
        "keywordType": keyword_type,
        "match_raw": raw,
    }
    if mode == "enterprise":
        subject.update({
            "enterprise": resolved.get("enterprise") or raw,
            "matchKeyword": resolved.get("enterprise") or raw,
            "resolved": bool(resolved.get("resolved")),
            "resolve_reason": resolved.get("reason", ""),
        })
    else:
        subject.update({
            "enterprise": "",
            "matchKeyword": filters.get("store_name") or filters.get("brand") or filters.get("category") or raw,
            "store_name": filters.get("store_name") or "",
            "brand": filters.get("brand") or "",
            "category": filters.get("category") or "",
            "address": filters.get("address") or "",
        })
    return subject


def build_metrics(branches: Any, branch_stats: Any, offline_search: Any) -> List[Dict[str, Any]]:
    metrics: List[Dict[str, Any]] = []
    b = branches if isinstance(branches, dict) else {}
    brand_total = _safe_total(b, "storeTotal", "total")
    if brand_total is not None:
        metrics.append({"label": "旗下品牌数", "value": _text(brand_total), "hint": "企业旗下餐饮品牌总数"})
    brand_list = _first_list(b.get("storeList") or b)
    if brand_list:
        # 旗下门店总数：汇总各品牌 brandStoreNum。
        total_stores = 0
        main_brand = ""
        main_n = 0
        for br in brand_list:
            if not isinstance(br, dict):
                continue
            n = _int(br.get("brandStoreNum")) or 0
            total_stores += n
            if n > main_n:
                main_n = n
                main_brand = _text(br.get("brandName")) or "-"
        if total_stores:
            metrics.append({"label": "门店总数(汇总)", "value": str(total_stores), "hint": "各品牌门店数汇总"})
        if main_brand and main_n:
            metrics.append({"label": "主力品牌门店数", "value": str(main_n), "hint": f"主力品牌“{main_brand}”门店数"})

    # 城市/省份覆盖：从 branches 主力品牌分布统计；回退到 branch_stats 接口。
    city_total: Any = None
    prov_total: Any = None
    if brand_list:
        try:
            top_brand = max(brand_list, key=lambda x: _int((x or {}).get("brandStoreNum")) or 0)
        except (TypeError, ValueError):
            top_brand = {}
        if isinstance(top_brand, dict):
            city_stats = _first_list(top_brand.get("brandStoreCityStats"))
            prov_stats = _first_list(top_brand.get("brandStoreProvinceStats"))
            city_total = len(city_stats) if city_stats else None
            prov_total = len(prov_stats) if prov_stats else None
    if city_total is None and isinstance(branch_stats, dict):
        city_total = branch_stats.get("cityStatsTotal")
    if prov_total is None and isinstance(branch_stats, dict):
        prov_total = branch_stats.get("provinceStatsTotal")
    if city_total is not None:
        metrics.append({"label": "覆盖城市数", "value": _text(city_total), "hint": "主力品牌门店覆盖城市数"})
    if prov_total is not None:
        metrics.append({"label": "覆盖省份数", "value": _text(prov_total), "hint": "主力品牌门店覆盖省份数"})

    offline_total = _safe_total(offline_search, "total")
    if offline_total is not None:
        metrics.append({"label": "线下门店检索结果", "value": _text(offline_total), "hint": "本次线下门店检索命中条数"})
    return [m for m in metrics if m.get("value") not in ("", None, "-")]


def build_caliber(subject: Mapping[str, Any]) -> Dict[str, Any]:
    if subject.get("mode") == "enterprise":
        match_target = subject.get("enterprise") or subject.get("match_raw")
        match_type = f"店铺大数据按企业主体匹配（keywordType={subject.get('keywordType', 'name')}）；门店分布统计按品牌 id 匹配"
    else:
        match_target = "、".join([v for v in (subject.get("store_name"), subject.get("brand"), subject.get("category")) if v]) or "线下门店检索条件"
        match_type = "店铺大数据按门店检索条件匹配（店铺名称 / 经营品牌 / 店铺分类）"
    return {
        "match_target": match_target,
        "match_type": match_type,
        "data_scope": "餐饮品牌门店、餐饮门店分布统计、线下门店检索明细",
        "products": ["餐饮品牌门店", "餐饮门店分布统计", "线下门店检索"],
        "limit": "数据来自店铺公开数据库；少量字段可能存在更新延迟。",
    }


def build_core_analysis(branches: Any, branch_stats: Any, offline_search: Any, subject: Mapping[str, Any]) -> Dict[str, Any]:
    # 餐饮品牌门店表 — brandClassification 是嵌套 dict {firstClassify, secondClassify}。
    b = branches if isinstance(branches, dict) else {}
    brand_rows = []
    for item in _first_list(b.get("storeList") or b):
        if not isinstance(item, dict):
            continue
        cls = item.get("brandClassification") or {}
        first_cls = cls.get("firstClassify") if isinstance(cls, dict) else None
        second_cls = cls.get("secondClassify") if isinstance(cls, dict) else None
        brand_rows.append({
            "品牌名称": _text(item.get("brandName")) or "-",
            "一级类别": _text(first_cls) or "-",
            "二级类别": _text(second_cls) or "-",
            "起源地": _text(item.get("brandCradle")) or "-",
            "门店数": _text(item.get("brandStoreNum")) or "-",
            "商场店数": _text(item.get("mallStoreNum")) or "-",
        })

    # 城市/省份分布：branches 响应里每个品牌已带 brandStoreCityStats /
    # brandStoreProvinceStats（[{city/province, count}]），无需再调 branch_stats。
    # 取门店数最大的品牌（主力品牌）作为分布主体，避免多品牌重复计数。
    stats_rows: List[Dict[str, Any]] = []
    top_brand_for_stats: Dict[str, Any] = {}
    if brand_rows:
        try:
            top_brand_for_stats = max(
                _first_list(b.get("storeList") or b),
                key=lambda x: _int((x or {}).get("brandStoreNum")) or 0,
            )
        except (TypeError, ValueError):
            top_brand_for_stats = {}
    if isinstance(top_brand_for_stats, dict):
        for item in _first_list(top_brand_for_stats.get("brandStoreCityStats")):
            if isinstance(item, dict):
                stats_rows.append({"地区类型": "城市", "地区": _text(item.get("city")) or "-", "门店数量": _text(item.get("count")) or "-"})
        for item in _first_list(top_brand_for_stats.get("brandStoreProvinceStats")):
            if isinstance(item, dict):
                stats_rows.append({"地区类型": "省份", "地区": _text(item.get("province")) or "-", "门店数量": _text(item.get("count")) or "-"})
    # 兜底：若 branches 未带分布数据而 branch_stats 接口（旧逻辑）有数据，则合并使用。
    bs = branch_stats if isinstance(branch_stats, dict) else {}
    if not stats_rows:
        for item in _first_list(bs.get("cityStatsList")):
            if isinstance(item, dict):
                stats_rows.append({"地区类型": "城市", "地区": _text(item.get("city")) or "-", "门店数量": _text(item.get("count")) or "-"})
        for item in _first_list(bs.get("provinceStatsList")):
            if isinstance(item, dict):
                stats_rows.append({"地区类型": "省份", "地区": _text(item.get("province")) or "-", "门店数量": _text(item.get("count")) or "-"})

    # 线下门店检索明细表
    offline_rows = []
    offline_total = _safe_total(offline_search, "total")
    for item in _first_list(offline_search):
        if not isinstance(item, dict):
            continue
        cls = item.get("ooStoreCalClassification")
        cls_text = _text(cls) if not isinstance(cls, dict) else "、".join(_text(v) for v in cls.values() if v)
        offline_rows.append({
            "店铺名称": _text(item.get("ooStoreName")) or "-",
            "店铺分类": cls_text or "-",
            "店铺状态": _text(item.get("ooStoreStatus")) or "-",
            "商圈": _text(item.get("ooStoreTradingArea")) or "-",
            "人均价格": _text(item.get("ooStorePerCapitaConsumption")) or "-",
            "店铺排名": _text(item.get("ooStoreRank")) or "-",
        })

    # 统计覆盖的城市/省份数（来自主力品牌的分布）。
    city_count = sum(1 for r in stats_rows if r.get("地区类型") == "城市")
    prov_count = sum(1 for r in stats_rows if r.get("地区类型") == "省份")

    sections = []
    if subject.get("mode") == "enterprise":
        if brand_rows:
            sections.append({"key": "brand_records", "title": "餐饮品牌门店", "kind": "table",
                             "note": f"共 {len(brand_rows)} 个品牌，展示前 N 个",
                             "columns": [("品牌名称", "品牌名称"), ("一级类别", "一级类别"), ("二级类别", "二级类别"), ("起源地", "起源地"), ("门店数", "门店数"), ("商场店数", "商场店数")]})
        if stats_rows:
            main_brand = top_brand_for_stats.get("brandName") if isinstance(top_brand_for_stats, dict) else None
            note_brand = f"（主力品牌“{main_brand}”）" if main_brand else ""
            sections.append({"key": "branch_stats", "title": "餐饮门店城市/省份分布", "kind": "bar",
                             "note": f"按主力品牌统计门店地域分布{note_brand}（覆盖城市 {city_count} / 省份 {prov_count}）",
                             "chart": {"name": "地区", "value": "门店数量", "orient": "h"},
                             "columns": [("地区类型", "地区类型"), ("地区", "地区"), ("门店数量", "门店数量")]})
    if offline_rows:
        sections.append({"key": "offline_records", "title": "线下门店检索明细", "kind": "table",
                         "note": f"本次检索命中 {offline_total if offline_total is not None else '若干'} 条，展示前 {len(brand_rows)} 条",
                         "columns": [("店铺名称", "店铺名称"), ("店铺分类", "店铺分类"), ("店铺状态", "店铺状态"), ("商圈", "商圈"), ("人均价格", "人均价格"), ("店铺排名", "店铺排名")]})

    return {
        "sections": sections,
        "brand_records": brand_rows,
        "branch_stats": stats_rows,
        "offline_records": offline_rows,
    }


def build_records(core: Mapping[str, Any]) -> List[Dict[str, Any]]:
    out = []
    for item in core.get("brand_records") or []:
        out.append({
            "品牌名称": item.get("品牌名称") or "-",
            "门店数": item.get("门店数") or "-",
        })
    for item in core.get("offline_records") or []:
        out.append({
            "品牌名称": item.get("店铺名称") or "-",
            "门店数": item.get("店铺状态") or "-",
        })
    return out[:20]


def _concentration(rows: List[Mapping[str, Any]], top_n: int = 3) -> Dict[str, Any]:
    """Compute top-N concentration (CRn) of门店数量 across 地区 rows."""
    items = []
    for r in rows:
        try:
            items.append((r.get("地区", "-"), float(str(r.get("门店数量", 0)).replace(",", ""))))
        except (TypeError, ValueError):
            items.append((r.get("地区", "-"), 0.0))
    total = sum(v for _, v in items)
    if not total:
        return {}
    items.sort(key=lambda x: x[1], reverse=True)
    cr = sum(v for _, v in items[:top_n]) / total * 100
    return {"top": items[0][0], "top_type": "", "top_share": items[0][1] / total * 100, "cr": cr, "total": total}


def build_insights(subject: Mapping[str, Any], core: Mapping[str, Any], metrics: List[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    insights: List[Dict[str, Any]] = []
    metric_map = {m["label"]: str(m["value"]) for m in metrics}
    total = metric_map.get("门店总数(汇总)") or metric_map.get("旗下门店总数")
    brand_n = metric_map.get("旗下品牌数") or metric_map.get("品牌数量")
    city_n = metric_map.get("覆盖城市数")
    offline_n = metric_map.get("线下门店检索结果")

    if subject.get("mode") == "enterprise":
        if total:
            insights.append({
                "feature": "门店资产规模",
                "evidence": f"企业旗下餐饮门店总数（汇总）{total}。",
                "interpretation": "门店总量反映企业在餐饮赛道的线下布局广度，是品牌影响力与渠道覆盖的直接信号。",
            })
        if brand_n:
            insights.append({
                "feature": "品牌矩阵",
                "evidence": f"旗下餐饮品牌 {brand_n} 个。",
                "interpretation": "多品牌矩阵通常意味着差异化定位与细分市场覆盖；单一品牌则代表集中化策略。",
            })
        if city_n:
            insights.append({
                "feature": "地域覆盖",
                "evidence": f"门店覆盖城市 {city_n} 个。",
                "interpretation": "覆盖城市数反映品牌可触达的消费市场广度；城市越分散，地域风险越分散。",
            })
    if offline_n:
        insights.append({
            "feature": "线下门店检索",
            "evidence": f"按检索条件命中线下门店 {offline_n} 家。",
            "interpretation": "检索命中量反映目标门店的密度；可结合商圈与人均消费筛选高价值门店。",
        })
    stats_rows = core.get("branch_stats") or []
    if stats_rows:
        conc = _concentration(stats_rows, 3)
        if conc:
            # find type of top region
            top_type = "-"
            for r in stats_rows:
                if r.get("地区") == conc["top"]:
                    top_type = r.get("地区类型", "-")
                    break
            insights.append({
                "feature": "门店集中度",
                "evidence": f"门店分布最多的{top_type}为“{conc['top']}”（占比约 {conc['top_share']:.0f}%），前 3 地区合计 {conc['cr']:.0f}%（CR3）。",
                "interpretation": "门店集中度反映品牌核心市场；CR3 越高代表深耕优势区域，但单一区域依赖也意味着区域收缩风险；分散则代表全国化布局。",
            })
    if not insights:
        insights.append({
            "feature": "数据完整性",
            "evidence": "部分维度未返回有效数据。",
            "interpretation": "建议核对匹配关键词（企业主体或门店检索条件），或检查 MCP 连接与上游数据产品覆盖范围。",
        })
    return insights


def build_abstract(subject: Mapping[str, Any], core: Mapping[str, Any], metrics: List[Mapping[str, Any]]) -> str:
    if subject.get("mode") == "enterprise":
        name = subject.get("enterprise") or subject.get("match_raw") or "目标企业"
        parts = [f"本报告以“{name}”为分析对象，基于店铺公开数据，系统呈现企业旗下餐饮品牌门店、餐饮门店分布统计与线下门店检索明细。"]
    else:
        cond = "、".join([v for v in (subject.get("store_name"), subject.get("brand"), subject.get("category")) if v]) or "门店检索条件"
        parts = [f"本报告以“{cond}”为检索对象，基于店铺公开数据，系统呈现线下门店检索明细。"]
    if metrics:
        kv = "、".join(f"{m['label']} {m['value']}" for m in metrics[:5])
        parts.append(f"关键指标包括：{kv}。")
    parts.append("报告同时给出门店资产规模、品牌矩阵与地域覆盖的结构化解读，便于市场调研、选址分析与商业合作参考。")
    return "".join(parts)


# --------------------------------------------------------------------------- #
# Dry-run sample
# --------------------------------------------------------------------------- #

def build_dry_run_payload(mode: str, raw: str, keyword_type: str, filters: Mapping[str, Any]) -> Dict[str, Any]:
    try:
        sample = load_json_file(SAMPLE_PATH)
    except Exception:
        sample = {}
    sample = sample if isinstance(sample, dict) else {}
    enterprise_resolved = {"enterprise": filters.get("enterprise") or raw, "resolved": True, "reason": "dry-run"}
    subject = sample.get("subject") or build_subject(mode, raw, enterprise_resolved, keyword_type, filters)
    subject = {**subject, "mode": mode, "match_raw": raw, "keywordType": keyword_type}
    core = sample.get("core_analysis") or {}
    metrics = sample.get("metrics") or []
    return _assemble(subject, core, metrics, dry_run=True)


# --------------------------------------------------------------------------- #
# Assembly
# --------------------------------------------------------------------------- #

def _assemble(subject: Mapping[str, Any], core: Mapping[str, Any], metrics: List[Mapping[str, Any]], *, dry_run: bool) -> Dict[str, Any]:
    abstract = build_abstract(subject, core, metrics)
    records = build_records(core)
    insights = build_insights(subject, core, metrics)
    # Quality gate: count populated core-analysis sections.
    ca = core if isinstance(core, dict) else {}
    secs = ca.get("sections", [])
    if secs:
        total_secs = len(secs)
        populated = sum(1 for s in secs if isinstance(s, dict) and ca.get(s.get("key")) not in (None, "", [], {}))
    else:
        total_secs = max(1, len([k for k in ca if k != "sections"]))
        populated = sum(1 for k in ca if k != "sections" and ca.get(k) not in (None, "", [], {}))
    quality_report = {
        "total_sections": total_secs,
        "populated_sections": populated,
        "empty_sections": total_secs - populated,
        "coverage_pct": round(populated / max(1, total_secs) * 100),
    }
    if populated == 0:
        import sys
        print("⚠️ 质量门禁警告: 所有核心分析维度均无数据", file=sys.stderr)
    if subject.get("mode") == "enterprise":
        title = f"{subject.get('enterprise') or '目标企业'} 店铺大数据报告"
    else:
        cond = "、".join([v for v in (subject.get("store_name"), subject.get("brand"), subject.get("category")) if v]) or "线下门店"
        title = f"“{cond}” 店铺大数据报告"
    return {
        "report_type": REPORT_TYPE,
        "title": title,
        "banner": REPORT_BANNER,
        "subject": dict(subject),
        "abstract": abstract,
        "summary": abstract,
        "executive_summary": [item["interpretation"] for item in insights][:5] or [abstract[:120]],
        "metrics": list(metrics),
        "caliber": build_caliber(subject),
        "core_analysis": dict(core),
        "representative_records": records,
        "insights": insights,
        "data_source": {
            "mcp_server": "store-mcp-server",
            "products": [
                {"name": "餐饮品牌门店", "product_id": "66f3d8bf64bd2be52d68a0e9"},
                {"name": "企业模糊查询", "product_id": "675cea1f0e009a9ea37edaa1"},
                {"name": "线下门店检索", "product_id": "66ed53be15858a879f40242f"},
                {"name": "餐饮门店分布统计", "product_id": "66f3d8c064bd2be52d68a159"},
            ],
            "generated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
            "dry_run": dry_run,
            "quality_report": quality_report,
        },
    }


def build_payload_enterprise(raw: str, keyword_type: str, page_size: int) -> Dict[str, Any]:
    resolved = resolve_enterprise_name(raw)
    enterprise = resolved["enterprise"]
    mk_args: Dict[str, Any] = {"matchKeyword": enterprise, "keywordType": keyword_type}
    branches = _safe_call(T_BRANCHES, mk_args)

    # NOTE: branches 响应不带 brandId，且 branch_stats 接口按品牌 id 查询；因此
    # 企业模式的门店分布直接来自 branches 响应里的 brandStoreCityStats /
    # brandStoreProvinceStats（见 build_core_analysis），不再调用 branch_stats。
    branch_stats: Any = {}

    subject = build_subject("enterprise", raw, resolved, keyword_type, {})
    core = build_core_analysis(branches, branch_stats, {}, subject)
    metrics = build_metrics(branches, branch_stats, {})
    _derive_core_metrics(metrics, core if isinstance(core, dict) else {})
    return _assemble(subject, core, metrics, dry_run=False)


def build_payload_search(filters: Mapping[str, Any], page_size: int) -> Dict[str, Any]:
    search_args: Dict[str, Any] = {"pageIndex": 1, "pageSize": page_size}
    if filters.get("store_name"):
        search_args["ooStoreName"] = filters["store_name"]
    if filters.get("brand"):
        search_args["ooStoreBrandList"] = filters["brand"]
    if filters.get("category"):
        search_args["ooStoreCalClassification"] = filters["category"]
    if filters.get("address"):
        search_args["address"] = filters["address"]
    offline_search = _safe_call(T_OFFLINE_SEARCH, search_args)

    raw = filters.get("store_name") or filters.get("brand") or filters.get("category") or ""
    subject = build_subject("search", raw, {}, "name", filters)
    core = build_core_analysis({}, {}, offline_search, subject)
    metrics = build_metrics({}, {}, offline_search)
    # --- Enterprise profile enrichment (from fuzzy_search) ---
    _enrich_metrics_with_profile(metrics, resolved.get("record") if isinstance(resolved, dict) else None)
    return _assemble(subject, core, metrics, dry_run=False)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main() -> None:
    parser = argparse.ArgumentParser(description="Compose a store big-data report via the store MCP. Two modes: enterprise (--enterprise) or search (--store-name/--brand/--category).")
    parser.add_argument("--enterprise", default=None, help="企业全称或关键词（关键词将自动模糊补全）；启用企业模式：餐饮品牌门店 + 门店分布统计")
    parser.add_argument("--keyword-type", default="name", help="主体类型：name/nameId/regNumber/socialCreditCode（仅企业模式）")
    parser.add_argument("--store-name", default=None, help="店铺名称（启用检索模式）")
    parser.add_argument("--brand", default=None, help="经营品牌（启用检索模式，多选用英文分号分隔）")
    parser.add_argument("--category", default=None, help="店铺分类（启用检索模式，格式如 汽车服务,汽车维修；多选用英文分号分隔）")
    parser.add_argument("--address", default=None, help="地区过滤（检索模式），如 广东省,广州市")
    parser.add_argument("--page-size", type=int, default=10, help="分页大小（最多 50）")
    parser.add_argument("--dry-run", action="store_true", help="不调用真实 MCP，使用样例数据组装报告骨架")
    parser.add_argument("--output", help="输出 JSON 路径；省略则打印到 stdout")
    parser.add_argument("--report-output", help="同时输出 HTML 报告（.html）与 Markdown 报告（.md）")
    parser.add_argument("--pdf-output", help="额外输出 PDF 报告（.pdf）；需要 Playwright + Chromium")
    args = parser.parse_args()

    search_mode = any([args.store_name, args.brand, args.category])
    if not args.enterprise and not search_mode:
        parser.error("必须提供 --enterprise（企业模式）或 --store-name/--brand/--category 之一（检索模式）")

    if args.enterprise:
        mode = "enterprise"
        raw = args.enterprise
    else:
        mode = "search"
        raw = args.store_name or args.brand or args.category or ""

    filters = {
        "store_name": args.store_name,
        "brand": args.brand,
        "category": args.category,
        "address": args.address,
        "enterprise": args.enterprise,
    }

    if args.dry_run:
        payload = build_dry_run_payload(mode, raw, args.keyword_type, filters)
    elif mode == "enterprise":
        payload = build_payload_enterprise(args.enterprise, args.keyword_type, args.page_size)
    else:
        payload = build_payload_search(filters, args.page_size)

    if args.output:
        out = pathlib.Path(args.output).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json_dumps(payload, pretty=True), encoding="utf-8")
        print_json({"ok": True, "json": str(out), "dry_run": args.dry_run, "mode": mode})
    else:
        print_json(payload)

    if args.report_output:
        base_out = pathlib.Path(args.report_output).expanduser()
        base_out.parent.mkdir(parents=True, exist_ok=True)
        html_path = base_out.with_suffix(".html") if base_out.suffix.lower() not in (".html", ".htm") else base_out
        md_path = html_path.with_suffix(".md")
        html_path.write_text(render_html(payload), encoding="utf-8")
        md_path.write_text(render_markdown(payload), encoding="utf-8")
        if args.pdf_output:
            pdf_path = pathlib.Path(args.pdf_output).expanduser()
            pdf_path.parent.mkdir(parents=True, exist_ok=True)
            html_to_pdf(render_html(payload), str(pdf_path))
        print_json({"ok": True, "html": str(html_path), "markdown": str(md_path), "pdf": str(pdf_path) if args.pdf_output else None, "dry_run": args.dry_run, "mode": mode})


if __name__ == "__main__":
    main()
