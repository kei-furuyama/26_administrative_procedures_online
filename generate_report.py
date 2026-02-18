#!/usr/bin/env python3
"""
Generate a complete Power BI report.json for the administrative procedures online dashboard.
Two pages:
  - Page 1: 都道府県一覧 (Prefecture overview with donut chart, KPI cards, and matrix)
  - Page 2: 市区町村詳細 (Municipality detail with slicers, donut, KPI cards, and cross-tab matrix)
"""

import json
import os

# ============================================================
# DESIGN CONSTANTS
# ============================================================
PRIMARY_BLUE = "#0017C1"
BG_VISUAL = "#F8F8FB"
PAGE_BG = "#FFFFFF"
TEXT_COLOR = "#1A1A1A"
TEXT_SECONDARY = "#666666"
TEXT_MUTED = "#999999"
BORDER_COLOR = "#F8F8FB"
BORDER_RADIUS = 20
GRID_LINE_COLOR = "#D8D8DB"
COMPLETED_COLOR = "#0017C1"
INCOMPLETE_GRAY = "#D8D8DB"
LIGHT_BLUE = "#C5D7FB"
HEADER_BG = "#F1F1F4"
FONT_FAMILY = "Arial"
DONUT_INNER_RADIUS = 82
PAGE_WIDTH = 1920
PAGE_HEIGHT = 1080
CARD_BORDER_COLOR = "#E8E8EB"


# ============================================================
# HELPER: literal expression builders
# ============================================================
def lit(val):
    """Wrap a value in a PBI Literal expression."""
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


def solid_color_raw(c):
    """Solid color without literal wrapping (for non-expression contexts)."""
    return {"solid": {"color": c}}


# ============================================================
# HELPER: standard vcObjects
# ============================================================
def std_vc_objects(show_bg=False, bg_color=BG_VISUAL, show_border=False,
                   border_color=BG_VISUAL, border_radius=BORDER_RADIUS):
    return {
        "title": [{"properties": {"show": lit_bool(False)}}],
        "background": [{"properties": {
            "show": lit_bool(show_bg),
            "color": solid_color(bg_color),
            "transparency": lit_double(0)
        }}],
        "border": [{"properties": {
            "show": lit_bool(show_border),
            "color": solid_color(border_color),
            "radius": lit_int(border_radius)
        }}],
        "padding": [{"properties": {
            "top": lit_double(0),
            "bottom": lit_double(0),
            "left": lit_double(0),
            "right": lit_double(0)
        }}]
    }


def hidden_vc_objects():
    """vcObjects that hide everything (for shapes, buttons)."""
    return {
        "title": [{"properties": {"show": lit_bool(False)}}],
        "background": [{"properties": {"show": lit_bool(False)}}],
        "border": [{"properties": {"show": lit_bool(False)}}],
        "visualHeader": [{"properties": {"show": lit_bool(False)}}]
    }


# ============================================================
# HELPER: make a visual container dict
# ============================================================
def make_visual_container(config_dict, filters_list, x, y, w, h, z):
    return {
        "config": json.dumps(config_dict, ensure_ascii=False),
        "filters": json.dumps(filters_list, ensure_ascii=False),
        "height": float(h),
        "width": float(w),
        "x": float(x),
        "y": float(y),
        "z": float(z)
    }


def position(x, y, z, w, h, tab=0):
    return {"x": x, "y": y, "z": z, "width": w, "height": h, "tabOrder": tab}


# ============================================================
# HELPER: textbox
# ============================================================
def make_textbox(name, x, y, w, h, z, paragraphs_json, vc_objects=None):
    if vc_objects is None:
        vc_objects = std_vc_objects()
    config = {
        "name": name,
        "layouts": [{"id": 0, "position": position(x, y, z, w, h)}],
        "singleVisual": {
            "visualType": "textbox",
            "objects": {
                "general": [{"properties": {
                    "paragraphs": lit(json.dumps(paragraphs_json, ensure_ascii=False))
                }}]
            },
            "vcObjects": vc_objects
        }
    }
    return make_visual_container(config, [], x, y, w, h, z)


