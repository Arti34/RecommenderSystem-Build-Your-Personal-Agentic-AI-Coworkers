"""Optional schedulable command: from project root, python -m scripts.generate_daily --mode live"""
import argparse
from pathlib import Path
from backend.memory import get_profile, save_brief
from backend.workflows import DAILY_GRAPH


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["live", "sample"], default="live")
    args = parser.parse_args()
    mode = "live_rss" if args.mode == "live" else "sample_data"
    brief = DAILY_GRAPH.invoke({"profile": get_profile(), "mode": mode})["brief"]
    save_brief(brief)
    out = Path("local_data") / f"daily_brief_{brief.date}_{args.mode}.md"
    out.parent.mkdir(exist_ok=True)
    rows = [f"# Daily Tech Brief — {brief.date}", "", brief.note, ""]
    for i, a in enumerate(brief.articles, 1):
        rows.extend([f"## {i}. {a.title}", f"{a.source} | {a.published_date}", a.url,
                     a.summary, f"Why it matters: {a.relevance_reason}", ""])
    out.write_text("\n".join(rows), encoding="utf-8")
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
