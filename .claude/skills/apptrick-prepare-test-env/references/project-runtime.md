# Complete and safe project runtime

Derive the environment from actual launch scripts, client API configuration and
service dependencies. For split repositories, identify each required checkout,
its current revision and local changes; do not assume sibling paths or switch
another checkout. Resolve UI URL separately from API and health URLs. A browser
scenario uses the product UI, not Swagger or an API documentation page.

Use `apptrick-prepare-test-env` to own startup/reuse/teardown. Extend the existing
descriptor additively with the required service inventory (name, source root,
revision, URL, health check and owned process identity). Preserve legacy app and
browser fields for existing consumers. Before reuse, verify every required
service's health, source/config identity and TTL, not only the backend PID.
A replaced PID is not owned by this run. On failure, clean up only resources this
run created; preserve pre-existing databases and other sessions. Retain lifecycle
checks for cold start, warm reuse, stale TTL, changed source, missing service,
foreign process and repeated teardown. Never close all browser sessions.

For a UI backed by an API, generation or repair must also prove one safe
representative browser-to-API round trip through the actual client configuration
(including its proxy, cookies or authorization headers). Use an existing smoke
scenario or a minimal reproducible readiness script: for example, a disposable
user signs in through the UI and the page reads that user's local profile.
Record the UI/API targets, each tested repository revision and run identity, the
command and observed result in the generation evidence. Separate healthy services
from a working connection: direct API requests or a rendered login page alone do
not prove it. Re-run this proof when the connection configuration or dependent
service identity changes. This is environment readiness, not feature QA; use
`apptrick-test` or `apptrick-verify` for acceptance of the feature. Static sites and
API-only projects record why the browser-to-API check is inapplicable. If browser
or test data is unavailable, report the missing integration proof and keep the
environment explicitly degraded rather than claim verified end-to-end readiness.

Inspect actual endpoint values and launch-time profiles before running anything.
List integration writes, email, payments, webhooks, scheduled jobs and migrations.
Local/test mode does not prove isolation. Prefer existing stubs, test accounts and
synthetic fixtures; override dangerous endpoints before startup and verify the
exercised write reaches the stub. GET can have side effects too. Browser-domain
restrictions do not isolate server egress or other tools. Unknown consequential
side effects block the affected live test pending evidence or explicit authority.

Scope credentials to the process that needs them. A private-package token may
be required by dependency resolution, but must not be inherited by the app,
browser, unrelated package scripts or forked test processes. Pass only the
necessary variables to the authorized build step; inspect that step's lifecycle
hooks, subprocesses and persistent build daemons before assuming it contains the
credential. Remove the variables for unrelated children or split resolution from
runtime/test execution. Keep runtime/demo credentials scoped to their actual
consumer too. Verify propagation with a harmless synthetic sentinel and report
only presence/absence in the relevant child processes. Never dump real process
environments, full command lines, credential files or token values as evidence.

Do not make production dumps, shared migrations or generated-client rewrites a
setup default. If project-authorized dump data is needed, follow the project's
anonymization and isolation process, verify it before screenshots, and report its
limits. A newly created empty test account is useful but does not prove every UI
surface is safe. Never publish raw data or credentials.

When Sentry or another diagnostics MCP is already relevant, offer its supported
project declaration as an optional setup step. Separate shared declaration from
per-user authentication. Inspect active tools and actual granted scope after
login; URL parameters and written intentions are not permission proof. Do not
create credentials, alter consent or provision production resources without the
required authorization. Missing diagnostics must not block unrelated local work.

A spec may carry a small executable acceptance checker when it can decide a real
criterion. Keep it beside the spec, document the command and limit, and avoid
adding scripts for prose-only criteria. Update every document that states a
changed configuration value. Removing a project requirement means removing all
active copies, not relocating or replacing it with a compensating approval gate.
