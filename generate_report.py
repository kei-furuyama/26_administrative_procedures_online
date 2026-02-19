#!/usr/bin/env python3
"""
Generate report.json matching Digital Agency Dashboard Design Template.

Page 1: 都道府県一覧 - Header + summary panel(left) + 47 prefecture cards(right)
Page 2: 市区町村詳細 - Header + slicers + KPI cards + matrix
"""

import json
import os
import sys

# ============================================================
# Helper functions
# ============================================================

def lit(val):
    return {"expr": {"Literal": {"Value": val}}}

def lit_str(s):
    return lit(f"'{s}'")

def lit_bool(b):
    return lit("true" if b else "false")

def lit_int(n):
    return lit(f"{n}L")

def lit_double(n):
    return lit(f"{n}D")

def solid_color(c):
    return {"solid": {"color": lit_str(c)}}

def position(x, y, z, w, h, tab=0):
    return {"x": x, "y": y, "z": z, "width": w, "height": h, "tabOrder": tab}

def make_vc(config_dict, filters_list, x, y, w, h, z):
    return {
        "config": json.dumps(config_dict, ensure_ascii=False),
        "filters": json.dumps(filters_list, ensure_ascii=False),
        "height": float(h),
        "width": float(w),
        "x": float(x),
        "y": float(y),
        "z": float(z),
    }

# ============================================================
# Visual builders
# ============================================================

def textbox(name, x, y, w, h, z, paragraphs):
    config = {
        "name": name,
        "layouts": [{"id": 0, "position": position(x, y, z, w, h)}],
        "singleVisual": {
            "visualType": "textbox",
            "objects": {
                "general": [{"properties": {
                    "paragraphs": lit(json.dumps(paragraphs, ensure_ascii=False))
                }}]
            },
            "vcObjects": {
                "title": [{"properties": {"show": lit_bool(False)}}],
                "background": [{"properties": {"show": lit_bool(False)}}],
                "border": [{"properties": {"show": lit_bool(False)}}],
                "visualHeader": [{"properties": {"show": lit_bool(False)}}],
            },
        },
    }
    return make_vc(config, [], x, y, w, h, z)


def shape_bg(name, x, y, w, h, z, fill="#FFFFFF", border_color="#E8E8EB", radius=20):
    config = {
        "name": name,
        "layouts": [{"id": 0, "position": position(x, y, z, w, h)}],
        "singleVisual": {
            "visualType": "shape",
            "objects": {
                "line": [{"properties": {
                    "lineColor": solid_color(border_color),
                    "weight": lit_double(1),
                    "roundEdge": lit_int(radius),
                }}],
                "fill": [{"properties": {
                    "fillColor": solid_color(fill),
                    "transparency": lit_double(0),
                }}],
            },
            "vcObjects": {
                "title": [{"properties": {"show": lit_bool(False)}}],
                "background": [{"properties": {"show": lit_bool(False)}}],
                "border": [{"properties": {"show": lit_bool(False)}}],
                "visualHeader": [{"properties": {"show": lit_bool(False)}}],
            },
        },
    }
    return make_vc(config, [], x, y, w, h, z)


def card(name, x, y, w, h, z, measure, *, font_size=None, show_category=False):
    objects = {}
    if font_size is not None:
        objects["labels"] = [{"properties": {
            "fontSize": lit_double(font_size),
            "color": solid_color("#1A1A1A"),
        }}]
    objects["categoryLabels"] = [{"properties": {"show": lit_bool(show_category)}}]
    config = {
        "name": name,
        "layouts": [{"id": 0, "position": position(x, y, z, w, h)}],
        "singleVisual": {
            "visualType": "card",
            "projections": {"Values": [{"queryRef": f"o.{measure}"}]},
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": "o", "Entity": "オンライン化状況", "Type": 0}],
                "Select": [{
                    "Measure": {
                        "Expression": {"SourceRef": {"Source": "o"}},
                        "Property": measure,
                    },
                    "Name": f"o.{measure}",
                }],
            },
            "objects": objects,
            "vcObjects": {
                "title": [{"properties": {"show": lit_bool(False)}}],
            },
        },
    }
    return make_vc(config, [], x, y, w, h, z)


