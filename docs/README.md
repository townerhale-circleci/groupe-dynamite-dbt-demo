# Demo documentation

Operator-facing docs for running and extending the **Groupe Dynamite dbt Core +
Snowflake** demo. Read them in this order the first time; on demo day you only
need the runbook and (open in a second tab) the recovery guide.

| # | Doc | Use it to… |
|---|-----|-----------|
| 1 | [demo-runbook.md](demo-runbook.md) | Run the exact 17-minute demo — minute marks, narration, clicks/commands, mini-closes, stop conditions. |
| 2 | [architecture.md](architecture.md) | Explain the environment (PR gates, PR schema, GitHub status, actionable artifacts, Cursor proof, main DEV → approval → PROD) with a Mermaid diagram. |
| 3 | [preflight-checklist.md](preflight-checklist.md) | Verify everything the morning of the demo — local commands, project/context names, expected checks, Snowflake objects, pass/fail gates. |
| 4 | [scenario-catalog.md](scenario-catalog.md) | Understand the four failure PRs and their fix branches, and the safe fast-forward / restore commands. |
| 5 | [recovery-fallback.md](recovery-fallback.md) | Recover when something breaks live (Snowflake auth, missing context vars, CircleCI/GitHub outage, cleanup failure, time pressure). |
| 6 | [cleanup.md](cleanup.md) | Tear everything down afterward — PR/DEV/PROD schemas, context secrets, remote branches/PRs, full SQL teardown. |
| 7 | [poc-extension.md](poc-extension.md) | Talk to the customer about turning this into their POC (Core enablement, prod auth, org restrictions, policy, orchestration, deploy markers). |
| 8 | [rehearsal-status.md](rehearsal-status.md) | See exactly what is verified vs. still unverified. **Read before promising anything live.** |
| 9 | [mcp-backup-flow.md](mcp-backup-flow.md) | Run the rehearsed 90-second Cursor proof for failure context and an operator-authorized rerun without making Preview behavior load-bearing. |

> **Ground rules that apply to every doc:** no fake success (say "unverified" when
> it is), no secrets in the repo or in commands, all destructive actions are
> manual/operator-gated, and CircleCI/MCP **never edits your code** — a human
> applies fixes and reruns.
