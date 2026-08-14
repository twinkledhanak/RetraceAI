"""Append an attempt to an existing upgrade session in Atlas — no curl needed.

Usage (from backend/):
    python scripts/remember.py s2 \
        --library vite --action downgrade --to-version 4.0.0 \
        --succeeded false --error-text "rolldown missing plugin"
"""

import argparse
import logging
import sys

from retraceai.memory import add_attempt_to_session

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def main() -> int:
    parser = argparse.ArgumentParser(description="Append an attempt to a session in Atlas.")
    parser.add_argument("session_id", help="sessionId of the document to update")
    parser.add_argument("--library", required=True)
    parser.add_argument("--action", required=True)
    parser.add_argument("--from-version")
    parser.add_argument("--to-version")
    parser.add_argument("--succeeded", type=lambda v: v.lower() == "true", default=True)
    parser.add_argument("--error-text")
    parser.add_argument("--notes")
    args = parser.parse_args()

    attempt = {
        "library": args.library,
        "action": args.action,
        "fromVersion": args.from_version,
        "toVersion": args.to_version,
        "succeeded": args.succeeded,
        "errorText": args.error_text,
        "notes": args.notes,
    }
    attempt = {k: v for k, v in attempt.items() if v is not None}

    doc = add_attempt_to_session(args.session_id, attempt)
    print(f"Updated document {doc['sessionId']}: attempts now has {len(doc['attempts'])} row(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