# ============================================================
# HELPER: card visual
# ============================================================
def make_card(name, x, y, w, h, z, measure_name, font_size=28, vc_objects=None):
    if vc_objects is None:
        vc_objects = std_vc_objects()
    config = {
        "name": name,
        "layouts": [{"id": 0, "position": position(x, y, z, w, h)}],
        "singleVisual": {
            "visualType": "card",
            "projections": {
                "Values": [{"queryRef": f"o.{measure_name}"}]
            },
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": "o", "Entity": "オンライン化状況", "Type": 0}],
                "Select": [
                    {
                        "Measure": {
                            "Expression": {"SourceRef": {"Source": "o"}},
                            "Property": measure_name
                        },
                        "Name": f"o.{measure_name}"
                    }
                ]
            },
            "objects": {
                "labels": [{"properties": {
                    "fontSize": lit_double(font_size),
                    "color": solid_color(TEXT_COLOR),
                    "fontFamily": lit_str(FONT_FAMILY)
                }}],
                "categoryLabels": [{"properties": {
                    "show": lit_bool(False)
                }}]
            },
            "vcObjects": vc_objects
        }
    }
    return make_visual_container(config, [], x, y, w, h, z)


# ============================================================
# HELPER: shape visual (rounded rectangle)
# ============================================================
def make_shape(name, x, y, w, h, z, fill_color=PAGE_BG, line_color=CARD_BORDER_COLOR,
               weight=1, round_edge=BORDER_RADIUS):
    config = {
        "name": name,
        "layouts": [{"id": 0, "position": position(x, y, z, w, h)}],
        "singleVisual": {
            "visualType": "shape",
            "objects": {
                "line": [{"properties": {
                    "lineColor": solid_color(line_color),
                    "weight": lit_double(weight),
                    "roundEdge": lit_int(round_edge)
                }}],
                "fill": [{"properties": {
                    "fillColor": solid_color(fill_color),
                    "transparency": lit_double(0)
                }}]
            },
            "vcObjects": hidden_vc_objects()
        }
    }
    return make_visual_container(config, [], x, y, w, h, z)


# ============================================================
# HELPER: donut chart data-point selectors
# ============================================================
def donut_data_point_selector(entity, prop, value, color):
    return {
        "properties": {
            "fill": solid_color(color)
        },
        "selector": {
            "data": [{
                "scopeId": {
                    "Comparison": {
                        "ComparisonKind": 0,
                        "Left": {
                            "Column": {
                                "Expression": {"SourceRef": {"Entity": entity}},
                                "Property": prop
                            }
                        },
                        "Right": {"Literal": {"Value": f"'{value}'"}}
                    }
                }
            }]
        }
    }


# ============================================================
# HELPER: donut chart
# ============================================================
def make_donut(name, x, y, w, h, z, label_font_size=36, vc_objects=None):
    if vc_objects is None:
        vc_objects = std_vc_objects()
    config = {
        "name": name,
        "layouts": [{"id": 0, "position": position(x, y, z, w, h)}],
        "singleVisual": {
            "visualType": "donutChart",
            "projections": {
                "Category": [{"queryRef": "k.ステータス"}],
                "Y": [{"queryRef": "k.完了状況値"}]
            },
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": "k", "Entity": "完了状況", "Type": 0}],
                "Select": [
                    {
                        "Column": {
                            "Expression": {"SourceRef": {"Source": "k"}},
                            "Property": "ステータス"
                        },
                        "Name": "k.ステータス"
                    },
                    {
                        "Measure": {
                            "Expression": {"SourceRef": {"Source": "k"}},
                            "Property": "完了状況値"
                        },
                        "Name": "k.完了状況値"
                    }
                ],
                "OrderBy": [{
                    "Direction": 1,
                    "Expression": {
                        "Column": {
                            "Expression": {"SourceRef": {"Source": "k"}},
                            "Property": "順序"
                        }
                    }
                }]
            },
            "objects": {
                "legend": [{"properties": {"show": lit_bool(False)}}],
                "dataPoint": [
                    donut_data_point_selector("完了状況", "ステータス", "完了", COMPLETED_COLOR),
                    donut_data_point_selector("完了状況", "ステータス", "未完了", INCOMPLETE_GRAY)
                ],
                "labels": [{"properties": {
                    "show": lit_bool(True),
                    "labelStyle": lit_str("Percent of total"),
                    "fontSize": lit_double(label_font_size),
                    "color": solid_color(TEXT_COLOR),
                    "fontFamily": lit_str(FONT_FAMILY)
                }}],
                "slices": [{"properties": {
                    "innerRadiusRatio": lit_int(DONUT_INNER_RADIUS)
                }}]
            },
            "vcObjects": vc_objects
        }
    }
    return make_visual_container(config, [], x, y, w, h, z)