def pref_card(name, x, y, w, h, z, pref_name):
    """A card for one prefecture, with title and visual-level filter."""
    config = {
        "name": name,
        "layouts": [{"id": 0, "position": position(x, y, z, w, h)}],
        "singleVisual": {
            "visualType": "card",
            "projections": {"Values": [{"queryRef": "o.子育て介護26手続完了率"}]},
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": "o", "Entity": "オンライン化状況", "Type": 0}],
                "Select": [{
                    "Measure": {
                        "Expression": {"SourceRef": {"Source": "o"}},
                        "Property": "子育て介護26手続完了率",
                    },
                    "Name": "o.子育て介護26手続完了率",
                }],
            },
            "objects": {
                "labels": [{"properties": {
                    "fontSize": lit_double(28),
                    "color": solid_color("#0017C1"),
                    "fontFamily": lit_str("Arial"),
                }}],
                "categoryLabels": [{"properties": {"show": lit_bool(False)}}],
            },
            "vcObjects": {
                "title": [{"properties": {
                    "show": lit_bool(True),
                    "text": lit_str(pref_name),
                    "fontColor": solid_color("#1A1A1A"),
                    "fontSize": lit_double(13),
                    "fontFamily": lit_str("Arial"),
                    "bold": lit_bool(True),
                }}],
                "background": [{"properties": {
                    "show": lit_bool(True),
                    "color": solid_color("#FFFFFF"),
                    "transparency": lit_double(0),
                }}],
                "border": [{"properties": {
                    "show": lit_bool(True),
                    "color": solid_color("#E8E8EB"),
                    "radius": lit_int(10),
                }}],
                "padding": [{"properties": {
                    "top": lit_double(8),
                    "bottom": lit_double(8),
                    "left": lit_double(12),
                    "right": lit_double(12),
                }}],
            },
        },
    }
    visual_filter = [{
        "name": f"f_{name}",
        "expression": {
            "Column": {
                "Expression": {"SourceRef": {"Entity": "オンライン化状況"}},
                "Property": "都道府県",
            }
        },
        "type": "Categorical",
        "filter": {
            "Version": 2,
            "From": [{"Name": "o", "Entity": "オンライン化状況", "Type": 0}],
            "Where": [{"Condition": {"Comparison": {
                "ComparisonKind": 0,
                "Left": {"Column": {
                    "Expression": {"SourceRef": {"Source": "o"}},
                    "Property": "都道府県",
                }},
                "Right": {"Literal": {"Value": f"'{pref_name}'"}},
            }}}],
        },
        "isHiddenInViewMode": True,
    }]
    return make_vc(config, visual_filter, x, y, w, h, z)


def slicer(name, x, y, w, h, z, column, title_text):
    config = {
        "name": name,
        "layouts": [{"id": 0, "position": position(x, y, z, w, h)}],
        "singleVisual": {
            "visualType": "slicer",
            "projections": {"Values": [{"queryRef": f"o.{column}"}]},
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": "o", "Entity": "オンライン化状況", "Type": 0}],
                "Select": [{
                    "Column": {
                        "Expression": {"SourceRef": {"Source": "o"}},
                        "Property": column,
                    },
                    "Name": f"o.{column}",
                }],
            },
            "objects": {
                "general": [{"properties": {"responsive": lit_bool(True)}}],
                "data": [{"properties": {"mode": lit_str("Dropdown")}}],
                "selection": [{"properties": {"singleSelect": lit_bool(False)}}],
                "header": [{"properties": {"show": lit_bool(False)}}],
                "items": [{"properties": {
                    "textSize": lit_double(14),
                    "fontFamily": lit_str("Arial"),
                    "padding": lit_int(6),
                }}],
            },
            "vcObjects": {
                "title": [{"properties": {
                    "show": lit_bool(True),
                    "text": lit_str(title_text),
                    "fontColor": solid_color("#1A1A1A"),
                    "fontSize": lit_double(12),
                    "fontFamily": lit_str("Arial"),
                }}],
                "background": [{"properties": {"show": lit_bool(False)}}],
                "border": [{"properties": {
                    "show": lit_bool(True),
                    "color": solid_color("#D8D8DB"),
                    "radius": lit_int(10),
                }}],
            },
        },
    }
    return make_vc(config, [], x, y, w, h, z)


# ============================================================
# 47 prefectures
# ============================================================

