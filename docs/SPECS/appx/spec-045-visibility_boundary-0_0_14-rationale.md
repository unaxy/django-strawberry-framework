# Rationale: sealed `get_queryset` visibility-boundary policy artifacts (spec-045)

The deliberative layer of [`docs/SPECS/spec-045-visibility_boundary-0_0_14.md`][spec]. The spec
states the contract the [visibility boundary][glossary-visibility-boundary] offers and
nothing else; this file carries, for each of that spec's numbered decisions, the
alternatives that were rejected and why each lost.

Every entry names its spec decision by heading text and anchor, so a reader working
through the spec can look the deliberation up and a reviewer cannot re-litigate a settled
alternative without first reading why it lost.

Decision numbers are a package-wide identifier: source and test docstrings across
[`django_strawberry_framework/utils/querysets.py`][querysets],
[`django_strawberry_framework/optimizer/walker.py`][walker], and
[`tests/utils/test_querysets.py`][queryset-tests] cite them as `spec-045 Decision N`, so
renumbering a decision is a source-wide rename, not a documentation edit.

## Decision 1 — The hook's source and result are each sealed into a fresh clone

Spec decision:
[Decision 1][spec-decision-1]
(`#decision-1--the-hooks-source-and-result-are-each-sealed-into-a-fresh-clone`).

**Alternatives rejected.**

- *Returning the candidate object itself.* A hook may return an evaluated queryset or a
  class-level queryset shared across requests; `QuerySet.__getitem__` answers a window
  from a populated `_result_cache`, so the surface would serve stale rows shared between
  requests. `candidate.all()` costs one clone and reads the rows again.
- *Rebuilding a plain `QuerySet` from the candidate's state.* It drops the project's own
  queryset class, so a hook cannot call its project methods and a project method cannot
  chain after the cascade, and it reimplements `QuerySet._clone` by hand, which drifts
  from Django with every release.
- *Treating a `Manager` whose `all()` returns a list as the plain-iterable bypass.* That
  would skip the visibility hook for a value the consumer meant as a queryset, so the
  coercion refuses it instead.

## Decision 2 — The seal is a clone and a cheap shape check, not a proof

Spec decision:
[Decision 2][spec-decision-2]
(`#decision-2--the-seal-is-a-clone-and-a-cheap-shape-check-not-a-proof`).

**Alternatives rejected.**

- *Proving the candidate's whole query graph made of Django's own classes, then
  canonically reconstructing it.* That treats application Python as an in-process
  adversary, which GOAL.md "Trust boundary" rules out: a hook, a project `QuerySet` class
  and a sidecar override are trusted. The proof cost thousands of lines that tracked
  Django's private query internals release by release, refused legitimate project
  expressions, lookups and row iterables, and still could not contain code running in the
  same process.
- *A blacklist of method overrides on the consumer `QuerySet` class.* The same objection,
  with less coverage: an inventory of overrides is a proof by enumeration.

## Decision 3 — The identity fast path is removed; hook results are always re-sealed and result caches dropped

Spec decision:
[Decision 3][spec-decision-3]
(`#decision-3--the-identity-fast-path-is-removed-hook-results-are-always-re-sealed-and-result-caches-dropped`).

**Alternatives rejected.**

- *Keeping `result is queryset` as a performance shortcut.* A hook given the sealed
  source can evaluate it, or put rows in its `_result_cache`, and return that same
  queryset; an identity shortcut serves those rows without executing the SQL. Object
  identity proves that no *other* object was returned; it proves nothing about the
  object, which the hook has held and can change.
- *Restricting the fast path to a provably unoverridden package-default hook.* The
  second seal is one clone; the bookkeeping that would prove it unnecessary costs more.

## Decision 4 — Alias threading with `require_shared_alias` for planned children

Spec decision:
[Decision 4][spec-decision-4]
(`#decision-4--alias-threading-with-require_shared_alias-for-planned-children`).

**Alternatives rejected.**

- *Leaving the child seal unpinned.* Django deliberately supports explicit cross-database
  prefetching, so an unpinned child is not inert metadata: a `shard_b` parent with a child
  routed to `default` splits one resolution across two databases, and overlapping
  relation keys can populate a shard-B parent with rows read from the default database
  while the generated many-side resolver consumes the prefetch cache directly.
- *Treating an unrouted parent as licence for a routed child.* The rule is symmetric and
  explicit rather than a side effect of passing `None` down: an unrouted parent forces an
  unrouted child, and an unrouted child inherits the parent's alias.

## Decision 5 — Queryset-shape rejections

Spec decision: [Decision 5][spec-decision-5] (`#decision-5--queryset-shape-rejections`).

