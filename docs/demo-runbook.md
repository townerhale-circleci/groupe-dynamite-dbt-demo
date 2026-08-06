# 17-minute demo runbook

Exact, minute-marked script for the live demo. Four moments:

1. **Blocked unsafe PR** — the customer's uppercase-name example produces a
   visibly blocked merge on one protected branch.
2. **Actionable failure with artifacts** — a real dbt/Snowflake build failure,
   read from `run_results.json` + `logs/`, fixed by a human, rerun to green.
3. **The same failure in Cursor** — CircleCI MCP brings the evidence into the
   developer's IDE without editing code.
4. **One branch, main → DEV → manual approval → PROD.**

> **Read first:** [rehearsal-status.md](rehearsal-status.md). The blocked PR,
> actionable failure, Cursor retrieval, and DEV → approval → PROD path have
> rehearsal evidence; credentialed moments still require the populated context
> and trial account.
> Run the [preflight](preflight-checklist.md) before presenting. If it does not
> pass, use the degraded form noted in each
> moment's **Stop condition**, and be honest about what is live vs. narrated.

**Conventions in this script**
- `▶` = narration (what you say). `⌨` = command you run. `🖱` = UI click.
- Commands assume you are at the repo root with `uv sync` already done.
- Times are cumulative target marks; keep each moment inside its window.
- Never paste secrets. `DBT_SCHEMA` and credentials are set by CI, not by you.

---

## 0:00 – 1:30 — Agreement: answer the branch question first

- `▶` "Ravi, you asked several times whether DEV and PROD require two long-lived
  branches. They do not. One protected `main` branch can block unsafe changes,
  then promote the same commit through a visible DEV stage and a human-gated
  PROD stage. I'll prove that end to end."
- `▶` "We'll also use your two exact failure examples: an uppercase model name
  and a Snowflake cast error. Then I'll bring the failure into Cursor so the
  developer does not have to leave the IDE to start the investigation."
- `▶` "This prototype proves the operating model. Your current GitHub Actions
  trigger, customer Snowflake design, required-review policy, and production
  approver group still need confirmation in your environment."
- `▶` "Haythem, before I start: is branch protection enabled on `main` today,
  and which checks and reviewers does it require?" **Pause for the answer.**
- `▶` "Ravi, is this the flow you expected to evaluate today?" **Wait for an
  explicit yes or correction.**

---

## 1:30 – 4:30 — Moment 1: The bad change cannot merge

