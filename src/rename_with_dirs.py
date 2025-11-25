#!/usr/bin/env python3
# rename_with_dirs.py
# 기능: 파일 이름 치환(기본) + 옵션으로 폴더(디렉토리) 이름도 치환
# 포지셔널: original, replacement, [folder]
# 옵션: --rename-dirs (디렉토리 이름도 변경), --backup-log, --verbose

import argparse
import csv
import datetime
import logging
import os
from pathlib import Path
from typing import Tuple

# --- 설정 ---
FORBIDDEN_CHARS = set('<>:"/\\|?*')
RESERVED_NAMES = {name for name in (
    ["CON","PRN","AUX","NUL"] + [f"COM{i}" for i in range(1,10)] + [f"LPT{i}" for i in range(1,10)]
)}
PATH_LENGTH_WARNING = 260

# --- 유틸 함수 ---
def has_forbidden_chars(s: str) -> bool:
    return any(ch in FORBIDDEN_CHARS for ch in s)

def is_reserved_name(name: str) -> bool:
    base = name.strip().split('.')[0].upper()
    return base in RESERVED_NAMES

def make_indexed_name(parent: Path, candidate_name: str) -> Path:
    stem = Path(candidate_name).stem
    suffix = Path(candidate_name).suffix
    i = 1
    while True:
        new_name = f"{stem}({i}){suffix}"
        new_path = parent / new_name
        if not new_path.exists():
            return new_path
        i += 1

def warn_long_path(full_path: Path):
    if len(str(full_path)) >= PATH_LENGTH_WARNING:
        logging.warning(f"경로 길이 경고: {full_path} (길이 {len(str(full_path))})")

# --- 검증 ---
def validate_inputs(original: str, replacement: str) -> Tuple[bool, str]:
    if original == "":
        return False, "변경될 문자열(원문)이 빈 문자열입니다. 종료합니다."
    if original == replacement:
        return False, "변경될 문자열과 변경할 문자열이 동일합니다. 변경할 항목이 없습니다."
    if has_forbidden_chars(original) or has_forbidden_chars(replacement):
        return False, f"입력에 금지 문자 포함(다음 중 하나): {''.join(sorted(FORBIDDEN_CHARS))}"
    return True, ""

# --- 핵심 로직 ---
def process_non_recursive(folder: Path, original: str, replacement: str, rename_dirs: bool, log_writer, timestamp):
    """
    하위 폴더 미포함 기본 처리. 파일 이름 변경은 해당 폴더의 파일들을,
    디렉토리 이름 변경은 해당 폴더에 있는 바로 아래 디렉토리들에 대해 수행.
    디렉토리 변경은 디렉토리 자체가 다른 디렉토리로 바뀔 수 있으므로
    디렉토리 변경은 파일 변경 후 처리하거나 별도로 하향식 처리 필요.
    여기선 같은 레벨(폴더 안의 항목들)에서 파일 먼저 처리하고 디렉토리는 나중에 처리.
    """
    changed_count = 0
    errors = 0

    # --- 1) 파일 처리 (폴더 내 파일만) ---
    # snapshot the entries to avoid iterator invalidation when renaming
    for entry in list(folder.iterdir()):
        if entry.is_file():
            orig_name = entry.name
            if original not in orig_name:
                continue
            new_name = orig_name.replace(original, replacement)
            new_path = entry.with_name(new_name)
            status = "ERROR"
            message = ""
            try:
                if has_forbidden_chars(new_name):
                    message = "새 이름에 금지 문자 포함"
                    logging.warning(f"건너뜀(파일): {entry} -> {new_name} : {message}")
                    log_writer.writerow([timestamp, str(entry), orig_name, new_name, "ERROR", message, "FILE"])
                    errors += 1
                    continue
                if new_name.strip() == "":
                    message = "새 이름이 빈 문자열"
                    logging.warning(f"건너뜀(파일): {entry} -> {new_name} : {message}")
                    log_writer.writerow([timestamp, str(entry), orig_name, new_name, "ERROR", message, "FILE"])
                    errors += 1
                    continue
                if is_reserved_name(new_name):
                    message = "예약 파일명으로 변경 가능"
                    logging.warning(f"건너뜀(파일): {entry} -> {new_name} : {message}")
                    log_writer.writerow([timestamp, str(entry), orig_name, new_name, "ERROR", message, "FILE"])
                    errors += 1
                    continue

                warn_long_path(folder / new_name)

                if new_path.exists():
                    target = make_indexed_name(folder, new_name)
                    msg2 = f"충돌 발생, 인덱스 처리 -> {target.name}"
                else:
                    target = new_path
                    msg2 = "CHANGED"

                os.replace(str(entry), str(target))
                logging.info(f"변경(파일): {entry.name} -> {target.name}")
                log_writer.writerow([timestamp, str(entry), orig_name, target.name, "CHANGED", msg2, "FILE"])
                changed_count += 1

            except Exception as e:
                message = f"예외: {e}"
                logging.error(f"오류(파일): {entry} : {e}")
                log_writer.writerow([timestamp, str(entry), orig_name, new_name, "ERROR", message, "FILE"])
                errors += 1
                continue

    # --- 2) 디렉토리 처리 (옵션) ---
    if rename_dirs:
        # 폴더 안의 바로 아래 디렉토리들에 대해 이름 변경 시도
        # 이름 변경은 같은 레벨에서 처리: 파일을 먼저 바꿨으니 디렉토리 이름만 안전히 변경 가능
        # snapshot entries for the same reason as files
        for entry in list(folder.iterdir()):
            if entry.is_dir():
                orig_name = entry.name
                if original not in orig_name:
                    continue
                new_name = orig_name.replace(original, replacement)
                new_path = entry.with_name(new_name)
                try:
                    if has_forbidden_chars(new_name):
                        message = "새 디렉토리 이름에 금지 문자 포함"
                        logging.warning(f"건너뜀(디렉토리): {entry} -> {new_name} : {message}")
                        log_writer.writerow([timestamp, str(entry), orig_name, new_name, "ERROR", message, "DIR"])
                        errors += 1
                        continue
                    if new_name.strip() == "":
                        message = "새 디렉토리 이름이 빈 문자열"
                        logging.warning(f"건너뜀(디렉토리): {entry} -> {new_name} : {message}")
                        log_writer.writerow([timestamp, str(entry), orig_name, new_name, "ERROR", message, "DIR"])
                        errors += 1
                        continue
                    if is_reserved_name(new_name):
                        message = "예약 이름으로 변경 가능"
                        logging.warning(f"건너뜀(디렉토리): {entry} -> {new_name} : {message}")
                        log_writer.writerow([timestamp, str(entry), orig_name, new_name, "ERROR", message, "DIR"])
                        errors += 1
                        continue

                    warn_long_path(folder / new_name)

                    if new_path.exists():
                        target = make_indexed_name(folder, new_name)
                        msg2 = f"충돌 발생, 인덱스 처리 -> {target.name}"
                    else:
                        target = new_path
                        msg2 = "CHANGED"

                    # 디렉토리 rename: Path.rename 또는 os.replace 사용 가능 (os.replace works for paths)
                    os.replace(str(entry), str(target))
                    logging.info(f"변경(디렉토리): {entry.name} -> {target.name}")
                    log_writer.writerow([timestamp, str(entry), orig_name, target.name, "CHANGED", msg2, "DIR"])
                    changed_count += 1

                except Exception as e:
                    message = f"예외: {e}"
                    logging.error(f"오류(디렉토리): {entry} : {e}")
                    final_name = target.name if 'target' in locals() else new_name
                    log_writer.writerow([timestamp, str(entry), orig_name, final_name, "ERROR", message, "DIR"])
                    errors += 1
                    continue

    return changed_count, errors

