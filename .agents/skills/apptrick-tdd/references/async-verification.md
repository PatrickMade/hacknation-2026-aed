# Observe asynchronous completion

Use this when tests sleep for an estimated duration or fail intermittently while
waiting for work. Prefer the framework's retrying assertion, an awaited operation,
or an event subscription over a custom polling helper.

```typescript
// Fragile: elapsed time does not establish that the job completed.
await sleep(50);
expect(await jobState(id)).toBe('complete');

// Illustrative: the project's retrying assertion observes fresh state.
await expect.poll(() => jobState(id), { timeout: 5000 }).toBe('complete');
```

Use the runner's equivalent; this example does not authorize adding a dependency.
Choose the timeout from the operation's expected bound and test environment, not
from this example. On timeout, report the awaited condition and last observed
state. Do not catch an unexpected exception and turn it into a successful retry.

Subscribe before triggering an event so fast completion cannot be missed. Read
fresh state on each retry, bound the wait and dispose listeners or timers after
success and failure. Do not prescribe one polling interval for every system.

When time itself is the behavior, such as a debounce window, use the project's
fake clock where supported. Advance to just before and at the required boundary
and assert the result. If a real delay is necessary, explain which timing contract
it measures; a generous sleep alone does not prove ordering or completion.
