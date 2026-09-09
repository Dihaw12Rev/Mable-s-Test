#!/usr/bin/env python3
"""
Fellow webhook debugger.

Logs every incoming webhook with its Svix headers, verifies the signature,
and classifies duplicates so you can tell WHERE a double-fire comes from.

Three outcomes it distinguishes:

  RETRY        same svix-id seen again
               -> Svix redelivered one message. Your endpoint didn't ack in
                  time or returned non-2xx. ONE event, delivered twice.

  DUPLICATE    different svix-id, byte-identical payload
               -> Fellow sent the same event as two separate messages.
                  Almost always two webhook endpoints subscribed to the same
                  event (or the same URL registered twice). TWO messages.

  DISTINCT     different svix-id, different payload
               -> Two genuinely different events. The diff printed alongside
                  shows which fields differ (event type, channel, note id),
                  which tells you which subscription to turn off.

Usage:
    python3 webhook_logger.py serve [--port 8000] [--secret whsec_...] [--log events.jsonl]
    python3 webhook_logger.py analyze [--log events.jsonl]
    python3 webhook_logger.py selftest
"""

import argparse
import base64
import hashlib
import hmac
import json
import os
import sys
import time
from collections import Counter, defaultdict, OrderedDict
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DEFAULT_LOG = "events.jsonl"
DEFAULT_PORT = 8000
# Svix's own tolerance for replay protection.
SIGNATURE_TOLERANCE_SECONDS = 5 * 60
# How far back to look when deciding whether a new message duplicates an old one.
CORRELATION_WINDOW_SECONDS = 300

SVIX_HEADERS = ("svix-id", "svix-timestamp", "svix-signature")


# --------------------------------------------------------------------------
# Signature verification (Svix scheme)
# --------------------------------------------------------------------------

def verify_signature(secret, svix_id, svix_timestamp, body, header_value):
    """Verify a Svix signature.

    Signed content is "{id}.{timestamp}.{raw body}". The secret is
    "whsec_" + base64 key material. Each signature in the header is
    "v1,<base64 hmac-sha256>", space delimited, and any one matching is
    enough -- multiple appear while a secret is being rotated.

    Returns (status, detail) where status is one of:
    "valid", "invalid", "skipped", "malformed".
    """
    if not secret:
        return "skipped", "no --secret passed"
    if not (svix_id and svix_timestamp and header_value):
        return "malformed", "missing one or more svix-* headers"

    key = secret
    if key.startswith("whsec_"):
        key = key[len("whsec_"):]
    try:
        key_bytes = base64.b64decode(key)
    except Exception:
        return "malformed", "secret is not valid base64 after the whsec_ prefix"

    signed = svix_id.encode() + b"." + svix_timestamp.encode() + b"." + body
    expected = base64.b64encode(
        hmac.new(key_bytes, signed, hashlib.sha256).digest()
    ).decode()

    presented = []
    for part in header_value.split():
        version, _, sig = part.partition(",")
        if version == "v1" and sig:
            presented.append(sig)
    if not presented:
        return "malformed", "no v1 signature found in svix-signature header"

    if any(hmac.compare_digest(expected, sig) for sig in presented):
        return "valid", check_timestamp_freshness(svix_timestamp)
    return "invalid", "no presented signature matched (wrong secret, or the body was re-serialized before verifying)"


def check_timestamp_freshness(svix_timestamp):
    try:
        sent = int(svix_timestamp)
    except (TypeError, ValueError):
        return "signature matched, but svix-timestamp is not an integer"
    age = time.time() - sent
    if abs(age) > SIGNATURE_TOLERANCE_SECONDS:
        return "signature matched, but timestamp is %.0fs old (outside Svix's %ds tolerance)" % (
            age, SIGNATURE_TOLERANCE_SECONDS
        )
    return "signature matched"


# --------------------------------------------------------------------------
# Payload inspection
# --------------------------------------------------------------------------