PREFECTURES = [
    "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
    "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
    "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県",
    "岐阜県", "静岡県", "愛知県", "三重県",
    "滋賀県", "京都府", "大阪府", "兵庫県", "奈良県", "和歌山県",
    "鳥取県", "島根県", "岡山県", "広島県", "山口県",
    "徳島県", "香川県", "愛媛県", "高知県",
    "福岡県", "佐賀県", "長崎県", "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県",
]


# ============================================================
# PAGE 1
# ============================================================

def build_page1():
    v = []

    # --- Header ---
    v.append(textbox("p1_title", 40, 24, 900, 44, 1, {"paragraphs": [{
        "textRuns": [{"value": "子育て・介護関係の26手続のオンライン化取組状況",
                      "textStyle": {"fontSize": "22px", "color": "#1A1A1A",
                                    "fontWeight": "bold", "fontFamily": "Arial"}}]
    }]}))
    v.append(textbox("p1_org", 1740, 24, 160, 36, 1, {"paragraphs": [{
        "textRuns": [{"value": "デジタル庁",
                      "textStyle": {"fontSize": "14px", "color": "#1A1A1A",
                                    "fontFamily": "Arial"}}],
        "horizontalTextAlignment": "right",
    }]}))

    # --- Left summary panel ---
    panel_x, panel_y, panel_w, panel_h = 20, 80, 440, 780
    v.append(shape_bg("p1_panel_bg", panel_x, panel_y, panel_w, panel_h, 0))

    # Subtitle
    v.append(textbox("p1_subtitle", 50, 100, 400, 56, 1, {"paragraphs": [
        {"textRuns": [{"value": "子育て・介護関係の全26手続を",
                       "textStyle": {"fontSize": "16px", "color": "#1A1A1A",
                                     "fontWeight": "bold", "fontFamily": "Arial"}}]},
        {"textRuns": [{"value": "オンライン手続できる自治体の割合",
                       "textStyle": {"fontSize": "16px", "color": "#1A1A1A",
                                     "fontWeight": "bold", "fontFamily": "Arial"}}]},
    ]}))

    # Donut chart
    donut_config = {
        "name": "p1_donut",
        "layouts": [{"id": 0, "position": position(100, 180, 1, 280, 280)}],
        "singleVisual": {
            "visualType": "donutChart",
            "projections": {
                "Category": [{"queryRef": "k.ステータス"}],
                "Y": [{"queryRef": "k.完了状況値"}],
            },
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": "k", "Entity": "完了状況", "Type": 0}],
                "Select": [
                    {"Column": {"Expression": {"SourceRef": {"Source": "k"}}, "Property": "ステータス"}, "Name": "k.ステータス"},
                    {"Measure": {"Expression": {"SourceRef": {"Source": "k"}}, "Property": "完了状況値"}, "Name": "k.完了状況値"},
                ],
                "OrderBy": [{"Direction": 1, "Expression": {"Column": {"Expression": {"SourceRef": {"Source": "k"}}, "Property": "順序"}}}],
            },
            "objects": {
                "legend": [{"properties": {"show": lit_bool(False)}}],
                "dataPoint": [
                    {"properties": {"fill": solid_color("#0017C1")},
                     "selector": {"data": [{"scopeId": {"Comparison": {"ComparisonKind": 0, "Left": {"Column": {"Expression": {"SourceRef": {"Entity": "完了状況"}}, "Property": "ステータス"}}, "Right": {"Literal": {"Value": "'完了'"}}}}}]}},
                    {"properties": {"fill": solid_color("#D8D8DB")},
                     "selector": {"data": [{"scopeId": {"Comparison": {"ComparisonKind": 0, "Left": {"Column": {"Expression": {"SourceRef": {"Entity": "完了状況"}}, "Property": "ステータス"}}, "Right": {"Literal": {"Value": "'未完了'"}}}}}]}},
                ],
                "labels": [{"properties": {
                    "show": lit_bool(True),
                    "labelStyle": lit_str("Percent of total"),
                    "fontSize": lit_double(36),
                    "color": solid_color("#1A1A1A"),
                    "fontFamily": lit_str("Arial"),
                }}],
                "slices": [{"properties": {"innerRadiusRatio": lit_int(82)}}],
            },
            "vcObjects": {
                "title": [{"properties": {"show": lit_bool(False)}}],
                "background": [{"properties": {"show": lit_bool(False)}}],
                "border": [{"properties": {"show": lit_bool(False)}}],
            },
        },
    }
    v.append(make_vc(donut_config, [], 100, 180, 280, 280, 1))

    # KPI label
    v.append(textbox("p1_kpi_label", 50, 480, 380, 24, 1, {"paragraphs": [{
        "textRuns": [{"value": "オンライン化が完了した自治体数／全自治体数",
                      "textStyle": {"fontSize": "12px", "color": "#666666", "fontFamily": "Arial"}}]
    }]}))

    # KPI completed
    v.append(card("p1_kpi_done", 80, 510, 130, 55, 1, "子育て介護26手続完了自治体数", font_size=28))
    # Slash
    v.append(textbox("p1_slash", 210, 516, 30, 42, 1, {"paragraphs": [{
        "textRuns": [{"value": "／", "textStyle": {"fontSize": "24px", "color": "#1A1A1A", "fontFamily": "Arial"}}]
    }]}))
    # KPI total
    v.append(card("p1_kpi_total", 240, 510, 130, 55, 1, "自治体数", font_size=28))

    # Legend
    v.append(textbox("p1_legend", 50, 590, 380, 120, 1, {"paragraphs": [
        {"textRuns": [{"value": "凡例", "textStyle": {"fontSize": "13px", "color": "#1A1A1A", "fontWeight": "bold", "fontFamily": "Arial"}}]},
        {"textRuns": [{"value": "", "textStyle": {"fontSize": "8px"}}]},
        {"textRuns": [
            {"value": "●", "textStyle": {"fontSize": "13px", "color": "#0017C1", "fontFamily": "Arial"}},
            {"value": " 100%（全26手続オンライン化完了）", "textStyle": {"fontSize": "13px", "color": "#666666", "fontFamily": "Arial"}},
        ]},
        {"textRuns": [
            {"value": "●", "textStyle": {"fontSize": "13px", "color": "#C5D7FB", "fontFamily": "Arial"}},
            {"value": " 80%以上100%未満", "textStyle": {"fontSize": "13px", "color": "#666666", "fontFamily": "Arial"}},
        ]},
        {"textRuns": [
            {"value": "●", "textStyle": {"fontSize": "13px", "color": "#D8D8DB", "fontFamily": "Arial"}},
            {"value": " 80%未満", "textStyle": {"fontSize": "13px", "color": "#666666", "fontFamily": "Arial"}},
        ]},
    ]}))

    # Date
    v.append(textbox("p1_date", 50, 810, 380, 24, 1, {"paragraphs": [{
        "textRuns": [{"value": "令和６年度末時点",
                      "textStyle": {"fontSize": "11px", "color": "#999999", "fontFamily": "Arial"}}],
        "horizontalTextAlignment": "right",
    }]}))

    # --- 47 prefecture cards (right side) ---
    cols = 6
    card_w = 228
    card_h = 125
    gap = 6
    grid_x = 480
    grid_y = 80

    for i, pref in enumerate(PREFECTURES):
        col = i % cols
        row = i // cols
        cx = grid_x + col * (card_w + gap)
        cy = grid_y + row * (card_h + gap)
        v.append(pref_card(f"p1_pref_{i:02d}", cx, cy, card_w, card_h, 0, pref))

    return {
        "config": json.dumps({"objects": {"background": [{"properties": {
            "color": solid_color("#FFFFFF"),
            "transparency": lit_double(0),
        }}]}}, ensure_ascii=False),
        "displayName": "都道府県一覧",
        "displayOption": 1,
        "filters": json.dumps([], ensure_ascii=False),
        "height": 1080.0,
        "name": "ReportSection_page1",
        "ordinal": 0,
        "visualContainers": v,
        "width": 1920.0,
    }