# ============================================================
# HELPER: slicer visual
# ============================================================
def make_slicer(name, x, y, w, h, z, column_name, title_text):
    slicer_vc = {
        "title": [{"properties": {
            "show": lit_bool(True),
            "text": lit_str(title_text),
            "fontColor": solid_color(TEXT_COLOR),
            "fontSize": lit_double(12),
            "fontFamily": lit_str(FONT_FAMILY)
        }}],
        "background": [{"properties": {"show": lit_bool(False)}}],
        "border": [{"properties": {
            "show": lit_bool(True),
            "color": solid_color(GRID_LINE_COLOR),
            "radius": lit_int(10)
        }}],
        "padding": [{"properties": {
            "top": lit_double(0),
            "bottom": lit_double(0),
            "left": lit_double(0),
            "right": lit_double(0)
        }}]
    }
    config = {
        "name": name,
        "layouts": [{"id": 0, "position": position(x, y, z, w, h)}],
        "singleVisual": {
            "visualType": "slicer",
            "projections": {
                "Values": [{"queryRef": f"o.{column_name}"}]
            },
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": "o", "Entity": "オンライン化状況", "Type": 0}],
                "Select": [
                    {
                        "Column": {
                            "Expression": {"SourceRef": {"Source": "o"}},
                            "Property": column_name
                        },
                        "Name": f"o.{column_name}"
                    }
                ]
            },
            "objects": {
                "general": [{"properties": {
                    "responsive": lit_bool(True)
                }}],
                "data": [{"properties": {
                    "mode": lit_str("Dropdown")
                }}],
                "selection": [{"properties": {
                    "singleSelect": lit_bool(False)
                }}],
                "header": [{"properties": {
                    "show": lit_bool(False)
                }}],
                "items": [{"properties": {
                    "textSize": lit_double(14),
                    "fontFamily": lit_str(FONT_FAMILY),
                    "padding": lit_int(6)
                }}]
            },
            "vcObjects": slicer_vc
        }
    }
    return make_visual_container(config, [], x, y, w, h, z)


# ============================================================
# MATRIX STYLING (shared between Page 1 and Page 2)
# ============================================================
def matrix_objects_base():
    return {
        "grid": [{"properties": {
            "gridVertical": lit_bool(True),
            "gridVerticalColor": solid_color(GRID_LINE_COLOR),
            "gridVerticalWeight": lit_int(1),
            "gridHorizontal": lit_bool(True),
            "gridHorizontalColor": solid_color(GRID_LINE_COLOR),
            "gridHorizontalWeight": lit_int(1),
            "outlineColor": solid_color(GRID_LINE_COLOR),
            "outlineWeight": lit_int(1),
            "textSize": lit_double(14),
            "rowPadding": lit_int(4)
        }}],
        "columnHeaders": [{"properties": {
            "fontColor": solid_color(TEXT_COLOR),
            "backColor": solid_color(HEADER_BG),
            "bold": lit_bool(True),
            "fontSize": lit_double(14),
            "fontFamily": lit_str(FONT_FAMILY),
            "outline": lit_str("Frame")
        }}],
        "rowHeaders": [{"properties": {
            "fontColor": solid_color(TEXT_COLOR),
            "backColor": solid_color(HEADER_BG),
            "bold": lit_bool(True),
            "fontSize": lit_double(14),
            "fontFamily": lit_str(FONT_FAMILY),
            "outline": lit_str("Frame")
        }}],
        "values": [{"properties": {
            "fontColorPrimary": solid_color(TEXT_COLOR),
            "backColorPrimary": solid_color(PAGE_BG),
            "fontColorSecondary": solid_color(TEXT_COLOR),
            "backColorSecondary": solid_color(BG_VISUAL),
            "fontSize": lit_double(16),
            "fontFamily": lit_str(FONT_FAMILY),
            "outline": lit_str("Frame"),
            "bandedRowHeaders": lit_bool(True)
        }}],
        "subTotals": [{"properties": {
            "rowSubtotals": lit_bool(False),
            "columnSubtotals": lit_bool(False)
        }}]
    }


