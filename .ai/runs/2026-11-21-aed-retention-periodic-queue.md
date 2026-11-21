# Kolejka periodic dla zadania retencji AED
Issue: APP-53
Run: de80de87-640d-4a10-a897-a25de42e2ddf
Source doc: .ai/specs/2026-11-21-aed-report-retention.md (section "Poprawka: kolejka zadania (APP-53)")
Route: agreed small change (coordinator, from the L4 #13 review)

## Progress
1. [x] Test RED, queue option (GREEN).
2. [x] Full gate.
3. [ ] PR, independent review, merge after L8 #11.

## Evidence
- Investigation: the Compose celery worker runs without `-Q`, so it consumes every queue in CELERY_TASK_QUEUES (including `default` and `periodic`); the task ran before, the fix is for the upstream rule in backend/mcod/tests/test_celery.py.
- RED: `BeatScheduleTests` failed with `AssertionError: None != 'periodic'`; GREEN after adding `options.queue = 'periodic'`.
- Full gate on main 6c85269 + this change: source verifier, compose config, 62 Django tests OK, copy check, client config: all exit 0.
- Upstream pytest cannot run (pytest is not installed in the image). Equivalent check in the live app config: all beat entries have a named queue; both AED entries use `periodic`.
- Limit: upstream `test_all_nonbeat_tasks_have_queue_defined` derives beat task names from `get_beat_schedule()` only, so app-registered beat tasks (this one and `aed_refresh_task`) would still be reported there; fixing that needs an upstream file (celeryapp.py or base settings) and is out of scope.
