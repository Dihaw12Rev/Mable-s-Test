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

Compare the two `svix-id` values from a single double-fire:

```
same svix-id      -> ONE event, delivered twice.  Receiver problem (retry).
different svix-id -> TWO messages were created.   Sender-side config problem.
```

Everything below hangs off that.

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

Read the two `svix-id` values and jump to the matching case below.

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

### 2. Different `svix-id`, identical payload → two subscriptions

Fellow created two separate messages carrying the same event. That means the
event is subscribed twice. In practice:

- the same Make URL registered as **two webhook endpoints** in Fellow, or
- a **second endpoint** someone added while testing and never removed.

These arrive near-simultaneously (well under a second apart), which is the
tell-tale difference from a retry.

**Fix:** delete the extra endpoint in Fellow's webhook settings. Fellow's own
docs are the authority on where that lives in the UI — I could not reach
`developers.fellow.ai` from this sandbox to quote the exact menu path, so I am
not going to invent one. Ask support to list the endpoints registered for your
workspace if you cannot find the screen; they can see them directly. The
**workspace audit log** they mentioned is genuinely useful here — it records
webhook creation, so it will show *when* a second endpoint was added, which
should line up with when the duplicates started.

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

Even after you find the cause, retries are a normal part of webhook delivery —
any endpoint should tolerate receiving the same message twice. Make this your
scenario's first two steps and a duplicate becomes harmless:

1. Add a **Data store** with `svix-id` as its key.
2. First module after the trigger: **Data store → Add/replace a record**, key
   `svix-id`, with *overwrite disabled* so a repeat key errors.
3. Set that module's error handling to stop the route quietly on failure.

The first delivery writes the key and continues; a repeat of the same `svix-id`
fails to write and stops. Note this only stops **cause 1** — two distinct
messages have two distinct IDs, so causes 2 and 3 still need their config fixed.
To guard those too, key the store on a payload field instead (the meeting or
notes ID) with a short TTL.