def matrix_vc_objects():
    return {
        "title": [{"properties": {"show": lit_bool(False)}}],
        "background": [{"properties": {
            "show": lit_bool(True),
            "color": solid_color(PAGE_BG),
            "transparency": lit_double(0)
        }}],
        "border": [{"properties": {
            "show": lit_bool(True),
            "color": solid_color(CARD_BORDER_COLOR),
            "radius": lit_int(BORDER_RADIUS)
        }}],
        "padding": [{"properties": {
            "top": lit_double(0),
            "bottom": lit_double(0),
            "left": lit_double(0),
            "right": lit_double(0)
        }}]
    }


# ============================================================
# PAGE 1: 都道府県一覧
# ============================================================
def build_page1():
    page_config = {
        "objects": {
            "background": [{"properties": {
                "color": solid_color(PAGE_BG),
                "transparency": lit_double(0)
            }}]
        }
    }

    visuals = []

    # 1. Title textbox
    title_paragraphs = {"paragraphs": [{
        "textRuns": [{
            "value": "子育て・介護関係の26手続のオンライン化取組状況",
            "textStyle": {
                "fontSize": "22px",
                "color": TEXT_COLOR,
                "fontWeight": "bold",
                "fontFamily": FONT_FAMILY
            }
        }]
    }]}
    visuals.append(make_textbox("vc_p1_title", 40, 24, 900, 44, 0, title_paragraphs))

    # 2. Org label
    org_paragraphs = {"paragraphs": [{
        "textRuns": [{
            "value": "デジタル庁",
            "textStyle": {
                "fontSize": "14px",
                "color": TEXT_COLOR,
                "fontFamily": FONT_FAMILY
            }
        }],
        "horizontalTextAlignment": "right"
    }]}
    visuals.append(make_textbox("vc_p1_org", 1740, 24, 160, 36, 0, org_paragraphs))

    # 3. Left panel background (shape)
    visuals.append(make_shape("vc_p1_left_bg", 20, 80, 440, 780, 0))

    # 4. Subtitle
    subtitle_paragraphs = {"paragraphs": [
        {"textRuns": [{
            "value": "子育て・介護関係の全26手続を",
            "textStyle": {"fontSize": "16px", "color": TEXT_COLOR, "fontWeight": "bold", "fontFamily": FONT_FAMILY}
        }]},
        {"textRuns": [{
            "value": "オンライン手続できる自治体の割合",
            "textStyle": {"fontSize": "16px", "color": TEXT_COLOR, "fontWeight": "bold", "fontFamily": FONT_FAMILY}
        }]}
    ]}
    visuals.append(make_textbox("vc_p1_subtitle", 50, 100, 400, 56, 1, subtitle_paragraphs))

    # 5. Donut chart
    visuals.append(make_donut("vc_p1_donut", 100, 180, 280, 280, 1, label_font_size=36))

    # 6. KPI label
    kpi_label_paragraphs = {"paragraphs": [{
        "textRuns": [{
            "value": "オンライン化が完了した自治体数／全自治体数",
            "textStyle": {"fontSize": "12px", "color": TEXT_SECONDARY, "fontFamily": FONT_FAMILY}
        }]
    }]}
    visuals.append(make_textbox("vc_p1_kpi_label", 50, 480, 380, 24, 1, kpi_label_paragraphs))

    # 7. KPI completed card
    visuals.append(make_card("vc_p1_kpi_completed", 80, 510, 130, 55, 1, "子育て介護26手続完了自治体数", 28))

    # 8. Slash textbox
    slash_paragraphs = {"paragraphs": [{
        "textRuns": [{
            "value": "／",
            "textStyle": {"fontSize": "24px", "color": TEXT_COLOR, "fontFamily": FONT_FAMILY}
        }]
    }]}
    visuals.append(make_textbox("vc_p1_slash", 210, 516, 30, 42, 1, slash_paragraphs))

    # 9. KPI total card
    visuals.append(make_card("vc_p1_kpi_total", 240, 510, 130, 55, 1, "自治体数", 28))

    # 10. Legend textbox
    legend_paragraphs = {"paragraphs": [
        {"textRuns": [{"value": "凡例", "textStyle": {
            "fontSize": "13px", "color": TEXT_COLOR, "fontWeight": "bold", "fontFamily": FONT_FAMILY
        }}]},
        {"textRuns": [{"value": "", "textStyle": {"fontSize": "8px"}}]},
        {"textRuns": [
            {"value": "●", "textStyle": {"fontSize": "13px", "color": COMPLETED_COLOR, "fontFamily": FONT_FAMILY}},
            {"value": " 100%（全26手続オンライン化完了）", "textStyle": {
                "fontSize": "13px", "color": TEXT_SECONDARY, "fontFamily": FONT_FAMILY
            }}
        ]},
        {"textRuns": [
            {"value": "●", "textStyle": {"fontSize": "13px", "color": LIGHT_BLUE, "fontFamily": FONT_FAMILY}},
            {"value": " 80%以上100%未満", "textStyle": {
                "fontSize": "13px", "color": TEXT_SECONDARY, "fontFamily": FONT_FAMILY
            }}
        ]},
        {"textRuns": [
            {"value": "●", "textStyle": {"fontSize": "13px", "color": INCOMPLETE_GRAY, "fontFamily": FONT_FAMILY}},
            {"value": " 80%未満", "textStyle": {
                "fontSize": "13px", "color": TEXT_SECONDARY, "fontFamily": FONT_FAMILY
            }}
        ]}
    ]}
    visuals.append(make_textbox("vc_p1_legend", 50, 590, 380, 120, 1, legend_paragraphs))

    # 11. Matrix (pivotTable)
    matrix_config = {
        "name": "vc_p1_matrix",
        "layouts": [{"id": 0, "position": position(480, 80, 0, 1420, 880)}],
        "singleVisual": {
            "visualType": "pivotTable",
            "projections": {
                "Rows": [
                    {"queryRef": "o.地域ブロック"},
                    {"queryRef": "o.都道府県"}
                ],
                "Values": [
                    {"queryRef": "o.子育て介護26手続完了率"},
                    {"queryRef": "o.子育て介護26手続完了自治体数"},
                    {"queryRef": "o.自治体数"}
                ]
            },
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": "o", "Entity": "オンライン化状況", "Type": 0}],
                "Select": [
                    {
                        "Column": {
                            "Expression": {"SourceRef": {"Source": "o"}},
                            "Property": "地域ブロック"
                        },
                        "Name": "o.地域ブロック"
                    },
                    {
                        "Column": {
                            "Expression": {"SourceRef": {"Source": "o"}},
                            "Property": "都道府県"
                        },
                        "Name": "o.都道府県"
                    },
                    {
                        "Measure": {
                            "Expression": {"SourceRef": {"Source": "o"}},
                            "Property": "子育て介護26手続完了率"
                        },
                        "Name": "o.子育て介護26手続完了率"
                    },
                    {
                        "Measure": {
                            "Expression": {"SourceRef": {"Source": "o"}},
                            "Property": "子育て介護26手続完了自治体数"
                        },
                        "Name": "o.子育て介護26手続完了自治体数"
                    },
                    {
                        "Measure": {
                            "Expression": {"SourceRef": {"Source": "o"}},
                            "Property": "自治体数"
                        },
                        "Name": "o.自治体数"
                    }
                ]
            },
            "objects": matrix_objects_base(),
            "vcObjects": matrix_vc_objects()
        }
    }
    visuals.append(make_visual_container(matrix_config, [], 480, 80, 1420, 880, 0))

    # 12. Date label
    date_paragraphs = {"paragraphs": [{
        "textRuns": [{
            "value": "令和６年度末時点",
            "textStyle": {"fontSize": "11px", "color": TEXT_MUTED, "fontFamily": FONT_FAMILY}
        }],
        "horizontalTextAlignment": "right"
    }]}
    visuals.append(make_textbox("vc_p1_date", 1620, 980, 280, 24, 1, date_paragraphs))

    return {
        "config": json.dumps(page_config, ensure_ascii=False),
        "displayName": "都道府県一覧",
        "displayOption": 1,
        "filters": "[]",
        "height": float(PAGE_HEIGHT),
        "name": "ReportSection_page1",
        "ordinal": 0,
        "visualContainers": visuals,
        "width": float(PAGE_WIDTH)
    }


