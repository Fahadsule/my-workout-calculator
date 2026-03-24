#!/usr/bin/env python3
"""
Daily Life Tracker — logs directly to your SQLite database.
Usage: python3 daily_log.py [path/to/your.db]
       python3 daily_log.py --date 2025-01-15   (log for a specific date)
       python3 daily_log.py --view               (view recent entries)
       python3 daily_log.py --summary            (weekly summary)
"""

import sqlite3
import sys
import os
import argparse
from datetime import date, datetime, timedelta
from pathlib import Path

# ── ANSI colors ────────────────────────────────────────────────────────────────
R = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
C_GOLD = "\033[38;5;220m"
C_GREEN = "\033[38;5;114m"
C_BLUE = "\033[38;5;111m"
C_PURPLE = "\033[38;5;141m"
C_CORAL = "\033[38;5;209m"
C_TEAL = "\033[38;5;80m"
C_GRAY = "\033[38;5;245m"
C_RED = "\033[38;5;203m"
C_YELLOW = "\033[38;5;227m"
BG_DARK = "\033[48;5;235m"

def clr(text, *codes):
    return "".join(codes) + str(text) + R

def header(title, color=C_GOLD):
    w = 60
    bar = "─" * w
    print(f"\n{clr(bar, color)}")
    print(f"{clr(f'  {title}', BOLD, color)}")
    print(f"{clr(bar, color)}")

def section(title, color=C_BLUE):
    print(f"\n{clr('▸ ' + title, BOLD, color)}")
    print(f"{clr('  ' + '─' * (len(title) + 2), DIM, color)}")

def ask(prompt, default=None, cast=float, optional=True):
    """Prompt for a numeric value. Returns None if skipped."""
    hint = f" {clr(f'[{default}]', DIM, C_GRAY)}" if default is not None else ""
    skip_hint = f" {clr('(enter to skip)', DIM, C_GRAY)}" if optional else ""
    full_prompt = f"  {clr(prompt, C_TEAL)}{hint}{skip_hint}: "
    while True:
        try:
            raw = input(full_prompt).strip()
            if not raw:
                return default
            return cast(raw)
        except ValueError:
            print(clr(f"  ✗ Invalid value, try again.", C_RED))
        except (EOFError, KeyboardInterrupt):
            print()
            return default

def ask_int(prompt, default=None, optional=True):
    return ask(prompt, default=default, cast=int, optional=optional)

def ask_prayer(name, current=None):
    """Toggle prayer: y/n/1/0"""
    cur_str = f" {clr(f'[{'✓' if current else '✗'}]', DIM, C_GRAY)}" if current is not None else ""
    raw = input(f"  {clr(name, C_TEAL)}{cur_str} {clr('y/n', DIM, C_GRAY)}: ").strip().lower()
    if raw in ("y", "1", "yes"):
        return 1
    if raw in ("n", "0", "no"):
        return 0
    return current if current is not None else 0

def ask_bool(prompt, default=True):
    d = "Y/n" if default else "y/N"
    raw = input(f"  {clr(prompt, C_YELLOW)} [{d}]: ").strip().lower()
    if not raw:
        return default
    return raw in ("y", "yes", "1")

def progress_bar(value, max_val, width=20, color=C_GREEN):
    if max_val <= 0:
        return clr("─" * width, C_GRAY)
    ratio = min(value / max_val, 1.0)
    filled = int(ratio * width)
    bar = "█" * filled + "░" * (width - filled)
    pct = f"{ratio*100:.0f}%"
    return clr(bar, color) + clr(f" {pct}", DIM, C_GRAY)

# ── DB helpers ─────────────────────────────────────────────────────────────────