def flatten(obj, prefix=""):
    """Flatten JSON into {dotted.path: scalar} so two payloads can be diffed."""
    out = {}
    if isinstance(obj, dict):
        for key, value in obj.items():
            out.update(flatten(value, "%s.%s" % (prefix, key) if prefix else str(key)))
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            out.update(flatten(value, "%s[%d]" % (prefix, index)))
    else:
        out[prefix] = obj
    return out


def diff_payloads(left, right, limit=12):
    """Return human-readable differences between two decoded payloads."""
    flat_left, flat_right = flatten(left), flatten(right)
    lines = []
    for key in sorted(set(flat_left) | set(flat_right)):
        a, b = flat_left.get(key, "<absent>"), flat_right.get(key, "<absent>")
        if a != b:
            lines.append("%s: %r -> %r" % (key, a, b))
    if len(lines) > limit:
        hidden = len(lines) - limit
        lines = lines[:limit] + ["... and %d more differing field(s)" % hidden]
    return lines


def describe_event(payload):
    """Best-effort label for an event, without assuming Fellow's exact schema."""
    if not isinstance(payload, dict):
        return "<non-object payload>"
    for key in ("type", "event", "event_type", "eventType", "action"):
        value = payload.get(key)
        if isinstance(value, str):
            return value
    return "<no type field>"


def find_ids(payload):
    """Collect id-ish fields, which is what you group by to spot a double-fire."""
    found = {}
    for path, value in flatten(payload).items():
        leaf = path.split(".")[-1].split("[")[0].lower()
        if leaf in ("id", "guid", "uuid") or leaf.endswith("_id") or leaf.endswith("id"):
            if isinstance(value, (str, int)) and not isinstance(value, bool):
                found[path] = value
    return found


# --------------------------------------------------------------------------
# Correlation
# --------------------------------------------------------------------------

class Correlator:
    """Classifies each delivery against what it has already seen."""

    def __init__(self, window=CORRELATION_WINDOW_SECONDS):
        self.window = window
        self.by_svix_id = OrderedDict()
        self.recent = []  # (received_at, svix_id, body_sha, payload)

    def classify(self, received_at, svix_id, body_sha, payload):
        self._evict(received_at)

        if svix_id and svix_id in self.by_svix_id:
            first = self.by_svix_id[svix_id]
            return {
                "verdict": "RETRY",
                "detail": (
                    "svix-id %s was already delivered %.1fs ago. Svix redelivered "
                    "the SAME message -- one event, two HTTP requests. Your endpoint "
                    "did not return 2xx fast enough." % (svix_id, received_at - first["received_at"])
                ),
                "related_svix_id": svix_id,
            }

        for prior_at, prior_id, prior_sha, prior_payload in reversed(self.recent):
            gap = received_at - prior_at
            if gap > self.window:
                break
            if prior_sha == body_sha:
                return {
                    "verdict": "DUPLICATE",
                    "detail": (
                        "byte-identical payload already arrived %.1fs ago as svix-id %s, "
                        "but this one is svix-id %s. Fellow sent the same event as TWO "
                        "separate messages -- you almost certainly have two webhook "
                        "endpoints subscribed to it, or the same URL registered twice."
                        % (gap, prior_id, svix_id)
                    ),
                    "related_svix_id": prior_id,
                }

        for prior_at, prior_id, _, prior_payload in reversed(self.recent):
            gap = received_at - prior_at
            if gap > self.window:
                break
            shared = set(find_ids(payload).values()) & set(find_ids(prior_payload).values())
            if shared:
                return {
                    "verdict": "DISTINCT",
                    "detail": (
                        "different payload, but shares id(s) %s with svix-id %s from %.1fs "
                        "ago. Two DIFFERENT events about the same object -- check the diff "
                        "below and unsubscribe whichever event type you do not want."
                        % (", ".join(sorted(str(s) for s in shared)), prior_id, gap)
                    ),
                    "related_svix_id": prior_id,
                    "diff": diff_payloads(prior_payload, payload),
                }

        return {"verdict": "FIRST", "detail": "no prior correlated delivery in the window"}

    def record(self, received_at, svix_id, body_sha, payload):
        if svix_id:
            self.by_svix_id.setdefault(svix_id, {"received_at": received_at, "count": 0})
            self.by_svix_id[svix_id]["count"] += 1
        self.recent.append((received_at, svix_id, body_sha, payload))

    def _evict(self, now):
        cutoff = now - self.window
        self.recent = [row for row in self.recent if row[0] >= cutoff]