# ============================================================
# PAGE 2: 市区町村詳細
# ============================================================
def build_page2():
    page_config = {
        "objects": {
            "background": [{"properties": {
                "color": solid_color(PAGE_BG),
                "transparency": lit_double(0)
            }}]
        }
    }

    # Page-level filter
    page_filters = [
        {
            "name": "filter_subcat",
            "expression": {
                "Column": {
                    "Expression": {"SourceRef": {"Entity": "オンライン化状況"}},
                    "Property": "サブカテゴリ"
                }
            },
            "type": "Categorical",
            "filter": {
                "Version": 2,
                "From": [{"Name": "o", "Entity": "オンライン化状況", "Type": 0}],
                "Where": [{
                    "Condition": {
                        "In": {
                            "Expressions": [{
                                "Column": {
                                    "Expression": {"SourceRef": {"Source": "o"}},
                                    "Property": "サブカテゴリ"
                                }
                            }],
                            "Values": [
                                [{"Literal": {"Value": "'ア.子育て関係'"}}],
                                [{"Literal": {"Value": "'イ.介護関係'"}}]
                            ]
                        }
                    }
                }]
            },
            "isHiddenInViewMode": True
        }
    ]

    visuals = []

    # 1. Back button
    back_config = {
        "name": "vc_p2_back",
        "layouts": [{"id": 0, "position": position(20, 20, 0, 240, 30)}],
        "singleVisual": {
            "visualType": "actionButton",
            "objects": {
                "icon": [{"properties": {"show": lit_bool(False)}}],
                "outline": [{"properties": {"show": lit_bool(False)}}],
                "text": [{"properties": {
                    "show": lit_bool(True),
                    "text": lit_str("< 都道府県一覧に戻る"),
                    "fontColor": solid_color(PRIMARY_BLUE),
                    "fontSize": lit_double(14),
                    "fontFamily": lit_str(FONT_FAMILY),
                    "alignment": lit_str("Left")
                }}],
                "action": [{"properties": {
                    "type": lit_str("PageNavigation"),
                    "destination": lit_str("ReportSection_page1")
                }}]
            },
            "vcObjects": hidden_vc_objects()
        }
    }
    visuals.append(make_visual_container(back_config, [], 20, 20, 240, 30, 0))

    # 2. Org label
    org_paragraphs = {"paragraphs": [{
        "textRuns": [{
            "value": "デジタル庁",
            "textStyle": {"fontSize": "14px", "color": TEXT_COLOR, "fontFamily": FONT_FAMILY}
        }],
        "horizontalTextAlignment": "right"
    }]}
    visuals.append(make_textbox("vc_p2_org", 1740, 24, 160, 36, 0, org_paragraphs))

    # 3. Left panel background
    visuals.append(make_shape("vc_p2_left_bg", 20, 60, 320, 620, 0))

    # 4. Prefecture slicer
    visuals.append(make_slicer("vc_p2_slicer_pref", 35, 75, 290, 55, 1, "都道府県", "都道府県で絞り込む"))

    # 5. Municipality slicer
    visuals.append(make_slicer("vc_p2_slicer_muni", 35, 145, 290, 55, 1, "団体名", "団体名で絞り込む"))

    # 6. Subtitle
    subtitle_paragraphs = {"paragraphs": [
        {"textRuns": [{
            "value": "子育て・介護関係の全26手続を",
            "textStyle": {"fontSize": "14px", "color": TEXT_COLOR, "fontWeight": "bold", "fontFamily": FONT_FAMILY}
        }]},
        {"textRuns": [{
            "value": "オンライン手続できる自治体の割合",
            "textStyle": {"fontSize": "14px", "color": TEXT_COLOR, "fontWeight": "bold", "fontFamily": FONT_FAMILY}
        }]}
    ]}
    visuals.append(make_textbox("vc_p2_subtitle", 35, 215, 290, 50, 1, subtitle_paragraphs))

    # 7. Donut chart (smaller)
    visuals.append(make_donut("vc_p2_donut", 70, 280, 220, 220, 1, label_font_size=28))

    # 8. KPI label
    kpi_label_paragraphs = {"paragraphs": [{
        "textRuns": [{
            "value": "オンライン化が完了した自治体数／全自治体数",
            "textStyle": {"fontSize": "11px", "color": TEXT_SECONDARY, "fontFamily": FONT_FAMILY}
        }]
    }]}
    visuals.append(make_textbox("vc_p2_kpi_label", 35, 520, 290, 22, 1, kpi_label_paragraphs))

    # 9. KPI completed card
    visuals.append(make_card("vc_p2_kpi_completed", 60, 548, 110, 50, 1, "子育て介護26手続完了自治体数", 24))

    # 10. Slash
    slash_paragraphs = {"paragraphs": [{
        "textRuns": [{
            "value": "／",
            "textStyle": {"fontSize": "20px", "color": TEXT_COLOR, "fontFamily": FONT_FAMILY}
        }]
    }]}
    visuals.append(make_textbox("vc_p2_slash", 170, 554, 24, 38, 1, slash_paragraphs))

    # 11. KPI total card
    visuals.append(make_card("vc_p2_kpi_total", 194, 548, 110, 50, 1, "自治体数", 24))

    # 12. Matrix (pivotTable) - cross-tab
    matrix2_config = {
        "name": "vc_p2_matrix",
        "layouts": [{"id": 0, "position": position(360, 20, 0, 1540, 1000)}],
        "singleVisual": {
            "visualType": "pivotTable",
            "projections": {
                "Rows": [
                    {"queryRef": "o.サブカテゴリ"},
                    {"queryRef": "o.手続名"}
                ],
                "Columns": [
                    {"queryRef": "o.団体名"}
                ],
                "Values": [
                    {"queryRef": "o.ステータス表示"}
                ]
            },
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": "o", "Entity": "オンライン化状況", "Type": 0}],
                "Select": [
                    {
                        "Column": {
                            "Expression": {"SourceRef": {"Source": "o"}},
                            "Property": "サブカテゴリ"
                        },
                        "Name": "o.サブカテゴリ"
                    },
                    {
                        "Column": {
                            "Expression": {"SourceRef": {"Source": "o"}},
                            "Property": "手続名"
                        },
                        "Name": "o.手続名"
                    },
                    {
                        "Column": {
                            "Expression": {"SourceRef": {"Source": "o"}},
                            "Property": "団体名"
                        },
                        "Name": "o.団体名"
                    },
                    {
                        "Measure": {
                            "Expression": {"SourceRef": {"Source": "o"}},
                            "Property": "ステータス表示"
                        },
                        "Name": "o.ステータス表示"
                    }
                ]
            },
            "objects": matrix_objects_base(),
            "vcObjects": matrix_vc_objects()
        }
    }
    visuals.append(make_visual_container(matrix2_config, [], 360, 20, 1540, 1000, 0))

    # 13. Legend
    legend_paragraphs = {"paragraphs": [{
        "textRuns": [
            {"value": "●", "textStyle": {"fontSize": "12px", "color": COMPLETED_COLOR, "fontFamily": FONT_FAMILY}},
            {"value": " オンライン手続できる　", "textStyle": {"fontSize": "12px", "color": TEXT_SECONDARY, "fontFamily": FONT_FAMILY}},
            {"value": "●", "textStyle": {"fontSize": "12px", "color": INCOMPLETE_GRAY, "fontFamily": FONT_FAMILY}},
            {"value": " オンライン手続できない　", "textStyle": {"fontSize": "12px", "color": TEXT_SECONDARY, "fontFamily": FONT_FAMILY}},
            {"value": "ー 該当する手続がない", "textStyle": {"fontSize": "12px", "color": TEXT_SECONDARY, "fontFamily": FONT_FAMILY}}
        ]
    }]}
    visuals.append(make_textbox("vc_p2_legend", 360, 1030, 700, 25, 0, legend_paragraphs))

    # 14. Date label
    date_paragraphs = {"paragraphs": [{
        "textRuns": [{
            "value": "令和６年度末時点",
            "textStyle": {"fontSize": "11px", "color": TEXT_MUTED, "fontFamily": FONT_FAMILY}
        }],
        "horizontalTextAlignment": "right"
    }]}
    visuals.append(make_textbox("vc_p2_date", 1620, 1045, 280, 25, 0, date_paragraphs))

    return {
        "config": json.dumps(page_config, ensure_ascii=False),
        "displayName": "市区町村詳細",
        "displayOption": 1,
        "filters": json.dumps(page_filters, ensure_ascii=False),
        "height": float(PAGE_HEIGHT),
        "name": "ReportSection_page2",
        "ordinal": 1,
        "visualContainers": visuals,
        "width": float(PAGE_WIDTH)
    }


