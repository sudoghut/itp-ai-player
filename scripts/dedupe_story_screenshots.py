from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageOps

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path("artifacts") / "interactive-session"
WORK_DIR_NAME = ".ocr-dedupe-work"
STATE_FILE_NAME = "state.json"
REPORT_FILE_PREFIX = "dedupe-report-"
WINDOWS_OCR_SCRIPT = r"""
param(
  [Parameter(Mandatory = $true)]
  [string]$ImagePath
)

Add-Type -AssemblyName System.Runtime.WindowsRuntime

function Await($Op, [Type]$ResultType) {
  $asTask = [System.WindowsRuntimeSystemExtensions].GetMethods() |
    Where-Object { $_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 } |
    Select-Object -First 1
  $generic = $asTask.MakeGenericMethod($ResultType)
  $task = $generic.Invoke($null, @($Op))
  $task.Wait()
  return $task.Result
}

$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType=WindowsRuntime]
$null = [Windows.Media.Ocr.OcrEngine, Windows.Media.Ocr, ContentType=WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics.Imaging, ContentType=WindowsRuntime]
$null = [Windows.Globalization.Language, Windows.Globalization, ContentType=WindowsRuntime]

$file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($ImagePath)) ([Windows.Storage.StorageFile])
$stream = Await ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
$decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
$bitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
$lang = [Windows.Globalization.Language]::new('zh-Hans-CN')
$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($lang)
$result = Await ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
$result.Text
"""

NOISE_PATTERNS = [
    r"离开游戏",
    r"设置",
    r"落笔",
    r"公元\d+年",
    r"姓名[\u4e00-\u9fffA-Za-z0-9 ]+",
    r"职业[\u4e00-\u9fffA-Za-z0-9 ]+",
    r"年龄?\d+",
]

SYSTEM_PHRASES = [
    "离开游戏",
    "开游戏",
    "设置",
    "落笔",
    "拖拽命河可查看过往决策",
    "点击落笔可施展技能",
    "正在加载中",
    "进入图鉴可查看已解锁人物及相关信息",
    "图鉴可查看已解锁人物及相关信息",
    "可查看过往决策",
    "可施展技能",
    "命河",
]


@dataclass
class CompareResult:
    is_duplicate: bool
    confidence: str
    reason: str
    seq_ratio: float
    jaccard: float
    hash_distance: int


class UnionFind:
    def __init__(self, items: list[str]) -> None:
        self.parent = {item: item for item in items}

    def find(self, item: str) -> str:
        parent = self.parent[item]
        if parent != item:
            self.parent[item] = self.find(parent)
        return self.parent[item]

    def union(self, left: str, right: str) -> None:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root != right_root:
            self.parent[right_root] = left_root


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="OCR top-level interactive-session screenshots and delete likely duplicates."
    )
    parser.add_argument("--root", type=Path, default=ROOT, help="Screenshot directory to process.")
    parser.add_argument("--dry-run", action="store_true", help="Compute duplicates but do not delete files.")
    parser.add_argument(
        "--keep-latest",
        action="store_true",
        help="Include latest.png in the frozen manifest. Default is to exclude it because it can still change.",
    )
    parser.add_argument(
        "--include-medium",
        action="store_true",
        help="Also delete medium-confidence duplicates. Default is to only delete high-confidence matches.",
    )
    return parser.parse_args()


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def print_progress(message: str) -> None:
    print(message, flush=True)


def state_path(root: Path) -> Path:
    return root / WORK_DIR_NAME / STATE_FILE_NAME


