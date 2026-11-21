# Test behavior through the project's interface

Use these examples when choosing an assertion or reviewing a test coupled to
implementation details. Syntax is illustrative; use the project's test runner.

```typescript
// Behavior remains observable even if payment internals change.
const result = await checkout(cart, declinedPayment);
expect(result.status).toBe('declined');
expect((await getOrder(result.orderId)).paid).toBe(false);
```

A test that only asserts `paymentService.process` was called would not establish
either result. Prefer assertions about the contract callers depend on. Interaction
assertions are appropriate when the interaction is itself the requirement, such
as sending exactly one message with a required payload.

For persistence, test through the relevant read interface when it exposes the
required behavior. Direct database assertions can be necessary for a migration,
constraint or repository contract; do not add a public getter solely for a test.

Implement one useful slice, prove GREEN, then choose the next slice. Do not draft
a large speculative test suite before checking the first behavior. A declined
payment and a successful payment may need separate tests; several assertions can
describe one coherent outcome.

## Distinguish RED from broken setup

A regression test must fail at the assertion for the defect. A fixture that
cannot start, an unsupported mock, or a missing credential is a setup failure.
Record the command, exit status and relevant assertion output, then show GREEN
against the corrected code. Tests added after a fix require a comparison against
unfixed code in an isolated copy before claiming regression proof.

For a behavior-preserving refactor, record characterization tests passing before
and after. Do not manufacture a failing test when behavior is meant to stay the same.
