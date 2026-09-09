#!/usr/bin/env python3
"""
Compare Svix header sets from two (or more) webhook deliveries and say what
the duplication actually is.

Feed it the header JSON that Make.com's execution history shows you once
"Get request headers" is enabled -- no server required.

Usage:
    python3 inspect_headers.py pair.json
    python3 inspect_headers.py a.json b.json

pair.json may be a JSON array of header objects, or several concatenated
JSON objects. Header names are matched case-insensitively.

Why svix-id is the pivot
------------------------
In Svix a *message* is the event, and message attempts are the per-endpoint
deliveries. One message fanned out to several endpoints keeps ONE message id,
and a retry of a message also reuses its id. So:

    same svix-id       -> one message, delivered more than once
                          (a retry, or a fan-out to two endpoints)
    different svix-id  -> two messages were CREATED upstream
                          (the event was published twice)

That distinction decides who can fix it, so it is what this script reports.
"""

import json
import sys
from datetime import datetime, timezone

RELEVANT = [
    "svix-id",
    "svix-timestamp",
    "svix-signature",
    "content-length",
    "content-type",
    "user-agent",
    "x-request-id",
    "cf-connecting-ip",
    "cf-ray",
]


def load_header_sets(paths):
    """Read header objects from the given files, tolerating a few shapes."""
    sets = []
    for path in paths:
        with open(path, encoding="utf-8") as handle:
            text = handle.read().strip()
        if not text:
            continue
        try:
            parsed = json.loads(text)
            found = parsed if isinstance(parsed, list) else [parsed]
        except json.JSONDecodeError:
            found = list(iter_concatenated(text))
        for item in found:
            if isinstance(item, dict):
                sets.append(lower_keys(item))
    return sets


def iter_concatenated(text):
    """Yield each top-level JSON object from concatenated/pasted objects."""
    decoder = json.JSONDecoder()
    index = 0
    while index < len(text):
        while index < len(text) and text[index] not in "{[":
            index += 1
        if index >= len(text):
            return
        try:
            obj, end = decoder.raw_decode(text, index)
        except json.JSONDecodeError:
            return
        yield obj
        index = end


def lower_keys(headers):
    out = {}
    for key, value in headers.items():
        out[str(key).lower()] = value
    # Make sometimes renders headers as [{name, value}, ...]
    if "name" in out and "value" in out and len(out) <= 3:
        return {str(out["name"]).lower(): out["value"]}
    return out


def normalize_header_list(sets):
    """Collapse Make's [{name,value}] rows back into one dict per delivery."""
    if all(len(s) == 1 for s in sets) and len(sets) > 2:
        merged = {}
        for item in sets:
            merged.update(item)
        return [merged]
    return sets


def common_prefix(a, b):
    count = 0
    for x, y in zip(a, b):
        if x != y:
            break
        count += 1
    return count


def show(sets):
    print("=" * 74)
    print("SVIX HEADER COMPARISON  --  %d deliveries" % len(sets))
    print("=" * 74)
    print("")

    labels = [chr(ord("A") + i) for i in range(len(sets))]
    for label, headers in zip(labels, sets):
        print("Delivery %s" % label)
        for key in RELEVANT:
            if key in headers:
                print("  %-18s %s" % (key, headers[key]))
        ts = headers.get("svix-timestamp")
        if ts and str(ts).isdigit():
            when = datetime.fromtimestamp(int(ts), timezone.utc).isoformat()
            print("  %-18s %s" % ("(sent at)", when))
        print("")


