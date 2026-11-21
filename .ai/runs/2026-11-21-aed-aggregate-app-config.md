# Register the aed_aggregate AppConfig - execution plan

Issue: APP-52
Run: app52-20261121T201235Z
Branch: fix/aed-aggregate-app-config (from origin/main fa95741)
Source doc: .ai/specs/2026-11-21-aed-aggregate.md (section "Follow-up APP-52")

## Steps

- [x] 1. Regression test test_app_config.py: RED on main (plain AppConfig loaded instead of AedAggregateConfig)
- [x] 2. default_app_config in mcod/aed_aggregate/__init__.py: GREEN
- [x] 3. Validation gate, review (APPROVE on 41b1de4), PR #13
- [ ] 4. Review minor: beat entry on the `periodic` queue; update from main; gate; review record; merge

## Progress

- RED: `manage.py test mcod.aed_aggregate.tests.test_app_config` -> AssertionError: <AppConfig: aed_aggregate> is not an instance of AedAggregateConfig.
- GREEN after the fix: 1 test OK.
- 41b1de4: fix + test; independent review APPROVE with one minor (beat entry used the default queue).
- Queue: test asserting `options.queue == 'periodic'` failed with KeyError: 'options'; passes after tasks.py adds the option.
