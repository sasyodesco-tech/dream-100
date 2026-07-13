# Dream 100

Stop building broad lead lists. This plugin sources a small, hand-picked batch
of *ideal-fit* dream clients — the ones you'd actually be excited to land —
fully profiled and ready for personalized outreach.

## What it does

Say **"help me build dream 100"** (or "find my dream 100", "dream 100
leads") and it will:

1. **Interview you once** about your ideal client — industry, offer, pain
   points, where they hang out online, red flags to avoid. It remembers this
   after the first run, so every future run skips straight to sourcing.
2. **Find a batch of 10** real, active candidates matching that profile.
3. **Verify every contact detail** — no guessed emails, no invented handles,
   no dormant accounts. Only what's confirmed live.
4. **Spot one concrete improvement** in each candidate's business — a real
   gap you could point to, not generic advice.
5. **Write a personalized outreach angle** for each lead, built around that
   improvement — ready to turn into a Loom video walkthrough.
6. **Deliver a formatted spreadsheet** with everything: name, platforms,
   contact info, the improvement found, and the outreach angle — plus a
   running database so repeat runs never duplicate a lead.

## Setup

Everything runs on free tools — no paid subscriptions required.

The only setup step: get a free **YouTube Data API v3** key (needed to verify
YouTube-based leads — subscriber counts, posting activity, etc.):

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project (or use an existing one).
3. Enable the **"YouTube Data API v3"** under APIs & Services.
4. Create an API key under Credentials.
5. In your workspace, create a file named `[C] api-keys.env` with:
   ```
   YOUTUBE_API_KEY=your-key-here
   ```

The free daily quota comfortably covers this workflow. If you skip this step,
the skill still works — it just falls back to verifying YouTube leads
manually instead of automatically.

If your niche lives on Instagram, LinkedIn, or elsewhere instead of YouTube,
no API key is needed at all — those platforms are verified via live page
checks.

## Requirements

- Python 3 (for the bundled verification/output scripts — installed by
  default in most environments)
- `openpyxl` Python package for the spreadsheet output (`pip install
  openpyxl` if not already present)

## Credit

Built by Salvatore Odesco — sharing this as free value. If you use it, I'd
love to see what you build.
