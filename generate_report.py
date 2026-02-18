#!/usr/bin/env python3
"""
Generate a clean, minimal report.json for the 26 administrative procedures
online status Power BI report (PBIP format).

Two pages:
  - Page 1: 都道府県一覧 (Prefecture overview with cards, donut chart, and matrix)
  - Page 2: 市区町村詳細 (Municipality detail with slicers, cards, and cross-tab matrix)

This script builds the JSON programmatically using json.dumps() to ensure
all embedded JSON strings are properly escaped.
"""

import json
import os
import sys


# ============================================================
# Helper: Power BI literal expression builders
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


# ============================================================
# Helper: layout position
# ============================================================

def position(x, y, z, w, h, tab=0):
    return {"x": x, "y": y, "z": z, "width": w, "height": h, "tabOrder": tab}


# ============================================================
# Helper: make a visual container dict
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


# ============================================================
# Helper: minimal vcObjects
# ============================================================

def minimal_vc_objects():
    """Hide title only, let the default theme handle everything else."""
    return {
        "title": [{"properties": {"show": lit_bool(False)}}]
    }


def hidden_vc_objects():
    """Hide title, background, border, and visual header."""
    return {
        "title": [{"properties": {"show": lit_bool(False)}}],
        "background": [{"properties": {"show": lit_bool(False)}}],
        "border": [{"properties": {"show": lit_bool(False)}}],
        "visualHeader": [{"properties": {"show": lit_bool(False)}}]
    }


# ============================================================
# Helper: textbox visual
# ============================================================

def make_textbox(name, x, y, w, h, z, paragraphs_obj, vc_objects=None):
    """Build a textbox visual container.

    paragraphs_obj: a dict like {"paragraphs": [...]} which will be
    json.dumps'd into the embedded literal string.
    """
    if vc_objects is None:
        vc_objects = hidden_vc_objects()
    config = {
        "name": name,
        "layouts": [{"id": 0, "position": position(x, y, z, w, h)}],
        "singleVisual": {
            "visualType": "textbox",
            "objects": {
                "general": [{"properties": {
                    "paragraphs": lit(json.dumps(paragraphs_obj, ensure_ascii=False))
                }}]
            },
            "vcObjects": vc_objects
        }
    }
    return make_visual_container(config, [], x, y, w, h, z)


# ============================================================
# Helper: card visual
# ============================================================

def make_card(name, x, y, w, h, z, measure_name):
    """Build a card visual showing a single measure from オンライン化状況."""
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
                "Select": [{
                    "Measure": {
                        "Expression": {"SourceRef": {"Source": "o"}},
                        "Property": measure_name
                    },
                    "Name": f"o.{measure_name}"
                }]
            },
            "objects": {
                "categoryLabels": [{"properties": {"show": lit_bool(False)}}]
            },
            "vcObjects": minimal_vc_objects()
        }
    }
    return make_visual_container(config, [], x, y, w, h, z)


# ============================================================
# Helper: slicer visual (dropdown)
# ============================================================

def make_slicer(name, x, y, w, h, z, column_name, title_text):
    """Build a dropdown slicer for a column from オンライン化状況."""
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
                "Select": [{
                    "Column": {
                        "Expression": {"SourceRef": {"Source": "o"}},
                        "Property": column_name
                    },
                    "Name": f"o.{column_name}"
                }]
            },
            "objects": {
                "general": [{"properties": {"responsive": lit_bool(True)}}],
                "data": [{"properties": {"mode": lit_str("Dropdown")}}],
                "selection": [{"properties": {"singleSelect": lit_bool(False)}}],
                "header": [{"properties": {"show": lit_bool(False)}}]
            },
            "vcObjects": {
                "title": [{"properties": {
                    "show": lit_bool(True),
                    "text": lit_str(title_text)
                }}]
            }
        }
    }
    return make_visual_container(config, [], x, y, w, h, z)


# ============================================================
# PAGE 1: 都道府県一覧
# ============================================================

