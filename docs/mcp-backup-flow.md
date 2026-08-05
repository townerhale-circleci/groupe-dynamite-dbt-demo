# MCP backup flow (code-safe, after the core demo)

The Cursor CircleCI MCP is a **backup**, used **after** the three core moments —
or if the CircleCI web UI is unavailable — to read pipeline status, logs, and
artifacts and, with operator approval, request a workflow rerun. It is
**read-only to your code**: a human applies any fix. Never present it as the
main story, and never claim it edits code or "self-heals" CI.

> Only run this segment if there's time and interest after the core demo, or as a
> fallback when the CircleCI UI is down (see
> [recovery-fallback.md](recovery-fallback.md) §3).

## The flow

1. **Retrieve status in Cursor.** Ask the MCP for the project's recent pipelines
   and the status of the relevant workflow/jobs for
   `gh/townerhale-circleci/groupe-dynamite-dbt-demo`.
   - `▶` "Instead of the CircleCI web UI, I'm reading the same pipeline status
     from Cursor via the CircleCI MCP."

2. **Read the failing job's logs / artifacts.** Have the MCP pull the failed
   job's log output and its stored artifacts (`run_results.json`, `logs/`).
   - This is exactly how the rehearsal identified `Customer_Lifetime_Value.sql`
     as the offending uppercase model (see
     [rehearsal-status.md](rehearsal-status.md)).
   - `▶` "It surfaces the failing node and the reason — the same evidence the
     artifacts show — without me leaving the editor."

3. **Explain the failure.** State what failed and why, in plain terms, from the
   retrieved evidence.
   - `▶` "This is the assistant *reading* CI, not changing it. It's a faster path
     to the evidence, nothing more."

4. **Operator applies the prepared fix.** A human makes the code change / applies
   the prepared repair and commits it (for the scenarios, this is the
   fast-forward in [scenario-catalog.md](scenario-catalog.md)).
   - `▶` "The fix is a human commit. The MCP didn't touch the code."

5. **Rerun.** After the human pushes the fix, use the CircleCI MCP rerun action
   if it is authorized, or use "Rerun from failed" in CircleCI. This is an
   explicit operator action, not an automatic retry. Reruns are at the job
   boundary; `dbt build` starts fresh.

6. **Confirm green via MCP.** Ask the MCP for the new pipeline's status to confirm
   the job recovered.
   - `▶` "The same backup loop closes it out: status back to green."

## What to say — and not say

**Do say:**
- "Backup for status, logs, artifacts, and an operator-authorized rerun."
- "A human applies fixes; the MCP never edits code."
- "Useful when the CircleCI UI is unavailable, or to pull evidence fast."

**Do not say:**
- ❌ "CircleCI/the MCP fixed the code."
- ❌ "It auto-remediates / self-heals the pipeline."
- ❌ Anything implying automatic reruns or automatic code changes.

## Boundaries

- Read-only with respect to your repository. It may request a CircleCI rerun,
  but it never changes source code.
- Not a substitute for the CircleCI UI in the core demo — it's the fallback.
- Verified today: MCP retrieval **identified the failing model** from a real
  pipeline. Retrieving a *credentialed failed build's* artifacts end-to-end is
  **unverified** (credentialed jobs haven't run live) — see
  [rehearsal-status.md](rehearsal-status.md). Don't over-claim.
