# Rationale: spec-050 — DjangoListField argument surface (deliberation and rejected alternatives)

Deliberative companion to [`spec-050-list_field_arguments-0_0_15.md`][spec-050]. The spec is the
contract; this file holds the alternatives each decision rejects and why each loses, and the
derivations that do not change how a decision is implemented.

## How to read this file

- **One entry per spec decision that has rejected alternatives or a derivation**, under the
  decision's own heading and anchor, so a citation such as "Decision 1's rejected alternatives"
  resolves to exactly one place. A decision with neither has no entry.
- **Load-bearing carve-outs.** Two things stay in the spec even though they read like
  deliberation: the parallel signature builder in [Decision 1][spec-050-d1] (importing the
  connection's builder would close a module cycle, because `connection.py` imports `list_field.py`),
  and the strict pipeline ordering with mechanical validation in [Decision 5][spec-050-d5]
  (visibility precedes ordering, which precedes slicing). When it is unclear whether a sentence is
  deliberation or instruction, it stays in the spec.

## Deliberation that belonged to no single decision

### Borrowing posture — what was deliberately not borrowed and why

- **From `graphene-django` connection semantics:** Refuses Relay cursor conversion, `before`
  composition, and connection-wide publication. Graphene pops `offset`, combines it with `after`,
  and converts the result back to a Relay offset cursor; `connection_resolver` additionally
  rejects `before` plus `offset`. Those make a skip look like a cursor while retaining skip
  instability. The package borrows only the discoverable spelling `offset: Int` on the flat-list
  field.
- **From `strawberry-graphql-django` pagination:** Refuses silent max-limit clamp, negative-limit
  unbounded spelling, generated result envelope, decorator surface, and nested raw-list window.
  Upstream's negative spelling reaches an unbounded tail when its maximum-limit clamp is
  disabled, which is the shipped default; when configured, the clamp silently rewrites that
  spelling to the maximum. Both behaviors are refused here. This package has a fail-closed
  resource policy, a Meta-class public API, and connections for nested windows.
- **From this package's connection field:** Refuses importing the connection's filter input,
  total-order tiebreaker, cursor codec, the Strawberry [`ConnectionExtension`][strawberry-relay-fields]
  that slices its page, or page-size rules. Reuses only the lazy sidecar signature synthesis
  mechanism and the `order_input_type` helper.

### Risks and open questions — the fallback positions

The spec keeps each risk and its preferred answer; the fallbacks, should a real consumer need
appear, are:

- **`orderBy` is published only where the target declares `Meta.orderset_class`:** Fallback if
  universal publication is required: choose a dynamic `OrderSet` policy explicitly first; never
  JSON or a dummy input as an invisible workaround.
- **GraphQL coercion errors cannot carry the package runtime code:** Fallback if one code is
  mandatory: a schema-wide audited error-normalization feature, not a weakened scalar local to
  this field.
- **Active order does not prove uniqueness, so the delivered contract is weaker than the words "stable subset" suggest:**
  Fallback: an opt-in deterministic list-order policy; never a silently appended pk.
- **The sync early-exit cleanup contract is declined, not solved:** Fallback once evidence shows
  retained sync generators leak in practice: one shared sync `close()` contract at the same
  bounding seam, carded on its own because it changes shipped relation-list behavior.
- **Document collection-cost accounting and the runtime coordinate ceilings are two different budgets and visibly disagree:**
  Fallback if the divergence becomes unacceptable to the resource-policy threat model: field
  metadata consumed by the walker, with its own evidence; never argument-name matching.
- **Nested `DjangoListField` arguments are unspecified while the glossary promises nested usage is functional:**
  Fallback: a deliberate deprecation that pays the compatibility cost explicitly.
- **`max_list_rows` may be too small as a migration offset ceiling:** Fallback after evidence: a
  distinct `ResourcePolicy.max_list_offset` bound in a dedicated policy change with its own
  document cost semantics.
- **Ordering an already-sliced consumer queryset is a migration trap:** Fallback: require the
  consumer resolver to return an unsliced base queryset; there is no safe filter/reorder-after-slice
  mode and no identity-hook exception.
- **Arbitrary custom `OrderSet.apply_*` code can discard visibility predicates:** Fallback if a
  product requires enforcement against consumer code itself: redesign `OrderSet` to return a
  declarative order plan; never claim predicate-lineage proof from arbitrary Python.
- **Django combined querysets do not compose uniformly with order and optimizer operations:**
  Fallback for a combined shape the primary-key rewrite cannot represent, should a real consumer
  need it: carded combinator-aware behavior with its own SQL matrix; until then the shape fails
  closed.
- **Upstream is retiring the instance spelling Decision 14 reads as a declaration:** Fallback
  when upstream removes instance entries: the ladder row goes with them and no shim re-admits the
  spelling; a consumer on that spelling migrates to the class or factory upstream documents.

## Decision entries

### Decision 1 — synthesize one resolver signature; do not widen consumer resolvers

Spec: [Decision 1][spec-050-d1].

*Alternatives rejected:*

- **Forwarding arguments to consumer resolvers:** Rejected because it would break every existing
  two-parameter resolver (`resolver(root, info)`) and would split the package contract between
  default and consumer fields.
- **Inspecting consumer signatures and forwarding only accepted names:** Rejected because
  behavior would change when a parameter is renamed and because the package, not the consumer,
  must own validation and slice ordering.

### Decision 2 — sidecar-conditional `orderBy` is the only truthful Meta-first surface

Spec: [Decision 2][spec-050-d2].

*Alternatives rejected for `orderBy`:*

- **Auto-generating an `OrderSet` from every model:** Would reverse a standing public decision,
  expose relation and column choices the consumer never approved, and create different ordering
  inputs for the same `DjangoType` depending on which field factory referenced it.
- **A JSON argument:** Would erase schema validation and the discoverable `Ordering` enum.
- **An empty placeholder input / dummy field:** An empty placeholder input is invalid GraphQL,
  while a dummy field or always-rejected enum would publish a capability that cannot succeed.
- **Requiring every `DjangoListField` target to declare `Meta.orderset_class`:** Would be a
  breaking change to the existing pagination-independent field.

*Capability rules rejected for `offset`:*

- **Publishing `offset` only where a declared order source exists:** Rejected because that source
  may be a model `Meta.ordering` that a consumer resolver clears at runtime, so the argument's
  presence still would not predict its usability — it would move the dishonesty into SDL instead
  of removing it.
- **Accepting a resolver's own `.order_by(...)` as a documented contract:** Rejected because
  hidden order cannot explain to a client why one field accepts offset and an otherwise-identical
  one does not.
- **Explicit Meta-first stable-order declaration:** Not refused on its merits, and not shipped:
  it is a new public Meta key, which needs its own parity evidence.

### Decision 4 — `max_list_rows` also bounds skip; trusted widening does not

Spec: [Decision 4][spec-050-d4].

*Alternatives rejected:*

- **A dedicated `max_list_offset` setting:** The two limits protect the same raw-list operation,
  and a new setting adds deployment surface before evidence shows the limits need to differ.
- **Requiring `offset + limit <= max_list_rows`:** Would make the accepted `limit` depend on
  `offset`, turn an otherwise-valid page into an error as it moves forward, and make the
  explicitly accepted `offset == max_list_rows` useful only with `limit: 0`.
- **Teaching the collection-cost walker to infer semantics from argument spelling (`_collection_rows` name matching):**
  The walker is schema-generic, with no trustworthy marker distinguishing this factory's
  validated `limit` from an unrelated consumer argument of the same name; inferring semantics from
  spelling would undercharge arbitrary lists.

*Derivation of coordinate ceilings vs scan budgets and collection-cost fixed estimate:*

- `max_list_rows` keeps its returned/materialized-row meaning on the return dimension and is
  reused as a separate accepted-skip ceiling. Both are accepted coordinate ceilings, not scan
  budgets: they bound what a client may ask for, never what the backend plan does to satisfy it.
  Even a small offset can force a sort or a large scan of a filtered relation, a to-many aggregate
  order can add `GROUP BY`, and high offsets commonly degrade with table size. The request deadline
  does not close that gap either: `check_deadline` is a cooperative check before each fetch, so it
  can refuse to start a query and cannot interrupt one already dispatched.
- The pre-execution collection-cost walker charge is a schema-generic fixed estimate, not a
  conservative upper bound. It overcharges when a field or a client narrows below the policy, and
  undercharges when positive offset admits up to another `max_list_rows` of logical skip work, or
  when `trusted_max_rows=True` returns more rows than charged. The accepted logical window is still
  bounded (`offset + returned <= 2P` untrusted, `P + F` trusted), but enforced at runtime, not by
  document accounting.

### Decision 5 — validate, then visibility, ordering, and exactly one slice

Spec: [Decision 5][spec-050-d5].

*Alternatives rejected:*

- **Comparing resolved aliases as the routing invariant:** Resolving the returned candidate's
  alias would call the consumer's router mid-validation, over hint state the override has already
  had. The seal instead compares routing intent (`_db` plus `_hints`, hint values by identity),
  which dispatches no consumer code during validation; the one router answer is taken at the
  snapshot, before the override runs, and the accepted result is pinned to it.
- **A fresh pagination helper that calls `bounded_rows` and then slices:** Rejected because it
  would either double-slice or apply offset after truncating the source. The seam runs the other
  way: `bounded_rows` delegates down to the private window seam, which slices once with the bound
  already known, and nothing sits above the exported helper re-slicing its output.
- **In-coroutine list materialization (`many_resolver` pattern):** The generated relation resolver
  in `many_resolver` materializes inside its own coroutine (`[row async for row in bounded]`) and
  hands graphql-core a plain list. That is correct for a relation, which is a leaf of an
  already-planned parent query. It is wrong for a root list: the root plan is applied to the value
  the resolver returns, so materializing before returning would hand `DjangoOptimizerExtension` a
  list with no queryset left to plan, silently dropping root-list optimization on every async
  request while every assertion about rows and SQL still passed.

*Derivation on the cost of the third seal:*

- The visibility boundary seals twice (source and hook result), and a supplied `orderBy` adds a
  third seal over the override's return. Each is a shape check and one `QuerySet.all()` clone,
  paid on every request that supplies an order.

### Decision 6 — nonzero offset requires a materially active order

Spec: [Decision 6][spec-050-d6].

*Alternatives rejected:*

- **Silently accepting unordered offset (Graphene-Django):** Database default order can change
  between requests, query plans, or backends. Graphene-Django's connection accepts offset without
  an ordering precondition, producing nondeterministic results.
- **Silently injecting `order_by("pk")` (Strawberry-GraphQL-Django):** Silently injecting
  primary-key tiebreakers changes SQL and usurps a consumer ordering choice; the no-argument fast
  path additionally must remain byte-identical. Unlike a connection, a list mints no cursor that
  requires a package-owned total order.
- **Classifying a string term from the name as written:** A relation name in a string is not a
  column. [`SQLCompiler.find_ordering_name`][django-compiler] replaces a path ending on a
  relation with the related model's own `Meta.ordering`, so a classifier that stops once a name
  resolves to a field certifies a default it never read and serves a positive offset over a
  result set the database re-shuffles. Reading the name as far as the compiler reads it is the
  same rule the annotation and `extra` steps already follow, one indirection further.
- **Treating a node as transparent because its children are readable:** Django publishes no
  such contract. `Func`, `Transform`, `Aggregate` and `Window` all emit SQL of their own around
  their sources, and any expression can be subclassed with an `as_sql` that emits anything -
  so a rule reading "has source expressions, therefore orders by them" certifies a one-class
  project expression spelling `RANDOM()` over a column, and a project transform registered on a
  built-in field does the same inside a predicate. Both reach the wire through `Meta.ordering`
  and a plain `offset` request. The approved-forms list matched by exact type inverts the
  exposure: a form nobody listed costs a refused request, where an unlisted volatile class would
  cost a silently re-shuffled page. Exact type rather than `isinstance` is the load-bearing half -
  a subclass of a pure function is a different `as_sql` wearing an approved name.
- **Reading only the value side of a predicate:** A comparison has two operands and both are
  compiled. A classifier that reads the value alone accepts `When(coin__gt=0.5)` over a random
  alias while refusing `order_by("coin")`, which makes the predicate a spelling that buys what
  the direct one is denied - the guard's rule is about the SQL the rows are ordered by, and a
  bypass reachable by rewriting the same order as a condition is not a narrower rule but a
  missing one.
- **Reading an expression reference through that same expansion:** It is the mirror error, and
  it refuses requests Django answers deterministically. Only strings reach
  `find_ordering_name`; [`Query.resolve_ref`][django-query] resolves an `F` to a column and
  never consults the related model's ordering, so `F("branch").asc()` is the foreign key order
  and classifying it like the string `"branch"` would reject a page over a stable column
  because a model it never orders by declares `Random()`. One resolution rule for both
  spellings is wrong in one direction or the other; the compiler's two rules are the contract.
- **Admitting the two reference forms by `isinstance`:** It leaves the approved list exact
  everywhere except at the two arms that run first. `F` and `Q` carry no `as_sql`, so what a
  subclass of either substitutes is `resolve_expression` - the compiler receives whatever that
  returns, while the classifier is still reading a column name or a set of children that never
  reach the statement. `Meta.ordering = (VolatileF("code"),)` is an ordinary model declaration,
  and `Case(When(VolatileQ(code__gt=...), ...))` wraps the same substitution in a composition
  the spec approves, so both would serve a positive offset over a re-shuffled result set. Exact
  type at every arm is one rule; exact type at the arms that happen to be reached last is a
  boundary with a door in it.
- **Deciding a term's form from its own Python type before asking whether it resolves:**
  [`_order_by_pairs`][django-compiler] asks for `resolve_expression` first and reads a term as a
  string only when it has none, so a `str` subclass carrying that method is an expression to
  Django and a field path to a classifier that tests for `str` first. The two readings disagree
  about the whole statement, not about a detail of it. Dispatching in the compiler's own order
  costs nothing and removes the disagreement: a name that resolves is classified as what it
  resolves to.

### Decision 7 — active order is not total order; no pk tiebreaker is appended

Spec: [Decision 7][spec-050-d7].

*Alternatives rejected:*

- **Requiring a provably total order and rejecting unprovable ties:** Infeasible over arbitrary
  Django expressions and backend-dependent even where possible.
- **Appending a deterministic terminal term:** Semantic change to requested order priority that
  would break no-argument SQL parity. Keeping the active-order guard while declining the stronger
  promise makes a unique final term a consumer documentation recommendation rather than framework
  enforcement.

### Decision 8 — queryset and iterable sources have explicit, different capabilities

Spec: [Decision 8][spec-050-d8].

*Alternatives rejected:*

- **Short-circuiting `None` after numeric-domain validation:** Capability check outranks null
  propagation; an unsupported argument must not succeed merely because the underlying field
  resolved to `None`.
- **Adding an early-exit `close()` on sync iterators:** `bounded_rows` is also the bound for
  every generated relation list, so closing a consumer's retained generator would be an
  observable behavior change on every relation list, not only on this field.
- **Directly reading `source.query.is_sliced` or importing the private seal in list field:**
  Would duplicate the shared classifier in the visibility boundary.
- **Treating `isinstance(value, QuerySet)` as the slice test:** `isinstance` falls back to the
  value's own `__class__`, so a non-queryset could select the SQL-slice arm. The test reads the
  real class instead.
- **Exact type plus `islice` as the whole fix:** Restores the row ceiling and loses the SQL one.
  A project queryset class returned by a custom manager is ordinary Django, and demoting every
  one of them to a counted Python truncation would fetch the whole relation to discard its tail
  - trading a wire-level bound for a database-level regression. A project queryset class is
  application code, trusted under GOAL.md "Trust boundary", so it is sliced as itself.
- **Rejecting every `QuerySet` subclass outright:** `Manager.from_queryset` and
  `QuerySet.as_manager` are the documented way to give a model its own queryset class, so this
  would refuse ordinary Django.

*Rejected — re-querying the relation instead of windowing its fetched rows:* The cached rows
are already in memory. Re-fetching them costs one query per parent row, and under async one
worker hop each.

*Rejected — mounting the live proof on a shape that never reaches the branch:* replacing the
reverse relation manager's queryset class. The optimizer seeds the generated `Prefetch` child
from the related model's `_default_manager.all()`, and Django's `prefetch_one_level` caches
`manager._apply_rel_filters(lookup.queryset._chain())`, so that mount leaves an exact `QuerySet`
in the cache and a row over it passes while exercising nothing. The live rows mount the model's
default manager instead (`Loan.objects = LoanQuerySet.as_manager()`).

### Decision 9 — a request with no list argument runs the plain bounded path; async only adapts completion

Spec: [Decision 9][spec-050-d9].

*Derivation of the LIMIT/OFFSET contract:*

- "LIMIT/OFFSET present exactly when supplied" does not describe a raw list: no-argument raw lists
  carry a policy LIMIT through `bounded_rows` ([`spec-047`][spec-047]). The contract is: omission
  preserves the existing policy LIMIT unchanged, a smaller client limit lowers the high mark, and a
  positive offset raises the low mark.

### Decision 10 — coercion errors stay GraphQL-owned; runtime domain errors are package-owned

Spec: [Decision 10][spec-050-d10].

*Alternatives rejected:*

- **A custom stricter integer scalar:** The published arguments are `Int`, and over-ceiling
  validation still needs request context unavailable to scalar coercion.
- **A schema extension rewriting all `Int` coercion errors:** Overbroad and unable to reliably
  identify which argument failed after validation.

### Decision 12 — graphql-core workarounds have a dependency-owned lifecycle

Spec: [Decision 12][spec-050-d12].

*Decision:* graphql-core owns asynchronous list completion and the package installs no
graphql-core patch; a graphql-core workaround, when one is needed, lives in its own patch module
gated by its own `APPLY_UPSTREAM_PATCHES` dependency key.

*Why:* The patched callable, upstream release cadence, retirement signal, and consumer opt-out
of such a workaround all belong to graphql-core. Strawberry happens to invoke that executor, but
its connection-page patch has a different owner and a different retirement condition. One module and
gate per patched dependency keeps disabling or retiring either workaround from silently changing
the other.

*Rejected:* Keeping a graphql-core executor wrapper in `_strawberry_patches.py` because
graphql-core is a transitive Strawberry dependency. That makes dependency topology decide
lifecycle ownership, couples unrelated escape hatches, and lets a Relay opt-out restore an
executor bug.

*Why upstream completion owns a queryset a resolver returns:* the completion order is
graphql-core's, and its asynchronous executor completes a value exposing `__aiter__` through
it. Strawberry turns that off for its synchronous executor only, so a synchronous operation
nested inside an asynchronous one keeps synchronous completion. Any value offering both
protocols completes the same way, a Django `QuerySet` included, so the package adds no
completion rule of its own for a resolver's return value.

*Rejected - the optimizer as the completion owner:* wrapping the planned root queryset in
`DjangoOptimizerExtension` would serve only roots the optimizer sees, so a schema without the
extension and every nested resolver would complete differently, and a completion owner beside
upstream's and the list field's would split one rule across modules.

*Rejected - running a plain `def` root resolver in a worker thread:* the resolver is application
code whose color the consumer chose; moving it off the loop changes which thread its
thread-locals and connection belong to for every resolver, not only the ones returning a
queryset, and contradicts Decision 5's callable-color rule. The package completes what a
resolver returns; what its body does stays where the executor runs it.

### Decision 13 — configuration authority is schema state; everything per-request is operation state

Spec: [Decision 13][spec-050-d13].

*Rejected:* Holding per-operation state on the extension instance. Strawberry hands the SAME
object to every operation for an instance entry and for a factory returning one long-lived
object, so one slot is written by two requests: a nested `info.schema.execute_sync(...)` leaves
the inner document in it, and two overlapping requests leave whichever assigned last. The charge
then lands on a benign document while the oversized one executes, and the mask lands on a result
that is not the one going to the client.

*Rejected:* Making the engine's `execution_context` assignment the authority. It would have to
survive a consumer entry's setter raising midway through that loop - a failure with no package
teardown to run, because no runner exists yet - and it is writable from a resolver, which can
forge a context naming the real schema as often as it likes.

### Decision 14 — an enforcement authority is a declaration, never an extension entry

Spec: [Decision 14][spec-050-d14].

*Rejected:* Deduplicating by identity - accepting an entry that IS the package's extension and
dropping the automatic one. Identity evidence authenticates the object, not what it will do on
the next operation, and the three spellings that keep identity while changing behavior (a
stateful factory, a closure over a mutable cell, a singleton selector) are exactly the ones a
resolver can reach through `info.schema.extensions`.

*Rejected:* Calling factories at construction so they could be typed there. It breaks the
fresh-per-operation lifecycle the optimizer's documented singleton-in-a-factory depends on, and
what a factory returns next is decided after the entry was accepted anyway.

### Decision 15 — the runner owns every binding, for the operation's whole lifetime

Spec: [Decision 15][spec-050-d15].

*Rejected:* Binding only around the operation scope. Upstream collects extension results AFTER
the synchronous operation teardown has unwound, and drives a streamed operation's frames from
whatever task holds the iterator, so both would read for no operation at all.

*Rejected:* Promising the raw-`strawberry.Schema` path the same isolation. That schema never
calls the package's runner factory, so the guarantee would be a claim with nothing behind it
for a shared instance; a class entry and a fresh factory are operation-local there because the
object is.

### Decision 16 — a factory resolving to an authority is an ordinary entry

Spec: [Decision 16][spec-050-d16].

*Rejected:* Refusing such a factory, on the wire with a coded refusal or by raising out of
extension resolution. Either contains a factory the deployment itself wrote; application Python
is trusted (Decision 19), and the schema's own authorities still bound and mask the request.

### Decision 17 — the configuration code stays exported

Spec: [Decision 17][spec-050-d17].

*Rejected:* Deleting the exported constant. It is root-exported public surface, and a consumer
matching on it is not broken by the schema no longer emitting it.

### Decision 18 — execution mode is operation state; the ambient event loop is a different fact

Spec: [Decision 18][spec-050-d18].

*Rejected:* Keeping `strawberry.utils.inspect.in_async_context` as the dispatch predicate. It
answers whether a loop is running in this thread, which is the right question for ORM safety and
the wrong one for executor dispatch; the two disagree precisely where the package supports
nesting a synchronous operation inside an asynchronous one.

*Rejected:* A list-field-local `ContextVar`. The same false predicate would sit in every sibling
field factory and relation resolver, so a field-local fix would leave two definitions of
execution color in the package and the defect in all the other ones.

*Rejected:* Blocking the event-loop thread - taking the synchronous branch under a running loop
and letting Django raise. The error names none of the cause, arrives from the ORM rather than
from the call that caused it, and a partially completed operation is worse than a refusal.

*Rejected:* Falling back to the synchronous branch silently when the mode is unknown. The one
place the mode is unknown is a plain `strawberry.Schema`, where ambient dispatch is what
upstream already does and what the documented spelling relies on; inventing a different answer
there would change a working path for schemas the runner was never asked to own.

*Derivation:* The `sync` flag `get_extensions` receives is the authoritative statement -
`execute_sync` is the only entry point that sets it, and `execute`, `stream` and `subscribe` all
leave it false. Nothing upstream carries that flag from `get_extensions` to
`create_extensions_runner`, and recording it on the schema would be the one-slot-two-operations
defect Decision 13 exists to close, so it travels as a member of the chain built for that one
operation.

### Decision 19 — application code is trusted, the wire is not; a finding is admitted by reachability

Spec: [Decision 19][spec-050-d19].

*Decision:* Django's reachability rule is this package's admission criterion; the three trust
levels are named; the shipped hardening stays for the ordinary-mistake class it guards.

*Why:* Each piece of shipped hardening has a legitimate job - cross-request error disclosure, a
budget charged to the wrong document, a nested operation corrupting the optimizer's frame, a
bound read from an object a resolver could overwrite - and each of those is reachable from
ordinary application code under ordinary load. A threat model that counts a consumer's own
Python as an adversary has no finish line: every repair of one construction exposes the next
(a `__class__` that lies, a `__getitem__` that ignores its slice, a `__bool__` that raises), and
the refusal vocabulary grows faster than the feature. Django's security policy already draws the
line this package needs, and a package running on Django cannot honestly promise more than
Django does about code inside the same process.

*Rejected:* Treating application Python as hostile. It is unenforceable - in-process code can
import, monkeypatch and rebind any package name - so every check it motivates is a check the
adversary it imagines steps around, and each one costs a real consumer a refusal path to learn.

*Rejected:* An architectural rewrite - one `ContextVar`, fresh adapters per operation, a
separately shared optimizer cache - judged by how much it deletes. The operation-state modules
(`extensions/operation_state.py`, `utils/execution_mode.py`) each carry a
guarantee ordinary code needs (nesting, concurrency, streaming resumption, masking the right
operation), the regression suite holds those guarantees, and a rewrite would spend the suite to
reach a shape that is smaller by assertion rather than by evidence. Consolidation follows
demonstrated duplication, not line count.

*Rejected:* Dropping the shipped hardening back to a simpler implementation. It is simpler partly
because it misses failure modes the suite pins.

*One seal for both fields' sidecar results.* The trust table's rule for application code is that
the package validates mechanically what it can establish about a hook's RESULT, and a hook's
result contract does not depend on which field called it; two fields invoking one public method
and validating it differently would break that rule. The row at stake is
[`spec-030`][spec-030] Decision 7's "later steps can only narrow" upper bound on the connection
pipeline, which an override that widens, re-routes, pre-evaluates, slices or combines its return
would otherwise defeat.

So both fields' sidecar returns run one seal.
[`django_strawberry_framework/list_field.py::_execute_queryset_pipeline_sync`][list-field] /
[`::_execute_queryset_pipeline_async`][list-field], and
[`django_strawberry_framework/connection.py::_pipeline_sync`][connection] /
[`::_pipeline_async`][connection] for both sidecar steps, all run
[`django_strawberry_framework/utils/querysets.py::apply_sidecar_sync`][utils-querysets] or
[`::apply_sidecar_async`][utils-querysets] under the one `_SIDECAR_RESULT_POLICY`. Both fields
therefore freeze the same routing intent before the consumer override receives the queryset and
validate what it hands back on the same result axes - lazy, model rows of the captured model,
unsliced, a combinator served as its primary-key set, same routing - before any later step,
including the Relay window, sees it.

*Rejected:* Requiring an unevaluated `get_queryset` result on the list field when list arguments
are supplied. That hook's contract is shared with the Relay node, connection and relation
surfaces, all of which rebuild their own query from the returned one, so a stricter rule on one
field would make the verdict depend on which field called the hook and on whether a client sent
window arguments. A hook that evaluates pays one extra query for the discarded `_result_cache`,
which is a cost, not a broken seal. The visibility seal therefore runs under the one default
policy (`_DEFAULT_SEAL_POLICY`) on both fields, whether or not a sidecar input or a list argument
is supplied.

### Decision 20 — the extension contract is upstream's; per-operation isolation is the guarantee this package adds

Spec: [Decision 20][spec-050-d20].

*Decision:* The docs present upstream's class-or-factory spellings, inherit upstream's
deprecation of the instance spelling, and state per-operation isolation of the package's own
extensions as an addition this package owns and tests.

*Why:* The optimizer recipe in [`GOAL.md`][goal] and the shipped docs is a singleton inside a
factory - exactly the shape upstream's guide warns shares request state. The runner makes that
shape safe for the package's extensions, which is a guarantee worth stating as this package's
own; presenting it as upstream behavior would be false, and presenting instance entries as a
package-defined declaration would build on a spelling upstream is removing.

*Rejected:* Package-defined instance semantics beyond the compatibility reading. A meaning of
`extensions=[MyExtension()]` that only `DjangoSchema` has is a migration trap on the day upstream
drops the spelling.

*Rejected:* Presenting "move the authority instance into a factory" as the migration off the
deprecated spelling. A factory that resolves to an authority is an ordinary entry that declares
nothing (Decision 16), so that advice would walk a consumer from a working declaration to one
that configures nothing; the migration is the `resource_policy=` / `error_policy=` keyword,
which is where enforcement is declared.

*Rejected:* Authenticating or containing a third-party extension's object graph. Its lifecycle is
upstream's, its attributes are its author's, and the package can no more make them thread-safe
than it can make a resolver's globals thread-safe. The package isolates what it wrote.

*Rejected in [`spec-047`][spec-047]:* Reusing upstream's `MaxTokensLimiter`, `MaxAliasesLimiter`
and `QueryDepthLimiter` instead of the package's one extension; spec-047's borrowing posture
carries the reasons.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[goal]: ../../../GOAL.md

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-030]: ../spec-030-connection_field-0_0_9.md
[spec-047]: ../spec-047-resource_policy-0_0_14.md
[spec-050]: ../spec-050-list_field_arguments-0_0_15.md
[spec-050-d1]: ../spec-050-list_field_arguments-0_0_15.md#decision-1--synthesize-one-resolver-signature-do-not-widen-consumer-resolvers
[spec-050-d10]: ../spec-050-list_field_arguments-0_0_15.md#decision-10--coercion-errors-stay-graphql-owned-runtime-domain-errors-are-package-owned
[spec-050-d12]: ../spec-050-list_field_arguments-0_0_15.md#decision-12--graphql-core-workarounds-have-a-dependency-owned-lifecycle
[spec-050-d13]: ../spec-050-list_field_arguments-0_0_15.md#decision-13--configuration-authority-is-schema-state-everything-per-request-is-operation-state
[spec-050-d14]: ../spec-050-list_field_arguments-0_0_15.md#decision-14--an-enforcement-authority-is-a-declaration-never-an-extension-entry
[spec-050-d15]: ../spec-050-list_field_arguments-0_0_15.md#decision-15--the-runner-owns-every-binding-for-the-operations-whole-lifetime
[spec-050-d16]: ../spec-050-list_field_arguments-0_0_15.md#decision-16--a-factory-resolving-to-an-authority-is-an-ordinary-entry
[spec-050-d17]: ../spec-050-list_field_arguments-0_0_15.md#decision-17--the-configuration-code-stays-exported
[spec-050-d18]: ../spec-050-list_field_arguments-0_0_15.md#decision-18--execution-mode-is-operation-state-the-ambient-event-loop-is-a-different-fact
[spec-050-d19]: ../spec-050-list_field_arguments-0_0_15.md#decision-19--application-code-is-trusted-the-wire-is-not-a-finding-is-admitted-by-reachability
[spec-050-d2]: ../spec-050-list_field_arguments-0_0_15.md#decision-2--sidecar-conditional-orderby-is-the-only-truthful-meta-first-surface
[spec-050-d20]: ../spec-050-list_field_arguments-0_0_15.md#decision-20--the-extension-contract-is-upstreams-per-operation-isolation-is-the-guarantee-this-package-adds
[spec-050-d4]: ../spec-050-list_field_arguments-0_0_15.md#decision-4--max_list_rows-also-bounds-skip-trusted-widening-does-not
[spec-050-d5]: ../spec-050-list_field_arguments-0_0_15.md#decision-5--validate-then-visibility-ordering-and-exactly-one-slice
[spec-050-d6]: ../spec-050-list_field_arguments-0_0_15.md#decision-6--nonzero-offset-requires-a-materially-active-order
[spec-050-d7]: ../spec-050-list_field_arguments-0_0_15.md#decision-7--active-order-is-not-total-order-no-pk-tiebreaker-is-appended
[spec-050-d8]: ../spec-050-list_field_arguments-0_0_15.md#decision-8--queryset-and-iterable-sources-have-explicit-different-capabilities
[spec-050-d9]: ../spec-050-list_field_arguments-0_0_15.md#decision-9--a-request-with-no-list-argument-runs-the-plain-bounded-path-async-only-adapts-completion

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[connection]: ../../../django_strawberry_framework/connection.py
[list-field]: ../../../django_strawberry_framework/list_field.py
[utils-querysets]: ../../../django_strawberry_framework/utils/querysets.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->
[django-compiler]: ../../../.venv/lib/python3.14/site-packages/django/db/models/sql/compiler.py
[django-query]: ../../../.venv/lib/python3.14/site-packages/django/db/models/sql/query.py
[strawberry-relay-fields]: ../../../.venv/lib/python3.14/site-packages/strawberry/relay/fields.py

<!-- External -->