# ============================================================
# REPORT-LEVEL CONFIG
# ============================================================
def build_report():
    report_config = {
        "version": "5.44",
        "themeCollection": {
            "baseTheme": {"name": "CY23SU08", "version": "5.46", "type": 2},
            "customTheme": {
                "name": "Digital_Agency_Dashboard_Desig3362615343750506.json",
                "version": "5.46",
                "type": 1
            }
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
            "useDefaultAggregateDisplayName": True
        }
    }

    resource_packages = [
        {
            "resourcePackage": {
                "disabled": False,
                "items": [{"name": "CY23SU08", "path": "BaseThemes/CY23SU08.json", "type": 202}],
                "name": "SharedResources",
                "type": 2
            }
        },
        {
            "resourcePackage": {
                "disabled": False,
                "items": [{
                    "name": "Digital_Agency_Dashboard_Desig3362615343750506.json",
                    "path": "Digital_Agency_Dashboard_Desig3362615343750506.json",
                    "type": 201
                }],
                "name": "RegisteredResources",
                "type": 1
            }
        }
    ]

    report = {
        "config": json.dumps(report_config, ensure_ascii=False),
        "layoutOptimization": 0,
        "resourcePackages": resource_packages,
        "sections": [
            build_page1(),
            build_page2()
        ],
        "theme": "Digital_Agency_Dashboard_Desig3362615343750506.json"
    }

    return report