def load_state(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def build_manifest(root: Path, keep_latest: bool) -> list[dict[str, Any]]:
    manifest: list[dict[str, Any]] = []
    for file_path in sorted(root.iterdir(), key=lambda p: p.name.lower()):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() != ".png":
            continue
        if file_path.name == "latest.png" and not keep_latest:
            continue
        manifest.append(
            {
                "name": file_path.name,
                "size": file_path.stat().st_size,
                "mtime_ns": file_path.stat().st_mtime_ns,
            }
        )
    return manifest


def create_state(root: Path, keep_latest: bool) -> dict[str, Any]:
    manifest = build_manifest(root, keep_latest)
    return {
        "version": 1,
        "root": str(root.resolve()),
        "created_at": now_iso(),
        "keep_latest": keep_latest,
        "manifest": manifest,
        "records": {},
        "duplicates": [],
        "deletion_done": False,
    }


def prepare_image(image_path: Path, crop_path: Path) -> Image.Image:
    image = Image.open(image_path).convert("RGB")
    width, height = image.size

    middle = image.crop(
        (
            int(width * 0.18),
            int(height * 0.16),
            int(width * 0.83),
            int(height * 0.73),
        )
    )
    lower = image.crop(
        (
            int(width * 0.04),
            int(height * 0.67),
            int(width * 0.96),
            int(height * 0.95),
        )
    )

    stacked_width = max(middle.width, lower.width)
    stacked_height = middle.height + lower.height + 30
    canvas = Image.new("L", (stacked_width, stacked_height), 255)

    middle_gray = ImageOps.autocontrast(middle.convert("L"))
    lower_gray = ImageOps.autocontrast(lower.convert("L"))

    canvas.paste(middle_gray, ((stacked_width - middle_gray.width) // 2, 0))
    canvas.paste(lower_gray, ((stacked_width - lower_gray.width) // 2, middle_gray.height + 30))

    # Upscale for more stable OCR on the stylized Chinese font.
    canvas = canvas.resize((canvas.width * 2, canvas.height * 2), Image.Resampling.LANCZOS)
    crop_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(crop_path)
    return image


def ensure_ocr_script(work_root: Path) -> Path:
    script_path = work_root / "windows_ocr.ps1"
    if not script_path.exists():
        script_path.parent.mkdir(parents=True, exist_ok=True)
        script_path.write_text(WINDOWS_OCR_SCRIPT, encoding="utf-8")
    return script_path


def run_windows_ocr(image_path: Path, work_root: Path) -> str:
    script_path = ensure_ocr_script(work_root)
    completed = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script_path),
            str(image_path.resolve()),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return completed.stdout.strip()


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text)
    for pattern in NOISE_PATTERNS:
        normalized = re.sub(pattern, " ", normalized)
    normalized = normalized.replace("\r", "\n")
    normalized = re.sub(r"\s+", "", normalized)
    normalized = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", normalized)
    return normalized


def extract_story_text(text: str) -> str:
    normalized = normalize_text(text)
    cleaned = normalized
    for phrase in SYSTEM_PHRASES:
        cleaned = cleaned.replace(phrase, "")

    # Remove obvious character-sheet labels and common stat/UI fragments after whitespace collapse.
    cleaned = re.sub(r"(姓名|职业|资财|势望|人情|心性|年岁|年龄)", "", cleaned)
    cleaned = re.sub(r"(拖拽|查看|过往|决策|技能|图鉴|解锁|人物|相关|信息)", "", cleaned)

    # Remove year-only fragments and isolated digits that usually come from UI chrome.
    cleaned = re.sub(r"公元\d+年", "", cleaned)
    cleaned = re.sub(r"\d{4,}", "", cleaned)

    # Keep text that is likely to be actual narrative/choice content.
    # OCR often glues all text together, so prefer longer Chinese spans and drop tiny leftovers.
    story_chunks = re.findall(r"[\u4e00-\u9fffA-Za-z0-9]{8,}", cleaned)
    story_text = "".join(story_chunks)
    story_text = re.sub(r"[A-Za-z]{4,}", "", story_text)
    story_text = re.sub(r"\d+", "", story_text)
    return story_text


def make_shingles(text: str, width: int = 5) -> set[str]:
    if len(text) < width:
        return {text} if text else set()
    return {text[i : i + width] for i in range(len(text) - width + 1)}


def average_hash(image: Image.Image, hash_size: int = 16) -> str:
    array = np.asarray(image.convert("L").resize((hash_size, hash_size), Image.Resampling.LANCZOS), dtype=np.float32)
    threshold = float(array.mean())
    bits = "".join("1" if value >= threshold else "0" for value in array.flatten())
    return f"{int(bits, 2):0{hash_size * hash_size // 4}x}"


def hash_distance(hash_a: str, hash_b: str) -> int:
    return (int(hash_a, 16) ^ int(hash_b, 16)).bit_count()


def compare_records(current: dict[str, Any], kept: dict[str, Any]) -> CompareResult:
    current_text = current["story_text"]
    kept_text = kept["story_text"]
    current_len = len(current_text)
    kept_len = len(kept_text)
    min_len = min(current_len, kept_len)
    max_len = max(current_len, kept_len) or 1
    len_ratio = min_len / max_len

    seq_ratio = SequenceMatcher(None, current_text, kept_text).ratio() if current_text and kept_text else 0.0
    shingles_a = make_shingles(current_text)
    shingles_b = make_shingles(kept_text)
    union = shingles_a | shingles_b
    jaccard = (len(shingles_a & shingles_b) / len(union)) if union else 0.0
    distance = hash_distance(current["panel_hash"], kept["panel_hash"])

    if current_text == kept_text and min_len >= 12:
        return CompareResult(True, "high", "normalized OCR text identical", seq_ratio, jaccard, distance)

    if min_len >= 40 and (jaccard >= 0.90 or (seq_ratio >= 0.95 and len_ratio >= 0.75)):
        return CompareResult(True, "high", "story OCR is nearly identical", seq_ratio, jaccard, distance)

    if min_len >= 26 and seq_ratio >= 0.90 and jaccard >= 0.76 and distance <= 24:
        return CompareResult(True, "high", "OCR and central panel hash both match closely", seq_ratio, jaccard, distance)

    if min_len >= 18 and seq_ratio >= 0.84 and jaccard >= 0.66:
        return CompareResult(True, "medium", "OCR mostly matches and image layout is nearly the same", seq_ratio, jaccard, distance)

    # Only allow hash-first matching when both screenshots are effectively textless transitions.
    if current_len < 6 and kept_len < 6 and distance <= 2:
        return CompareResult(True, "medium", "both screenshots have almost no text and the cropped image hash is nearly identical", seq_ratio, jaccard, distance)

    return CompareResult(False, "low", "not similar enough", seq_ratio, jaccard, distance)


def ensure_record(root: Path, work_root: Path, item: dict[str, Any], state: dict[str, Any], index: int, total: int) -> dict[str, Any]:
    records: dict[str, Any] = state["records"]
    name = item["name"]
    if name in records:
        record = records[name]
        if "normalized_text" not in record:
            record["normalized_text"] = normalize_text(record.get("raw_text", ""))
        if "story_text" not in record:
            record["story_text"] = extract_story_text(record.get("raw_text", ""))
        if "text_length" not in record:
            record["text_length"] = len(record["normalized_text"])
        if "story_text_length" not in record:
            record["story_text_length"] = len(record["story_text"])
        print_progress(f"[OCR {index}/{total}] cached {name}")
        return record

    image_path = root / name
    crop_path = work_root / "crops" / name
    image = prepare_image(image_path, crop_path)
    width, height = image.size
    panel = image.crop(
        (
            int(width * 0.18),
            int(height * 0.16),
            int(width * 0.83),
            int(height * 0.73),
        )
    )

    raw_text = run_windows_ocr(crop_path, work_root)
    normalized_text = normalize_text(raw_text)
    story_text = extract_story_text(raw_text)
    record = {
        "name": name,
        "raw_text": raw_text,
        "normalized_text": normalized_text,
        "story_text": story_text,
        "text_length": len(normalized_text),
        "story_text_length": len(story_text),
        "panel_hash": average_hash(panel),
        "ocr_completed_at": now_iso(),
    }
    records[name] = record
    print_progress(
        f"[OCR {index}/{total}] done {name} | story_chars={record['story_text_length']} | preview={record['story_text'][:36]}"
    )
    return record


def compute_duplicates(state: dict[str, Any]) -> list[dict[str, Any]]:
    ordered_names = [item["name"] for item in state["manifest"]]
    order_index = {name: index for index, name in enumerate(ordered_names)}
    records: dict[str, Any] = state["records"]
    pair_results: dict[tuple[str, str], CompareResult] = {}
    union_find = UnionFind(ordered_names)

    for left_index, left_name in enumerate(ordered_names):
        left_record = records[left_name]
        for right_name in ordered_names[left_index + 1 :]:
            compare = compare_records(left_record, records[right_name])
            if compare.is_duplicate:
                pair_results[(left_name, right_name)] = compare
                union_find.union(left_name, right_name)

    groups: dict[str, list[str]] = {}
    for name in ordered_names:
        root = union_find.find(name)
        groups.setdefault(root, []).append(name)

    duplicates: list[dict[str, Any]] = []
    seen_duplicate_names: set[str] = set()
    for group_names in groups.values():
        if len(group_names) <= 1:
            continue

        representative = group_names[0]
        for name in group_names[1:]:
            if name in seen_duplicate_names:
                continue
            compare = pair_results.get((representative, name))
            if compare is None:
                best_anchor = representative
                best_compare: CompareResult | None = None
                for candidate_anchor in group_names:
                    if candidate_anchor == name:
                        continue
                    if order_index[candidate_anchor] < order_index[name]:
                        pair_key = (candidate_anchor, name)
                    else:
                        pair_key = (name, candidate_anchor)
                    candidate_compare = pair_results.get(pair_key)
                    if candidate_compare is None:
                        continue
                    if best_compare is None:
                        best_anchor = candidate_anchor
                        best_compare = candidate_compare
                        continue
                    candidate_rank = (
                        1 if candidate_compare.confidence == "high" else 0,
                        candidate_compare.seq_ratio,
                        candidate_compare.jaccard,
                        -candidate_compare.hash_distance,
                    )
                    best_rank = (
                        1 if best_compare.confidence == "high" else 0,
                        best_compare.seq_ratio,
                        best_compare.jaccard,
                        -best_compare.hash_distance,
                    )
                    if candidate_rank > best_rank:
                        best_anchor = candidate_anchor
                        best_compare = candidate_compare
                if best_compare is None:
                    continue
                compare = best_compare
                duplicate_of = best_anchor
            else:
                duplicate_of = representative

            duplicates.append(
                {
                    "name": name,
                    "duplicate_of": duplicate_of,
                    "confidence": compare.confidence,
                    "reason": compare.reason,
                    "seq_ratio": round(compare.seq_ratio, 4),
                    "jaccard": round(compare.jaccard, 4),
                    "hash_distance": compare.hash_distance,
                    "cluster_representative": representative,
                }
            )
            seen_duplicate_names.add(name)

    return duplicates


def write_report(root: Path, duplicates: list[dict[str, Any]], delete_candidates: list[dict[str, Any]]) -> Path:
    report_name = f"{REPORT_FILE_PREFIX}{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    report_path = root / report_name
    report_payload = {
        "created_at": now_iso(),
        "duplicate_count": len(duplicates),
        "delete_candidate_count": len(delete_candidates),
        "duplicates": duplicates,
        "delete_candidates": delete_candidates,
    }
    report_path.write_text(json.dumps(report_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return report_path


def write_csv_report(root: Path, report_path: Path, duplicates: list[dict[str, Any]], delete_candidates: list[dict[str, Any]]) -> Path:
    csv_path = root / f"{report_path.stem}.csv"
    delete_names = {item["name"] for item in delete_candidates}
    fieldnames = [
        "name",
        "duplicate_of",
        "cluster_representative",
        "confidence",
        "will_delete",
        "reason",
        "seq_ratio",
        "jaccard",
        "hash_distance",
    ]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in duplicates:
            writer.writerow(
                {
                    "name": item["name"],
                    "duplicate_of": item["duplicate_of"],
                    "cluster_representative": item.get("cluster_representative", ""),
                    "confidence": item["confidence"],
                    "will_delete": "yes" if item["name"] in delete_names else "no",
                    "reason": item["reason"],
                    "seq_ratio": item["seq_ratio"],
                    "jaccard": item["jaccard"],
                    "hash_distance": item["hash_distance"],
                }
            )
    return csv_path


def finalize_success(work_root: Path) -> None:
    if work_root.exists():
        shutil.rmtree(work_root)


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    if not root.exists():
        print(f"Directory not found: {root}", file=sys.stderr)
        return 1

    work_root = root / WORK_DIR_NAME
    state_file = state_path(root)
    state = load_state(state_file)
    if state is None:
        state = create_state(root, args.keep_latest)
        save_state(state_file, state)
        print_progress(
            f"Frozen manifest with {len(state['manifest'])} PNG files from {root}"
        )
    else:
        print_progress(
            f"Resuming existing run with {len(state['manifest'])} frozen PNG files from {root}"
        )

    manifest = state["manifest"]
    total = len(manifest)
    for index, item in enumerate(manifest, start=1):
        ensure_record(root, work_root, item, state, index, total)
        save_state(state_file, state)

    duplicates = compute_duplicates(state)
    state["duplicates"] = duplicates
    save_state(state_file, state)
    delete_candidates = [
        duplicate for duplicate in duplicates if duplicate["confidence"] == "high" or args.include_medium
    ]
    print_progress(
        f"OCR finished. Found {len(duplicates)} duplicate screenshots out of {total} frozen files."
    )

    for index, duplicate in enumerate(duplicates, start=1):
        print_progress(
            f"[DUP {index}/{len(duplicates)}] {duplicate['name']} -> {duplicate['duplicate_of']} "
            f"| {duplicate['confidence']} | seq={duplicate['seq_ratio']} "
            f"| jac={duplicate['jaccard']} | hash={duplicate['hash_distance']}"
        )

    high_count = sum(1 for duplicate in duplicates if duplicate["confidence"] == "high")
    medium_count = sum(1 for duplicate in duplicates if duplicate["confidence"] == "medium")
    print_progress(
        f"High-confidence duplicates: {high_count}. Medium-confidence duplicates kept for manual review: {medium_count}."
    )

    report_path = write_report(root, duplicates, delete_candidates)
    print_progress(f"Report written to {report_path}")
    csv_path = write_csv_report(root, report_path, duplicates, delete_candidates)
    print_progress(f"CSV written to {csv_path}")

    if args.dry_run:
        print_progress("Dry run only. Temporary OCR cache was kept for resume.")
        return 0

    deleted = 0
    for index, duplicate in enumerate(delete_candidates, start=1):
        duplicate_path = root / duplicate["name"]
        if not duplicate_path.exists():
            print_progress(f"[DEL {index}/{len(delete_candidates)}] skipped missing {duplicate['name']}")
            continue
        duplicate_path.unlink()
        deleted += 1
        print_progress(f"[DEL {index}/{len(delete_candidates)}] deleted {duplicate['name']}")

    state["deletion_done"] = True
    save_state(state_file, state)
    print_progress(f"Deleted {deleted} duplicate screenshots.")

    finalize_success(work_root)
    print_progress("Removed temporary OCR cache and state files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
