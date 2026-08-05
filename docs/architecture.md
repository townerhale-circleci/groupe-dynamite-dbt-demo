# Environment architecture

Two branch-selected CircleCI workflows drive one dbt Core project against one
Snowflake database. Credentials live **only** in the `snowflake-dbt-demo`
context and attach **only** to the five jobs that touch Snowflake. The Cursor
CircleCI MCP is a **backup** for retrieving status/logs and requesting a rerun
when the web UI is unavailable — it is never the primary flow and never edits code.

```mermaid
flowchart TB
  dev["Developer<br/>pushes branch / opens PR"]

  subgraph PRW["CircleCI &laquo;pr&raquo; workflow — every branch EXCEPT main"]
    direction TB
    subgraph OFF["Offline gates — NO context, NO Snowflake credentials"]
      vmn["validate-model-names<br/>(snake_case filename gate)"]
      pt["python-tests<br/>(offline pytest, JUnit)"]
      sf["sqlfluff<br/>(Snowflake dialect lint)"]
    end
    dc["dbt-compile<br/>(credentialed)"]
    prb["dbt-pr-build<br/>&rarr; GROUPE_DYNAMITE_DEMO_PR_&lt;n&gt;"]
    prc["dbt-pr-cleanup<br/>drops prefixed PR schema (guarded)"]
  end

  gh["GitHub commit status<br/>one check per job"]
  art[("Artifacts<br/>run_results.json · manifest.json<br/>compiled/ · logs/")]

  subgraph MAIN["CircleCI &laquo;main&raquo; workflow — main ONLY"]
    direction TB
    mdev["dbt-main-dev<br/>&rarr; DEV schema"]
    appr{{"hold-promote-prod<br/>MANUAL approval"}}
    mprod["dbt-main-prod<br/>&rarr; PROD schema"]
  end

  mcp[["Cursor CircleCI MCP<br/>status/logs + rerun backup"]]

  dev --> OFF
  OFF --> dc --> prb --> prc
  OFF -. "posts status" .-> gh
  dc -. "posts status" .-> gh
  prb -. "posts status" .-> gh
  prb --> art
  dev -->|"merge to main"| MAIN
  mdev --> appr --> mprod
  mdev --> art
  mprod --> art
  gh -. "read status/logs when UI down" .-> mcp
  art -. "retrieve artifacts" .-> mcp
  mcp -. "operator-authorized rerun" .-> prb

  classDef offline fill:#e6f4ea,stroke:#137333,color:#0b3d1e;
  classDef cred fill:#fce8e6,stroke:#b3261e,color:#5c0f0a;
  classDef backup fill:#f1f3f4,stroke:#5f6368,color:#202124,stroke-dasharray:5 3;
  class vmn,pt,sf offline;
  class dc,prb,prc,mdev,mprod cred;
  class mcp backup;
```

## How to read it

- **Developer → PR.** Any branch except `main` runs the `pr` workflow. The
  developer never handles Snowflake credentials.
- **Separate checks.** The three offline gates (`validate-model-names`,
  `python-tests`, `sqlfluff`) run **without** the context. An unsafe change is
  caught here **before** any credential is loaded — this is the "blocked unsafe
  PR" moment.
- **PR schema.** `dbt-pr-build` materialises into a disposable, deterministic
  `GROUPE_DYNAMITE_DEMO_PR_<…>` schema. Concurrent PRs never collide.
- **GitHub status.** CircleCI posts one commit status per job back to the PR.
  These red/green checks are the merge signal. See
  [rehearsal-status.md](rehearsal-status.md) for the branch-protection
  entitlement caveat on this personal-account repo.
- **main DEV → approval → PROD.** Merging to `main` builds into
  `GROUPE_DYNAMITE_DEMO_DEV`, pauses at `hold-promote-prod`, then builds into
  `GROUPE_DYNAMITE_DEMO_PROD`. One branch, one promotion path.
- **Artifacts.** `run_results.json`, `manifest.json`, `compiled/`, and `logs/`
  are stored after the build step (`when: always`), so they persist even when
  `dbt build` fails — that is what makes a failure *actionable*.
- **Cursor CircleCI MCP — backup only.** Used **after** the core demo, or if the
  CircleCI UI is unavailable, to read pipeline status/logs, retrieve artifacts,
  and request a rerun after a human applies the fix. It never edits code. See
  [mcp-backup-flow.md](mcp-backup-flow.md).

## Credential boundary (must stay true)

| Jobs | Context `snowflake-dbt-demo`? | Touches Snowflake? |
|------|:---:|:---:|
| `validate-model-names`, `python-tests`, `sqlfluff` | ❌ no | ❌ no |
| `dbt-compile`, `dbt-pr-build`, `dbt-pr-cleanup` | ✅ yes | ✅ yes |
| `dbt-main-dev`, `dbt-main-prod` | ✅ yes | ✅ yes |

`DBT_SCHEMA` is set by CI to a fully prefixed PR, DEV, or PROD schema.
