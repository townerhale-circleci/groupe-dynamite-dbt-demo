# Recovery & fallback guide

What to do when something breaks during (or just before) the demo. For each
failure mode: how to recognize it, the graceful fallback, and what **not** to
say. The golden rule everywhere: **never present a fallback or a narrated step
as a live success.**

Keep this open in a second tab during the demo.

---

## 1. Snowflake auth failure

**Looks like:** a credentialed job (`dbt-compile`, `dbt-pr-build`, `dbt-main-dev`,
`dbt-main-prod`) fails fast with a connection/authentication error, or local
`dbt debug` reports the connection check failing.

**Recover:**
- Confirm the `snowflake-dbt-demo` context has all six variable **names** set
  (see [preflight](preflight-checklist.md) C2). Don't read values.
- Confirm the Snowflake user/role aren't locked or password-expired (the
  bootstrap sets `MUST_CHANGE_PASSWORD = TRUE` — a never-rotated demo user will
  fail here). The Snowflake owner can confirm in a worksheet.
- If it can't be fixed in the moment: pivot. Moment 1 (offline) still runs live.
  For Moments 2 & 3, **narrate** from `.circleci/config.yml` and the
  [architecture diagram](architecture.md).

**Don't say:** that the build succeeded, or that a connection error was "the cast
failure." Say: "Snowflake auth isn't available right now; here's the shape of
what runs when it is."

---

## 2. Missing context variables

**Looks like:** credentialed jobs fail with a missing-env-var error (e.g.
`DBT_SNOWFLAKE_ACCOUNT` unset) rather than an auth rejection. This is the current
known state — see [rehearsal-status.md](rehearsal-status.md).

**Recover:**
- A person with access adds the missing variable(s) to the `snowflake-dbt-demo`
  context in the CircleCI UI, using values from a trusted secret store — **never**
  from this repo, chat, or a screen-share. Then rerun the job.
- If they can't be added in time, treat it exactly like case 1: offline moment
  live, credentialed moments narrated.

**Don't say:** the values, or that the context is "basically set up." State which
names are present and which are missing.

---

## 3. CircleCI outage / UI unavailable

**Looks like:** the CircleCI app won't load, pipelines don't start, or status
checks don't post to GitHub.

**Recover, in order:**
1. Use the **Cursor CircleCI MCP** backup to pull recent pipeline status and job
   logs/artifacts (see [mcp-backup-flow.md](mcp-backup-flow.md)). After a human
   pushes a fix, it can also request an operator-authorized rerun.
2. If MCP is also unavailable, run the offline gates **locally** to demonstrate
   the same checks:
   ```bash
   uv run python scripts/validate_model_names.py models   # Moment 1
   uv run pytest
   uv run sqlfluff lint models
   uv run dbt parse --profiles-dir . --project-dir .       # with throwaway env vars
   ```
3. Walk the pipeline design from `.circleci/config.yml` and the diagram.

**Don't say:** that CI ran green if you only ran things locally. Say: "CircleCI is
down; these are the same gates running on my machine."

---

## 4. GitHub branch protection unavailable

**Reality (record it honestly):** this demo repo is a **private repo under a
personal GitHub account**. Attempting to configure branch protection / required
status checks returns **HTTP 403** — an **entitlement limitation**: enforced
required checks on a private repo require **GitHub Pro** (or the repo must be
public / owned by an org with the entitlement). See
[rehearsal-status.md](rehearsal-status.md).

**Recover / how to present:**
- Demonstrate the *block signal* — the offline gate posting a **red** required-
  style check on the unsafe PR — and simply **do not merge** it.
- Say: "In your org, that red check is a hard, enforced merge block. Here, on a
  personal private repo, we can't enable enforced required checks (a GitHub
  entitlement, not a pipeline gap), so I'm showing the failing check that the rule
  keys off of."

**Don't say:** that required checks are configured/enforced on this repo, or that
the merge was automatically blocked. They are **not** established here.

---

## 5. Cleanup failure (PR schema not dropped)

**Looks like:** `dbt-pr-cleanup` fails, or you're unsure a `PR_` schema was
dropped.

**Recover:**
- `dbt-pr-cleanup` runs after a started `dbt-pr-build` succeeds, fails, is
  canceled, or becomes unauthorized, so a failed build still triggers cleanup.
  It intentionally skips `not_run`, because no schema was created. If cleanup
  itself failed, rerun that job from the CircleCI UI.
- Manually drop the leftover schema with the guarded macro (it refuses anything
  not prefixed `PR_`, and refuses `DEV`/`PROD`):
  ```bash
  # DBT_SCHEMA must be the PR_ schema to drop; credentials from your local .env.
  uv run dbt run-operation drop_pr_schema \
      --args '{schema_name: PR_<the_schema>}' --profiles-dir . --project-dir .
  ```
- Full manual options are in [cleanup.md](cleanup.md).

**Don't say:** "it's cleaned up" unless you've confirmed the schema is gone.

---

## 6. Demo branch already fixed

**Looks like:** a `demo/fail-*` branch already points at its fixed commit (offline
gate is green when you expected red), usually because a rehearsal didn't restore
it.

**Recover (off-demo, operator action):**
- Restore the branch to its recorded failing SHA using the **force-with-lease**
  procedure in [scenario-catalog.md](scenario-catalog.md) → "Restoring a
  scenario". This requires the `<BAD_SHA>` you recorded in preflight.
- If you don't have the recorded SHA, use a different scenario whose fail branch
  is still failing, and restore the affected one afterward.

**Don't say:** don't `--force` blindly to "make it fail again." Use
force-with-lease pinned to the expected remote SHA, as a deliberate human step.

---

## 7. Time pressure

You're running long. Cut in this order, protecting the three moments' core point:

1. **Drop the alternate scenarios** (#5 broken ref, #2 business rule) — they're
   follow-ups, not the spine.
2. **Shorten Moment 2's rerun:** stop at "green offline gates + artifacts explain
   the failure," state the fix is a one-command fast-forward, and skip watching
   the green rerun.
3. **Narrate Moment 3** from a prior successful `main` pipeline + the diagram
   instead of triggering a live promotion — but keep the **approval click** story,
   it's the punchline.
4. **Skip the MCP backup** entirely (it's already optional and post-core).

Never cut by faking speed — don't claim a run finished that didn't. A crisp
"here's what would happen next, and it's one command" is honest and lands.

---

## Universal don'ts

- No fabricated green runs, no "trust me it passes."
- No secrets shown, typed, or read aloud — not even partially.
- No `--force` pushes; force-with-lease only, by a human, off-demo.
- CircleCI and the MCP **never edit code**. Every fix is a human commit + rerun.
- Don't over-promise: deploy markers, enforced required checks, and live
  PROD are **not** verified yet (see [rehearsal-status.md](rehearsal-status.md)).
