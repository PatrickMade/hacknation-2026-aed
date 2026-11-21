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

Inspect actual endpoint values and launch-time profiles before running anything.
List integration writes, email, payments, webhooks, scheduled jobs and migrations.
Local/test mode does not prove isolation. Prefer existing stubs, test accounts and
synthetic fixtures; override dangerous endpoints before startup and verify the
exercised write reaches the stub. GET can have side effects too. Browser-domain
restrictions do not isolate server egress or other tools. Unknown consequential
side effects block the affected live test pending evidence or explicit authority.

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