def verdict(sets):
    print("=" * 74)
    print("WHAT THIS TELLS US")
    print("=" * 74)
    print("")

    ids = [s.get("svix-id") for s in sets]
    stamps = [s.get("svix-timestamp") for s in sets]
    lengths = [s.get("content-length") for s in sets]
    sigs = [s.get("svix-signature") for s in sets]
    agents = [s.get("user-agent") for s in sets]

    missing = [i for i, v in enumerate(ids) if not v]
    if missing:
        print("  !! %d delivery/deliveries have NO svix-id. Those did not come from" % len(missing))
        print("     Fellow via Svix -- something else is posting to your URL.")
        print("")

    unique_ids = {i for i in ids if i}
    print("  svix-id        : %s" % ("ALL DIFFERENT" if len(unique_ids) == len(
        [i for i in ids if i]) and len(unique_ids) > 1 else "REPEATED"))
    print("  svix-timestamp : %s" % ("IDENTICAL" if len(set(stamps)) == 1 else "different"))
    print("  content-length : %s" % ("IDENTICAL" if len(set(lengths)) == 1 else "different"))
    print("  signature      : %s" % ("identical" if len(set(sigs)) == 1 else "different"))
    print("  user-agent     : %s" % ("identical" if len(set(agents)) == 1 else "different"))

    # How close together were the message ids minted?
    real_ids = [i for i in ids if i]
    if len(real_ids) >= 2:
        cores = [i[4:] if i.startswith("msg_") else i for i in real_ids]
        shared = min(common_prefix(cores[0], c) for c in cores[1:])
        print("  id similarity  : first %d characters shared -> minted %s apart" % (
            shared,
            "milliseconds" if shared >= 4 else "some time" if shared >= 2 else "far",
        ))
    print("")

    repeated_id = len(unique_ids) < len([i for i in ids if i])
    same_stamp = len(set(stamps)) == 1
    same_length = len(set(lengths)) == 1

    if repeated_id:
        print("  VERDICT: RETRY / FAN-OUT of ONE message.")
        print("")
        print("  The same svix-id arrived more than once. In Svix that is one")
        print("  message -- either redelivered because your endpoint did not ack")
        print("  in time, or fanned out to two endpoints that both point at your")
        print("  URL. Check whether the timestamps differ: a gap means a retry,")
        print("  the same second means fan-out to two endpoints.")
        print("")
        print("  GOOD NEWS: dedupe on svix-id in Make and this stops dead.")
        return

    if len(unique_ids) > 1 and same_stamp and same_length:
        print("  VERDICT: THE EVENT WAS PUBLISHED TWICE, upstream of delivery.")
        print("")
        print("  Two DIFFERENT svix-ids means two separate Svix messages were")
        print("  created. A single message keeps one id no matter how many")
        print("  endpoints it fans out to, and a retry reuses its id -- so this is")
        print("  neither a retry nor simple fan-out to two endpoints.")
        print("")
        print("  Same svix-timestamp and same content-length says both messages")
        print("  were created in the SAME SECOND carrying the SAME NUMBER OF BYTES.")
        print("  Two genuinely different events would almost never match on both.")
        print("")
        print("  So: something upstream emitted this one event twice.")
        print("")
        print("  IMPORTANT CONSEQUENCE: deduping on svix-id will NOT help you,")
        print("  because the two ids genuinely differ. You must dedupe on a")
        print("  payload field (the meeting or note id) instead.")
        print("")
        print("  Two sub-cases remain, and the signatures can tell them apart --")
        print("  see 'verify-secrets' in webhook_logger.py:")
        print("    (a) both signatures verify under the SAME signing secret")
        print("        -> one endpoint, fed two messages. Fellow-side duplicate")
        print("           publication. Only Fellow can fix it; escalate with both")
        print("           message ids.")
        print("    (b) each signature verifies under a DIFFERENT secret")
        print("        -> two registered endpoints, and a message is being minted")
        print("           per endpoint. Delete the duplicate endpoint and it stops.")
        return

    if len(unique_ids) > 1 and not same_length:
        print("  VERDICT: TWO DIFFERENT EVENTS.")
        print("")
        print("  Different ids and different payload sizes. These are probably two")
        print("  distinct event types (for example notes-created and notes-updated)")
        print("  that both fire when AI notes land. Compare the payloads' `type`")
        print("  field, then unsubscribe the one you do not want, or filter on")
        print("  `type` as the first step in Make.")
        return

    print("  VERDICT: two separate messages, but the timestamps differ.")
    print("")
    print("  Compare the payload `type` field to see whether these are two event")
    print("  types firing in sequence, or the same event published twice.")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__.strip())
    sets = normalize_header_list(load_header_sets(sys.argv[1:]))
    if len(sets) < 2:
        sys.exit("Need at least two header sets to compare; found %d." % len(sets))
    show(sets)
    verdict(sets)
    print("")


if __name__ == "__main__":
    main()
