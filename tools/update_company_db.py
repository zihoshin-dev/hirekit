#!/usr/bin/env python3
"""기업 DB 통합 갱신 — 모든 소스에서 최신 데이터 수집."""
import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
LOG_PATH = ROOT / "docs/demo/data/update_log.json"


def run_step(name: str, script: str, dry_run: bool, company: str | None = None) -> tuple[bool, str]:
    """단일 스텝 실행. (성공여부, 메시지) 반환."""
    script_path = ROOT / script
    if not script_path.exists():
        return False, f"{script} 파일 없음"

    cmd = [sys.executable, str(script_path)]
    if company:
        cmd += ["--company", company]

    print(f"\n[{name}] 시작...", flush=True)
    if dry_run:
        print(f"  [dry-run] {' '.join(cmd)}")
        return True, "dry-run skip"

    start = time.time()
    result = subprocess.run(cmd, capture_output=False, text=True)
    elapsed = time.time() - start

    if result.returncode == 0:
        print(f"  완료 ({elapsed:.1f}s)")
        return True, f"완료 ({elapsed:.1f}s)"
    else:
        print(f"  실패 (returncode={result.returncode})")
        return False, f"실패 (returncode={result.returncode})"


def run_sync(dry_run: bool) -> tuple[bool, str]:
    """meta.json 동기화 스텝."""
    script_path = ROOT / "tools/sync_meta_from_dart.py"
    if not script_path.exists():
        return False, "sync_meta_from_dart.py 파일 없음"

    print("\n[meta.json 동기화] 시작...", flush=True)
    if dry_run:
        print(f"  [dry-run] {sys.executable} {script_path}")
        return True, "dry-run skip"

    start = time.time()
    result = subprocess.run([sys.executable, str(script_path)], capture_output=False, text=True)
    elapsed = time.time() - start

    if result.returncode == 0:
        print(f"  완료 ({elapsed:.1f}s)")
        return True, f"완료 ({elapsed:.1f}s)"
    else:
        print(f"  실패 (returncode={result.returncode})")
        return False, f"실패 (returncode={result.returncode})"


STEPS = {
    "dart":   ("DART 기본정보",      "tools/build_company_db.py"),
    "market": ("KRX 시장데이터",     "tools/collect_market_data.py"),
    "ai":     ("GitHub AI 메트릭",   "tools/collect_ai_metrics.py"),
}


def main() -> None:
    parser = argparse.ArgumentParser(description="HireKit 기업 DB 갱신")
    parser.add_argument(
        "--source",
        choices=["all", "dart", "fsc", "nts", "market", "ai", "hf", "papers"],
        default="all",
        help="갱신할 소스 선택 (기본: all)",
    )
    parser.add_argument("--company", help="특정 기업만 갱신")
    parser.add_argument("--dry-run", action="store_true", help="실제 API 호출 없이 시뮬레이션")
    args = parser.parse_args()

    print("=" * 60)
    print(f"HireKit 기업 DB 갱신 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if args.dry_run:
        print("[DRY-RUN 모드]")
    if args.company:
        print(f"대상 기업: {args.company}")
    print("=" * 60)

    # 실행할 소스 결정
    if args.source == "all":
        targets = list(STEPS.keys())
    elif args.source in STEPS:
        targets = [args.source]
    else:
        # fsc, nts, hf, papers 는 현재 미구현 소스 — 알림 후 종료
        print(f"'{args.source}' 소스는 아직 구현되지 않았습니다.")
        sys.exit(0)

    sources_updated: list[str] = []
    errors: list[str] = []

    for key in targets:
        name, script = STEPS[key]
        ok, msg = run_step(name, script, args.dry_run, args.company)
        if ok:
            sources_updated.append(key)
        else:
            errors.append(f"{name}: {msg}")

    # meta.json 동기화 (all 또는 dart 실행 후)
    if "dart" in sources_updated or (args.source == "all"):
        ok, msg = run_sync(args.dry_run)
        if ok:
            sources_updated.append("sync")
        else:
            errors.append(f"meta.json 동기화: {msg}")

    # 갱신 이력 기록
    try:
        with open(ROOT / "docs/demo/data/meta.json") as f:
            companies = json.load(f)
        companies_count = len(companies)
    except Exception:
        companies_count = 0

    log: dict = {
        "updated_at": datetime.now().isoformat(),
        "source": args.source,
        "sources_updated": sources_updated,
        "companies_updated": companies_count,
        "dry_run": args.dry_run,
        "errors": errors,
    }

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not args.dry_run:
        with open(LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(log, f, ensure_ascii=False, indent=2)
        print(f"\n갱신 이력 저장: {LOG_PATH}")
    else:
        print(f"\n[dry-run] 갱신 이력 (저장 생략):")
        print(json.dumps(log, ensure_ascii=False, indent=2))

    print("\n" + "=" * 60)
    print(f"완료: {len(sources_updated)}개 소스 갱신, {len(errors)}개 오류")
    if errors:
        print("오류 목록:")
        for e in errors:
            print(f"  - {e}")
    print("=" * 60)

    sys.exit(1 if errors and not sources_updated else 0)


if __name__ == "__main__":
    main()