def build_page1():
    visuals = []

    # 1. Title textbox
    title_paragraphs = {"paragraphs": [{
        "textRuns": [{
            "value": "子育て・介護関係の26手続のオンライン化取組状況",
            "textStyle": {"fontWeight": "bold"}
        }]
    }]}
    visuals.append(make_textbox("vc_p1_title", 40, 20, 900, 50, 0, title_paragraphs))

    # 2. Card: 子育て介護26手続完了率
    visuals.append(make_card("vc_p1_card_rate", 40, 90, 250, 80, 0, "子育て介護26手続完了率"))

    # 3. Card: 子育て介護26手続完了自治体数
    visuals.append(make_card("vc_p1_card_completed", 300, 90, 250, 80, 0, "子育て介護26手続完了自治体数"))

    # 4. Card: 自治体数
    visuals.append(make_card("vc_p1_card_total", 560, 90, 250, 80, 0, "自治体数"))

    # 5. Donut chart
    donut_config = {
        "name": "vc_p1_donut",
        "layouts": [{"id": 0, "position": position(40, 190, 0, 400, 400)}],
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
                "legend": [{"properties": {"show": lit_bool(True)}}]
            },
            "vcObjects": minimal_vc_objects()
        }
    }
    visuals.append(make_visual_container(donut_config, [], 40, 190, 400, 400, 0))

    # 6. MultiRowCard: 47都道府県カード一覧
    multirowcard_config = {
        "name": "vc_p1_pref_cards",
        "layouts": [{"id": 0, "position": position(40, 190, 0, 1860, 870)}],
        "singleVisual": {
            "visualType": "multiRowCard",
            "projections": {
                "Values": [
                    {"queryRef": "o.都道府県"},
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
            "objects": {},
            "vcObjects": minimal_vc_objects()
        }
    }
    visuals.append(make_visual_container(multirowcard_config, [], 40, 190, 1860, 870, 0))

    return {
        "config": json.dumps({}, ensure_ascii=False),
        "displayName": "都道府県一覧",
        "displayOption": 1,
        "filters": json.dumps([], ensure_ascii=False),
        "height": 1080.0,
        "name": "ReportSection_page1",
        "ordinal": 0,
        "visualContainers": visuals,
        "width": 1920.0
    }


# ============================================================
# PAGE 2: 市区町村詳細
# ============================================================

def build_page2():
    # Page-level filter: サブカテゴリ IN {子育て, 介護}
    page_filters = [{
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
    }]

    visuals = []

    # 1. Back button
    back_config = {
        "name": "vc_p2_back",
        "layouts": [{"id": 0, "position": position(20, 20, 0, 240, 36)}],
        "singleVisual": {
            "visualType": "actionButton",
            "objects": {
                "icon": [{"properties": {"show": lit_bool(False)}}],
                "outline": [{"properties": {"show": lit_bool(False)}}],
                "text": [{"properties": {
                    "show": lit_bool(True),
                    "text": lit_str("< 都道府県一覧に戻る")
                }}],
                "action": [{"properties": {
                    "type": lit_str("PageNavigation"),
                    "destination": lit_str("ReportSection_page1")
                }}]
            },
            "vcObjects": hidden_vc_objects()
        }
    }
    visuals.append(make_visual_container(back_config, [], 20, 20, 240, 36, 0))

    # 2. Slicer: 都道府県
    visuals.append(make_slicer("vc_p2_slicer_pref", 20, 70, 280, 55, 0, "都道府県", "都道府県"))

    # 3. Slicer: 団体名
    visuals.append(make_slicer("vc_p2_slicer_muni", 320, 70, 280, 55, 0, "団体名", "団体名"))

    # 4. Card: 子育て介護26手続完了率
    visuals.append(make_card("vc_p2_card_rate", 620, 70, 200, 55, 0, "子育て介護26手続完了率"))

    # 5. Card: 子育て介護26手続完了自治体数
    visuals.append(make_card("vc_p2_card_completed", 840, 70, 200, 55, 0, "子育て介護26手続完了自治体数"))

    # 6. Card: 自治体数
    visuals.append(make_card("vc_p2_card_total", 1060, 70, 200, 55, 0, "自治体数"))

    # 7. Matrix: Detail cross-tab
    matrix2_config = {
        "name": "vc_p2_matrix",
        "layouts": [{"id": 0, "position": position(20, 140, 0, 1880, 920)}],
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
            "objects": {
                "subTotals": [{"properties": {
                    "rowSubtotals": lit_bool(False),
                    "columnSubtotals": lit_bool(False)
                }}]
            },
            "vcObjects": minimal_vc_objects()
        }
    }
    visuals.append(make_visual_container(matrix2_config, [], 20, 140, 1880, 920, 0))

    return {
        "config": json.dumps({}, ensure_ascii=False),
        "displayName": "市区町村詳細",
        "displayOption": 1,
        "filters": json.dumps(page_filters, ensure_ascii=False),
        "height": 1080.0,
        "name": "ReportSection_page2",
        "ordinal": 1,
        "visualContainers": visuals,
        "width": 1920.0
    }


# ============================================================
# REPORT-LEVEL CONFIG
# ============================================================

def build_report():
    report_config = {
        "version": "5.44",
        "themeCollection": {
            "baseTheme": {"name": "CY23SU08", "version": "5.46", "type": 2},
            "customTheme": {"name": "Digital_Agency_Dashboard_Desig3362615343750506.json", "version": "5.46", "type": 1}
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
                "items": [{"name": "Digital_Agency_Dashboard_Desig3362615343750506.json", "path": "Digital_Agency_Dashboard_Desig3362615343750506.json", "type": 201}],
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
# VALIDATION
# ============================================================

def validate_report(report):
    """Validate all embedded JSON strings and structural requirements."""
    errors = []

    # Validate top-level config
    try:
        top = json.loads(report["config"])
        assert "version" in top, "Top config missing 'version'"
        assert "themeCollection" in top, "Top config missing 'themeCollection'"
        assert "customTheme" in top.get("themeCollection", {}), "Should have customTheme"
    except (json.JSONDecodeError, AssertionError) as e:
        errors.append(f"Top-level config: {e}")

    # 'theme' key at top level should exist
    if "theme" not in report:
        errors.append("Top-level 'theme' property should exist")

    # Validate each section
    for i, section in enumerate(report["sections"]):
        sec_name = section.get("displayName", f"section_{i}")

        try:
            json.loads(section["config"])
        except json.JSONDecodeError as e:
            errors.append(f"Section '{sec_name}' config: {e}")

        try:
            filters = json.loads(section["filters"])
            assert isinstance(filters, list), "Filters must be a JSON array"
        except (json.JSONDecodeError, AssertionError) as e:
            errors.append(f"Section '{sec_name}' filters: {e}")

        # Validate visual containers
        visual_names = set()
        for j, vc in enumerate(section.get("visualContainers", [])):
            try:
                vc_config = json.loads(vc["config"])
                name = vc_config.get("name", "")
                if not name:
                    errors.append(f"Section '{sec_name}', visual {j}: missing 'name'")
                if name in visual_names:
                    errors.append(f"Section '{sec_name}', visual {j}: duplicate name '{name}'")
                visual_names.add(name)

                sv = vc_config.get("singleVisual", {})
                vt = sv.get("visualType", "")
                if not vt:
                    errors.append(f"Visual '{name}': missing visualType")

                pq = sv.get("prototypeQuery")
                if pq:
                    assert pq.get("Version") == 2, f"Visual '{name}': Version must be 2"
                    assert "From" in pq, f"Visual '{name}': missing 'From'"
                    assert "Select" in pq, f"Visual '{name}': missing 'Select'"
                    for frm in pq["From"]:
                        assert frm.get("Type") == 0, f"Visual '{name}': From Type must be 0"

            except (json.JSONDecodeError, AssertionError) as e:
                errors.append(f"Section '{sec_name}', visual {j}: {e}")

            try:
                vc_filters = json.loads(vc["filters"])
                assert isinstance(vc_filters, list)
            except (json.JSONDecodeError, AssertionError) as e:
                errors.append(f"Section '{sec_name}', visual {j} filters: {e}")

    return errors


# ============================================================
# MAIN
# ============================================================

def main():
    output_path = "/Users/kei/Git/26_administrative_procedures_online/26_administrative_procedures_online.Report/report.json"

    print("Building report.json...")
    report = build_report()

    print("Validating...")
    errors = validate_report(report)
    if errors:
        print("VALIDATION ERRORS:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)

    json_str = json.dumps(report, ensure_ascii=False, indent=2)

    # Double-check round-trip
    readback = json.loads(json_str)

    # Recursively validate all embedded JSON strings
    def validate_embedded(obj, path="root"):
        if isinstance(obj, dict):
            for key, val in obj.items():
                if key in ("config", "filters") and isinstance(val, str):
                    try:
                        json.loads(val)
                    except json.JSONDecodeError as e:
                        raise ValueError(f"Invalid embedded JSON at {path}.{key}: {e}")
                else:
                    validate_embedded(val, f"{path}.{key}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                validate_embedded(item, f"{path}[{i}]")

    validate_embedded(readback)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(json_str)

    # Summary
    p1_count = len(report["sections"][0]["visualContainers"])
    p2_count = len(report["sections"][1]["visualContainers"])
    print(f"\nWrote: {output_path}")
    print(f"  Pages: {len(report['sections'])}")
    print(f"  Page 1 '{report['sections'][0]['displayName']}': {p1_count} visuals")
    print(f"  Page 2 '{report['sections'][1]['displayName']}': {p2_count} visuals")
    print(f"  JSON size: {len(json_str):,} bytes")
    print(f"  No 'theme' at top level: {'theme' not in report}")
    print("  All embedded JSON validated OK.")


if __name__ == "__main__":
    main()
