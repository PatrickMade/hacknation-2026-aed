# Boundaries, mocks and refactoring

Read this when a test is difficult to arrange or a green slice exposes duplication.
Keep existing framework conventions and project-specific test doubles.

Inject an external dependency through an existing seam when that makes behavior
controllable. For example, a payment client can return a decline without making a
real charge. Avoid adding a wrapper or public interface solely to satisfy an
abstract testing pattern.

Prefer real internal collaborators when they are cheap and deterministic. A mock
is justified when it isolates a relevant failure, follows the project's fixtures,
or avoids unrelated expensive setup. Do not replace established Spring test beans
or similar fixtures just because they are internal. Check the observable result,
not every internal call.

For external adapters, assert the required request, result mapping and meaningful
failure paths. Decide between a test database and a double from the contract under
test: a mocked query cannot prove database constraints or transaction behavior.

## Keep interfaces small for a concrete reason

A function accepting a payment dependency is easier to control than one creating
a live client internally. A calculation that returns a value is often easier to
check than one that also sends a message. Separate those concerns only when the
current behavior benefits; side effects still require tests through their actual
boundary.

While GREEN, consider duplication, hidden coupling or a long method exposed by
the completed slice. Extract a helper or move logic only if it simplifies that
case without changing the public contract. Re-run affected tests after each change.
Do not add value objects, layers or guards without a current requirement.
