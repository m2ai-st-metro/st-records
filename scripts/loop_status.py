#!/usr/bin/env python3
"""Snow-Town Loop Status Reporter.

Reads from SQLite (status-aware query layer) to report
the current state of the feedback loop.

Usage:
    python scripts/loop_status.py
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from contracts.store import ContractStore


def report_status() -> None:
    """Print feedback loop status report."""
    store = ContractStore()

    # Use query_* methods (SQLite) for status-aware data
    outcomes = store.query_outcomes(limit=10000)
    all_recs = store.query_recommendations(limit=10000)

    # Categorize recommendations by status and target
    pending_recs = store.query_recommendations(status="pending", limit=10000)
    applied_recs = store.query_recommendations(status="applied", limit=10000)
    persona_recs = [r for r in pending_recs if r.target_system == "persona"]
    claude_md_recs = [r for r in pending_recs if r.target_system == "claude_md"]
    pipeline_recs = [r for r in pending_recs if r.target_system == "pipeline"]

    # Outcome distribution
    outcome_counts: dict[str, int] = {}
    for o in outcomes:
        outcome_counts[o.outcome.value] = outcome_counts.get(o.outcome.value, 0) + 1

    # Oldest unprocessed items
    oldest_rec = None
    if pending_recs:
        oldest_rec = min(r.emitted_at for r in pending_recs)

    # Print report
    print("=" * 60)
    print("  Snow-Town Feedback Loop Status")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    print(f"\n  Outcome Records:           {len(outcomes)}")
    for outcome, count in sorted(outcome_counts.items()):
        print(f"    - {outcome}: {count}")

    print(f"\n  Improvement Recommendations: {len(all_recs)}")
    print(f"    - Pending (persona):     {len(persona_recs)}")
    print(f"    - Pending (claude_md):   {len(claude_md_recs)}")
    print(f"    - Pending (pipeline):    {len(pipeline_recs)}")
    print(f"    - Applied:               {len(applied_recs)}")

    if oldest_rec:
        age = datetime.now() - oldest_rec
        print(f"  Oldest Pending Rec:        {age.days}d {age.seconds // 3600}h ago")

    # Research signals
    all_signals = store.query_signals(limit=10000)
    signal_by_source: dict[str, int] = {}
    signal_by_relevance: dict[str, int] = {}
    for s in all_signals:
        signal_by_source[s.source.value] = signal_by_source.get(s.source.value, 0) + 1
        signal_by_relevance[s.relevance.value] = signal_by_relevance.get(s.relevance.value, 0) + 1

    print(f"\n  Research Signals:          {len(all_signals)}")
    for src, cnt in sorted(signal_by_source.items()):
        print(f"    - {src}: {cnt}")
    if signal_by_relevance:
        print("    By relevance:")
        for rel, cnt in sorted(signal_by_relevance.items()):
            print(f"      {rel}: {cnt}")

    # Research signal freshness
    if all_signals:
        newest_signal = max(s.emitted_at for s in all_signals)
        age = datetime.now() - newest_signal
        print(f"  Last Signal Received:      {age.days}d {age.seconds // 3600}h ago")

    # Health check
    print("\n  Health:")
    if not outcomes:
        print("    [!] No outcome records yet - run ideas through Metroplex pipeline")
    elif not all_recs:
        print("    [!] No recommendations yet - run Sky-Lynx analyzer")
    elif pending_recs:
        print(f"    [!] {len(pending_recs)} recommendations pending")
    else:
        print("    [OK] Loop is flowing")

    print("=" * 60)

    store.close()


if __name__ == "__main__":
    report_status()
