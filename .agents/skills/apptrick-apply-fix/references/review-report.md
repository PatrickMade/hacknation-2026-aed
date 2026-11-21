# Review hand-off - authoritative review runs after PR creation

`apptrick-apply-fix` validates and hands the change to the PR-opening step. The chain performs its single authoritative code-review pass later through `apptrick-review`.

## apptrick-apply-fix specifics

The later `apptrick-review` pass must apply these checks to a fix produced from an analyzer brief:

- No API response fields removed.
- No data-scoping or permission-check rules weakened; the project's data-access conventions followed in every changed production file.
- Fix remains minimal - edit only what the analyzer named plus tests; refactors belong in their own PR.

Do not run `apptrick-review-code` directly in `apptrick-apply-fix`; `apptrick-review` invokes it once after `apptrick-open-pr`, driven by `apptrick-deliver` or the external flow runner.
