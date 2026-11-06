#!/usr/bin/env python3
"""Offline content review for an existing store report.

Pure ``apply_content_review(report)`` labels search conditions separately,
formats rank/per-capita fields, hides all-empty columns, and discloses that the
city/province tables are top-N samples rather than full coverage. No MCP calls.
"""
from __future__ import annotations

import argparse
import copy
import json
import pathlib
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Mapping

_EMPTY = {"", "-", "—", "None", "null"}


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _is_empty(value: Any) -> bool:
    return _text(value) in _EMPTY


def _number_text(raw: Any, unit: str = "") -> str:
    text = _text(raw)
    if _is_empty(text):
        return "-"
    try:
        number = Decimal(text.replace(",", ""))
    except InvalidOperation:
        return text
    if number == number.to_integral():
        body = f"{int(number):,}"
    else:
        body = f"{number:,.2f}".rstrip("0").rstrip(".")
    return f"{body}{unit}"


def _int_value(value: Any) -> int:
    try:
        return int(float(str(value).replace(",", "")))
    except (TypeError, ValueError):
        return 0


def _sum_values(rows: List[Mapping[str, Any]], key: str) -> int:
    total = 0
    for row in rows:
        try:
            total += int(float(str(row.get(key, 0)).replace(",", "")))
        except (TypeError, ValueError):
            continue
    return total


def _fix_caliber(report: Dict[str, Any]) -> None:
    subject = report.get("subject") if isinstance(report.get("subject"), dict) else {}
    caliber = report.get("caliber")
    if not isinstance(caliber, dict):
        return
    if subject.get("mode") == "search":
        parts = []
        if subject.get("store_name"):
            parts.append(f"店铺名称：{subject['store_name']}")
        if subject.get("brand"):
            parts.append(f"经营品牌：{subject['brand']}")
        if subject.get("category"):
            parts.append("店铺分类：" + str(subject["category"]).replace(",", " / "))
        if subject.get("address"):
            parts.append("地区：" + str(subject["address"]).replace(",", " / "))
        if subject.get("address_value"):
            parts.append(f"地址：{subject['address_value']}")
        caliber["match_target"] = "；".join(parts) or "线下门店检索条件"
        caliber["match_type"] = "按门店检索条件匹配（店铺名称 / 经营品牌 / 店铺分类 / 地区 / 地址）；检索条件之间是并列筛选，不构成企业主体"
        caliber["limit"] = "数据来自店铺公开数据库；少量字段可能存在更新延迟。检索条件为并列筛选，不构成企业主体；多品牌检索值是查询条件，不代表每条记录同时命中全部品牌"
    else:
        caliber["match_type"] = "店铺大数据按企业主体匹配；支持企业名称、注册号、统一社会信用代码和企业 ID"


