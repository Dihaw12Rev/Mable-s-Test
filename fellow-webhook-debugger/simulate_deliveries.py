#!/usr/bin/env python3
"""
Send fake Fellow-style webhook deliveries at a running webhook_logger, so you
can confirm the logger works before pointing the real Fellow webhook at it.

Reproduces all three duplicate shapes:
    retry      one message delivered twice (same svix-id)
    duplicate  one event sent as two messages (two endpoints)
    distinct   two different events about the same meeting

Usage:
    python3 simulate_deliveries.py --url http://localhost:8000 [--secret whsec_...]
"""

import argparse
import base64
import hashlib
import hmac
import json
import time
import urllib.request


def sign(secret, svix_id, timestamp, body):
    key = secret[len("whsec_"):] if secret.startswith("whsec_") else secret
    digest = hmac.new(
        base64.b64decode(key),
        svix_id.encode() + b"." + str(timestamp).encode() + b"." + body,
        hashlib.sha256,
    ).digest()
    return "v1," + base64.b64encode(digest).decode()


def deliver(url, svix_id, payload, secret=None, timestamp=None):
    body = json.dumps(payload).encode()
    timestamp = timestamp or int(time.time())
    headers = {
        "Content-Type": "application/json",
        "svix-id": svix_id,
        "svix-timestamp": str(timestamp),
        "user-agent": "Svix-Webhooks/1.0",
    }
    if secret:
        headers["svix-signature"] = sign(secret, svix_id, timestamp, body)
    else:
        headers["svix-signature"] = "v1,unsigned-simulation"

    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=10) as response:
        return response.status


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000/fellow")
    parser.add_argument("--secret")
    args = parser.parse_args()

    notes_ready = {
        "type": "meeting.ai_notes.ready",
        "meeting": {"id": "mtg_9f21", "title": "Weekly Revenue Sync"},
        "channel_id": 4471,
        "notes": {"id": "note_5510", "summary": "Discussed Q3 pipeline."},
    }
    notes_updated = {
        "type": "meeting.ai_notes.updated",
        "meeting": {"id": "mtg_9f21", "title": "Weekly Revenue Sync"},
        "channel_id": 4471,
        "notes": {"id": "note_5510", "summary": "Discussed Q3 pipeline. Added owners."},
    }

    print("1. normal single delivery")
    deliver(args.url, "msg_aaa111", notes_ready, args.secret)
    time.sleep(0.4)

    print("2. RETRY -- same svix-id delivered again")
    deliver(args.url, "msg_aaa111", notes_ready, args.secret)
    time.sleep(0.4)

    print("3. DUPLICATE -- identical payload, new svix-id (two endpoints)")
    other = dict(notes_ready, meeting={"id": "mtg_7c04", "title": "Design Review"})
    deliver(args.url, "msg_bbb222", other, args.secret)
    time.sleep(0.3)
    deliver(args.url, "msg_ccc333", other, args.secret)
    time.sleep(0.4)

    print("4. DISTINCT -- two different event types, same meeting")
    deliver(args.url, "msg_ddd444", notes_updated, args.secret)
    time.sleep(0.3)

    print("5. bad signature")
    body = json.dumps(notes_ready).encode()
    request = urllib.request.Request(
        args.url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "svix-id": "msg_eee555",
            "svix-timestamp": str(int(time.time())),
            "svix-signature": "v1,d29uZ3NpZ25hdHVyZQ==",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        response.read()

    print("\nDone. Now run:  python3 webhook_logger.py analyze")


if __name__ == "__main__":
    main()
