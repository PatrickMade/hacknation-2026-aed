# Adopt portable delivery metrics

Apply independently of upgrade-log availability, after the complete package has
been updated and checked by its owning installer. Honour `--dry-run`, `--yes`
and local policy; this procedure never edits managed skill copies.

1. Require the installed `apptrick-report-task-metrics` and its checkpoint helper.
   Missing files are a package-update prerequisite, not permission to fetch a
   companion or use global copies. Inspect the pinned lock's client roots.
2. Detailed time/token capture is opt-in. Leave a missing `metrics.enabled`
   unset (capture stays off) and report the opt-in change and how to enable it.
   Preserve all explicit settings, including an existing `true` or `false`,
   private local bindings and unknown fields. A second upgrade makes no changes. Invalid/conflicting settings are a named
   migration gap, never an excuse to overwrite local customisation.
3. Leave destination unbound unless the owner has already approved it. Report
   the installed setup skill's metrics onboarding procedure by skill name;
   never copy a pilot credential, infer project membership, modify IAM/OAuth or
   change global client configuration. Existing native login is developer-local.
4. Preserve historical reports, revisions and pending publication identities.
   Keep existing project extension hooks. If both local and shipped workflows
   invoke the reporter at the same boundary, reconcile their ownership explicitly
   before enabling the new hook: one invocation and one unchanged revision.
   Later collection does not reconstruct missing history or reset run identity.
5. Verify config parsing, capture/helper package files and local runtime privacy.
   Report capture/reporting readiness separately from actual native receipt
   evidence and membership/login gaps. Leave project edits uncommitted per this
   skill's normal handback contract.