# ============================================================
# PAGE 2
# ============================================================

def build_page2():
    page_filters = [{
        "name": "filter_subcat",
        "expression": {
            "Column": {
                "Expression": {"SourceRef": {"Entity": "オンライン化状況"}},
                "Property": "サブカテゴリ",
            }
        },
        "type": "Categorical",
        "filter": {
            "Version": 2,
            "From": [{"Name": "o", "Entity": "オンライン化状況", "Type": 0}],
            "Where": [{"Condition": {"In": {
                "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "o"}}, "Property": "サブカテゴリ"}}],
                "Values": [[{"Literal": {"Value": "'ア.子育て関係'"}}], [{"Literal": {"Value": "'イ.介護関係'"}}]],
            }}}],
        },
        "isHiddenInViewMode": True,
    }]

    v = []

    # Back button
    back_config = {
        "name": "p2_back",
        "layouts": [{"id": 0, "position": position(20, 20, 0, 240, 30)}],
        "singleVisual": {
            "visualType": "actionButton",
            "objects": {
                "icon": [{"properties": {"show": lit_bool(False)}}],
                "outline": [{"properties": {"show": lit_bool(False)}}],
                "text": [{"properties": {
                    "show": lit_bool(True),
                    "text": lit_str("< 都道府県一覧に戻る"),
                    "fontColor": solid_color("#0017C1"),
                    "fontSize": lit_double(14),
                    "fontFamily": lit_str("Arial"),
                    "alignment": lit_str("Left"),
                }}],
                "action": [{"properties": {
                    "type": lit_str("PageNavigation"),
                    "destination": lit_str("ReportSection_page1"),
                }}],
            },
            "vcObjects": {
                "title": [{"properties": {"show": lit_bool(False)}}],
                "background": [{"properties": {"show": lit_bool(False)}}],
                "border": [{"properties": {"show": lit_bool(False)}}],
                "visualHeader": [{"properties": {"show": lit_bool(False)}}],
            },
        },
    }
    v.append(make_vc(back_config, [], 20, 20, 240, 30, 0))

    # Org
    v.append(textbox("p2_org", 1740, 24, 160, 36, 0, {"paragraphs": [{
        "textRuns": [{"value": "デジタル庁", "textStyle": {"fontSize": "14px", "color": "#1A1A1A", "fontFamily": "Arial"}}],
        "horizontalTextAlignment": "right",
    }]}))

    # Left panel bg
    v.append(shape_bg("p2_panel_bg", 20, 60, 320, 620, 0))

    # Slicers
    v.append(slicer("p2_sl_pref", 35, 75, 290, 55, 1, "都道府県", "都道府県で絞り込む"))
    v.append(slicer("p2_sl_muni", 35, 145, 290, 55, 1, "団体名", "団体名で絞り込む"))

    # Subtitle
    v.append(textbox("p2_subtitle", 35, 215, 290, 50, 1, {"paragraphs": [
        {"textRuns": [{"value": "子育て・介護関係の全26手続を", "textStyle": {"fontSize": "14px", "color": "#1A1A1A", "fontWeight": "bold", "fontFamily": "Arial"}}]},
        {"textRuns": [{"value": "オンライン手続できる自治体の割合", "textStyle": {"fontSize": "14px", "color": "#1A1A1A", "fontWeight": "bold", "fontFamily": "Arial"}}]},
    ]}))

    # Donut
    donut2 = {
        "name": "p2_donut",
        "layouts": [{"id": 0, "position": position(70, 280, 1, 220, 220)}],
        "singleVisual": {
            "visualType": "donutChart",
            "projections": {"Category": [{"queryRef": "k.ステータス"}], "Y": [{"queryRef": "k.完了状況値"}]},
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": "k", "Entity": "完了状況", "Type": 0}],
                "Select": [
                    {"Column": {"Expression": {"SourceRef": {"Source": "k"}}, "Property": "ステータス"}, "Name": "k.ステータス"},
                    {"Measure": {"Expression": {"SourceRef": {"Source": "k"}}, "Property": "完了状況値"}, "Name": "k.完了状況値"},
                ],
                "OrderBy": [{"Direction": 1, "Expression": {"Column": {"Expression": {"SourceRef": {"Source": "k"}}, "Property": "順序"}}}],
            },
            "objects": {
                "legend": [{"properties": {"show": lit_bool(False)}}],
                "dataPoint": [
                    {"properties": {"fill": solid_color("#0017C1")}, "selector": {"data": [{"scopeId": {"Comparison": {"ComparisonKind": 0, "Left": {"Column": {"Expression": {"SourceRef": {"Entity": "完了状況"}}, "Property": "ステータス"}}, "Right": {"Literal": {"Value": "'完了'"}}}}}]}},
                    {"properties": {"fill": solid_color("#D8D8DB")}, "selector": {"data": [{"scopeId": {"Comparison": {"ComparisonKind": 0, "Left": {"Column": {"Expression": {"SourceRef": {"Entity": "完了状況"}}, "Property": "ステータス"}}, "Right": {"Literal": {"Value": "'未完了'"}}}}}]}},
                ],
                "labels": [{"properties": {"show": lit_bool(True), "labelStyle": lit_str("Percent of total"), "fontSize": lit_double(28), "color": solid_color("#1A1A1A"), "fontFamily": lit_str("Arial")}}],
                "slices": [{"properties": {"innerRadiusRatio": lit_int(82)}}],
            },
            "vcObjects": {"title": [{"properties": {"show": lit_bool(False)}}], "background": [{"properties": {"show": lit_bool(False)}}], "border": [{"properties": {"show": lit_bool(False)}}]},
        },
    }
    v.append(make_vc(donut2, [], 70, 280, 220, 220, 1))

    # KPI
    v.append(textbox("p2_kpi_label", 35, 520, 290, 22, 1, {"paragraphs": [{"textRuns": [{"value": "オンライン化が完了した自治体数／全自治体数", "textStyle": {"fontSize": "11px", "color": "#666666", "fontFamily": "Arial"}}]}]}))
    v.append(card("p2_kpi_done", 60, 548, 110, 50, 1, "子育て介護26手続完了自治体数", font_size=24))
    v.append(textbox("p2_slash", 170, 554, 24, 38, 1, {"paragraphs": [{"textRuns": [{"value": "／", "textStyle": {"fontSize": "20px", "color": "#1A1A1A", "fontFamily": "Arial"}}]}]}))
    v.append(card("p2_kpi_total", 194, 548, 110, 50, 1, "自治体数", font_size=24))

    # Legend
    v.append(textbox("p2_legend", 360, 1030, 700, 25, 0, {"paragraphs": [{"textRuns": [
        {"value": "●", "textStyle": {"fontSize": "12px", "color": "#0017C1", "fontFamily": "Arial"}},
        {"value": " オンライン手続できる　", "textStyle": {"fontSize": "12px", "color": "#666666", "fontFamily": "Arial"}},
        {"value": "●", "textStyle": {"fontSize": "12px", "color": "#D8D8DB", "fontFamily": "Arial"}},
        {"value": " オンライン手続できない　", "textStyle": {"fontSize": "12px", "color": "#666666", "fontFamily": "Arial"}},
        {"value": "ー 該当する手続がない", "textStyle": {"fontSize": "12px", "color": "#666666", "fontFamily": "Arial"}},
    ]}]}))

    # Date
    v.append(textbox("p2_date", 1620, 1045, 280, 25, 0, {"paragraphs": [{"textRuns": [{"value": "令和６年度末時点", "textStyle": {"fontSize": "11px", "color": "#999999", "fontFamily": "Arial"}}], "horizontalTextAlignment": "right"}]}))

    # Matrix
    matrix_config = {
        "name": "p2_matrix",
        "layouts": [{"id": 0, "position": position(360, 20, 0, 1540, 1000)}],
        "singleVisual": {
            "visualType": "pivotTable",
            "projections": {
                "Rows": [{"queryRef": "o.サブカテゴリ"}, {"queryRef": "o.手続名"}],
                "Columns": [{"queryRef": "o.団体名"}],
                "Values": [{"queryRef": "o.ステータス表示"}],
            },
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": "o", "Entity": "オンライン化状況", "Type": 0}],
                "Select": [
                    {"Column": {"Expression": {"SourceRef": {"Source": "o"}}, "Property": "サブカテゴリ"}, "Name": "o.サブカテゴリ"},
                    {"Column": {"Expression": {"SourceRef": {"Source": "o"}}, "Property": "手続名"}, "Name": "o.手続名"},
                    {"Column": {"Expression": {"SourceRef": {"Source": "o"}}, "Property": "団体名"}, "Name": "o.団体名"},
                    {"Measure": {"Expression": {"SourceRef": {"Source": "o"}}, "Property": "ステータス表示"}, "Name": "o.ステータス表示"},
                ],
            },
            "objects": {
                "subTotals": [{"properties": {"rowSubtotals": lit_bool(False), "columnSubtotals": lit_bool(False)}}],
            },
            "vcObjects": {
                "title": [{"properties": {"show": lit_bool(False)}}],
                "background": [{"properties": {"show": lit_bool(True), "color": solid_color("#FFFFFF"), "transparency": lit_double(0)}}],
                "border": [{"properties": {"show": lit_bool(True), "color": solid_color("#E8E8EB"), "radius": lit_int(20)}}],
            },
        },
    }
    v.append(make_vc(matrix_config, [], 360, 20, 1540, 1000, 0))

    return {
        "config": json.dumps({"objects": {"background": [{"properties": {
            "color": solid_color("#FFFFFF"),
            "transparency": lit_double(0),
        }}]}}, ensure_ascii=False),
        "displayName": "市区町村詳細",
        "displayOption": 1,
        "filters": json.dumps(page_filters, ensure_ascii=False),
        "height": 1080.0,
        "name": "ReportSection_page2",
        "ordinal": 1,
        "visualContainers": v,
        "width": 1920.0,
    }