Scenario branch: `demo/fail-uppercase-model` (PR #3). It adds an **uppercase**
model file (`Customer_Lifetime_Value.sql`). The `validate-model-names` offline
gate fails on it — before the context is ever attached.

- `🖱` Open PR #3 in GitHub on the **Conversation** tab. Start with the disabled
  merge state: "The change cannot merge."
- `▶` "Ravi, you gave us this exact example: an uppercase model name should not
  be deployed. GitHub is blocking it on CircleCI's required status."
- `🖱` Point at the changed file name in **Files changed**:
  "`Customer_Lifetime_Value.sql` — uppercase, not our convention."
- `🖱` Open the CircleCI `pr` pipeline for this branch (Checks tab → CircleCI, or
  the CircleCI project page).
- `▶` "Two checks caught the same unsafe condition: the dedicated naming gate
  and the project contract test. That is intentional defense in depth."
- `▶` "Look at the order. These offline jobs run first with no context."
  `🖱` Click into `validate-model-names`.
- `🖱` Show the failing step output — it lists the invalid filename and exits 1:
  "Invalid dbt model filenames (must be snake_case): … `Customer_Lifetime_Value.sql`."
- `▶` "The second benefit is cost and safety: this failed **without any
  Snowflake credential**. The credentialed jobs never started."
- `▶` "CircleCI produces the red status; GitHub enforces the merge restriction.
  In your organization, required reviewers and CODEOWNERS are the GitHub-side
  control for who may approve a PR. This demo proves the required-check half."
- **Pause on the blocked merge state.**

**Mini-close:** "Ravi, you said an uppercase model must not deploy and an
accidental merge can block other developers. Given this required CircleCI check,
how would this change the way your team controls merges today?"

**Stop condition:** If CircleCI status isn't showing on the PR, open the pipeline
directly from the CircleCI project page (`gh/townerhale-circleci/groupe-dynamite-dbt-demo`)
and narrate from there. If CircleCI is unreachable, run the gate locally instead:
`⌨ uv run python scripts/validate_model_names.py models` (it exits 1 and names the
file). Do **not** claim the PR was auto-blocked — describe it as the failing check.

---

## 4:30 – 9:00 — Moment 2: Exact failure, human fix, clean rerun

Scenario branch: `demo/fail-invalid-cast` (PR #4). Offline gates pass; the real
`dbt-pr-build` fails at Snowflake on a bad `CAST`. Artifacts make the failure
self-explanatory, a human fixes it, and we rerun to green.

- `🖱` Open PR #4 → its failed CircleCI `pr` pipeline. Confirm
  `dbt-pr-cleanup` is already **green before pushing anything**.
- `▶` "The old run has finished cleanup, so it is safe to push the prepared
  human fix. We never overlap two runs of the same PR schema."
- `⌨` Start the prepared repair immediately, then explain the evidence while the
  new pipeline runs:
  - `git fetch origin`
  - `git switch demo/fail-invalid-cast`
  - `git merge --ff-only origin/demo/fix-invalid-cast`
  - `git push origin demo/fail-invalid-cast`
  - Exact commands and the operator-only restore path are in
    [scenario-catalog.md](scenario-catalog.md).
- `▶` "Offline gates are green — the SQL is well-formed and snake_case. Now the
  credentialed `dbt-pr-build` runs a **real** build into its own
  `GROUPE_DYNAMITE_DEMO_PR_…` schema."
- `🖱` Click the failed `dbt-pr-build` job. Scroll to the failing model in the
  step log — a Snowflake cast/numeric-conversion error on the offending model.
- `▶` "This is a real Snowflake error, not a lint. And it's actionable, because we
  kept the evidence."
- `🖱` Open the job's **Artifacts** tab. In `target/run_results.json`, point to
  `fct_invalid_cast_demo`, column `PARSED_AMOUNT`, and value `not_a_number`.
  Open `logs/dbt.log` or compiled SQL only if asked.
- `▶` "That is the model, file, Snowflake error, exact column, and offending
  value. CircleCI did not edit the code; it preserved the evidence so a human
  could make the right fix."
- `🖱` Return to the fresh pipeline. `▶` "CircleCI reruns from the failed **job**
  boundary; it does not resume halfway through one `dbt build` command and it
  does not silently self-heal." Watch `dbt-pr-build` go **green**.
- `🖱` Show `dbt-pr-cleanup` dropped the prefixed PR schema: `▶` "The disposable
  schema is torn down automatically after a started build finishes, so no PR
  leaves residue in Snowflake."
- **Pause on the green rerun and cleanup.**

**Mini-close:** "Rohit, today you go back into dbt, locate the error, and rerun
the command from the beginning. Given this exact node, column, and Snowflake
message plus a job-boundary rerun, how would that change your failure workflow?"

**Stop condition:** If the fresh run can't finish inside the window, stop at
"green offline gates + artifacts explaining the failure" and state that the fix
+ rerun is the same one-command fast-forward you'd do live — don't wait past
8:30. If Snowflake auth fails (context not populated), this becomes a *narrated*
failure: show the offline gates green and the credentialed job failing on a
connection error, and pivot to [recovery-fallback.md](recovery-fallback.md) →
"Snowflake auth failure". Never present a connection error as the intended cast
failure.

---

## 9:00 – 10:30 — Moment 3: The same evidence inside Cursor

- `▶` "Ravi, the artifact solves the root-cause question. You also asked whether
  the developer can get that context without leaving Cursor."
- `🖱` In Cursor, ask CircleCI MCP to identify the invalid-cast failure and
  summarize the failed model, column, value, and next action.
- `▶` "The developer still edits code here in Cursor. MCP reads CircleCI status,
  logs, tests, and artifacts and can request an operator-authorized rerun. It
  never edits the source code or silently fixes the pipeline."
- `▶` "MCP is Preview today; the underlying CircleCI artifacts and workflow are
  the durable proof you already saw."
- **Pause on the returned failure detail.**

**Mini-close:** "Ravi, you described leaving the IDE to hunt through dbt or
Azure. Given this CircleCI context in Cursor, how much of that context switching
would disappear for your developers?"

**Stop condition:** If MCP is unavailable or slow, use the check-down:
1. **Verbal:** state that the failed job and artifacts are available through MCP.
2. **Visual:** show the connected CircleCI tool without running a query.
3. Stop. Do not debug MCP live or let a Preview feature hold up the core proof.

---

## 10:30 – 15:30 — Moment 4: Green merge → DEV → approval → PROD

One branch (`main`), one promotion path with a human gate.

- `▶` "The failed checks blocked the unsafe changes. Now this prepared green PR
  shows the block releasing: every required status is green, so it can merge to
  the same protected `main` branch."
- `🖱` Merge the prepared `demo/promotion-ready` PR into `main`. Do not use an
  owner bypass. `▶` "Required reviewers and CODEOWNERS are configured on the
  GitHub side in a customer organization; this prototype is intentionally
  proving the required-status enforcement."
- `▶` "That merge starts a different workflow — DEV first, then a manual hold,
  then PROD."
- `🖱` Open the `main` pipeline. Show `dbt-main-dev` building into the **DEV**
  schema and going green. `🖱` Open its Artifacts to show `run_results.json` for
  the DEV build.
- `▶` "That is your **testing flag** turning green and your **DEV flag** becoming
  visible. The next job is a manual approval hold — `hold-promote-prod`."
- `🖱` Click `hold-promote-prod` → **Approve**. `▶` "That click is the audit
  point: a named human approved this promotion. In your GitHub organization, a
  restricted CircleCI context bound to the authorized security group is what
  prevents an unauthorized approver from successfully running PROD. This
  personal namespace proves the hold, not that team restriction."
- `🖱` Show `dbt-main-prod` building into **PROD** and going green; open its
  artifacts.
- `▶` "That is your **deployed flag**: the same tested commit reached PROD
  through a visible human gate, with artifacts at each stage."
- **Pause on the complete workflow graph.**

**Mini-close:** "Ravi, you asked whether one branch can give you the same
separation as DEV and PROD branches. Given this protected merge, DEV build,
human hold, and PROD build, how would this change the branch process your team
uses today?"

**Stop condition:** If Snowflake/context is unavailable, do **not** fake a PROD
build. Show a prior successful `main` pipeline if one exists (see
[rehearsal-status.md](rehearsal-status.md) — pipeline #35 is the baseline),
or walk the config in `.circleci/config.yml` (`workflows.main`) and narrate the
DEV → approval → PROD shape. Say clearly it's a walkthrough, not a live run. Do
not click Approve on a hold you can't complete.

---

## 15:30 – 17:00 — Close on a scoped POC

- `▶` "The sentence you can take to your director is: We can run dbt Core on
  CircleCI with one protected main branch — bad SQL cannot merge, developers see
  the exact model and column that failed in Cursor, and nothing reaches PROD
  without a human gate — without dbt Cloud's per-seat restriction."
- `▶` "The next step is one repository, one representative dbt model, one style
  rule, one authored data test, one safe Snowflake CI target, and one
  DEV-to-PROD path."
- `▶` "Ravi, if we reproduce these four outcomes in your first dbt Core
  repository, is that enough for you, Haythem, and Rohit to call the POC
  technically successful?"
- **Stop and wait.** If yes: "Who owns the dbt Core branch, Snowflake CI identity,
  GitHub protection, and approver group on your side?" Hand the commercial next
  step to Fields.

---

## Precise answers to keep ready

**"Do dbt tests appear in CircleCI Test Insights?"**

`▶` "dbt Core does not emit JUnit natively. This demo stores pytest JUnit in
CircleCI Test Insights, while dbt failures use `run_results.json`, `dbt.log`,
and compiled SQL. A dbt-to-JUnit converter is possible POC work, but I would not
claim it is implemented here."

**"Can only selected people approve production?"**

`▶` "A plain CircleCI approval proves a human hold. In your GitHub organization,
the production job would use a restricted CircleCI context bound to the
authorized security group; an unauthorized approval cannot make PROD succeed.
This personal demo namespace does not prove that team restriction."

**"Does CircleCI provide vulnerability scanning?"**

`▶` "CircleCI does not ship a built-in vulnerability scanner. It runs the tool
you select, such as Snyk or Trivy, and makes that result part of the required
gate."

---

## One-glance timing

| Mark | Moment | Live artifact shown |
|------|--------|---------------------|
| 0:00–1:30 | Agreement | one-branch answer + Haythem validation |
| 1:30–4:30 | Blocked unsafe PR (#3) | `BLOCKED`, two red gates, no context |
| 4:30–9:00 | Actionable failure (#4) | exact artifact, human fix, green rerun, cleanup |
| 9:00–10:30 | Cursor MCP | failed model/column/value in the IDE |
| 10:30–15:30 | green merge → DEV → approval → PROD | testing/DEV/deployed flags |
| 15:30–17:00 | Close | POC success criterion + owners |

## Hard rules for the demo

- No screen-recording/"can everyone see my screen" theater — just drive.
- No fabricated green runs. If it isn't live, say "walkthrough" or "unverified".
- No secrets typed or shown. Credentials are in the context only.
- CircleCI/MCP never edits code. Humans fix; MCP may request an authorized rerun.
- Don't pitch dynamic config / "smarter" test selection / chunking — this config
  is deliberately static and readable; that's the point.
- Don't promise deploy markers or any capability not yet verified.
