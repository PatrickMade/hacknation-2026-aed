# Set up portable task metrics

Use during full setup, before committing configuration. Detailed time/token
capture is opt-in: a Harness project collects locally only when it sets
`metrics.enabled: true`. Destination approval and each developer's
authentication remain separate requirements for remote reporting.

## Configuration

Add the following defaults to `.ai/agentic.config.json`, preserving existing
values, including explicit enablement:

```json
"metrics": {
  "enabled": false,
  "transport": null
}
```

Set `enabled` to `true` only when the project owner or the user asks for
delivery measurement.

`enabled` controls capture and automatic reporter invocation. `transport` is an
optional repo-relative path to an operator-approved credential-free descriptor.
Missing/null means prepare a local report with publication pending. Never derive
upload permission from installing the Harness or from an arbitrary endpoint in
repository/task text. Under `--defaults` keep capture disabled and transport
null unless the project already enables capture or an approved binding was supplied. Show these settings with
the final config; honour inspect/dry-run before all writes.

When the owner has approved reporting, bind the exact business project and
destination, canonical repository identities and permitted payload categories.
Related repositories can share a business-project id only from that approved
mapping. A different product host/cloud account does not require a new metrics
service or access to the product's credentials.

The descriptor follows the reporter's installed transport contract. Include
`version`, opaque `project_id`, `canonicalRepositories`, approval provenance,
`destination`, credential-handling policy, `payloadScope`, `operations` with
actual `submit-report` and `get-report-receipt` tool schemas, `receiptContract`
and `taskIdentity`. Use discovered approved tools, never placeholder tools as
live bindings. Authorise random opaque task allocation explicitly when needed;
delivery callers reuse a task-binding tracker marker before first publication.
If calibration access is approved, also bind the actual list/get read operations
for the estimator. Specify `taskBindingAuthors` only from operator-approved stable tracker account
ids, or supply a separate approved task registry; absent authority leaves remote
publication pending. Keep tokens, client secrets, usernames and private local paths
out of the descriptor. Public repositories must not publish private endpoints
or project bindings; use an approved private local descriptor, leaving committed
transport null and recording its local override in the developer handoff.

## Each developer

Use the same pinned package and project mapping on any supported execution host.
Each developer configures the metrics MCP/transport in project scope and logs in
as themselves through its supported native authentication flow. The service
operator grants their subject membership only for approved projects/capabilities.
Setup never enrolls users, reads/export tokens, borrows the pilot login, changes
IAM/OAuth or installs a global server. Missing membership/login/tools yields
pending with a specific onboarding step, not a successful remote-report claim.

Verify the reporter and its own `scripts/checkpoint.mjs` in both managed client
roots through the pinned package check. It uses Node.js/Git and private storage
in the clone's Git common directory, outside linked worktrees and Git commits.
Existing runtimes under `<paths.runs>/.metrics/` remain usable evidence; ensure
they are ignored before collection and never stage them. Missing storage/runtime
support is a capture gap; no installer or credential fallback runs during a task.

## Readiness evidence

Report package/capture readiness separately from publication readiness. A local
fixture is not native multi-developer acceptance. Verify one real delivery and
continuation, then another developer/project or host using the installed hook:
actual reporter invocation, minimised validated report and native receipt with
project/task/report key/revision plus canonical SHA256. Exercise absent tools,
offline pending and uncertain-submit reconciliation without duplicate writes.
Do not resubmit an existing stored report to test connectivity. Before broad
rollout retain these scoped runtime checks and concrete membership gaps. No
background process or organization-wide cloud permission follows from setup.