# --------------------------------------------------------------------------
# HTTP server
# --------------------------------------------------------------------------

def make_handler(log_path, secret, correlator):
    counter = Counter()

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"
        server_version = "FellowWebhookDebugger/1.0"

        def log_message(self, fmt, *args):
            pass  # we do our own logging

        def do_POST(self):
            received_at = time.time()
            length = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(length) if length else b""

            # Ack immediately. A slow ack is itself a cause of duplicate
            # deliveries, so never do analysis before responding. Content-Length
            # is computed, not hardcoded -- a truncated response reads as a
            # failed delivery and earns you a retry.
            ack = b'{"received":1}\n'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(ack)))
            self.end_headers()
            self.wfile.write(ack)
            self.wfile.flush()

            try:
                self.handle_delivery(received_at, body)
            except Exception as exc:  # never let analysis crash the listener
                print("  !! logging error: %r" % (exc,), flush=True)

        def handle_delivery(self, received_at, body):
            counter["total"] += 1
            headers = {k.lower(): v for k, v in self.headers.items()}
            svix_id = headers.get("svix-id")
            svix_timestamp = headers.get("svix-timestamp")
            svix_signature = headers.get("svix-signature")

            try:
                payload = json.loads(body.decode("utf-8"))
                parse_error = None
            except Exception as exc:
                payload, parse_error = None, str(exc)

            body_sha = hashlib.sha256(body).hexdigest()
            sig_status, sig_detail = verify_signature(
                secret, svix_id, svix_timestamp, body, svix_signature
            )

            classification = correlator.classify(
                received_at, svix_id, body_sha, payload if payload is not None else {}
            )
            correlator.record(
                received_at, svix_id, body_sha, payload if payload is not None else {}
            )
            counter[classification["verdict"]] += 1

            record = {
                "received_at": datetime.fromtimestamp(received_at, timezone.utc).isoformat(),
                "received_at_epoch": round(received_at, 3),
                "seq": counter["total"],
                "path": self.path,
                "remote_addr": self.client_address[0],
                "svix_id": svix_id,
                "svix_timestamp": svix_timestamp,
                "svix_signature": svix_signature,
                "signature_status": sig_status,
                "signature_detail": sig_detail,
                "event_type": describe_event(payload),
                "body_sha256": body_sha,
                "body_bytes": len(body),
                "verdict": classification["verdict"],
                "verdict_detail": classification["detail"],
                "related_svix_id": classification.get("related_svix_id"),
                "headers": headers,
                "payload": payload,
                "raw_body": None if payload is not None else body.decode("utf-8", "replace"),
                "parse_error": parse_error,
            }
            with open(log_path, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(record) + "\n")

            self.print_delivery(record, classification, counter)

        def print_delivery(self, record, classification, counter):
            print("", flush=True)
            print("=" * 78, flush=True)
            print("#%d  %s  %s" % (record["seq"], record["received_at"], record["path"]), flush=True)
            print("-" * 78, flush=True)
            print("  svix-id        : %s" % record["svix_id"], flush=True)
            print("  svix-timestamp : %s" % record["svix_timestamp"], flush=True)
            print("  signature      : %s (%s)" % (record["signature_status"], record["signature_detail"]), flush=True)
            print("  event type     : %s" % record["event_type"], flush=True)
            print("  body sha256    : %s (%d bytes)" % (record["body_sha256"][:16], record["body_bytes"]), flush=True)

            ids = find_ids(record["payload"] or {})
            if ids:
                shown = list(ids.items())[:6]
                print("  ids in payload : %s" % ", ".join("%s=%s" % kv for kv in shown), flush=True)

            print("", flush=True)
            print("  VERDICT: %s" % classification["verdict"], flush=True)
            for line in wrap(classification["detail"], 70):
                print("    %s" % line, flush=True)

            if classification.get("diff"):
                print("", flush=True)
                print("  differences vs the correlated delivery:", flush=True)
                for line in classification["diff"]:
                    print("    - %s" % line, flush=True)

            print("", flush=True)
            print("  running totals : %s" % format_counter(counter), flush=True)

        def do_GET(self):
            payload = json.dumps({
                "service": "fellow-webhook-debugger",
                "totals": dict(counter),
                "log": os.path.abspath(log_path),
            }).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    return Handler


