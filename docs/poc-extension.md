# Customer POC extension notes

How to turn this demo into a customer proof-of-concept. These are talking points
and prerequisites — commitments only where something is already verified. Where
a capability is **not yet verified in this repo**, say so and scope it as POC
work, not a promise.

---

## 1. dbt Core enablement is a prerequisite

This demo is **dbt Core** (open-source dbt run by CircleCI), not dbt Cloud. Before
a customer POC:

- Confirm the customer is moving to / already on **dbt Core** for the pipelines in
  scope. The migration story here is "dbt Cloud → dbt Core on CircleCI."
- The customer's dbt project must run on Core (adapters, packages, and any
  Cloud-only features — Cloud jobs, the Cloud IDE, Cloud-hosted docs, Semantic
  Layer endpoints — need Core-equivalent replacements or removal).
- Lock dbt + adapter versions via `uv`/lockfile (as this repo does) so CI is
  reproducible.

**Prerequisite gate:** don't scope CI work until Core enablement for the target
project is confirmed.

## 2. Production authentication

The demo uses a key-pair service identity in a CircleCI context. For a customer
POC, align it with their real authentication posture:

- Prefer **key-pair auth** or an **OAuth/externally-managed** Snowflake identity
  over static passwords; Snowflake is moving toward MFA/key-pair for service
  users. The dbt profile reads only env vars, so swapping auth is a context/profile
  change, not a code change.
- Use a **least-privilege service identity** scoped to the POC database/warehouse
  (mirror `SQL/bootstrap.sql`: usage on WH/DB, full rights only on the target
  schema, never `ACCOUNTADMIN`).
- Secrets live in a **CircleCI context** (ideally restricted to specific
  projects/groups), sourced from the customer's secret store. Never in the repo.

**Say honestly:** production auth wiring is POC scope; this demo proves the
pipeline shape, not the customer's specific auth integration.

## 3. Org / team restrictions

The demo repo is **public under a personal GitHub account** after an explicit
operator decision (see [rehearsal-status.md](rehearsal-status.md)):

- **Enforced required status checks / branch protection are demonstrated** on
  `main`; PR #1 was verified `BLOCKED` while a required CircleCI check was red.
- **Context restriction** (limiting `snowflake-dbt-demo` to specific projects or
  security groups) and **restricted contexts** are org-level CircleCI features —
  available to the customer, not demonstrated on the personal account.
- Plan CODEOWNERS, protected `main`, and required reviewers in the customer org.

**Don't claim** org/team approval or context restriction is shown here. The
customer POC should keep source private under an entitled organization while
retaining the same required-check behavior.

## 4. Standardization: private orbs & config policies

Right now `.circleci/config.yml` is deliberately a **single static file, no orbs,
no dynamic config** — readable and auditable, which is the demo's strength. At
customer scale, standardize with:

- **Private orbs** to package the repeated command/job patterns (setup, PR-schema
  resolve, artifact persistence, guarded cleanup) so many dbt repos share one
  vetted implementation.
- **Config policies** (OPA-based) to enforce org rules at pipeline compile time —
  e.g. "credentialed jobs must use the approved context," "no job runs against
  PROD without an approval upstream," "offline gates must precede credentialed
  jobs."

**Scope note:** orbs/policies are a standardization *next step*, not part of this
demo. Introducing them changes the "single readable file" story, so do it when the
customer has many pipelines to govern — not to win this demo.

## 5. Orchestration boundaries (Step Functions / MWAA)

Some customers trigger dbt from an external orchestrator. Draw the boundary
clearly:

- **CircleCI owns** build/test/promotion **CI**: PR gates, per-PR schema
  build+cleanup, DEV → approval → PROD, artifacts, status.
- **Step Functions / MWAA (Airflow) owns** production **scheduling/orchestration**:
  when dbt runs in prod, upstream/downstream data dependencies, retries,
  backfills, cross-system DAGs.
- Integration pattern: the orchestrator invokes the **same versioned dbt project**
  (via a CircleCI pipeline trigger, or by running the pinned dbt image directly),
  so CI-validated code is exactly what prod orchestration runs. Keep one source of
  truth for the project and its lockfile.

**Say honestly:** this demo shows the CI half. Orchestrator integration is POC
design work with the customer's platform team; don't imply it's built here.

## 6. Deploy markers — only after verified

Deploy markers / release annotations (marking a PROD deploy on a dashboard or in
CircleCI/observability tooling) are a natural add **after** a promotion is
verified end-to-end. They are **not** implemented or verified in this repo.

- Emit a deploy marker **only after** `dbt-main-prod` has *actually* succeeded —
  gated on verified success, never optimistically.
- PROD promotion is verified live, but deploy-marker rendering is not. Do not
  promise markers until a separate rehearsal confirms them for this dbt flow.

---

## POC scoping summary

| Area | In this demo? | POC work |
|------|:---:|---------|
| dbt Core pipeline shape | ✅ shown | confirm Core enablement for target project |
| Snowflake auth | ✅ key-pair service user | customer-approved key-pair/OAuth identity |
| Enforced merge blocks | ✅ (public demo) | reproduce on private customer org/plan |
| Context restriction | ❌ | org/group-restricted contexts |
| Orbs / config policies | ❌ (static config) | private orbs + OPA policies at scale |
| Step Functions / MWAA | ❌ | orchestrator ↔ CI integration design |
| Deploy markers | ❌ | add only after verified PROD promotion |

Lead with what is proven offline: the pipeline/config shape, deterministic
checks, and explicit approval definition. Treat the live credential boundary,
Snowflake builds, and human-gated PROD execution as POC verification work until
the rehearsal status moves them to verified.
