#!/usr/bin/env python3
"""Validate milestone-specific completeness of a Unity game design sheet."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from design_document_set import (
    AC_ID_RE,
    acceptance_tables,
    design_item_blocks as document_design_item_blocks,
    load_document_set,
)
from validate_design_contract import (
    PROJECT_REQUIREMENT_IDS,
    parse_conformance_rows,
    validate_contract,
)


MILESTONES = (
    "Concept",
    "Prototype",
    "Vertical Slice",
    "Alpha",
    "Beta",
    "Release",
)
MILESTONE_INDEX = {name: index for index, name in enumerate(MILESTONES)}
PHASE_IDS = tuple(f"PHASE-{index:02d}" for index in range(10))
MANDATORY_HREQS = {
    "HREQ-DESIGN-001",
    "HREQ-PROJECT-001",
    "HREQ-VALIDATION-001",
}
APPROVED_PHASE_STATE = "人間承認済"
PASSING_AUDITS = {"SELF REVIEW", "SUBAGENT PASS"}
VALID_VERIFICATION_TYPES = {
    "AUTO:STATIC",
    "AUTO:EDIT",
    "AUTO:PLAY",
    "AUTO:ASSET",
    "AUTO:BUILD",
    "MANUAL:EDITOR",
    "MANUAL:PLAY",
}
CROSS_CUTTING_AREAS = (
    "Accessibility",
    "Localization",
    "Multiplayer / Online",
    "Account / Authentication / Cloud Save",
    "Analytics / Crash Reporting",
    "Privacy / Consent / Compliance",
    "Security / Abuse Prevention",
    "LiveOps / Remote Config",
    "IAP / Ads / Entitlements",
    "Moderation / Community",
    "Modding / UGC",
    "XR",
    "Performance / Device Budgets",
    "Diagnostics / Debug / Cheat Controls",
)
CHOICE_PLACEHOLDERS = {
    "Concept / Prototype / Vertical Slice / Alpha / Beta / Release",
    "Draft / Review / Approved",
    "未開始 / 対話中 / 確認待ち / マイルストーン承認済",
    "NOT RUN / SELF REVIEW / SUBAGENT PASS / SUBAGENT FINDINGS",
    "回答待ち / 要約確認待ち / 確定反映済",
    "標準推奨 / ゲーム個別 / 両方",
    "採用 / 不採用 / 保留",
    "Small / Standard / Large / 未決定",
    "Built-in / URP / HDRP / 未決定",
    "可 / 不可 / 未決定",
    "Single / Additive / 未決定",
    "Development / QA / Release",
}
PLACEHOLDER_MARKERS = (
    "未決定",
    "未発行",
    "未作成",
    "未記録",
    "回答待ち",
    "<DOMAIN>",
    "<NNN>",
    "<短い名称>",
)

PHASE_REQUIREMENTS = {
    "Concept": {
        "PHASE-00",
        "PHASE-01",
        "PHASE-02",
        "PHASE-03",
        "PHASE-08",
        "PHASE-09",
    },
    "Prototype": set(PHASE_IDS),
    "Vertical Slice": set(PHASE_IDS),
    "Alpha": set(PHASE_IDS),
    "Beta": set(PHASE_IDS),
    "Release": set(PHASE_IDS),
}

HREQ_REQUIREMENTS = {
    "Concept": {
        "HREQ-DESIGN-001",
        "HREQ-PROJECT-001",
        "HREQ-VALIDATION-001",
    },
    "Prototype": set(PROJECT_REQUIREMENT_IDS),
    "Vertical Slice": set(PROJECT_REQUIREMENT_IDS),
    "Alpha": set(PROJECT_REQUIREMENT_IDS),
    "Beta": set(PROJECT_REQUIREMENT_IDS),
    "Release": set(PROJECT_REQUIREMENT_IDS),
}

CONCEPT_FIELDS = (
    ("0. 文書情報", "プロジェクト名"),
    ("0. 文書情報", "作成者・責任者"),
    ("1. コンセプト", "一文コンセプト"),
    ("1. コンセプト", "ジャンル"),
    ("1. コンセプト", "対象プレイヤー"),
    ("1. コンセプト", "提供する中心体験"),
    ("1. コンセプト", "差別化要素"),
    ("1. コンセプト", "今回作らないもの"),
    (
        "HREQ-PLATFORM-001: Unityバージョン・対象プラットフォーム",
        "主対象プラットフォーム",
    ),
    (
        "HREQ-PLATFORM-001: Unityバージョン・対象プラットフォーム",
        "入力方式",
    ),
)

PROTOTYPE_FIELDS = CONCEPT_FIELDS + (
    ("1. コンセプト", "1プレイの想定時間"),
    ("1. コンセプト", "継続プレイの動機"),
    (
        "HREQ-PLATFORM-001: Unityバージョン・対象プラットフォーム",
        "Unity Editor完全バージョン",
    ),
    (
        "HREQ-PLATFORM-001: Unityバージョン・対象プラットフォーム",
        "決定根拠",
    ),
    (
        "HREQ-PLATFORM-001: Unityバージョン・対象プラットフォーム",
        "開発時検証環境",
    ),
    (
        "HREQ-PLATFORM-001: Unityバージョン・対象プラットフォーム",
        "必要なBuild Support",
    ),
    (
        "HREQ-PLATFORM-001: Unityバージョン・対象プラットフォーム",
        "基準解像度・画面向き",
    ),
    (
        "HREQ-PLATFORM-001: Unityバージョン・対象プラットフォーム",
        "目標FPS・性能予算",
    ),
    ("3. グラフィック・アート", "2D / 3D / Hybrid"),
    ("3. グラフィック・アート", "Render Pipeline"),
    ("3. グラフィック・アート", "アートスタイル"),
    ("3. グラフィック・アート", "カメラ方式"),
    ("3. グラフィック・アート", "色・可読性方針"),
    ("HREQ-ARCH-001: アーキテクチャプロファイル", "選択Profile"),
    ("HREQ-ARCH-001: アーキテクチャプロファイル", "選択理由"),
    ("HREQ-PROJECT-001: プロジェクト構造の適用記録", "自作Asset root"),
    ("HREQ-PROJECT-001: プロジェクト構造の適用記録", "asmdef構成"),
    ("HREQ-PROJECT-001: プロジェクト構造の適用記録", ".meta・GUID運用"),
    ("HREQ-SAVE-001: セーブ互換性と復旧", "採否"),
    ("HREQ-REPO-001: Repository・Asset運用", "Default branch"),
    ("HREQ-REPO-001: Repository・Asset運用", "Review・Required CI"),
    ("HREQ-REPO-001: Repository・Asset運用", "Serialization mode"),
    ("HREQ-REPO-001: Repository・Asset運用", "Meta Files"),
)

VERTICAL_SLICE_FIELDS = PROTOTYPE_FIELDS + (
    ("3. グラフィック・アート", "ライティング方針"),
    ("3. グラフィック・アート", "VFX方針"),
    ("HREQ-ARCH-001: アーキテクチャプロファイル", "Assembly / Package境界"),
    ("HREQ-ARCH-001: アーキテクチャプロファイル", "依存方向"),
    ("HREQ-ARCH-001: アーキテクチャプロファイル", "Composition方式"),
    ("HREQ-ARCH-001: アーキテクチャプロファイル", "次Profileへの移行条件"),
    ("HREQ-ARCH-001: アーキテクチャプロファイル", "承認者・承認日"),
    ("9. Addressables・性能・診断", "Addressables採否"),
    ("9. Addressables・性能・診断", "FPS予算"),
    ("9. Addressables・性能・診断", "Memory予算"),
    ("9. Addressables・性能・診断", "Load時間予算"),
    ("9. Addressables・性能・診断", "Profiler確認地点"),
    ("HREQ-BUILD-001: Build Profile", "Clean Build条件"),
    ("HREQ-BUILD-001: Build Profile", "Scripting Backend"),
    ("HREQ-BUILD-001: Build Profile", "Architecture"),
    ("HREQ-BUILD-001: Build Profile", "CIで使用するProfile"),
)

ALPHA_FIELDS = VERTICAL_SLICE_FIELDS + (
    ("HREQ-REPO-001: Repository・Asset運用", "Branch寿命・命名"),
    ("HREQ-REPO-001: Repository・Asset運用", "Merge方式"),
    ("HREQ-REPO-001: Repository・Asset運用", "Release / hotfix経路"),
    ("HREQ-REPO-001: Repository・Asset運用", "LFS採否・対象Path"),
    ("HREQ-REPO-001: Repository・Asset運用", "UnityYAMLMerge"),
    ("HREQ-REPO-001: Repository・Asset運用", "Scene・Prefab owner / lock"),
)

RELEASE_FIELDS = ALPHA_FIELDS + (
    ("HREQ-BUILD-001: Build Profile", "Signing・証明書"),
    ("HREQ-BUILD-001: Build Profile", "Store・配布経路"),
)

FIELD_REQUIREMENTS = {
    "Concept": CONCEPT_FIELDS,
    "Prototype": PROTOTYPE_FIELDS,
    "Vertical Slice": VERTICAL_SLICE_FIELDS,
    "Alpha": ALPHA_FIELDS,
    "Beta": ALPHA_FIELDS,
    "Release": RELEASE_FIELDS,
}


@dataclass(frozen=True)
class MarkdownTable:
    section: str
    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate milestone-specific phases, decisions, HREQs, design "
            "items, acceptance criteria, deferrals, audits, and approval."
        )
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Unity project root containing docs/game_design/",
    )
    parser.add_argument(
        "--milestone",
        choices=MILESTONES,
        help="Target milestone. Defaults to the design sheet target.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional project-relative or absolute JSON report path.",
    )
    return parser.parse_args()


def normalize_cell(value: str) -> str:
    return value.strip().strip("`").strip()


def split_row(line: str) -> tuple[str, ...]:
    return tuple(
        normalize_cell(cell)
        for cell in line.strip().strip("|").split("|")
    )


def is_separator(line: str) -> bool:
    if not line.lstrip().startswith("|"):
        return False
    cells = split_row(line)
    return bool(cells) and all(
        re.fullmatch(r":?-{3,}:?", cell) is not None for cell in cells
    )


def parse_tables(text: str) -> list[MarkdownTable]:
    lines = text.splitlines()
    tables: list[MarkdownTable] = []
    section = ""
    index = 0
    while index < len(lines):
        heading = re.match(r"^#{2,4}\s+(.+?)\s*$", lines[index])
        if heading:
            section = normalize_cell(heading.group(1))
            index += 1
            continue
        if (
            lines[index].lstrip().startswith("|")
            and index + 1 < len(lines)
            and is_separator(lines[index + 1])
        ):
            headers = split_row(lines[index])
            rows: list[tuple[str, ...]] = []
            index += 2
            while index < len(lines) and lines[index].lstrip().startswith("|"):
                row = split_row(lines[index])
                if len(row) < len(headers):
                    row = row + ("",) * (len(headers) - len(row))
                rows.append(row)
                index += 1
            tables.append(
                MarkdownTable(section, headers, tuple(rows))
            )
            continue
        index += 1
    return tables


def is_placeholder(value: str) -> bool:
    normalized = normalize_cell(value)
    if not normalized:
        return True
    if normalized in CHOICE_PLACEHOLDERS:
        return True
    return any(marker in normalized for marker in PLACEHOLDER_MARKERS)


def table_for(
    tables: list[MarkdownTable],
    section: str,
    required_headers: set[str],
) -> MarkdownTable | None:
    for table in tables:
        if table.section == section and required_headers.issubset(table.headers):
            return table
    return None


def field_value(
    tables: list[MarkdownTable],
    section: str,
    key: str,
) -> str | None:
    for table in tables:
        if table.section != section or len(table.headers) < 2:
            continue
        for row in table.rows:
            if len(row) >= 2 and row[0] == key:
                return row[1]
    return None


def require_field(
    errors: list[str],
    tables: list[MarkdownTable],
    section: str,
    key: str,
) -> None:
    value = field_value(tables, section, key)
    if value is None:
        errors.append(f"missing readiness field: {section} -> {key}")
    elif is_placeholder(value):
        errors.append(f"unresolved readiness field: {section} -> {key}")


def complete_rows(
    table: MarkdownTable | None,
    required_columns: tuple[str, ...],
) -> list[dict[str, str]]:
    if table is None:
        return []
    indices = []
    for column in required_columns:
        if column not in table.headers:
            return []
        indices.append(table.headers.index(column))
    complete: list[dict[str, str]] = []
    for row in table.rows:
        values = [row[index] if index < len(row) else "" for index in indices]
        if all(not is_placeholder(value) for value in values):
            complete.append(dict(zip(required_columns, values)))
    return complete


def validate_session(
    milestone: str,
    tables: list[MarkdownTable],
    errors: list[str],
) -> None:
    target = field_value(tables, "初期設計対話", "対象マイルストーン")
    if target != milestone:
        errors.append(
            f"target milestone mismatch: expected {milestone}, "
            f"got {target or '<missing>'}"
        )
    current = field_value(tables, "0. 文書情報", "現在のマイルストーン")
    if current != milestone:
        errors.append(
            f"current milestone mismatch: expected {milestone}, "
            f"got {current or '<missing>'}"
        )
    review = field_value(tables, "0. 文書情報", "設計レビュー状態")
    if review != "Approved":
        errors.append(
            f"design review state must be Approved: {review or '<missing>'}"
        )
    session = field_value(tables, "初期設計対話", "セッション状態")
    if session != "マイルストーン承認済":
        errors.append(
            "initial-design session must be マイルストーン承認済: "
            f"{session or '<missing>'}"
        )
    audit = field_value(tables, "初期設計対話", "最終監査")
    if audit not in PASSING_AUDITS:
        errors.append(
            "final audit must be SELF REVIEW or SUBAGENT PASS: "
            f"{audit or '<missing>'}"
        )
    require_field(errors, tables, "初期設計対話", "意思決定者")


def validate_phases(
    milestone: str,
    tables: list[MarkdownTable],
    errors: list[str],
) -> None:
    table = table_for(
        tables,
        "初期設計対話",
        {"Phase ID", "状態", "確定内容・再検討理由", "確認者・日付", "監査"},
    )
    if table is None:
        errors.append("missing initial-design phase progress table")
        return
    indices = {name: table.headers.index(name) for name in table.headers}
    rows = {
        row[indices["Phase ID"]]: row
        for row in table.rows
        if len(row) > indices["Phase ID"] and row[indices["Phase ID"]] in PHASE_IDS
    }
    for phase_id in PHASE_IDS:
        if phase_id not in rows:
            errors.append(f"missing phase progress row: {phase_id}")
    for phase_id in sorted(PHASE_REQUIREMENTS[milestone]):
        row = rows.get(phase_id)
        if row is None:
            errors.append(f"missing required phase row: {phase_id}")
            continue
        state = row[indices["状態"]]
        if state != APPROVED_PHASE_STATE:
            errors.append(
                f"required phase is not human-approved: {phase_id} -> {state}"
            )
        decision = row[indices["確定内容・再検討理由"]]
        if is_placeholder(decision):
            errors.append(f"required phase lacks confirmed summary: {phase_id}")
        confirmation = row[indices["確認者・日付"]]
        if is_placeholder(confirmation):
            errors.append(f"required phase lacks confirmer and date: {phase_id}")
        audit = row[indices["監査"]]
        if audit not in PASSING_AUDITS:
            errors.append(
                f"required phase audit is incomplete: {phase_id} -> {audit}"
            )
        if "Blocking未決事項ID" in indices:
            blocking = row[indices["Blocking未決事項ID"]]
            if normalize_cell(blocking) not in {"", "なし"}:
                errors.append(
                    f"required phase has blocking open question: "
                    f"{phase_id} -> {blocking}"
                )


def validate_hreqs(
    milestone: str,
    project_root: Path,
    text: str,
    errors: list[str],
) -> None:
    errors.extend(validate_contract(project_root))
    rows, _ = parse_conformance_rows(text)
    for requirement_id in sorted(HREQ_REQUIREMENTS[milestone]):
        row = rows.get(requirement_id)
        if row is None:
            continue
        if len(row) >= 2 and row[1] == "未決定":
            errors.append(
                f"milestone-required HREQ remains unresolved: {requirement_id}"
            )
        if len(row) >= 2 and (
            requirement_id in MANDATORY_HREQS
            and row[1] == "対象外"
        ):
            errors.append(
                f"mandatory HREQ cannot be target-excluded: {requirement_id}"
            )


def validate_core_design(
    milestone: str,
    text: str,
    tables: list[MarkdownTable],
    errors: list[str],
) -> None:
    for section, key in FIELD_REQUIREMENTS[milestone]:
        require_field(errors, tables, section, key)

    match = re.search(
        r"^### コアループ\s*$.*?```(?:text)?\s*(.*?)\s*```",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if match is None or is_placeholder(match.group(1)):
        errors.append("core loop is unresolved")

    win_table = table_for(
        tables,
        "勝利・失敗・終了条件",
        {"種別", "条件", "結果"},
    )
    if win_table is None:
        errors.append("missing win/fail/end condition table")
    else:
        rows = {row[0]: row for row in win_table.rows if row}
        for kind in ("勝利", "失敗", "中断・終了"):
            row = rows.get(kind)
            if row is None or len(row) < 3 or any(
                is_placeholder(value) for value in row[1:3]
            ):
                errors.append(f"unresolved game outcome: {kind}")

    mechanics = table_for(
        tables,
        "メカニクス一覧",
        {"設計ID", "状態", "メカニクス", "入力・開始条件", "ルール", "結果・報酬"},
    )
    if not complete_rows(
        mechanics,
        ("設計ID", "メカニクス", "入力・開始条件", "ルール", "結果・報酬"),
    ):
        errors.append("no complete core mechanic row")

    if MILESTONE_INDEX[milestone] >= MILESTONE_INDEX["Prototype"]:
        input_table = table_for(
            tables,
            "Input",
            {"Action", "Device", "Binding", "Gameplay条件", "Rebind"},
        )
        if not complete_rows(
            input_table,
            ("Action", "Device", "Binding", "Gameplay条件", "Rebind"),
        ):
            errors.append("no complete input row for Prototype or later")

        build_table = table_for(
            tables,
            "HREQ-BUILD-001: Build Profile",
            {"Profile asset", "Platform", "用途", "Scene List", "Output"},
        )
        build_rows = complete_rows(
            build_table,
            ("Profile asset", "Platform", "用途", "Scene List", "Output"),
        )
        if not any("Development" in row["用途"] for row in build_rows):
            errors.append("no complete Development Build Profile row")

    if MILESTONE_INDEX[milestone] >= MILESTONE_INDEX["Vertical Slice"]:
        table_requirements = (
            ("状態一覧", ("状態", "開始条件", "許可する操作", "終了条件", "次状態")),
            (
                "Scene一覧",
                ("Scene", "役割", "Load方式", "Entry条件", "Exit条件", "Build Profile"),
            ),
            ("Scene遷移", ("From", "Trigger", "To", "引き継ぐデータ", "失敗時")),
            ("UI", ("画面・HUD", "用途", "表示条件", "操作", "Accessibility考慮")),
        )
        for section, columns in table_requirements:
            table = table_for(tables, section, set(columns))
            if not complete_rows(table, columns):
                errors.append(
                    f"no complete {section} row for Vertical Slice or later"
                )

def validate_save(
    milestone: str,
    tables: list[MarkdownTable],
    errors: list[str],
) -> None:
    if MILESTONE_INDEX[milestone] < MILESTONE_INDEX["Prototype"]:
        return
    section = "HREQ-SAVE-001: セーブ互換性と復旧"
    adoption = field_value(tables, section, "採否")
    if adoption not in {"採用", "不採用"}:
        errors.append(
            "save adoption must be 採用 or 不採用 for Prototype or later"
        )
        return
    if adoption == "不採用":
        return
    required = ["保存対象", "端末設定との分離", "保存形式・保存先"]
    if MILESTONE_INDEX[milestone] >= MILESTONE_INDEX["Vertical Slice"]:
        required.extend(
            [
                "Current schema",
                "Supported oldest schema",
                "Atomic write",
                "Backup / rollback",
                "Migration",
                "Future schema",
                "Integrity / encryption",
                "Platform制約",
            ]
        )
    for key in required:
        require_field(errors, tables, section, key)


def validate_cross_cutting(
    milestone: str,
    tables: list[MarkdownTable],
    errors: list[str],
) -> None:
    table = table_for(
        tables,
        "HREQ-CROSS-001: 横断機能採否",
        {
            "領域",
            "状態",
            "理由・対象範囲",
            "Package / Service",
            "データ・規制・安全性",
            "設計ID・AC",
            "決定者",
            "再評価条件・期限",
        },
    )
    if table is None:
        errors.append(
            "cross-cutting table requires 決定者 and readiness columns"
        )
        return
    index = {name: table.headers.index(name) for name in table.headers}
    rows_by_area = {
        row[index["領域"]]: row
        for row in table.rows
        if len(row) > index["領域"]
    }
    for area in CROSS_CUTTING_AREAS:
        if area not in rows_by_area:
            errors.append(f"missing cross-cutting row: {area}")
    for row in table.rows:
        if len(row) <= index["領域"]:
            continue
        area = row[index["領域"]]
        if is_placeholder(area):
            continue
        state = row[index["状態"]]
        reason = row[index["理由・対象範囲"]]
        reevaluation = row[index["再評価条件・期限"]]
        if state not in {"採用", "不採用", "保留"}:
            errors.append(f"cross-cutting state unresolved: {area} -> {state}")
            continue
        if is_placeholder(reason):
            errors.append(f"cross-cutting reason missing: {area}")
        if state == "採用":
            for column in ("Package / Service", "データ・規制・安全性"):
                if is_placeholder(row[index[column]]):
                    errors.append(
                        f"adopted cross-cutting field missing: {area} -> {column}"
                    )
            if (
                MILESTONE_INDEX[milestone] >= MILESTONE_INDEX["Prototype"]
                and (
                    re.search(
                        r"\b[A-Z][A-Z0-9]*-\d{3}\b",
                        row[index["設計ID・AC"]],
                    )
                    is None
                    or re.search(
                        AC_ID_RE,
                        row[index["設計ID・AC"]],
                    )
                    is None
                )
            ):
                errors.append(
                    f"adopted cross-cutting design ID/AC missing: {area}"
                )
        elif state == "不採用":
            if is_placeholder(reevaluation):
                errors.append(
                    f"cross-cutting reevaluation condition missing: {area}"
                )
        else:
            if is_placeholder(row[index["決定者"]]):
                errors.append(f"deferred cross-cutting owner missing: {area}")
            if is_placeholder(reevaluation):
                errors.append(
                    f"deferred cross-cutting deadline missing: {area}"
                )
            else:
                mentioned = deadline_milestones(reevaluation)
                if any(
                    MILESTONE_INDEX[item] <= MILESTONE_INDEX[milestone]
                    for item in mentioned
                ):
                    errors.append(
                        f"deferred cross-cutting decision is due by target "
                        f"milestone: {area} -> {reevaluation}"
                    )
                date_match = re.fullmatch(r"\d{4}-\d{2}-\d{2}", reevaluation)
                if date_match:
                    try:
                        deadline_date = date.fromisoformat(reevaluation)
                    except ValueError:
                        errors.append(
                            f"invalid cross-cutting deadline date: "
                            f"{area} -> {reevaluation}"
                        )
                    else:
                        if deadline_date <= date.today():
                            errors.append(
                                f"cross-cutting deadline has passed: "
                                f"{area} -> {reevaluation}"
                            )


def deadline_milestones(value: str) -> set[str]:
    return {
        milestone
        for milestone in MILESTONES
        if milestone.lower() in value.lower()
    }


def validate_open_questions(
    milestone: str,
    tables: list[MarkdownTable],
    errors: list[str],
    warnings: list[str],
) -> None:
    table = table_for(
        tables,
        "未決事項",
        {
            "ID",
            "状態",
            "分類",
            "内容",
            "影響・Blocking対象",
            "決定者",
            "期限・マイルストーン",
        },
    )
    if table is None:
        errors.append("open-question table requires state and blocking target")
        return
    index = {name: table.headers.index(name) for name in table.headers}
    for row in table.rows:
        question_id = row[index["ID"]]
        if question_id in {"", "なし", "Q-001"} and is_placeholder(
            row[index["内容"]]
        ):
            continue
        state = row[index["状態"]]
        if state in {"解決済", "対象外"}:
            continue
        if state != "未解決":
            errors.append(
                f"invalid open-question state: {question_id} -> {state}"
            )
            continue
        owner = row[index["決定者"]]
        deadline = row[index["期限・マイルストーン"]]
        blocking = row[index["影響・Blocking対象"]]
        if is_placeholder(owner):
            errors.append(f"open question lacks owner: {question_id}")
        if is_placeholder(deadline):
            errors.append(f"open question lacks deadline: {question_id}")
        blocking_phases = set(re.findall(r"PHASE-\d{2}", blocking))
        if blocking_phases.intersection(PHASE_REQUIREMENTS[milestone]):
            errors.append(
                f"open question blocks required phase: {question_id} -> "
                f"{', '.join(sorted(blocking_phases))}"
            )
        mentioned = deadline_milestones(deadline)
        if any(
            MILESTONE_INDEX[item] <= MILESTONE_INDEX[milestone]
            for item in mentioned
        ):
            errors.append(
                f"open question is due by target milestone: "
                f"{question_id} -> {deadline}"
            )
        date_match = re.fullmatch(r"\d{4}-\d{2}-\d{2}", deadline)
        if date_match:
            try:
                deadline_date = date.fromisoformat(deadline)
            except ValueError:
                errors.append(
                    f"invalid open-question deadline date: "
                    f"{question_id} -> {deadline}"
                )
            else:
                if deadline_date <= date.today():
                    errors.append(
                        f"open-question deadline has passed: "
                        f"{question_id} -> {deadline}"
                    )
                else:
                    warnings.append(
                        f"open question remains after {milestone}: "
                        f"{question_id} -> {deadline}"
                    )


def validate_design_items(
    milestone: str,
    documents,
    errors: list[str],
) -> None:
    approved_ac_count = 0
    for table in acceptance_tables(documents):
        state_index = table.headers.index("状態")
        approved_ac_count += sum(
            row[state_index] == "Approved" for row in table.rows
        )
    if approved_ac_count == 0:
        errors.append(f"{milestone} requires an Approved acceptance criterion")

    approved_count = 0
    for _, design_id, block in document_design_item_blocks(documents):
        state_match = re.search(
            r"^\*\*状態:\*\*\s*(Draft|Approved|廃止)\s*$",
            block,
            re.MULTILINE,
        )
        state = state_match.group(1) if state_match else ""
        if state == "Draft" and (
            MILESTONE_INDEX[milestone] >= MILESTONE_INDEX["Alpha"]
        ):
            errors.append(
                f"Draft design item remains for {milestone}: {design_id}"
            )
        if state != "Approved":
            continue
        approved_count += 1
        spec_match = re.search(
            r"\*\*仕様\*\*\s*(.*?)(?:\n\*\*依存・影響\*\*|\n####|\Z)",
            block,
            re.DOTALL,
        )
        if spec_match is None or is_placeholder(spec_match.group(1)):
            errors.append(f"approved design item lacks specification: {design_id}")
    if approved_count == 0:
        errors.append(f"{milestone} requires an Approved design item")


def validate_release_profiles(
    milestone: str,
    tables: list[MarkdownTable],
    errors: list[str],
) -> None:
    if MILESTONE_INDEX[milestone] < MILESTONE_INDEX["Alpha"]:
        return
    table = table_for(
        tables,
        "HREQ-BUILD-001: Build Profile",
        {"Profile asset", "Platform", "用途", "Scene List", "Output"},
    )
    rows = complete_rows(
        table,
        ("Profile asset", "Platform", "用途", "Scene List", "Output"),
    )
    required_usages = {"Development", "QA"}
    if milestone == "Release":
        required_usages.add("Release")
    for usage in sorted(required_usages):
        if not any(usage in row["用途"] for row in rows):
            errors.append(
                f"no complete {usage} Build Profile row for {milestone}"
            )


def determine_milestone(
    requested: str | None,
    tables: list[MarkdownTable],
) -> tuple[str | None, list[str]]:
    if requested:
        return requested, []
    target = field_value(tables, "初期設計対話", "対象マイルストーン")
    if target in MILESTONES:
        return target, []
    return None, [
        "cannot infer target milestone; use --milestone or update "
        "初期設計対話 -> 対象マイルストーン"
    ]


def validate_readiness(
    project_root_or_index: Path,
    requested_milestone: str | None = None,
) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        documents = load_document_set(project_root_or_index)
    except ValueError as error:
        return {
            "status": "FAIL",
            "milestone": requested_milestone,
            "errors": [str(error)],
            "warnings": [],
        }
    errors.extend(documents.errors)
    text = documents.text
    tables = parse_tables(text)
    milestone, milestone_errors = determine_milestone(
        requested_milestone,
        tables,
    )
    errors.extend(milestone_errors)
    if milestone is not None:
        validate_session(milestone, tables, errors)
        validate_phases(milestone, tables, errors)
        validate_hreqs(milestone, documents.project_root, text, errors)
        validate_core_design(milestone, text, tables, errors)
        validate_save(milestone, tables, errors)
        validate_cross_cutting(milestone, tables, errors)
        validate_open_questions(milestone, tables, errors, warnings)
        validate_design_items(milestone, documents, errors)
        validate_release_profiles(milestone, tables, errors)
    return {
        "status": "PASS" if not errors else "FAIL",
        "milestone": milestone,
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "errors": len(errors),
            "warnings": len(warnings),
        },
    }


def output_path(project_root: Path, requested: Path | None) -> Path | None:
    if requested is None:
        return None
    if requested.is_absolute():
        return requested
    return project_root / requested


def main() -> int:
    args = parse_args()
    project_root = args.project_root.resolve()
    report = validate_readiness(
        project_root,
        requested_milestone=args.milestone,
    )
    destination = output_path(project_root, args.output)
    if destination is not None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    if report["status"] == "PASS":
        milestone = report["milestone"]
        print(f"Design readiness validation: PASS ({milestone})")
        for warning in report["warnings"]:
            print(f"WARNING: {warning}")
        return 0
    for error in report["errors"]:
        print(f"ERROR: {error}")
    for warning in report["warnings"]:
        print(f"WARNING: {warning}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