def format_counter(counter):
    parts = ["%d total" % counter["total"]]
    for key in ("FIRST", "RETRY", "DUPLICATE", "DISTINCT"):
        if counter[key]:
            parts.append("%d %s" % (counter[key], key))
    return ", ".join(parts)


def wrap(text, width):
    words, lines, current = text.split(), [], ""
    for word in words:
        if current and len(current) + 1 + len(word) > width:
            lines.append(current)
            current = word
        else:
            current = "%s %s" % (current, word) if current else word
    if current:
        lines.append(current)
    return lines


def serve(args):
    log_path = args.log
    correlator = Correlator(window=args.window)
    handler = make_handler(log_path, args.secret, correlator)
    server = ThreadingHTTPServer(("0.0.0.0", args.port), handler)

    print("Fellow webhook debugger listening on 0.0.0.0:%d" % args.port, flush=True)
    print("Logging to %s" % os.path.abspath(log_path), flush=True)
    if args.secret:
        print("Signature verification: ON", flush=True)
    else:
        print("Signature verification: OFF (pass --secret whsec_... to enable)", flush=True)
    print("Correlation window: %ds" % args.window, flush=True)
    print("", flush=True)
    print("Expose it with a tunnel, then point the Fellow webhook at the tunnel URL:", flush=True)
    print("    cloudflared tunnel --url http://localhost:%d" % args.port, flush=True)
    print("    ngrok http %d" % args.port, flush=True)
    print("", flush=True)
    print("Waiting for deliveries. Ctrl-C to stop, then run:  %s analyze" % sys.argv[0], flush=True)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.", flush=True)
    finally:
        server.server_close()


# --------------------------------------------------------------------------
# Offline analysis
# --------------------------------------------------------------------------

