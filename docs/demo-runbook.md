# 15-minute demo runbook

Exact, minute-marked script for the live demo. Three moments:

1. **Blocked unsafe PR** — an uppercase model name is caught by an offline gate
   *before* any Snowflake credential is used.
2. **Actionable failure with artifacts** — a real dbt/Snowflake build failure,
   read from `run_results.json` + `logs/`, fixed by a human, rerun to green.
3. **One branch, main → DEV → manual approval → PROD.**

> **Read first:** [rehearsal-status.md](rehearsal-status.md). Moments 2 and 3
> require a populated `snowflake-dbt-demo` context and a live Snowflake; both are
> **unverified** until the [preflight](preflight-checklist.md) passes. If
> preflight did not pass, run the demo in the degraded form noted in each
> moment's **Stop condition**, and be honest about what is live vs. narrated.

**Conventions in this script**
- `▶` = narration (what you say). `⌨` = command you run. `🖱` = UI click.
- Commands assume you are at the repo root with `uv sync` already done.
- Times are cumulative target marks; keep each moment inside its window.
- Never paste secrets. `DBT_SCHEMA` and credentials are set by CI, not by you.

---

## 0:00 – 1:30 — Frame the environment

- `▶` "This is a dbt Core + Snowflake pipeline prototype for Groupe Dynamite's
  planned move from dbt Cloud. Every pull request runs offline gates with **no** database
  credentials, then a real Snowflake build into a throwaway per-PR schema. Merges
  to `main` build DEV, pause for a human approval, then build PROD."
- `🖱` Show [architecture.md](architecture.md) diagram for ~15 seconds. Point at
  the credential boundary: "The three green jobs never see a credential."
- `▶` "I'll show three things: an unsafe PR getting blocked before it can touch
  Snowflake, a real failure that's actionable from artifacts, and a promotion to
  PROD gated by a human."

**Mini-close (say it):** "So: safety before credentials, evidence on failure,
and a human in front of PROD. Let's watch it happen."

---

## 1:30 – 5:00 — Moment 1: Blocked unsafe PR (uppercase model)

Scenario branch: `demo/fail-uppercase-model` (PR #3). It adds an **uppercase**
model file (`Customer_Lifetime_Value.sql`). The `validate-model-names` offline
gate fails on it — before the context is ever attached.

- `🖱` Open PR #3 in GitHub. Point at the changed file name in the **Files
  changed** tab: "`Customer_Lifetime_Value.sql` — uppercase, not our convention."
- `🖱` Open the CircleCI `pr` pipeline for this branch (Checks tab → CircleCI, or
  the CircleCI project page).
- `▶` "Look at the order. The offline jobs run first with no context.
  `validate-model-names` is **red**." `🖱` Click into `validate-model-names`.
- `🖱` Show the failing step output — it lists the invalid filename and exits 1:
  "Invalid dbt model filenames (must be snake_case): … `Customer_Lifetime_Value.sql`."
- `▶` "Two things matter. One: this failed **without any Snowflake credential** —
  the context isn't attached to offline jobs, so an unsafe change can't reach the
  warehouse. Two: this red check is the exact signal a required-status
  branch-protection rule would key off of in an entitled customer organization."
- `▶` "This public demo repo has strict required checks on `main`; we verified
  GitHub reports a PR as `BLOCKED` while a required CircleCI check is red. Before
  the live demo, retarget this scenario PR from `feature/build-demo` to `main`
  so the same protection applies here." (See
  [scenario-catalog.md](scenario-catalog.md) → "Base retargeting".)

**Optional 30s repair preview:** `🖱` Show that `demo/fix-uppercase-model` renames
the file to `customer_lifetime_value.sql`. Don't merge; the point is the block.

**Mini-close:** "Unsafe change, caught early, no credentials spent. That's the
cheap failure we want."

**Stop condition:** If CircleCI status isn't showing on the PR, open the pipeline
directly from the CircleCI project page (`gh/townerhale-circleci/groupe-dynamite-dbt-demo`)
and narrate from there. If CircleCI is unreachable, run the gate locally instead:
`⌨ uv run python scripts/validate_model_names.py models` (it exits 1 and names the
file). Do **not** claim the PR was auto-blocked — describe it as the failing check.

---

## 5:00 – 10:00 — Moment 2: Actionable failure with artifacts (invalid cast)

Scenario branch: `demo/fail-invalid-cast` (PR #4). Offline gates pass; the real
`dbt-pr-build` fails at Snowflake on a bad `CAST`. Artifacts make the failure
self-explanatory, a human fixes it, and we rerun to green.

- `🖱` Open PR #4 → its CircleCI `pr` pipeline.
- `▶` "Offline gates are green — the SQL is well-formed and snake_case. Now the
  credentialed `dbt-pr-build` runs a **real** build into its own
  `GROUPE_DYNAMITE_DEMO_PR_…` schema."
- `🖱` Click the failed `dbt-pr-build` job. Scroll to the failing model in the
  step log — a Snowflake cast/numeric-conversion error on the offending model.
- `▶` "This is a real Snowflake error, not a lint. And it's actionable, because we
  kept the evidence."
- `🖱` Open the job's **Artifacts** tab. Open `target/run_results.json` (search the
  failing node → `status: "error"` and the message) and `logs/dbt.log`.
