# Fellow webhook duplicate debugger

Fellow suddenly fires two webhooks per event and your Make.com scenario runs
twice. This tells you **which of four causes** it is, because the fix is
different for each one.

Fellow delivers webhooks through **Svix**, which is why their support pointed you
at `svix-*` headers. Every delivery carries:

| Header | Meaning |
| --- | --- |
| `svix-id` | unique ID **per message**. Retries of one message reuse it. |
| `svix-timestamp` | Unix seconds when Svix sent it |
| `svix-signature` | `v1,<base64 HMAC-SHA256>`, space-delimited if multiple |

## The one question that decides everything

Compare the two `svix-id` values from a single double-fire.

The reason this works is Svix's data model. A **message** is the event; a
**message attempt** is one delivery of it to one endpoint. The `svix-id` header
carries the *message* id, so:

- a **retry** of a message reuses its id, and
- **one message fanned out to several endpoints keeps that same id** across all
  of them.

Which gives you:

```
same svix-id      -> ONE message. Either a retry, or fan-out to two
                     endpoints. Dedupe on svix-id and it stops.
different svix-id -> TWO messages were CREATED upstream. The event was
                     published twice. Dedupe on svix-id will NOT help,
                     because the ids genuinely differ.
```

That last point is the one most easily got wrong: two different ids is *not*
the fingerprint of "two endpoints subscribed". Two endpoints receiving one
message would both show the **same** id. Two different ids means something
minted two messages.

---

## Fastest path: no server needed

You do **not** have to build a receiving server. Make already logs every
incoming request — it just hides the headers until you ask for them.

1. Open your scenario, click the **Custom webhook** module → **Edit** the webhook.
2. Open **Show advanced settings**.
3. Set **Get request headers** to **Yes**.
4. Save, run the scenario, and let one meeting produce its duplicate.
5. Open **History**, find the two executions, and expand the webhook module's
   output bundle. `headers[]` now contains `svix-id`, `svix-timestamp`, and
   `svix-signature`.

Read the two `svix-id` values and jump to the matching case below. To have that
comparison done for you, paste both header objects into a file as a JSON array
and run:

```bash
python3 inspect_headers.py pair.json
```

which prints the differences and the verdict, no server needed.

> While you are in History, check the **number of executions**. If Make shows
> **two executions**, two HTTP requests arrived. If it shows **one execution**
> that processed twice, the duplication is inside your scenario (a loop, an
> iterator, or a second router branch) and Fellow is innocent.

---

## The four causes

### 1. Same `svix-id` twice → Svix is retrying

Fellow sent one message. Your endpoint did not return a `2xx` fast enough, so
Svix redelivered it. The `svix-timestamp` will differ between the two, and the
gap follows a backoff pattern (seconds, then minutes) rather than being
near-simultaneous.

**Why it usually starts "out of nowhere":** the scenario got slower. A new
module, a bigger AI-notes payload, or an API call that now takes longer pushes
you past the ack window, and Svix starts retrying something it never used to.

**Fix in Make:** make the webhook acknowledge immediately instead of after the
whole scenario finishes. In the webhook module's settings there is a response
behaviour option; set it so the webhook responds at once, or place a **Webhook
response** module returning status `200` as the *first* step after the trigger.
Then let the slow work continue behind it.

### 2. Different `svix-id`, identical payload → the event was published twice

Two separate messages were created for one event. Corroborating signs: an
**identical `svix-timestamp`** (both minted in the same second) and an
**identical `content-length`** (same payload size, which two genuinely
different events would rarely match on).

This splits into two sub-cases, and **each Svix endpoint has its own signing
secret**, which is what tells them apart. Capture both deliveries with the
logger, then:

```bash
python3 webhook_logger.py verify-secrets \
    --secret whsec_FIRST_ENDPOINT  --label first \
    --secret whsec_SECOND_ENDPOINT --label second
```

- **Both verify under the same secret** → one endpoint was fed two
  separately-created messages. The duplication happens upstream, before
  delivery. Not fixable from your side: escalate to Fellow with both message
  ids and ask why one event produced two messages.
- **Each verifies under a different secret** → two registered endpoints, each
  getting its own message. Delete the one you did not intend to keep. Fixable
  from your side.

If you only have one endpoint registered and only one signing secret, you are
already in the first case.

Fellow's own docs are the authority on where the endpoint list lives in the UI —
I could not reach `developers.fellow.ai` from this sandbox to quote the exact
menu path, so I am not going to invent one. Ask support to list the endpoints
registered for your workspace if you cannot find the screen; they can see them
directly. The **workspace audit log** they mentioned is genuinely useful here —
it records webhook creation, so it shows *when* a second endpoint was added,
which should line up with when the duplicates started.