# ============================================================
# MAIN
# ============================================================
def main():
    output_path = "/Users/kei/Git/26_administrative_procedures_online/26_administrative_procedures_online.Report/report.json"

    report = build_report()

    # Validate JSON round-trip before writing
    json_str = json.dumps(report, ensure_ascii=False, indent=2)
    validated = json.loads(json_str)  # will raise if invalid

    # Also validate all embedded JSON strings
    def validate_embedded_json(obj, path="root"):
        if isinstance(obj, dict):
            for key, val in obj.items():
                if key in ("config", "filters") and isinstance(val, str):
                    try:
                        json.loads(val)
                    except json.JSONDecodeError as e:
                        raise ValueError(f"Invalid embedded JSON at {path}.{key}: {e}\nValue: {val[:200]}")
                else:
                    validate_embedded_json(val, f"{path}.{key}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                validate_embedded_json(item, f"{path}[{i}]")

    validate_embedded_json(validated)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(json_str)

    # Summary statistics
    p1_visuals = len(report["sections"][0]["visualContainers"])
    p2_visuals = len(report["sections"][1]["visualContainers"])
    total_size = len(json_str)

    print(f"Report generated successfully: {output_path}")
    print(f"  Pages: {len(report['sections'])}")
    print(f"  Page 1 '{report['sections'][0]['displayName']}': {p1_visuals} visual containers")
    print(f"  Page 2 '{report['sections'][1]['displayName']}': {p2_visuals} visual containers")
    print(f"  Total JSON size: {total_size:,} bytes")
    print("  All embedded JSON validated successfully.")


if __name__ == "__main__":
    main()