def _fix_offline(core: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = core.get("offline_records")
    if not isinstance(rows, list):
        return []
    out: List[Dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        reviewed = dict(row)
        reviewed["人均价格"] = _number_text(reviewed.get("人均价格"), " 元")
        reviewed["店铺排名"] = _number_text(reviewed.get("店铺排名"))
        out.append(reviewed)
    core["offline_records"] = out

    empty_columns = [c for c in ("实际品牌", "实际地区", "实际地址")
                     if all(_is_empty(r.get(c)) for r in out)]
    constant_columns = [c for c in ("品牌匹配验证", "地址匹配验证")
                        if out and len({_text(r.get(c)) for r in out}) == 1]
    sections = core.get("sections")
    if isinstance(sections, list):
        for section in sections:
            if not (isinstance(section, dict) and section.get("key") == "offline_records"):
                continue
            columns = [col for col in (section.get("columns") or [])
                       if col[0] not in empty_columns and col[0] not in constant_columns]
            section["columns"] = columns
            note = _text(section.get("note"))
            extras = []
            if empty_columns:
                extras.append("、".join(empty_columns) + " 全部为空，已隐藏空列")
            if constant_columns:
                extras.append("、".join(constant_columns) + " 对全部记录取值相同，已隐藏")
            extras.append("人均价格为上游字段，非餐饮场景的语义可能不适用")
            for extra in extras:
                if extra not in note:
                    note = note.rstrip("。") + "；" + extra
            section["note"] = note
    return out


def _fix_brand_stats(core: Dict[str, Any]) -> None:
    brands = [r for r in (core.get("brand_records") or []) if isinstance(r, dict)]
    if not brands:
        return
    main = max(brands, key=lambda r: _int_value(r.get("门店数")))
    main_n = _int_value(main.get("门店数"))
    for key, label in (("branch_city_stats", "城市"), ("branch_province_stats", "省份")):
        rows = [r for r in (core.get(key) or []) if isinstance(r, dict)]
        if not rows:
            continue
        covered = _sum_values(rows, "门店数量")
        pct = covered / main_n * 100 if main_n else None
        core[f"{key}_coverage"] = {"返回行数": len(rows), "合计门店": covered, "主力品牌门店": main_n,
                                   "覆盖率": f"{pct:.1f}%" if pct is not None else "-"}
        sections = core.get("sections")
        if isinstance(sections, list):
            for section in sections:
                if isinstance(section, dict) and section.get("key") == key:
                    base = f"上游返回{label}统计 {len(rows)} 行"
                    if pct is not None:
                        base += f"，合计 {covered} 家，占主力品牌“{main.get('品牌名称')}”{main_n} 家的 {pct:.1f}%"
                    section["note"] = base + "；为 Top 统计样本，不代表全部覆盖地区"


def _fix_metrics(report: Dict[str, Any], core: Dict[str, Any]) -> None:
    metrics = [m for m in (report.get("metrics") or []) if isinstance(m, dict)]
    brands = [r for r in (core.get("brand_records") or []) if isinstance(r, dict)]
    categories = sorted({_text(r.get("一级类别")) for r in brands if _text(r.get("一级类别")) not in ("", "-")})
    city_cov = core.get("branch_city_stats_coverage") or {}
    prov_cov = core.get("branch_province_stats_coverage") or {}
    for metric in metrics:
        label = _text(metric.get("label"))
        if label == "覆盖城市数":
            metric["label"] = "已返回城市数"
            metric["hint"] = f"上游返回城市统计行数（{city_cov.get('返回行数', '-')} 行，合计 {city_cov.get('合计门店', '-')} 家门店）"
        elif label == "覆盖省份数":
            metric["label"] = "已返回省份数"
            metric["hint"] = f"上游返回省份统计行数（{prov_cov.get('返回行数', '-')} 行，合计 {prov_cov.get('合计门店', '-')} 家门店）"
        elif label == "城市CR3":
            metric["label"] = "已返回城市CR3"
            metric["hint"] = f"仅在已返回城市统计内计算；覆盖 {city_cov.get('合计门店', '-')}/{city_cov.get('主力品牌门店', '-')} 家"
        elif label == "门店总数(汇总)":
            metric["hint"] = "各品牌门店数字段汇总；来源为品牌级字段，不做去重"
        elif label == "餐饮类别数":
            metric["value"] = str(len(categories))
            metric["hint"] = "当前品牌记录中出现的一级类别数（不含空值）"
        elif label == "线下门店检索结果":
            metric["hint"] = "本次检索命中总数；明细表仅为当前样本"
    report["metrics"] = metrics


def _status_counts(rows: List[Mapping[str, Any]]) -> str:
    counts: Dict[str, int] = {}
    for row in rows:
        state = _text(row.get("店铺状态")) or "待核实"
        counts[state] = counts.get(state, 0) + 1
    return "、".join(f"{k} {v} 家" for k, v in sorted(counts.items(), key=lambda kv: -kv[1]))


def _build_insights(report: Dict[str, Any], core: Dict[str, Any], offline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    subject = report.get("subject") if isinstance(report.get("subject"), dict) else {}
    metrics = {m.get("label"): _text(m.get("value")) for m in (report.get("metrics") or []) if isinstance(m, dict)}
    insights: List[Dict[str, Any]] = []
    if subject.get("mode") == "enterprise":
        if metrics.get("门店总数(汇总)"):
            insights.append({
                "feature": "门店资产规模",
                "evidence": f"各品牌门店数字段汇总 {metrics['门店总数(汇总)']} 家（来源为品牌级字段，未去重）。",
                "interpretation": "该汇总只反映品牌级门店数字段之和；若品牌间存在重叠门店，不能视为去重后的实体门店总数。",
            })
        if metrics.get("旗下品牌数"):
            insights.append({
                "feature": "品牌矩阵",
                "evidence": f"上游返回 {metrics['旗下品牌数']} 个餐饮品牌。",
                "interpretation": "仅表示该产品返回的品牌记录数；不推断品牌定位差异、市场份额或经营策略。",
            })
        city_cov = core.get("branch_city_stats_coverage") or {}
        if city_cov:
            insights.append({
                "feature": "地域覆盖（Top 样本）",
                "evidence": f"上游返回城市统计 {city_cov.get('返回行数')} 行，合计 {city_cov.get('合计门店')} 家门店，占主力品牌门店的 {city_cov.get('覆盖率')}。",
                "interpretation": "这是上游返回的 Top 城市统计样本，不是全部覆盖城市；不能据此计算全国城市覆盖数。",
            })
        city_rows = [r for r in (core.get("branch_city_stats") or []) if isinstance(r, dict)]
        if city_rows:
            values = []
            for row in city_rows:
                try:
                    values.append((_text(row.get("城市")), float(str(row.get("门店数量", 0)).replace(",", ""))))
                except (TypeError, ValueError):
                    values.append((_text(row.get("城市")), 0.0))
            total = sum(v for _, v in values)
            values.sort(key=lambda kv: -kv[1])
            if total:
                top = values[0]
                cr3 = sum(v for _, v in values[:3]) / total * 100
                insights.append({
                    "feature": "城市集中度（已返回样本内）",
                    "evidence": f"已返回城市中“{top[0]}”最多（{top[1]:g} 家，占 {top[1] / total * 100:.1f}%），CR3 为 {cr3:.1f}%。",
                    "interpretation": f"该比例只在合计 {total:g} 家的已返回城市统计内计算，不代表全部门店；省份口径单独统计，不混合。",
                })
    if offline:
        total = metrics.get("线下门店检索结果") or str(len(offline))
        insights.append({
            "feature": "线下门店检索（当前样本）",
            "evidence": f"检索命中 {total} 家，当前返回 {len(offline)} 家，状态：" + _status_counts(offline) + "。",
            "interpretation": "状态仅描述当前样本；不能据此推算全部命中门店的在营/停业比例，也不证明经营质量。",
        })
    records = report.get("representative_records")
    if isinstance(records, list) and records:
        empty_keys = [k for k in ("实际品牌", "实际地址", "实际地区")
                      if all(not isinstance(r, dict) or _is_empty(r.get(k)) for r in records)]
        for record in records:
            if isinstance(record, dict):
                for key in empty_keys:
                    record.pop(key, None)
    if not insights:
        insights.append({
            "feature": "数据完整性",
            "evidence": "部分维度未返回有效数据。",
            "interpretation": "建议核对检索条件或企业主体，或检查上游数据覆盖；不得将缺失解释为零门店。",
        })
    return insights


def _core_has_body(core: Mapping[str, Any]) -> bool:
    return any(core.get(k) for k in ("brand_records", "branch_city_stats", "branch_province_stats", "offline_records"))


def _build_abstract(report: Dict[str, Any]) -> str:
    subject = report.get("subject") if isinstance(report.get("subject"), dict) else {}
    core = report.get("core_analysis") if isinstance(report.get("core_analysis"), dict) else {}
    data_source = report.get("data_source") if isinstance(report.get("data_source"), dict) else {}
    errors = [str(x) for x in (data_source.get("tool_errors") or []) if _text(x)]
    has_body = _core_has_body(core)
    if not has_body:
        if errors:
            return "本次查询未获得有效核心数据，且存在上游调用失败维度：" + "、".join(errors) + "。不据此生成业务规模或市场结论。"
        # A successful empty result has no tool error. Keep the explicit
        # no-data disclosure instead of replacing it with a data-bearing
        # narrative; 0-valued metrics stay in the report as source values.
        existing = _text(report.get("abstract"))
        if existing and any(marker in existing for marker in ("未返回有效核心数据", "无有效核心数据", "查询数据为空")):
            return existing
        return "本次查询未返回有效核心数据；报告仅记录查询边界，不生成业务规模或市场结论。"
    failure = ("本次查询存在上游调用失败维度：" + "、".join(errors) + "；相关字段缺失，不据此生成业务规模或市场结论。"
               if errors else "")
    metrics = [m for m in (report.get("metrics") or []) if isinstance(m, dict)]
    if subject.get("mode") == "search":
        parts = []
        if subject.get("store_name"):
            parts.append(f"店铺名称：{subject['store_name']}")
        if subject.get("brand"):
            parts.append(f"经营品牌：{subject['brand']}")
        if subject.get("category"):
            parts.append("店铺分类：" + str(subject["category"]).replace(",", " / "))
        if subject.get("address"):
            parts.append("地区：" + str(subject["address"]).replace(",", " / "))
        cond = "；".join(parts) or "门店检索条件"
        text = f"本报告以检索条件（{cond}）为对象，基于店铺公开数据，呈现线下门店检索命中总量与当前样本明细。"
    else:
        name = _text(subject.get("enterprise")) or _text(subject.get("match_raw")) or "目标企业"
        text = f"本报告以“{name}”为分析对象，基于店铺公开数据，呈现企业旗下餐饮品牌、品牌级门店数与已返回的地区统计样本。"
    text = failure + text
    if metrics:
        text += "关键指标包括：" + "、".join(f"{m.get('label')} {m.get('value')}" for m in metrics[:5]) + "。"
    text += "报告仅对返回字段作结构化展示；品牌级汇总、地区 Top 样本和检索命中量口径不同，不可互相补齐。"
    return text


def _has_review_body(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (str, list, dict, tuple)) and len(value) == 0:
        return False
    return True


def _refresh_quality_report(report: Dict[str, Any]) -> None:
    """Recompute section-fill stats from the final sections and bodies.

    0 counts as populated; only None and empty containers/strings are empty.
    coverage_pct is section fill rate, never an accuracy claim.
    """
    core = report.get("core_analysis") if isinstance(report.get("core_analysis"), dict) else {}
    sections = core.get("sections") if isinstance(core.get("sections"), list) else []
    total = len([s for s in sections if isinstance(s, dict)])
    populated = 0
    for section in sections:
        if not isinstance(section, dict):
            continue
        key = section.get("key")
        if key and _has_review_body(core.get(key)):
            populated += 1
    data_source = report.get("data_source")
    if not isinstance(data_source, dict):
        data_source = {}
        report["data_source"] = data_source
    quality = data_source.get("quality_report")
    if not isinstance(quality, dict):
        quality = {}
        data_source["quality_report"] = quality
    quality.update({
        "total_sections": total,
        "populated_sections": populated,
        "empty_sections": total - populated,
        "coverage_pct": round(populated / total * 100) if total else 0,
    })


def apply_content_review(report: Mapping[str, Any]) -> Dict[str, Any]:
    """Return a reviewed deep copy of a frozen store report."""
    reviewed = copy.deepcopy(dict(report))
    if ((reviewed.get("subject") or {}).get("blocked_reason")
            or (reviewed.get("data_source") or {}).get("blocked_reason")):
        _refresh_quality_report(reviewed)
        return reviewed
    core = reviewed.get("core_analysis") if isinstance(reviewed.get("core_analysis"), dict) else {}
    _fix_caliber(reviewed)
    offline = _fix_offline(core)
    _fix_brand_stats(core)
    _fix_metrics(reviewed, core)
    insights = _build_insights(reviewed, core, offline)
    reviewed["insights"] = insights
    prefix = [x for x in (report.get("executive_summary") or []) if _text(x).startswith(("主体解析受阻", "数据缺口"))]
    seen, summaries = set(), []
    for insight in insights:
        key = _text(insight.get("interpretation"))
        if key and key not in seen:
            seen.add(key)
            summaries.append(key)
    reviewed["executive_summary"] = prefix + summaries[:5]
    reviewed["abstract"] = _build_abstract(reviewed)
    reviewed["summary"] = reviewed["abstract"]
    subject = reviewed.get("subject") if isinstance(reviewed.get("subject"), dict) else {}
    if subject.get("mode") == "search":
        cond = []
        for key in ("store_name", "brand"):
            if subject.get(key):
                cond.append(str(subject[key]))
        if subject.get("category"):
            cond.append(str(subject["category"]).replace(",", " / "))
        if subject.get("address"):
            cond.append(str(subject["address"]).replace(",", " / "))
        reviewed["title"] = "“" + "；".join(cond or [subject.get("match_raw") or "门店检索"]) + "” 门店检索报告"
    _refresh_quality_report(reviewed)
    return reviewed


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply offline content review to a store report.json")
    parser.add_argument("--input", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    input_path = pathlib.Path(args.input).expanduser().resolve()
    output_path = pathlib.Path(args.out_dir).expanduser()
    target = (output_path / "report.json").resolve()
    same = target == input_path
    if not same and target.exists():
        try:
            same = target.samefile(input_path)
        except OSError:
            same = False
    if same:
        raise SystemExit("拒绝写入：--out-dir 的 report.json 指向 --input，冻结源报告不可覆盖")
    import sys
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    from render_report import render_html, render_markdown

    source = json.loads(pathlib.Path(args.input).read_text(encoding="utf-8"))
    reviewed = apply_content_review(source)
    out = pathlib.Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.json").write_text(json.dumps(reviewed, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "report.md").write_text(render_markdown(reviewed), encoding="utf-8")
    (out / "report.html").write_text(render_html(reviewed), encoding="utf-8")
    print(json.dumps({"ok": True, "out": str(out)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