# ============================================================
# Build report
# ============================================================

def build_report():
    report_config = {
        "version": "5.44",
        "themeCollection": {
            "baseTheme": {"name": "CY23SU08", "version": "5.46", "type": 2},
            "customTheme": {"name": "Digital_Agency_Dashboard_Desig3362615343750506.json", "version": "5.46", "type": 1},
        },
        "activeSectionIndex": 0,
        "defaultDrillFilterOtherVisuals": True,
        "linguisticSchemaSyncVersion": 2,
        "settings": {
            "useNewFilterPaneExperience": True,
            "allowChangeFilterTypes": True,
            "useStylableVisualContainerHeader": True,
            "queryLimitOption": 6,
            "useEnhancedTooltips": True,
            "exportDataMode": 1,
            "useDefaultAggregateDisplayName": True,
        },
    }
    return {
        "config": json.dumps(report_config, ensure_ascii=False),
        "layoutOptimization": 0,
        "resourcePackages": [
            {"resourcePackage": {"disabled": False, "items": [{"name": "CY23SU08", "path": "BaseThemes/CY23SU08.json", "type": 202}], "name": "SharedResources", "type": 2}},
            {"resourcePackage": {"disabled": False, "items": [{"name": "Digital_Agency_Dashboard_Desig3362615343750506.json", "path": "Digital_Agency_Dashboard_Desig3362615343750506.json", "type": 201}], "name": "RegisteredResources", "type": 1}},
        ],
        "sections": [build_page1(), build_page2()],
        "theme": "Digital_Agency_Dashboard_Desig3362615343750506.json",
    }