def run_main(original: str, replacement: str, folder: Path, rename_dirs: bool, log_path: Path):
    timestamp = datetime.datetime.now().isoformat(timespec='seconds')
    changed_total = 0
    errors_total = 0

    with log_path.open('w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["timestamp", "original_path", "original_name", "new_name", "status", "message", "type"])
        # 현재는 비재귀 기본: 폴더 자체의 바로 아래 항목들에 대해서만 처리
        changed, errors = process_non_recursive(folder, original, replacement, rename_dirs, writer, timestamp)
        changed_total += changed
        errors_total += errors

    return changed_total, errors_total, log_path

# --- CLI 진입점 ---
def main():
    parser = argparse.ArgumentParser(description="파일 및 선택적 디렉토리 이름 일괄 치환 (비재귀 기본)")
    parser.add_argument("original", help="변경될 문자열 (원문)")
    parser.add_argument("replacement", help="변경할 문자열 (대체문) — 빈 문자열 허용(삭제)")
    parser.add_argument("folder", nargs="?", default=".", help="대상 폴더(옵션). 없으면 현재 디렉토리")
    parser.add_argument("--rename-dirs", action="store_true", help="디렉토리 이름도 변경하려면 이 플래그 추가")
    parser.add_argument("--backup-log", default=None, help="로그 CSV 파일 경로 (기본 자동생성)")
    parser.add_argument("--verbose", action="store_true", help="상세 로그 출력")

    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")

    ok, msg = validate_inputs(args.original, args.replacement)
    if not ok:
        logging.error(msg)
        return

    folder = Path(args.folder).resolve()
    if not folder.exists() or not folder.is_dir():
        logging.error(f"대상 폴더가 존재하지 않거나 디렉토리가 아닙니다: {folder}")
        return

    if args.backup_log:
        log_path = Path(args.backup_log)
    else:
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = Path.cwd() / f"rename_log_{ts}.csv"

    logging.info(f"실행 대상 폴더: {folder}")
    logging.info(f"원문: '{args.original}' -> 대체: '{args.replacement}'")
    logging.info(f"디렉토리 이름도 변경: {'예' if args.rename_dirs else '아니오'}")
    logging.info(f"로그 파일: {log_path}")

    changed_count, errors, log_file = run_main(args.original, args.replacement, folder, args.rename_dirs, log_path)

    print(f"{changed_count} 개의 항목(파일/폴더)이 변경되었습니다.")
    logging.info(f"완료: 변경 {changed_count}개, 오류 {errors}개, 로그: {log_file}")

if __name__ == "__main__":
    main()