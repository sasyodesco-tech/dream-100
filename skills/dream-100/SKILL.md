---
name: dream-100
description: >
  Builds and iterates a "Dream 100" list — a small batch of extremely
  specific dream clients, fully profiled with contact info and a personalized
  outreach angle. Use when the user says: "help me build dream 100", "build my
  dream 100", "find my dream 100", "dream 100 leads", "aiutami a costruire la
  dream 100", "trovami i dream 100", or asks for more dream clients in an
  already-established niche.
---

# Dream 100 Skill

Finds a small, hand-picked batch (default 10) of ideal-fit clients — not a broad
lead list. Every lead gets: verified contact info across platforms, one concrete
improvement spotted in their business, and an outreach angle built around a Loom
video showing that improvement.

## Golden rules — the discipline that keeps this cheap and clean

1. **No guessed emails or handles.** Every contact detail must come from a live
   page or API response fetched during this run. Unresolvable in 2 attempts →
   drop the lead rather than guess.
2. **No stale leads.** If a platform exposes activity (YouTube uploads, recent
   posts), confirm it's within the last 6 months before including someone.
3. **No raw dumps, no per-lead tool calls.** Batch all per-lead verification
   through the bundled scripts (one compact line per candidate). Never paste
   raw API/page JSON or HTML into chat. Keep progress updates to one line.
4. **ICP is set once, then remembered.** The interview in Step 1 only runs the
   first time, or when the user explicitly says the profile needs updating.

## Files

`<root>` = this project's folder (the "Dream 100" workspace). State lives at
the root, next to `CLAUDE.md`:

- `[C] Dream 100 ICP Profile.md` — the confirmed ideal-client profile: industry,
  offer, pain points, where they live online, red flags/deal-breakers, default
  batch size. **Check for this file every run.** Missing → run Step 1. Present
  → skip straight to Step 2.
- `[dream100-lead-bank].csv` — dedup only. `Name,Instagram,YouTube,Email`;
  lowercase, handles without `@`. Create fresh (header-only) only if missing.
- `[C] Dream 100 Client Database.md` — full record, Markdown table, append-only
  (the user edits rows by hand).
- `[C] api-keys.env` — needs `YOUTUBE_API_KEY` for YouTube verification. Get a
  free key from the Google Cloud Console: create a project, enable the
  "YouTube Data API v3", then create an API key under Credentials — the free
  daily quota comfortably covers this workflow. Save it as
  `YOUTUBE_API_KEY=<key>` in this file. Missing/invalid key → the script exits
  with `API_ERROR` and Step 3 falls back to manual verification.
- **Bundled scripts** in `Source/scripts/` next to this file: `verify_leads.py`,
  `emit_outputs.py`. Tested — run them as-is, don't re-derive their logic
  inline. Interpreter is `python` on Windows, `python3` on POSIX.

## Step 1 — ICP setup (first run only)

Ask conversationally, a few at a time — not a wall of questions:

1. **Industry & offer** — what industry is the client in, what does the user
   offer them?
2. **Pain points** — if the user has them, use them. If not, help them find
   them (quick web research on the niche).
3. **Where they live online** — platforms, content types they engage with.
   Depends entirely on the niche; don't assume YouTube/Instagram if the niche
   points elsewhere (e.g. LinkedIn for B2B).
4. **Deal-breakers** — who NOT to find. Red flags to screen out.
5. **Batch size** — confirm default of 10 per run (spec default; adjustable).

Write the confirmed profile to `[C] Dream 100 ICP Profile.md`. This is what
makes every future run skip the interview.

## Step 2 — Harvest (wide and cheap)

Collect a raw pool of 2-3x the batch size (~20-30 candidates for a batch of 10)
before any per-lead work. Prefer list/directory pages and niche communities —
one result often yields many names. Dedup immediately against the lead bank
(normalize: lowercase, strip `@`/spaces); silent discard on match, spend
nothing verifying a name already in the bank.

Write survivors to `candidates.json` in the scratchpad:
`[{"name": "...", "platform": "youtube|instagram|linkedin|other", "handle": "@x or URL"}]`
— only include `handle` if actually seen on a live page or snippet.

## Step 3 — Verify (one script call for YouTube candidates)

```
python "<skill dir>/scripts/verify_leads.py" --candidates candidates.json \
  --env "<root>/[C] api-keys.env" --months 6
```

For YouTube candidates: prints one TSV line per candidate — canonical
`@handle`, subs, last upload, verdict, plus emails and link-in-bio URLs mined
from the channel description and last 5 video descriptions (most emails show
up free right here). `DROP_not_found` / `DROP_dormant` / `DROP_no_uploads` →
gone, zero further fetches.

For Instagram/LinkedIn/other candidates (no API available): verify manually —
a live page fetch or search snippet confirming the account is real and active
is enough. Same drop rule if it can't be confirmed in 2 attempts.

Script exits `API_ERROR` → fall back to one Bash loop over the YouTube
candidates: for each handle, `curl -s -H "Cookie: SOCS=CAI" -H "User-Agent:
Mozilla/5.0 ... Chrome/126.0 Safari/537.36" https://www.youtube.com/@[handle]/videos`,
grep `canonicalBaseUrl":"/@[^"]*` (handle), `"[0-9.,]+[KM]? subscribers"`,
`"[0-9]+ (second|minute|hour|day|week|month|year)s? ago"` (recency); print one
line per candidate, `sleep 1` between requests. Mention the fallback at
delivery.

## Step 4 — Business-gap research (Dream 100–specific, do this yourself)

For each surviving candidate, look at their public presence (site, recent
posts/videos, socials) and find ONE concrete, specific improvement
opportunity — something real, not generic ("post more"). This is the seed for
both the outreach angle and the Loom video topic. One compact note per lead —
no raw page dumps in chat.

## Step 5 — Outreach angle

3-4 sentences per lead referencing the actual gap found and what the Loom
video would walk through. No generic filler — if you can't point to something
specific, the lead isn't ready yet; do a bit more digging before writing it.

## Step 6 — Emit outputs (one script call)

Write the final batch to `leads.json` in the scratchpad — keys: `Name,
Industry, Platforms, Instagram, YouTube, Email, ImprovementFound,
OutreachAngle, ContactMethod, Fit` ("green"|"yellow"|"red" — ICP fit).

```
python "<skill dir>/scripts/emit_outputs.py" --leads leads.json --base "<root>"
```

Builds `[C] Dream 100 Leads - [YYYY-MM-DD].xlsx` (navy header, alternating
rows, green/yellow/red fit overlay, freeze B2), appends the client database
and the lead bank, prints a two-line summary. If it errors, fix `leads.json`,
 not the script.

## Step 7 — Deliver

Short message only: lead count, emails found vs N/A, one interesting
observation, new bank total, file link. Don't re-list leads in chat — the
sheet is the deliverable.

## Self-improvement

After a run, if you spot a better search strategy, a bug, or repeated
friction, edit this SKILL.md and/or the scripts directly — keep it lean, don't
let it re-bloat.