# ============================================================
# Validation & main
# ============================================================

def validate(report):
    errors = []

    def check_json(val, path):
        try:
            return json.loads(val)
        except json.JSONDecodeError as e:
            errors.append(f"{path}: {e}")
            return None

    check_json(report["config"], "report.config")

    names_all = set()
    for si, sec in enumerate(report["sections"]):
        sp = f"sections[{si}]"
        check_json(sec["config"], f"{sp}.config")
        check_json(sec["filters"], f"{sp}.filters")
        for vi, vc in enumerate(sec.get("visualContainers", [])):
            vp = f"{sp}.vc[{vi}]"
            cfg = check_json(vc["config"], f"{vp}.config")
            check_json(vc["filters"], f"{vp}.filters")
            if cfg:
                n = cfg.get("name", "")
                if n in names_all:
                    errors.append(f"{vp}: duplicate name '{n}'")
                names_all.add(n)
                pq = cfg.get("singleVisual", {}).get("prototypeQuery")
                if pq:
                    if pq.get("Version") != 2:
                        errors.append(f"{vp}: Version != 2")
    return errors


def main():
    out = "/Users/kei/Git/26_administrative_procedures_online/26_administrative_procedures_online.Report/report.json"
    report = build_report()
    errs = validate(report)
    if errs:
        for e in errs:
            print(f"  ERROR: {e}")
        sys.exit(1)

    s = json.dumps(report, ensure_ascii=False, indent=2)
    json.loads(s)  # round-trip check

    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(s)

    p1 = len(report["sections"][0]["visualContainers"])
    p2 = len(report["sections"][1]["visualContainers"])
    print(f"OK: {out}")
    print(f"  Page 1: {p1} visuals, Page 2: {p2} visuals, {len(s):,} bytes")


if __name__ == "__main__":
    main()