def load_log(log_path):
    if not os.path.exists(log_path):
        sys.exit("No log at %s -- run 'serve' first and let some webhooks arrive." % log_path)
    records = []
    with open(log_path, encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except Exception as exc:
                print("skipping malformed log line %d: %s" % (line_no, exc), file=sys.stderr)
    return records


def analyze(args):
    records = load_log(args.log)
    if not records:
        sys.exit("Log %s is empty." % args.log)

    records.sort(key=lambda r: r.get("received_at_epoch") or 0)

    print("=" * 78)
    print("FELLOW WEBHOOK ANALYSIS  --  %d deliveries" % len(records))
    print("%s  ..  %s" % (records[0]["received_at"], records[-1]["received_at"]))
    print("=" * 78)

    by_svix_id = defaultdict(list)
    by_body = defaultdict(list)
    for record in records:
        by_svix_id[record.get("svix_id")].append(record)
        by_body[record.get("body_sha256")].append(record)

    unique_ids = len([k for k in by_svix_id if k])
    missing_ids = len(by_svix_id.get(None, []))

    print("")
    print("HEADLINE NUMBERS")
    print("  HTTP requests received      : %d" % len(records))
    print("  distinct svix-id values     : %d" % unique_ids)
    if missing_ids:
        print("  requests with NO svix-id    : %d  <-- not from Fellow/Svix" % missing_ids)
    print("  distinct payload bodies     : %d" % len([k for k in by_body if k]))

    sig_counts = Counter(r.get("signature_status") for r in records)
    print("  signature verification      : %s" % ", ".join(
        "%s=%d" % (k, v) for k, v in sorted(sig_counts.items())
    ))

    print("")
    print("EVENT TYPES SEEN")
    for event_type, count in Counter(r.get("event_type") for r in records).most_common():
        print("  %-40s %d" % (event_type, count))

    # -- retries: one svix-id delivered more than once
    retries = {k: v for k, v in by_svix_id.items() if k and len(v) > 1}
    print("")
    print("A) REDELIVERIES  (same svix-id more than once)")
    if not retries:
        print("  none. Every message was delivered exactly once, so nothing is being")
        print("  retried and your endpoint is acking properly.")
    else:
        print("  %d message(s) were delivered more than once:" % len(retries))
        for svix_id, group in list(retries.items())[:10]:
            gaps = [
                group[i + 1]["received_at_epoch"] - group[i]["received_at_epoch"]
                for i in range(len(group) - 1)
            ]
            print("    %s  x%d  gaps: %s" % (
                svix_id, len(group), ", ".join("%.1fs" % g for g in gaps)
            ))
        print("")
        print("  MEANING: Svix retried the same message. That is a receiver problem,")
        print("  not a Fellow problem -- your endpoint did not return 2xx in time.")
        print("  In Make, the fix is to have the webhook respond immediately instead")
        print("  of after the whole scenario finishes.")

    # -- duplicates: distinct svix-ids, identical body
    dup_clusters = {
        k: v for k, v in by_body.items()
        if k and len({r.get("svix_id") for r in v}) > 1
    }
    print("")
    print("B) DUPLICATE EVENTS  (different svix-id, identical payload)")
    if not dup_clusters:
        print("  none. No event was sent to you twice as two separate messages.")
    else:
        print("  %d event(s) arrived as multiple distinct messages:" % len(dup_clusters))
        for body_sha, group in list(dup_clusters.items())[:10]:
            # Collapse retries: count DISTINCT messages, not HTTP requests, so a
            # redelivered message is not double-counted as a duplicate event.
            first_per_id = {}
            for record in sorted(group, key=lambda r: r["received_at_epoch"]):
                first_per_id.setdefault(record.get("svix_id"), record)
            messages = sorted(first_per_id.values(), key=lambda r: r["received_at_epoch"])
            spread = messages[-1]["received_at_epoch"] - messages[0]["received_at_epoch"]
            print("    payload %s  x%d messages  within %.1fs  type=%s" % (
                body_sha[:16], len(messages), spread, messages[0].get("event_type")
            ))
            for record in messages:
                redeliveries = len([r for r in group if r.get("svix_id") == record.get("svix_id")])
                suffix = "  (+%d redelivery)" % (redeliveries - 1) if redeliveries > 1 else ""
                print("        svix-id %s  at %s%s" % (
                    record.get("svix_id"), record["received_at"], suffix
                ))
        print("")
        print("  MEANING: Fellow generated two separate messages carrying the same")
        print("  event. This is the signature of TWO WEBHOOK ENDPOINTS subscribed to")
        print("  the same event -- commonly the same Make URL registered twice, or a")
        print("  second endpoint someone added while testing.")
        print("  FIX: delete the duplicate endpoint in Fellow's webhook settings.")

    # -- distinct events sharing an object id
    print("")
    print("C) DIFFERENT EVENTS ABOUT THE SAME OBJECT")
    id_index = defaultdict(list)
    for record in records:
        for value in set(find_ids(record.get("payload") or {}).values()):
            id_index[value].append(record)

    interesting = []
    for value, group in id_index.items():
        types = {r.get("event_type") for r in group}
        bodies = {r.get("body_sha256") for r in group}
        if len(group) > 1 and len(bodies) > 1:
            interesting.append((value, group, types))

    if not interesting:
        print("  none found.")
    else:
        for value, group, types in interesting[:8]:
            group = sorted(group, key=lambda r: r["received_at_epoch"])
            spread = group[-1]["received_at_epoch"] - group[0]["received_at_epoch"]
            print("    object id %s -> %d deliveries within %.1fs, types: %s" % (
                value, len(group), spread, ", ".join(sorted(str(t) for t in types))
            ))
            first, last = group[0], group[-1]
            diff = diff_payloads(first.get("payload") or {}, last.get("payload") or {})
            for line in diff[:8]:
                print("        %s" % line)
        print("")
        print("  MEANING: if the types differ, ONE endpoint is subscribed to two event")
        print("  types that both fire when notes land (for example a 'created' and an")
        print("  'updated' event). Your Make scenario runs on both.")
        print("  FIX: in the Fellow webhook endpoint, unsubscribe the event type you")
        print("  do not want, or filter on the payload's type field in Make.")

    print("")
    print("=" * 78)
    print("DIAGNOSIS")
    print("=" * 78)
    if retries and not dup_clusters:
        print("  Your duplicates are RETRIES. Fellow fired once; your endpoint failed")
        print("  to ack in time and Svix redelivered. Fix the receiver, not Fellow.")
    elif dup_clusters and not retries:
        print("  Your duplicates are TWO SUBSCRIPTIONS. Fellow is sending the same")
        print("  event twice as two messages. Delete the extra webhook endpoint.")
    elif dup_clusters and retries:
        print("  You have BOTH problems: an extra subscription AND retries. Remove the")
        print("  duplicate endpoint first, then fix the ack timing.")
    elif interesting:
        print("  No true duplicates. You are receiving two DIFFERENT events per meeting.")
        print("  Narrow the subscribed event types, or filter on type in Make.")
    else:
        print("  Only one delivery per event in this log. If Make still ran twice, the")
        print("  duplication is inside Make -- check for two scenarios sharing this")
        print("  webhook, or a second trigger in the same scenario.")
    print("")


# --------------------------------------------------------------------------
# Self test
# --------------------------------------------------------------------------

def selftest(args):
    failures = []

    def check(name, condition, detail=""):
        if condition:
            print("  PASS  %s" % name)
        else:
            print("  FAIL  %s %s" % (name, detail))
            failures.append(name)

    print("Signature verification")
    secret = "whsec_" + base64.b64encode(b"super-secret-key-material").decode()
    body = b'{"type":"note.published","note":{"id":42}}'
    svix_id, svix_timestamp = "msg_2abc", str(int(time.time()))
    key = base64.b64decode(secret[len("whsec_"):])
    good = base64.b64encode(hmac.new(
        key, svix_id.encode() + b"." + svix_timestamp.encode() + b"." + body, hashlib.sha256
    ).digest()).decode()

    status, _ = verify_signature(secret, svix_id, svix_timestamp, body, "v1," + good)
    check("accepts a correct signature", status == "valid", "(got %s)" % status)

    status, _ = verify_signature(secret, svix_id, svix_timestamp, body, "v1,AAAA")
    check("rejects a wrong signature", status == "invalid", "(got %s)" % status)

    status, _ = verify_signature(secret, svix_id, svix_timestamp, body, "v1,AAAA v1," + good)
    check("accepts during secret rotation", status == "valid", "(got %s)" % status)

    status, _ = verify_signature(secret, svix_id, svix_timestamp, body + b" ", "v1," + good)
    check("rejects a tampered body", status == "invalid", "(got %s)" % status)

    status, _ = verify_signature(None, svix_id, svix_timestamp, body, "v1," + good)
    check("skips when no secret given", status == "skipped", "(got %s)" % status)

    status, _ = verify_signature(secret, svix_id, svix_timestamp, body, None)
    check("flags a missing signature header", status == "malformed", "(got %s)" % status)

    _, detail = verify_signature(
        secret,
        svix_id,
        svix_timestamp,
        body,
        "v1," + base64.b64encode(hmac.new(
            key, svix_id.encode() + b"." + svix_timestamp.encode() + b"." + body, hashlib.sha256
        ).digest()).decode(),
    )
    check("reports freshness on success", "signature matched" in detail, "(got %r)" % detail)

    print("Duplicate classification")
    now = time.time()
    corr = Correlator()
    payload_a = {"type": "note.published", "note": {"id": 42}}
    payload_b = {"type": "note.updated", "note": {"id": 42}}

    result = corr.classify(now, "msg_1", "sha_a", payload_a)
    check("first delivery is FIRST", result["verdict"] == "FIRST", "(got %s)" % result["verdict"])
    corr.record(now, "msg_1", "sha_a", payload_a)

    result = corr.classify(now + 1, "msg_1", "sha_a", payload_a)
    check("same svix-id is RETRY", result["verdict"] == "RETRY", "(got %s)" % result["verdict"])

    corr2 = Correlator()
    corr2.record(now, "msg_1", "sha_a", payload_a)
    result = corr2.classify(now + 2, "msg_2", "sha_a", payload_a)
    check("new id + same body is DUPLICATE", result["verdict"] == "DUPLICATE", "(got %s)" % result["verdict"])

    corr3 = Correlator()
    corr3.record(now, "msg_1", "sha_a", payload_a)
    result = corr3.classify(now + 3, "msg_2", "sha_b", payload_b)
    check("new id + new body is DISTINCT", result["verdict"] == "DISTINCT", "(got %s)" % result["verdict"])
    check("DISTINCT carries a diff", bool(result.get("diff")), "(got %r)" % result.get("diff"))

    corr4 = Correlator(window=10)
    corr4.record(now - 3600, "msg_old", "sha_a", payload_a)
    result = corr4.classify(now, "msg_new", "sha_a", payload_a)
    check("outside the window is FIRST", result["verdict"] == "FIRST", "(got %s)" % result["verdict"])

    print("Payload helpers")
    check("describe_event reads type", describe_event(payload_a) == "note.published")
    check("describe_event tolerates junk", describe_event(None) == "<non-object payload>")
    check("describe_event handles no type", describe_event({"a": 1}) == "<no type field>")
    ids = find_ids({"note": {"id": 42}, "channel_id": 7, "name": "x"})
    check("find_ids finds nested ids", set(ids.values()) == {42, 7}, "(got %r)" % ids)
    diff = diff_payloads(payload_a, payload_b)
    check("diff_payloads isolates the change", len(diff) == 1 and "type" in diff[0], "(got %r)" % diff)
    check("flatten walks lists", flatten({"a": [{"b": 1}]}) == {"a[0].b": 1})

    print("")
    if failures:
        print("%d test(s) FAILED: %s" % (len(failures), ", ".join(failures)))
        return 1
    print("All tests passed.")
    return 0


# --------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Log and classify Fellow webhook deliveries to find duplicates."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_serve = sub.add_parser("serve", help="listen for webhooks and log them")
    p_serve.add_argument("--port", type=int, default=DEFAULT_PORT)
    p_serve.add_argument("--log", default=DEFAULT_LOG)
    p_serve.add_argument("--secret", default=os.environ.get("FELLOW_WEBHOOK_SECRET"),
                         help="Svix signing secret (whsec_...). Defaults to $FELLOW_WEBHOOK_SECRET.")
    p_serve.add_argument("--window", type=int, default=CORRELATION_WINDOW_SECONDS,
                         help="seconds to correlate deliveries across (default %d)" % CORRELATION_WINDOW_SECONDS)
    p_serve.set_defaults(func=serve)

    p_analyze = sub.add_parser("analyze", help="summarize a log and diagnose the cause")
    p_analyze.add_argument("--log", default=DEFAULT_LOG)
    p_analyze.set_defaults(func=analyze)

    p_selftest = sub.add_parser("selftest", help="verify this tool works")
    p_selftest.set_defaults(func=selftest)

    args = parser.parse_args()
    sys.exit(args.func(args) or 0)


if __name__ == "__main__":
    main()