### 3. Different `svix-id`, different payload → two event types

One endpoint subscribed to two event types that both fire when AI notes land —
for example a "notes ready" event and a "notes updated" event, where the AI
finishes writing and then a moment later something is revised. Both are real,
distinct events. Your scenario simply doesn't distinguish them.

**Fix:** either unsubscribe the event type you don't want on the Fellow
endpoint, or add a filter in Make immediately after the trigger that only
continues when the payload's `type` field matches the one you want.

### 4. Only one delivery logged, but Make still ran twice → it's Make

Check for a second scenario listening on the same webhook URL. A cloned
scenario that was never deactivated will happily process the same webhook.

---

## Using the logger in this repo

Use this when you want the raw truth, independent of Make — it also verifies
signatures, which Make's header dump won't do for you.

```bash
# confirm the tool itself works (19 checks, no network, no dependencies)
python3 webhook_logger.py selftest

# listen
python3 webhook_logger.py serve --port 8000 --secret whsec_YOUR_SIGNING_SECRET

# in another terminal, expose it and point the Fellow webhook at the tunnel URL
cloudflared tunnel --url http://localhost:8000
```

Python 3 standard library only — nothing to install.

Each delivery prints a verdict as it arrives:

```
  svix-id        : msg_2abc...
  signature      : valid (signature matched)
  event type     : meeting.ai_notes.ready
  ids in payload : meeting.id=mtg_9f21, channel_id=4471, notes.id=note_5510

  VERDICT: DUPLICATE
    byte-identical payload already arrived 0.3s ago as svix-id msg_bbb222,
    but this one is svix-id msg_ccc333. Fellow sent the same event as TWO
    separate messages -- you almost certainly have two webhook endpoints
    subscribed to it, or the same URL registered twice.
```

The four verdicts map onto the four causes above: `RETRY` → cause 1,
`DUPLICATE` → cause 2, `DISTINCT` → cause 3 (and it prints a field-by-field
diff so you can see *which* field differs), `FIRST` → nothing wrong.

Everything lands in `events.jsonl` — full payload and every header. Then:

```bash
python3 webhook_logger.py analyze
```

which groups the whole log and ends with a diagnosis naming the cause.

To attribute deliveries to endpoints by signing secret:

```bash
python3 webhook_logger.py verify-secrets --secret whsec_ONE --secret whsec_TWO
```

To rehearse before wiring up the real thing:

```bash
python3 simulate_deliveries.py --url http://localhost:8000 --secret whsec_...
```

This replays all four shapes so you can confirm the logger catches them.

### Signature verification

The logger implements Svix's scheme: HMAC-SHA256 over
`{svix-id}.{svix-timestamp}.{raw request body}`, keyed on the signing secret
with its `whsec_` prefix stripped and the remainder base64-decoded, compared
against each `v1,` entry in `svix-signature`.

The one trap: you must sign the **raw bytes** as received. If you parse the JSON
and re-serialize it before verifying, the bytes change and every signature
fails. The logger keeps the raw body for exactly this reason.

Signature verification also answers a question worth ruling out early: whether
both requests are actually from Fellow. If one fails verification or has no
`svix-*` headers at all, something else is posting to your URL.

---

## Worth doing regardless: make the automation idempotent

Retries are a normal part of webhook delivery, so any endpoint should tolerate
receiving the same event twice. A guard as the first step after the trigger
makes a duplicate harmless whatever its cause.

**Choose the key by which cause you have** — this matters, and the usual advice
gets it wrong for cause 2:

| Cause | Dedupe key |
| --- | --- |
| 1 (retry, same `svix-id`) | `svix-id` |
| 2 (published twice, different `svix-id`) | a **payload id** — the meeting or note id |
| 3 (two event types) | filter on `type` instead |

For cause 2, `svix-id` is useless: the two ids genuinely differ, so both would
pass the guard. Key on the meeting or note id instead.

Setup:

1. Add a **Data store** whose key is whichever field the table above selects.
2. First module after the trigger: **Data store → Add/replace a record**, using
   that key, with *overwrite disabled* so a repeat key errors.
3. Set that module's error handling to stop the route quietly on failure.

The first delivery writes the key and continues; the second fails to write and
stops. Give the store a short TTL (or a periodic cleanup) so a legitimate
later event for the same meeting isn't suppressed forever — a few minutes is
enough to absorb same-second duplicates.