**Alternatives rejected.**

- *Passing a combinator through as it is.* Every recomposing surface narrows, projects or
  prefetches the sealed queryset, and Django refuses `.filter()` / `.only()` after a
  combinator and silently drops a reverse-FK `Prefetch`'s parent predicate from one. The
  primary-key rewrite is the one shape every surface can take.
- *Rewriting a combinator with a branch over another model.* The rewrite selects this
  model's rows whose primary key is in the combinator's set, so a branch over another
  table would match rows by an unrelated table's primary keys and serve the wrong rows
  silently; it fails closed as `table` instead.

## Decision 6 — Typed `ConfigurationError` fail-closed error contract

Spec decision: [Decision 6][spec-decision-6] (`#decision-6--typed-configurationerror-fail-closed-error-contract`).

**Alternatives rejected.**

- *Letting backend and interpreter exceptions propagate.* An `OperationalError` from
  malformed SQL leaks nothing actionable to the consumer and is not a fail-closed
  contract: the caller cannot distinguish a configuration mistake from a database outage.
- *A distinct exception class per defect code.* `ConfigurationError` stays the single
  typed boundary error and the code selects bespoke wording, with
  [`::SyncMisuseError`][querysets] the one subclass and only because it must also be
  catchable as `RuntimeError` for consumers catching that after the `FilterSet.apply`
  rethrow. A class per code would put a taxonomy in the public surface that no consumer
  asked to branch on.
- *Rendering the cascade's path-rich per-edge prose inside the shared boundary.* A
  caller-supplied `render_error` seam lets the shared checker own the codes and the
  caller own its wording, rather than the boundary accumulating per-caller message
  branches ([`::_visibility_result_error`][querysets]).
- *Ending each message ladder in an unconditional branch for its last code.* A code added
  to the seal without an arm at a site would then MISLABEL the rejection instead of
  failing loudly. Dispatch is exhaustive ([`::_defect_message`][querysets]): an
  unrendered code says it is a framework defect.

## Decision 7 — No version bump: the `0.0.14` cut already landed

Spec decision: [Decision 7][spec-decision-7] (`#decision-7--no-version-bump-the-0014-cut-already-landed`).

**Alternatives rejected.**

- *Treating this card as the release-cut owner (the lone-card version-bump shape).* The
  `0.0.14` release this card documents was already cut, so a documentation card at that
  patch line owns no bump.

## Decision 8 — Threat model: a mistaken hook, not an in-process adversary

Spec decision:
[Decision 8][spec-decision-8]
(`#decision-8--threat-model-a-mistaken-hook-not-an-in-process-adversary`).

**Alternatives rejected.**

- *Defending against a hook or project class that means harm.* Code running in the
  server process can reach the database connection, the request and every module the
  package imports; no check on the objects it returns contains it. The boundary's
  guarantee is the one GOAL.md "Trust boundary" states: what the wire sends cannot widen
  the rows a declared contract admits, and a mistaken return fails closed.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

[glossary-visibility-boundary]: ../../GLOSSARY.md#visibility-boundary

<!-- docs/SPECS/ -->

[spec]: ../spec-045-visibility_boundary-0_0_14.md
[spec-decision-1]: ../spec-045-visibility_boundary-0_0_14.md#decision-1--the-hooks-source-and-result-are-each-sealed-into-a-fresh-clone
[spec-decision-2]: ../spec-045-visibility_boundary-0_0_14.md#decision-2--the-seal-is-a-clone-and-a-cheap-shape-check-not-a-proof
[spec-decision-3]: ../spec-045-visibility_boundary-0_0_14.md#decision-3--the-identity-fast-path-is-removed-hook-results-are-always-re-sealed-and-result-caches-dropped
[spec-decision-4]: ../spec-045-visibility_boundary-0_0_14.md#decision-4--alias-threading-with-require_shared_alias-for-planned-children
[spec-decision-5]: ../spec-045-visibility_boundary-0_0_14.md#decision-5--queryset-shape-rejections
[spec-decision-6]: ../spec-045-visibility_boundary-0_0_14.md#decision-6--typed-configurationerror-fail-closed-error-contract
[spec-decision-7]: ../spec-045-visibility_boundary-0_0_14.md#decision-7--no-version-bump-the-0014-cut-already-landed
[spec-decision-8]: ../spec-045-visibility_boundary-0_0_14.md#decision-8--threat-model-a-mistaken-hook-not-an-in-process-adversary

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

[querysets]: ../../../django_strawberry_framework/utils/querysets.py
[walker]: ../../../django_strawberry_framework/optimizer/walker.py

<!-- tests/ -->

[queryset-tests]: ../../../tests/utils/test_querysets.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