def get_db(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    # Ensure table exists with full schema
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS daily_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        w_date DATE NOT NULL UNIQUE,
        fajr_sunnah INTEGER DEFAULT 0,
        fajr INTEGER DEFAULT 0,
        dhuhr INTEGER DEFAULT 0,
        sunnah_dhuhr INTEGER DEFAULT 0,
        asr INTEGER DEFAULT 0,
        sunnah_asr INTEGER DEFAULT 0,
        maghrib INTEGER DEFAULT 0,
        sunnah_maghrib INTEGER DEFAULT 0,
        isha INTEGER DEFAULT 0,
        sunnah_isha INTEGER DEFAULT 0,
        tahajjud INTEGER DEFAULT 0,
        fardh_score REAL,
        water_taken REAL,
        workout_hours REAL,
        workout_intended REAL,
        sleep_hours REAL,
        sleep_intended REAL,
        calories_taken INTEGER,
        maintenance_calories INTEGER,
        bodyweight REAL,
        protein_taken_g REAL,
        calculus_hours REAL,
        calculus_intended REAL,
        stats_hours REAL,
        stats_intended REAL,
        quran_hours REAL,
        quran_intended REAL,
        quran_memorized REAL,
        python_hours REAL,
        python_intended REAL,
        general_finance_hours REAL,
        general_finance_intended REAL,
        project_time_hours REAL,
        project_time_intended REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        mood DECIMAL(4,2)
    );
    """)
    conn.commit()
    return conn


def load_entry(conn, w_date: str):
    row = conn.execute("SELECT * FROM daily_log WHERE w_date = ?", (w_date,)).fetchone()
    return dict(row) if row else {}


def upsert_entry(conn, data: dict):
    cols = ", ".join(data.keys())
    placeholders = ", ".join("?" for _ in data)
    updates = ", ".join(f"{k}=excluded.{k}" for k in data if k != "w_date")
    sql = f"""
    INSERT INTO daily_log ({cols}) VALUES ({placeholders})
    ON CONFLICT(w_date) DO UPDATE SET {updates}
    """
    conn.execute(sql, list(data.values()))
    conn.commit()


# ── Entry logging ──────────────────────────────────────────────────────────────

def log_entry(conn, target_date: str, existing: dict):
    is_update = bool(existing)
    action = "Updating" if is_update else "New entry for"
    header(f"📿  Daily Log  —  {action} {target_date}")

    data = {"w_date": target_date}

    # ── Prayers ────────────────────────────────────────────────────────────────
    section("Prayers", C_GOLD)
    fardh_prayers = ["fajr", "dhuhr", "asr", "maghrib", "isha"]
    sunnah_prayers = ["fajr_sunnah", "sunnah_dhuhr", "sunnah_asr", "sunnah_maghrib", "sunnah_isha", "tahajjud"]

    print(clr("\n  Fardh (obligatory):", BOLD))
    for p in fardh_prayers:
        data[p] = ask_prayer(p.capitalize(), existing.get(p))

    print(clr("\n  Sunnah / Voluntary:", BOLD))
    for p in sunnah_prayers:
        label = p.replace("_", " ").title()
        data[p] = ask_prayer(label, existing.get(p))

    fardh_done = sum(data[p] for p in fardh_prayers)
    data["fardh_score"] = round(fardh_done / len(fardh_prayers) * 100, 1)
    bar = progress_bar(fardh_done, len(fardh_prayers), color=C_GOLD)
    fs_label = f'{fardh_done}/{len(fardh_prayers)}'
    fs_pct = f'{data["fardh_score"]}%'
    print(f"\n  Fardh score: {clr(fs_label, BOLD, C_GOLD)}  {bar}  {clr(fs_pct, C_GOLD)}")

    # ── Mood ───────────────────────────────────────────────────────────────────
    section("Mood", C_PURPLE)
    print(clr("  Scale: 1.0 (terrible) → 10.0 (amazing)", DIM, C_GRAY))
    data["mood"] = ask("Mood today", default=existing.get("mood"), cast=float)

    # ── Health ─────────────────────────────────────────────────────────────────
    section("Health", C_GREEN)
    data["bodyweight"] = ask("Bodyweight (kg)", default=existing.get("bodyweight"))
    data["water_taken"] = ask("Water taken (liters)", default=existing.get("water_taken"))
    data["sleep_hours"] = ask("Sleep actual (hours)", default=existing.get("sleep_hours"))
    data["sleep_intended"] = ask("Sleep intended (hours)", default=existing.get("sleep_intended"))
    data["calories_taken"] = ask_int("Calories eaten", default=existing.get("calories_taken"))
    data["maintenance_calories"] = ask_int("Maintenance calories", default=existing.get("maintenance_calories"))
    data["protein_taken_g"] = ask("Protein (grams)", default=existing.get("protein_taken_g"))
    data["workout_hours"] = ask("Workout actual (hours)", default=existing.get("workout_hours"))
    data["workout_intended"] = ask("Workout intended (hours)", default=existing.get("workout_intended"))

    # ── Studies ────────────────────────────────────────────────────────────────
    section("Studies", C_BLUE)
    study_subjects = [
        ("calculus", "Calculus"),
        ("stats", "Statistics"),
        ("quran", "Quran"),
        ("python", "Python"),
    ]
    for key, label in study_subjects:
        print(clr(f"\n  {label}:", BOLD))
        data[f"{key}_hours"] = ask(f"{label} actual (hours)", default=existing.get(f"{key}_hours"))
        data[f"{key}_intended"] = ask(f"{label} intended (hours)", default=existing.get(f"{key}_intended"))
        if key == "quran":
            data["quran_memorized"] = ask("Quran memorized (pages/ayahs)", default=existing.get("quran_memorized"))

    # ── Finance & Projects ─────────────────────────────────────────────────────
    section("Finance & Projects", C_CORAL)
    data["general_finance_hours"] = ask("Finance actual (hours)", default=existing.get("general_finance_hours"))
    data["general_finance_intended"] = ask("Finance intended (hours)", default=existing.get("general_finance_intended"))
    data["project_time_hours"] = ask("Project actual (hours)", default=existing.get("project_time_hours"))
    data["project_time_intended"] = ask("Project intended (hours)", default=existing.get("project_time_intended"))

    # ── Confirm & Save ─────────────────────────────────────────────────────────
    print(f"\n{clr('─' * 60, C_GRAY)}")
    _print_summary(data)
    print()
    if ask_bool("Save this entry?", default=True):
        # Remove None values to avoid overwriting existing with NULL
        clean = {k: v for k, v in data.items() if v is not None}
        upsert_entry(conn, clean)
        print(clr(f"\n  ✓ Saved to database for {target_date}\n", BOLD, C_GREEN))
    else:
        print(clr("\n  ✗ Not saved.\n", C_RED))


def _print_summary(data: dict):
    header("Summary", C_TEAL)
    fardh = ["fajr", "dhuhr", "asr", "maghrib", "isha"]
    done = sum(data.get(p, 0) or 0 for p in fardh)
    print(f"  Prayers  {progress_bar(done, 5, color=C_GOLD)}  {done}/5 fardh")

    if data.get("sleep_hours") and data.get("sleep_intended"):
        s, si = data["sleep_hours"], data["sleep_intended"]
        print(f"  Sleep    {progress_bar(s, si, color=C_BLUE)}  {s}h / {si}h")

    if data.get("water_taken"):
        print(f"  Water    {progress_bar(data['water_taken'], 3.0, color=C_TEAL)}  {data['water_taken']}L")

    if data.get("calories_taken") and data.get("maintenance_calories"):
        cal, maint = data["calories_taken"], data["maintenance_calories"]
        diff = cal - maint
        sign = "+" if diff >= 0 else ""
        color = C_CORAL if diff > 200 else C_GREEN if diff < -200 else C_YELLOW
        print(f"  Calories {clr(f'{cal} kcal', BOLD)}  ({clr(f'{sign}{diff}', color)} vs maintenance)")

    study_keys = ["calculus", "stats", "quran", "python", "general_finance", "project_time"]
    total_h = sum((data.get(f"{k}_hours") or 0) for k in study_keys)
    total_i = sum((data.get(f"{k}_intended") or 0) for k in study_keys)
    if total_i > 0:
        print(f"  Study    {progress_bar(total_h, total_i, color=C_PURPLE)}  {total_h:.1f}h / {total_i:.1f}h")

    if data.get("mood"):
        m = data["mood"]
        color = C_GREEN if m >= 7 else C_YELLOW if m >= 4 else C_RED
        print(f"  Mood     {clr(f'{m}/10', BOLD, color)}")


# ── View / summary ─────────────────────────────────────────────────────────────

def view_recent(conn, days=7):
    header(f"📊  Recent {days} Days", C_TEAL)
    rows = conn.execute(
        "SELECT * FROM daily_log ORDER BY w_date DESC LIMIT ?", (days,)
    ).fetchall()
    if not rows:
        print(clr("  No entries found.", C_GRAY))
        return
    fardh = ["fajr", "dhuhr", "asr", "maghrib", "isha"]
    study_keys = ["calculus", "stats", "quran", "python", "general_finance", "project_time"]
    print(f"\n  {'Date':<12} {'Fardh':^8} {'Sleep':^8} {'Water':^7} {'Study':^8} {'Cal':^7} {'Mood':^6}")
    print(f"  {clr('─'*60, DIM, C_GRAY)}")
    for row in rows:
        r = dict(row)
        d = r["w_date"]
        fp = sum(r.get(p, 0) or 0 for p in fardh)
        sl = f"{r['sleep_hours'] or '─':>4}" if r.get("sleep_hours") else "  ─ "
        wa = f"{r['water_taken']:.1f}L" if r.get("water_taken") else "  ─  "
        th = sum((r.get(f"{k}_hours") or 0) for k in study_keys)
        ti = sum((r.get(f"{k}_intended") or 0) for k in study_keys)
        study_str = f"{th:.1f}/{ti:.1f}" if ti > 0 else f"{th:.1f}h"
        cal = str(r.get("calories_taken") or "─")
        mood_val = r.get("mood")
        mood = f"{mood_val:.1f}" if mood_val else "─"
        fp_color = C_GREEN if fp == 5 else C_YELLOW if fp >= 3 else C_RED
        print(f"  {clr(d, BOLD):<12} {clr(f'{fp}/5', fp_color):^8} {sl:^8} {wa:^7} {study_str:^8} {cal:^7} {mood:^6}")
    print()


def weekly_summary(conn):
    today = date.today()
    week_ago = today - timedelta(days=6)
    header(f"📈  Weekly Summary  ({week_ago} → {today})", C_PURPLE)

    rows = conn.execute(
        "SELECT * FROM daily_log WHERE w_date BETWEEN ? AND ? ORDER BY w_date",
        (str(week_ago), str(today))
    ).fetchall()
    if not rows:
        print(clr("  No entries for this week.", C_GRAY))
        return

    fardh = ["fajr", "dhuhr", "asr", "maghrib", "isha"]
    study_keys = ["calculus", "stats", "quran", "python", "general_finance", "project_time"]
    days_logged = len(rows)

    # Aggregates
    total_fardh = sum(sum(dict(r).get(p, 0) or 0 for p in fardh) for r in rows)
    max_fardh = days_logged * 5
    total_study = sum(sum((dict(r).get(f"{k}_hours") or 0) for k in study_keys) for r in rows)
    avg_sleep = sum((dict(r).get("sleep_hours") or 0) for r in rows) / days_logged
    avg_water = sum((dict(r).get("water_taken") or 0) for r in rows) / days_logged
    avg_mood = [dict(r).get("mood") for r in rows if dict(r).get("mood")]
    avg_mood_val = sum(avg_mood) / len(avg_mood) if avg_mood else None

    section("Overview", C_BLUE)
    print(f"  Days logged:    {clr(days_logged, BOLD)}/{min(7, (today - week_ago).days + 1)}")
    print(f"  Total fardh:    {progress_bar(total_fardh, max_fardh, color=C_GOLD)}  {total_fardh}/{max_fardh}")
    print(f"  Total study:    {clr(f'{total_study:.1f}h', BOLD, C_BLUE)}")
    print(f"  Avg sleep:      {clr(f'{avg_sleep:.1f}h', BOLD, C_TEAL)}")
    print(f"  Avg water:      {clr(f'{avg_water:.1f}L', BOLD, C_GREEN)}")
    if avg_mood_val:
        mood_color = C_GREEN if avg_mood_val >= 7 else C_YELLOW if avg_mood_val >= 4 else C_RED
        print(f"  Avg mood:       {clr(f'{avg_mood_val:.1f}/10', BOLD, mood_color)}")

    section("Study breakdown", C_PURPLE)
    labels = {"calculus": "Calculus", "stats": "Statistics", "quran": "Quran",
              "python": "Python", "general_finance": "Finance", "project_time": "Projects"}
    for key, label in labels.items():
        actual = sum((dict(r).get(f"{key}_hours") or 0) for r in rows)
        intended = sum((dict(r).get(f"{key}_intended") or 0) for r in rows)
        if actual > 0 or intended > 0:
            bar = progress_bar(actual, intended or actual, color=C_BLUE) if intended else clr("─" * 20, C_GRAY)
            print(f"  {label:<14} {bar}  {actual:.1f}h / {intended:.1f}h")
    print()


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Daily Life Tracker — logs to your SQLite database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("db", nargs="?", default="data/daily_log.db",
                        help="Path to SQLite database file (default: data/daily_log.db)")
    parser.add_argument("--date", "-d", default=str(date.today()),
                        help="Date to log (YYYY-MM-DD), default: today")
    parser.add_argument("--view", "-v", action="store_true",
                        help="View recent entries")
    parser.add_argument("--summary", "-s", action="store_true",
                        help="Show weekly summary")
    parser.add_argument("--days", type=int, default=7,
                        help="Number of recent days to show with --view")
    args = parser.parse_args()

    db_path = args.db
    print(clr(f"\n  Using database: {db_path}", DIM, C_GRAY))
    conn = get_db(db_path)

    if args.view:
        view_recent(conn, days=args.days)
        return

    if args.summary:
        weekly_summary(conn)
        return

    # Validate date
    try:
        datetime.strptime(args.date, "%Y-%m-%d")
    except ValueError:
        print(clr(f"  ✗ Invalid date: {args.date}. Use YYYY-MM-DD format.", C_RED))
        sys.exit(1)

    existing = load_entry(conn, args.date)
    if existing:
        print(clr(f"\n  Entry for {args.date} already exists. Updating...", C_YELLOW))

    try:
        log_entry(conn, args.date, existing)
    except KeyboardInterrupt:
        print(clr("\n\n  Interrupted. Nothing was saved.\n", C_GRAY))


if __name__ == "__main__":
    main()