- `▶` "`run_results.json` pins the exact node that failed and why; `logs/` has the
  compiled SQL Snowflake rejected. A developer knows precisely what to fix without
  re-running blind."
- `▶` "CircleCI didn't fix anything — it gave us evidence. A **human** applies the
  fix." Apply the prepared repair by fast-forwarding the PR branch to its fix:
  - `⌨ git fetch origin`
  - `⌨ git switch demo/fail-invalid-cast`
  - `⌨ git merge --ff-only origin/demo/fix-invalid-cast`
  - `⌨ git push origin demo/fail-invalid-cast`
  - (Exact commands and the operator-only restore path:
    [scenario-catalog.md](scenario-catalog.md).)
- `🖱` Back on the PR/pipeline, the new push starts a fresh run. `▶` "Reruns are at
  the job boundary and human-triggered — `dbt build` always starts fresh, there's
  no silent auto-retry." Watch `dbt-pr-build` go **green**.
- `🖱` Show `dbt-pr-cleanup` dropped the prefixed PR schema: `▶` "The disposable
  schema is torn down automatically after a started build finishes, so no PR
  leaves residue in Snowflake."

**Mini-close:** "Real failure, evidence in artifacts, human fix, clean rerun, no
leftover schema. That's the daily-driver loop."

**Stop condition:** If the fresh run can't finish inside the window, stop at
"green offline gates + artifacts explaining the failure" and state that the fix
+ rerun is the same one-command fast-forward you'd do live — don't wait past
9:30. If Snowflake auth fails (context not populated), this becomes a *narrated*
failure: show the offline gates green and the credentialed job failing on a
connection error, and pivot to [recovery-fallback.md](recovery-fallback.md) →
"Snowflake auth failure". Never present a connection error as the intended cast
failure.

---

## 10:00 – 14:00 — Moment 3: main → DEV → approval → PROD

One branch (`main`), one promotion path with a human gate.

- `▶` "Now the promotion. When a PR is approved and merged to `main`, a different
  workflow runs — DEV first, then a manual hold, then PROD."
- `🖱` Trigger it the real way if time allows: merge an already-green PR into
  `main` (or push the agreed promotion commit to `main`). Otherwise open the most
  recent `main` pipeline.
- `🖱` Open the `main` pipeline. Show `dbt-main-dev` building into the **DEV**
  schema and going green. `🖱` Open its Artifacts to show `run_results.json` for
  the DEV build.
- `▶` "DEV is green. Notice the next job is a **manual approval hold** —
  `hold-promote-prod`. Nothing reaches PROD without a person."
- `🖱` Click `hold-promote-prod` → **Approve**. `▶` "That click is the audit
  point: a named human approved this promotion."
- `🖱` Show `dbt-main-prod` building into **PROD** and going green; open its
  artifacts.
- `▶` "Same code, same tests, promoted DEV → PROD through one human gate, with
  artifacts at each stage."

**Mini-close:** "One branch to production, a human in front of PROD, evidence on
both sides of the gate."

**Stop condition:** If Snowflake/context is unavailable, do **not** fake a PROD
build. Show a prior successful `main` pipeline if one exists (see
[rehearsal-status.md](rehearsal-status.md) — currently PROD is **unverified**),
or walk the config in `.circleci/config.yml` (`workflows.main`) and narrate the
DEV → approval → PROD shape. Say clearly it's a walkthrough, not a live run. Do
not click Approve on a hold you can't complete.

---

## 14:00 – 15:00 — Close

- `▶` "Three moments: unsafe PR blocked before touching Snowflake; a real failure
  made actionable by stored artifacts and fixed by a human; and one branch
  promoted to PROD through a manual gate."
- `▶` "Everything you saw is dbt Core + CircleCI + Snowflake with credentials
  isolated to a context. Next step is [wiring this to your Snowflake and org
  controls](poc-extension.md)."
- If asked "can the assistant fix CI for me?": `▶` "It can read status and logs
  and request a rerun as a backup, but a human always applies the code fix. It
  never edits your code." Optionally show [mcp-backup-flow.md](mcp-backup-flow.md).

---

## One-glance timing

| Mark | Moment | Live artifact shown |
|------|--------|---------------------|
| 0:00–1:30 | Frame | architecture diagram |
| 1:30–5:00 | Blocked unsafe PR (#3) | red `validate-model-names`, no context |
| 5:00–10:00 | Actionable failure (#4) | `run_results.json`, `logs/`, green rerun, cleanup |
| 10:00–14:00 | main DEV → approval → PROD | DEV build, approval click, PROD build |
| 14:00–15:00 | Close | recap + next step |

## Hard rules for the demo

- No screen-recording/"can everyone see my screen" theater — just drive.
- No fabricated green runs. If it isn't live, say "walkthrough" or "unverified".
- No secrets typed or shown. Credentials are in the context only.
- CircleCI/MCP never edits code. Humans fix and rerun.
- Don't pitch dynamic config / "smarter" test selection / chunking — this config
  is deliberately static and readable; that's the point.
- Don't promise deploy markers or any capability not yet verified.
