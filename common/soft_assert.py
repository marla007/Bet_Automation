"""Soft assertions (shared by UI and API tests): collect every failed check and report
them all at the end of the test.

A normal assert stops the test at the first failure, so later bugs stay hidden.
SoftAssert keeps going and lists every mismatch in one AssertionError.
"""


class KnownBugFailure(AssertionError):
    """Raised when EVERY failed check belongs to a known bug.

    Tests mark known bugs with @pytest.mark.xfail(raises=KnownBugFailure). Any other failure
    (a new bug, a broken locator, a timeout) raises a plain error instead, so pytest reports
    it as FAILED rather than hiding it as an expected failure.
    """


class SoftAssert:
    def __init__(self, on_fail=None):
        """on_fail: optional function called with the check label when a check fails.
        UI tests pass a screenshot function, so every failed check gets its own screenshot."""
        self.errors = []
        self.on_fail = on_fail

    def equal(self, actual, expected, message):
        if actual != expected:
            self._fail(f"{message}: expected {expected!r}, got {actual!r}", message)

    def true(self, condition, message):
        if not condition:
            self._fail(message, message)

    def assert_all(self, known_bugs=()):
        """Call once at the end of the test.

        known_bugs: bug IDs this test is expected to hit, e.g. ("BUG-03", "BUG-04").
        If every failed check starts with one of them -> KnownBugFailure (expected failure).
        If any failed check is new -> plain AssertionError (real failure).
        """
        if not self.errors:
            return
        report = "\n".join(f"  - {error}" for error in self.errors)
        message = f"{len(self.errors)} check(s) failed:\n{report}"
        new_failures = [error for error in self.errors if not error.startswith(tuple(known_bugs))]
        if known_bugs and not new_failures:
            raise KnownBugFailure(message)
        raise AssertionError(message)

    def _fail(self, error, label):
        self.errors.append(error)
        if self.on_fail:
            self.on_fail(label)
