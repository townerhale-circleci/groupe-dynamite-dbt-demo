# Cursor MCP proof (code-safe, 90-second finish)

The Cursor CircleCI MCP is a rehearsed, timeboxed proof that the failure context
can reach the developer's IDE. It reads pipeline status, logs, tests, and
artifacts and, with operator approval, can request a workflow rerun. It is
**read-only to source code**: a human applies any fix. Never claim it edits code
or "self-heals" CI.

> Keep this segment under 90 seconds. MCP is Preview and deliberately
> non-load-bearing: if it is unavailable, use the verbal/visual check-down and
> continue to the verified promotion flow.

## The flow

1. **Retrieve the real invalid-cast failure in Cursor.** Ask the MCP for the
   failed workflow/job for
   `gh/townerhale-circleci/groupe-dynamite-dbt-demo`.
   - `▶` "Ravi, this is the same real failure you just saw, now inside Cursor."

2. **Read the failing job's logs / artifacts.** Have the MCP pull the failed
   job's evidence and identify `fct_invalid_cast_demo`, column
   `PARSED_AMOUNT`, and value `not_a_number`.
   - `▶` "It surfaces the model, column, and rejected value without the
     developer leaving the editor."

3. **Explain the failure.** State what failed and why, in plain terms, from the
   retrieved evidence.
   - `▶` "This is the assistant *reading* CI, not changing it. It's a faster path
     to the evidence, nothing more."

4. **Operator applies the prepared fix.** A human makes the code change / applies
   the prepared repair and commits it (for the scenarios, this is the
   fast-forward in [scenario-catalog.md](scenario-catalog.md)).
   - `▶` "The fix is a human commit. The MCP didn't touch the code."

5. **Explain rerun control.** MCP can request "Rerun from failed" when
   authorized. This is an explicit operator action, not an automatic retry.
   Reruns are at the job boundary; `dbt build` starts fresh. Do not trigger an
   extra rerun merely for this segment if the human fix already started a fresh
   pipeline.

6. **Confirm green via MCP.** Ask the MCP for the new pipeline's status to confirm
   the job recovered.
   - `▶` "The same backup loop closes it out: status back to green."

## What to say — and not say

**Do say:**
- "The same status, logs, artifacts, and operator-authorized rerun are available
  in Cursor."
- "A human applies fixes; the MCP never edits code."
- "MCP is Preview; the durable proof is the CircleCI workflow and its artifacts."

**Do not say:**
- ❌ "CircleCI/the MCP fixed the code."
- ❌ "It auto-remediates / self-heals the pipeline."
- ❌ Anything implying automatic reruns or automatic code changes.

## Boundaries

- Read-only with respect to your repository. It may request a CircleCI rerun,
  but it never changes source code.
- A vivid IDE finish after the artifact proof, not a prerequisite for merge
  safety or promotion.
- Verified today: MCP retrieval identified real failures, exposed the
  credentialed build evidence, and requested an operator-authorized
  rerun-from-failed. The rerun reproduced the error and completed guarded
  cleanup. It still never edits source code.
