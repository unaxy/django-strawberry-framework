# Spec: Form-based mutations — `DjangoFormMutation` / `DjangoModelFormMutation` on the DRF-shaped `class Meta` surface, reusing the shared `FieldError` envelope and the `DjangoMutation` foundation

The **form-validated** write flavor on top of the model-driven mutation
foundation [`spec-036`][spec-036] defines: two bases —
[`DjangoFormMutation`][glossary-djangoformmutation] (a Django `Form`) and
[`DjangoModelFormMutation`][glossary-djangomodelformmutation] (a `ModelForm`) —
declared through a nested `class Meta` (`Meta.form_class`, the DRF / graphene-django
shape, **not** graphene's `MutationOptions` / `__init_subclass_with_meta__`
pattern). It is a Required [`graphene-django`][upstream-forms-mutation] parity item:
graphene-django ships `DjangoFormMutation` / `DjangoModelFormMutation` as the
dominant write-side abstraction for consumers who already encode their validation in
a `Form` / `ModelForm`. The flavor reuses the contracts [`spec-036`][spec-036]
defines: the shared [`errors: list[FieldError]`][glossary-fielderror-envelope]
envelope (populated here from `form.errors`), the generated `<Name>Payload` wrapper
with its uniform `node` / `result` object slot, the
[`DjangoMutationField`][glossary-djangomutationfield] exposure factory, the
write-authorization seam ([`DjangoModelPermission`][glossary-djangomodelpermission] /
`Meta.permission_classes` / `check_permission`), and the overridable
[`_resolve_model`][spec-036] seam ([`spec-036`][spec-036] Decision 5) through which
the form flavor supplies its model from `form_class._meta.model`. The form-specific
machinery is the `forms/converter.py` form-field → Strawberry-input mapping and a
form pipeline (`is_valid()` → `form.errors` → `FieldError` → `form.save()`) in place
of the model-construct + `full_clean()` heart of the [`spec-036`][spec-036] resolver.

Status: **SHIPPED (`0.0.12`)** — card [`DONE-038-0.0.12`][kanban]. The
[Slice checklist](#slice-checklist) stays unticked; the `Status:` line is the
completion source of truth.

Owner: package maintainer.

Related specs: [`spec-036-mutations-0_0_11.md`][spec-036] (the foundation this flavor
extends: the [`FieldError` envelope][glossary-fielderror-envelope], the
`<Name>Payload` uniform slot, the [`DjangoMutationField`][glossary-djangomutationfield]
factory, the [`DjangoModelPermission`][glossary-djangomodelpermission] write-auth
seam, and the [`_resolve_model`][spec-036] hook);
[`spec-037-upload_file_image_mapping-0_0_11.md`][spec-037] (the
[`Upload`][glossary-upload-scalar] scalar a form's `forms.FileField` /
`forms.ImageField` maps to, [Edge cases](#edge-cases-and-constraints));
[`spec-034-permissions-0_0_10.md`][spec-034] (the [`get_queryset`][glossary-get_queryset-visibility-hook]
visibility hook the `update` locate composes with);
[`spec-027-filters-0_0_8.md`][spec-027] / [`spec-028-orders-0_0_8.md`][spec-028]
(the set-family subpackage layout / phase-2.5 binding / materialize-before-`Schema`
discipline `mutations/` and `forms/` follow);
[`spec-010-foundation-0_0_4.md`][spec-010] (the relation-override contract the
input generation honors).

Each Decision's justification and rejected alternatives live in the rationale companion
[`docs/SPECS/appx/spec-038-form_mutations-0_0_12-rationale.md`][spec-038-rationale].

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the
vocabulary used throughout the spec:

- [`DjangoFormMutation`][glossary-djangoformmutation] /
  [`DjangoModelFormMutation`][glossary-djangomodelformmutation] — the two subjects.
  Both consume a Django `Form` / `ModelForm` (`Meta.form_class`) and surface
  validation through the shared [`FieldError` envelope][glossary-fielderror-envelope]
  (populated from `form.errors`). **The one point the entries must not blur:**
  **only `DjangoModelFormMutation` subclasses [`DjangoMutation`][glossary-djangomutation]**
  (it has a model, so it returns the post-save object in the uniform `node` / `result`
  slot), while the **plain `DjangoFormMutation` is a model-less sibling** — its own
  metaclass, no `DjangoType` object slot, the pinned `ok` + `errors` payload
  ([Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)) —
  accepted by the **generalized mutation-field family**
  ([Decision 5](#decision-5--public-surface-djangoformmutation--djangomodelformmutation-exported-from-the-root)).
- [`DjangoMutation`][glossary-djangomutation] /
  [Input type generation][glossary-input-type-generation] /
  [`DjangoMutationField`][glossary-djangomutationfield] — the
  [`spec-036`][spec-036] foundation the form flavor builds on. The form flavor reuses the
  [`DjangoMutationField`][glossary-djangomutationfield] exposure factory and the
  generated-payload lifecycle, and `DjangoModelFormMutation` subclasses the
  [`DjangoMutation`][glossary-djangomutation] base outright; the input *generation*,
  by contrast, is **form-derived here**, not model-derived
  ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)).
- [`FieldError` envelope][glossary-fielderror-envelope] — the shared error contract
  [`spec-036`][spec-036] defines for every write flavor. A form mutation maps
  `form.errors` (a `field → [messages]` dict, with the form's `NON_FIELD_ERRORS`
  bucket) onto that same envelope, keying form-level errors to the same
  `"__all__"` sentinel `036` pinned
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)).
- [`DjangoModelPermission`][glossary-djangomodelpermission] — the default
  write-authorization class the `ModelForm` flavor inherits unchanged (the form's
  model resolves the `add` / `change` perm); the plain-`Form` flavor's permission
  default is settled in
  [Decision 11](#decision-11--write-authorization-reuse-the-036-seam-djangomodelpermission-for-the-modelform-explicit-classes-for-the-plain-form).
- [`get_queryset` visibility hook][glossary-get_queryset-visibility-hook] /
  [`apply_cascade_permissions`][glossary-apply_cascade_permissions] — the
  visibility seam the `update` locate composes with: a `DjangoModelFormMutation`
  `update` binds the form to a row located through the target type's
  [`get_queryset`][glossary-get_queryset-visibility-hook], so a hidden row is
  not-found, never an existence leak — the same contract `036`'s model-driven
  `update` uses
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)).
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] /
  [`only()` projection][glossary-only-projection] — the post-save re-fetch
  cooperation. The `ModelForm` payload's object is re-fetched and optimizer-planned
  for the response selection through the **same** `036` re-fetch path, so the
  [`spec-035`][spec-035] **G2** mutation gate (keep `select_related` /
  `prefetch_related`, introduce no `.only(...)`) comes for free
  ([Decision 9](#decision-9--optimizer-composition-the-modelform-payload-re-fetch-rides-the-spec-036-g2-path)).
- [`Meta.primary`][glossary-metaprimary] / [`Meta.model`][glossary-metamodel] /
  [`DjangoType`][glossary-djangotype] — the return-payload type resolves the form
  model's **primary** [`DjangoType`][glossary-djangotype] through the registry
  primary lookup, exactly as `036`'s `DjangoMutation` does
  ([Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)).
- [`Meta.fields`][glossary-metafields] / [`Meta.exclude`][glossary-metaexclude] —
  the `only_fields` / `exclude_fields` graphene-django surface, here named for the
  package's own [`Meta.fields`][glossary-metafields] / [`Meta.exclude`][glossary-metaexclude]
  shape, narrowing which **form** fields become input fields
  ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)).
- [Scalar field conversion][glossary-scalar-field-conversion] /
  [Choice enum generation][glossary-choice-enum-generation] /
  [`Upload` scalar][glossary-upload-scalar] — the converters the form-field mapping
  reuses where a form field's type overlaps a Django column type (so a
  form-derived input field resolves to the same scalar / enum / `Upload` the
  read side and the `036` model-driven input use; a choice field whose static
  choices admit fewer of the column's values publishes a generated enum of the
  values it admits)
  ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)).
- [`ConfigurationError`][glossary-configurationerror] /
  [`SyncMisuseError`][glossary-syncmisuseerror] — the validation / misuse
  exceptions the form flavor raises: `ConfigurationError` at form-mutation-class
  creation (missing `Meta.form_class`, a non-`Form` / non-`ModelForm` value, a
  `ModelForm` with no resolvable model), and `SyncMisuseError` when a sync form
  pipeline meets an `async def` target
  [`get_queryset`][glossary-get_queryset-visibility-hook] (the discipline `036`
  routes through).
- [`SerializerMutation`][glossary-serializermutation] / [Auth mutations][glossary-auth-mutations]
  — the sibling write flavors on the same `036` envelope; named here only to fix
  the out-of-scope boundary ([Out of scope](#out-of-scope-explicitly-tracked-elsewhere)).
- [Cross-subsystem invariants][glossary-cross-subsystem-invariants] /
  [`FieldSet`][glossary-fieldset] / [Per-field permission hooks][glossary-per-field-permission-hooks]
  — the invariant a form mutation keeps (a `DjangoType` `Meta` key is promoted only
  when its subsystem applies it end-to-end). A form mutation adds **no** `DjangoType`
  `Meta` key, so [`DEFERRED_META_KEYS`][types-base] is untouched
  ([Decision 13](#decision-13--finalization-seam-reuse-the-mutation-phase-25-bind-no-deferred_meta_keys-change)).

Project conventions that shape the flavor:

- [`AGENTS.md`][agents] — the test-placement rule (package-internal form-converter /
  base / resolver mechanics under [`tests/forms/`][test-forms] mirroring source;
  live consumer behavior over `/graphql/` when a realistic request reaches it —
  [Decision 12](#decision-12--live-coverage-products-grows-a-modelform-and-a-plain-form-mutation));
  the settings-keys-only-when-needed rule (the form flavor adds no settings key).
- [`START.md`][start] — "Meta classes on every consumer surface": the decisive rule
  for [Decision 3](#decision-3--class-meta-surface-not-graphenes-mutationoptions);
  also the behavior-from-`strawberry-graphql-django`, surface-from-`django-graphene-filters`
  + DRF rule (the form mutation is a graphene-django surface borrow on a Strawberry
  engine).
- [`CONTRIBUTING.md`][contributing] — the 100% coverage target
  (`fail_under = 100`); every converter branch, the `is_valid()` / `form.errors`
  paths, the `save()` path, and both base classes earn coverage in
  [`tests/forms/`][test-forms] plus the live products suite.
- [`GOAL.md`][goal] — success-criterion 6 ("Write mutations declaratively from
  `ModelForm`, `ModelSerializer`, or auto-generated `Input` types — one shared
  `errors: [FieldError!]!` envelope across every flavor"); the form flavor is
  criterion 6's `ModelForm` flavor, plus the plain-`Form` flavor, which is **not** a
  criterion-6 item (criterion 6 names `ModelForm` / `ModelSerializer` / `Input`, not a
  bare `Form`): it is a graphene-django parity addition.

## Slice checklist

**Five slices: form-field converter + input generation (Slice 1), the two base
classes (Slice 2), the resolver pipeline + field exposure (Slice 3), the products
live form surface (Slice 4), and the docs (Slice 5).** Slices 1–3 are
package-internal; Slice 4 is the live consumer surface.

- [ ] Slice 1: form-field → Strawberry input mapping + the form-derived input
  generator (per
  [Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth))
  - [ ] [`forms/converter.py`][forms-converter]: a `convert_form_field(field)`
    registry (the graphene-django [`convert_form_field`][upstream-forms-converter]
    parity shape) returning the Strawberry annotation + required-ness for each
    supported form-field class (`CharField` / `ChoiceField` → `str`, `IntegerField` →
    `int`, `BooleanField` → `bool`, `FloatField` → `float`, `DecimalField` → `Decimal`,
    `DateField` / `DateTimeField` / `TimeField` → Python-native, `UUIDField` →
    `uuid.UUID`, `JSONField` → `strawberry.scalars.JSON` (its own row, or the
    `CharField` parent types a JSON payload as `String`),
    `ModelChoiceField` → the target's id, `ModelMultipleChoiceField` /
    `MultipleChoiceField` → `list[<id>]` / `list[str]`, `forms.FileField` /
    `forms.ImageField`, or any field rendered with a `forms.FileInput`, →
    [`Upload`][glossary-upload-scalar]). **Fail-loud dispatch:** the fallthrough default **raises** — supported classes are registered
    individually (subclasses map via MRO), bare `forms.Field` is an explicit exact-type
    special case → `str`, and **no base-`forms.Field` catch-all** is registered (which
    would shadow the raise), so a custom `forms.Field` subclass with no supported
    ancestor raises [`ConfigurationError`][glossary-configurationerror] naming the field
    and class. Where a form field maps to a Django column type the read side already
    converts, reuse the [Scalar field conversion][glossary-scalar-field-conversion] /
    [Choice enum generation][glossary-choice-enum-generation] registry rather than
    re-deriving the scalar; a choice field whose static choices admit fewer of a choice
    column's values publishes a generated enum of the admitted column values instead,
    and a field whose kind (`form_field_kind`) disagrees with its backing column's, other
    than a scalar field over a relation column, is a `ConfigurationError`.
    Record, per generated input field, a
    [`utils/inputs.py`][utils-inputs]`::InputFieldSpec` — the one reverse-map record
    type every write flavor shares, whose `target_name` on this path is the form's
    declared field name — carrying `kind ∈ {scalar, relation_single, relation_multi,
    file}` and a relation's build-time `related_model`, so the resolver can build a
    form-field-keyed payload: `categoryId` / `category_id`
    → `category` / `relation_single`, an `Upload` field flagged `file`
    ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)). This module owns
    the four `kind` constants and re-exports them from
    [`utils/inputs.py`][utils-inputs]; it does not own the record type.
  - [ ] [`forms/inputs.py`][forms-inputs] (its own module, per the committed
    four-module `forms/` layout — [Decision 4](#decision-4--module-and-test-locations-forms-subpackage-mirroring-mutations)):
    build **two** `@strawberry.input` classes from the **form's declared fields**
    (`form_class.base_fields`, narrowed by `Meta.fields` / `Meta.exclude`) — `<FormClass>Input`
    (create; each field's requiredness from `field.required`, graphene-django parity)
    and `<FormClass>PartialInput` (update; model-backed fields optional, a **non-model
    extra field keeps its `field.required`**) — under the **shape-identity +
    naming + collision discipline** of `036` adapted to forms: identity `(form_class,
    operation kind, frozenset(effective field names), field-discovery basis content
    identity)`, canonical `<FormClass>Input` /
    shape-derived narrowed names, identical shapes dedupe, two distinct shapes on one
    name → finalize-time [`ConfigurationError`][glossary-configurationerror].
    Reuse [`utils/inputs.py`][utils-inputs]'s `build_strawberry_input_class` +
    `materialize_generated_input_class` core (the latter's ledger gives the collision
    raise for free) and materialize as module globals of the `forms` input namespace
    for the [`strawberry.lazy`][glossary-djangomutationfield] forward-ref. Normalize +
    fail-loud `Meta.fields` / `Meta.exclude` against `form_class.base_fields` (bare string,
    a lazy translation string or bytes-like value included, duplicates, unknown names,
    empty effective set → `ConfigurationError`, via the shared
    `utils/inputs.py::resolve_effective_fields` spine).
  - [ ] Package coverage: [`tests/forms/test_converter.py`][test-forms] — each
    supported form-field class → its annotation + required-ness; the
    `ModelChoiceField` / `ModelMultipleChoiceField` id mapping (Relay-`GlobalID`
    vs raw pk by the target's primary [`DjangoType`][glossary-djangotype]); the
    `forms.FileField` → [`Upload`][glossary-upload-scalar] mapping; the unknown
    form-field [`ConfigurationError`][glossary-configurationerror]. And
    [`tests/forms/test_inputs.py`][test-forms] — the form-derived input shape (fields
    from `form_class.base_fields`, required-ness from `field.required`, `Meta.fields` /
    `Meta.exclude` narrowing, a form-only non-model field included), materialized as a
    module global.
- [ ] Slice 2: the `DjangoFormMutation` / `DjangoModelFormMutation` bases + `Meta`
  validation + the phase-2.5 bind (per
  [Decision 5](#decision-5--public-surface-djangoformmutation--djangomodelformmutation-exported-from-the-root)
  /
  [Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling))
  - [ ] [`mutations/sets.py`][mutations-sets]: the class-creation validation is the
    overridable `DjangoMutation._validate_meta(meta)` classmethod the metaclass
    invokes (the model base's body is `_validate_mutation_meta`), beside the
    overridable `build_input(meta, primary_type)` bind hook +
    `input_type_name(meta)` / `input_module_path` + `resolve_sync` / `resolve_async`
    seams ([Decision 5](#decision-5--public-surface-djangoformmutation--djangomodelformmutation-exported-from-the-root)
    / [Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)),
    each defaulting to the model behavior.
  - [ ] [`forms/sets.py`][forms-sets]: `DjangoModelFormMutation` (subclasses
    [`DjangoMutation`][glossary-djangomutation], overriding [`_resolve_model`][spec-036]
    → `Meta.form_class._meta.model`, plus the `_validate_meta` / `build_input` /
    `input_type_name` / `input_module_path` / `resolve_*` seams above) and
    `DjangoFormMutation` (the model-less sibling — its own metaclass + declaration
    registry + `bind_form_mutations()` wired into [`types/finalizer.py`][types-finalizer],
    [Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)
    / [Decision 13](#decision-13--finalization-seam-reuse-the-mutation-phase-25-bind-no-deferred_meta_keys-change)).
    The form-flavor `_validate_meta` override: `Meta.form_class` is required. In
    Django, **`forms.ModelForm` is NOT a subclass of `forms.Form`** — both are
    siblings under `forms.BaseForm` (`issubclass(ModelForm, Form)` is `False`;
    `ModelForm` → `BaseModelForm` → `BaseForm`, `Form` → `BaseForm`). So the plain
    `DjangoFormMutation` **checks `issubclass(form_class, forms.ModelForm)` first** and
    raises a `ConfigurationError` naming `DjangoModelFormMutation` as the correct base
    (a *targeted* message — without this explicit check a bare `issubclass(…,
    forms.Form)` gate would still reject a `ModelForm`, but with a confusing generic
    "not a `Form`" message; and the targeting matters because, were a `ModelForm` let
    through, it would silently write via `form.save()` and return only `{ ok errors }`
    with no object slot, no `DjangoModelPermission` default, and no optimizer re-fetch,
    defeating the two-base split). It then requires a `forms.Form` subclass.
    `DjangoModelFormMutation` requires a `forms.ModelForm` subclass. The check runs
    **before** `_resolve_model` (so a missing / wrong-type `form_class` is a clean
    [`ConfigurationError`][glossary-configurationerror], never a raw `AttributeError`
    from `form_class._meta.model`); a `ModelForm` with no resolvable `_meta.model`
    raises. **`operation` is split by base:** `DjangoModelFormMutation` requires
    `Meta.operation ∈ {"create", "update"}` (a `"delete"` form mutation is **rejected**
    — the form flavor has no delete pipeline,
    [Decision 10](#decision-10--operations-create--update-for-the-modelform-no-form-delete)),
    and its shape-identity operation component is that value; the plain
    `DjangoFormMutation` **rejects any `Meta.operation`** as unsupported (a model-less
    mutation has no model operation — Decision 10) and uses the fixed identity
    sentinel **`"form"`** for the operation component of its input-shape cache key,
    whose fourth component is the field-discovery basis content identity
    ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)).
    There are **two** allowed-key sets, not one:
    `forms/sets.py::_ALLOWED_MODELFORM_META_KEYS` is
    `MODEL_BACKED_WRITE_META_KEYS | {form_class}` =
    `{fields, exclude, permission_classes, operation, select_for_update, form_class}`,
    and `forms/sets.py::_ALLOWED_PLAIN_FORM_META_KEYS` is
    `COMMON_WRITE_META_KEYS | {form_class}` =
    `{fields, exclude, permission_classes, form_class}`. Both add `form_class` and drop
    `model` / `input_class` / `partial_input_class`; the plain set additionally drops
    `operation` (Decision 10) **and** `select_for_update`, since row locking is a
    model-backed key a model-less mutation has nothing to lock with.
    `Meta.fields` / `Meta.exclude` are mutually exclusive.
  - [ ] No change to [`DEFERRED_META_KEYS`][types-base] / `ALLOWED_META_KEYS`: a
    form-mutation `Meta` is its own validation namespace
    ([Decision 13](#decision-13--finalization-seam-reuse-the-mutation-phase-25-bind-no-deferred_meta_keys-change)).
  - [ ] Package coverage: [`tests/forms/test_sets.py`][test-forms] — the `Meta`
    validation matrix (missing / wrong-type `form_class`, a `ModelForm` on the plain
    base rejected naming `DjangoModelFormMutation`, `ModelForm`-with-no-model,
    `DjangoModelFormMutation` `operation = "delete"` rejected, **any `Meta.operation`
    on the plain base rejected**, `form_class` accepted as a known key,
    `fields` + `exclude` both set, unknown key), **plain-form input dedupe** (the
    `"form"` sentinel — two plain mutations over one form + effective set dedupe),
    registration, finalizer binding (both the `DjangoMutation`-path bind and the
    `bind_form_mutations()` path), the no-registered-primary-type error for
    `DjangoModelFormMutation`, and the
    model-flavor seam defaults unchanged (a `DjangoMutation` still validates +
    materializes its model-column input).
- [ ] Slice 3: the form resolver pipeline + `DjangoMutationField` exposure (per
  [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)
  /
  [Decision 9](#decision-9--optimizer-composition-the-modelform-payload-re-fetch-rides-the-spec-036-g2-path))
  - [ ] [`forms/resolvers.py`][forms-resolvers]: the sync + async pipeline, in the
    order **locate → authorize → decode → construct/validate → write → re-fetch →
    return** ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)) —
    (`update`) **locate** the row through the target type's
    [`get_queryset`][glossary-get_queryset-visibility-hook] (not-found → a `FieldError`
    on `id`, no existence leak); **authorize** via the inherited `check_permission` /
    `Meta.permission_classes`, **before** the decode, since the decode issues
    visibility-scoped queries an unauthorized caller must not be able to probe;
    **decode** the `data:` input via the reverse map into a form-field-keyed
    `provided_data` and a `provided_files` (files kept out of `data`), each relation id
    — `GlobalID` *or* **raw pk** — type-checked, resolved to the **visible** object
    through the related primary `DjangoType.get_queryset` (both branches) and
    converted by `to_field_name`
    (`obj.serializable_value(field.to_field_name)`, or `obj.pk` when the field sets
    none) before landing under the form field name, a hidden target, or a visible one
    whose stored `to_field` key is `NULL`, → field-keyed `FieldError`;
    **construct** the form once via the overridable
    `get_form_kwargs(info, *, data, files, instance=None)` hook — create:
    `form_class(**get_form_kwargs(info, data=provided_data, files=provided_files))`;
    **update (partial):** reconstruct the full bound `data` from the located row's
    values under the form's **full declared** field set, overlaid by `provided_data`,
    with `files = provided_files`, then
    `form_class(**get_form_kwargs(info, data=, files=, instance=<row>))` (omitted
    fields preserved); **bind** each value under the keys its widget reads
    (`form.add_prefix`, a multi-key widget's own keys; a list longer than a
    `SplitArrayWidget`'s `size` → that field's `max_length` error); **validate** via
    `form.is_valid()` — a failure maps
    `form.errors` onto the [`FieldError` envelope][glossary-fielderror-envelope] (each
    form field name re-keyed to the GraphQL input field the client sent, the form's
    `NON_FIELD_ERRORS` bucket → the `"__all__"` sentinel `036` defined, via the reused
    `validation_error_to_field_errors(ValidationError(form.errors.as_data()), key_map)`)
    and returns a null-object payload (on an update whose located row a concurrent
    transaction removed meanwhile, the skeleton's probe answers the `conflict` envelope
    on `id` instead); an explicit `null` a `null=False` column's own form field cleaned
    to a storable value (a `BooleanField`'s `False`, a `blank=True` text or
    text-choice column's `""`) → that column's field-keyed `null` error, nothing
    written; **write** via the form's save (`ModelForm`; an
    update and a client-assigned-key create split around `commit=False`) /
    `perform_mutate` (plain form), **wrapped by the `036` save-time mappers**
    (`save_or_field_errors`; a `ModelForm` update `forced_save_or_field_errors`: an
    `IntegrityError` or a consumer save-time Django `ValidationError` → envelope, a
    located row deleted before the update → `conflict`, no top-level error at write), the
    `ModelForm` save also mapping a `null=False` column the form cleaned
    to a value it cannot store (`None`, or `""` on a column that stores no empty string: a non-text choice column, an `ArrayField`) onto that
    column's field-keyed `null` error; **re-fetch**
    the saved object by pk + optimizer-plan (the `ModelForm` flavor); **return** the
    `<Name>Payload` (`node` / `result` for the `ModelForm`, the pinned `ok` + `errors`
    for the plain form). The whole pipeline runs inside one `transaction.atomic()`
    pinned to one write alias, behind a pre-transaction deadline check and over an
    immutable post-locate `authorized_pk` snapshot, and
    the async path runs the sync body in one `sync_to_async(thread_sensitive=True)`
    call — the same boundary `036` set.
  - [ ] [`mutations/fields.py`][mutations-fields]:
    [`DjangoMutationField`][glossary-djangomutationfield] is generic along three axes
    ([Decision 5](#decision-5--public-surface-djangoformmutation--djangomodelformmutation-exported-from-the-root)) —
    (a) the `_validate_mutation_target` check accepts the whole mutation family
    (duck-typed, not `issubclass(DjangoMutation)`); (b) `_resolve` dispatches to
    `mutation_cls.resolve_sync` / `resolve_async`, so a form flavor routes to
    [`forms/resolvers.py`][forms-resolvers]; (c) the synthesized `data:` lazy ref
    consults `mutation_cls.input_type_name(meta)` + `input_module_path`.
  - [ ] Package coverage: [`tests/forms/test_resolvers.py`][test-forms] — create /
    update happy paths, the `form.errors` → envelope (incl. a `NON_FIELD_ERRORS`
    `clean()` error → `"__all__"`), the **decode split** (`categoryId` → `{"category":
    pk}` in `data=`, an `Upload` → `files=`), the **partial-update reconstruction**
    (omitted scalar / FK / M2M / file preserved; `unique_item_per_category` on a
    one-field change), the **plain-form `ok` + `errors` payload + `perform_mutate`
    default/override**, the visibility-scoped `update` locate (hidden row →
    not-found), write-auth denial vs success, sync + async, and the G2 plan-shape (the
    `ModelForm` re-fetch keeps `select_related` / `prefetch_related` and introduces no
    `.only(...)`).
- [ ] Slice 4: the products live form surface (per
  [Decision 12](#decision-12--live-coverage-products-grows-a-modelform-and-a-plain-form-mutation))
  - [ ] [`examples/fakeshop/apps/products/forms.py`][products-forms]: the
    `ItemModelForm` (`forms.ModelForm` over `Item`, with a `clean_name`),
    `ItemFileModelForm` (adds `Item.attachment`, the nullable `FileField`),
    `StampedItemModelForm` (requires a `user` constructor kwarg),
    `DefaultCategoryItemModelForm` (narrows `category` away and takes it as a kwarg),
    `ItemHoldModelForm` (over `ItemHold`, whose `item` is `blank=True, null=False`),
    and the plain `ContactForm` / `PingForm`; `products/schema.py` wraps them in
    `CreateItemViaForm` / `UpdateItemViaForm`, `CreateItemWithFileViaForm` /
    `UpdateItemWithFileViaForm`, `CreateStampedItemViaForm`,
    `CreateDefaultCategoryItemViaForm`, `CreateItemHoldViaForm` (each a
    `DjangoModelFormMutation`) and
    `SubmitContact` / `SubmitPing` (each a `DjangoFormMutation`).
  - [ ] [`test_products_api.py`][test-products-api] (seeded via `seed_data` /
    `create_users`): live `/graphql/` create / update through the `ModelForm`
    mutation; `categoryId` validating + writing through the form's `category` field;
    **partial-update preservation** (a `name`-only update preserves `category` /
    `description`, and `unique_item_per_category` fires on a one-field change); the
    `form.errors` envelope (`clean_<field>` keyed to the field's input name; the
    constraint error keyed to `"__all__"`); write authorization; the visibility-scoped `update`; **a
    raw `django.test.Client` multipart upload** to a form-backed `Upload` field
    (the file-routing contract); and the plain `Form` mutation's **success**
    (`ok: true`) **and** validation-failure (`ok: false`, field-keyed `errors`) shapes.
- [ ] Slice 5: doc updates (per [Doc updates](#doc-updates))
  - [ ] [`docs/GLOSSARY.md`][glossary] carries
    [`DjangoFormMutation`][glossary-djangoformmutation] /
    [`DjangoModelFormMutation`][glossary-djangomodelformmutation] as shipped, in
    **Public exports**, the **Index** and the **Mutations** browse-by-category row;
    [`docs/README.md`][docs-readme] / [`README.md`][readme] list form mutations;
    [`GOAL.md`][goal] criterion 6 names the `ModelForm` flavor; [`TODAY.md`][today]
    notes the products `ModelForm` write surface; [`docs/TREE.md`][tree] carries the
    `forms/` / [`tests/forms/`][test-forms] summary lines.

## Problem statement

The package's model-driven write side ([`spec-036`][spec-036]) is the
[`DjangoMutation`][glossary-djangomutation] base, auto-generated
[`Input` / `PartialInput`][glossary-input-type-generation] types, the shared
[`FieldError` envelope][glossary-fielderror-envelope], and `create` / `update` /
`delete` resolvers. It validates a write through Django **model** machinery —
construct / locate the instance, call `full_clean()`, `save()`.

But a large class of Django consumers already encode their write validation in a
`Form` / `ModelForm`, not on the model. graphene-django serves them with
[`DjangoFormMutation`][upstream-forms-mutation] (a plain `Form`) and
`DjangoModelFormMutation` (a `ModelForm`): the mutation runs `form.is_valid()`,
surfaces `form.errors` to the client, and `form.save()`s the object — reusing the
consumer's existing form, including its custom `clean_<field>` / `clean()` validation,
its widget coercions, and its declared (non-model) fields. Without an equivalent, a
graphene-django migrant with form-backed mutations must:

- rewrite each form's field-level and cross-field validation against the model's
  `full_clean()` (losing the `clean_<field>` / `clean()` logic the form already
  carries), and
- re-declare the input shape against the model's editable columns rather than the
  form's declared fields (a plain `Form` may declare fields that are *not* model
  columns — a `confirm_email`, a `captcha`, a computed field — which the
  model-driven [`spec-036`][spec-036] generator cannot express).

This is a Required `graphene-django` parity item, foundational by the
[`START.md`][start] "both libraries provide it" test: graphene-django ships form
mutations as a first-class write surface, and [`GOAL.md`][goal] success-criterion 6
names `ModelForm` explicitly as a target write flavor. The flavor is **small in new
machinery** because [`spec-036`][spec-036] defines the reusable contracts (the
[`FieldError` envelope][glossary-fielderror-envelope], the payload wrapper, the
[`DjangoMutationField`][glossary-djangomutationfield] factory, the
[`DjangoModelPermission`][glossary-djangomodelpermission] seam, the
[`_resolve_model`][spec-036] hook): the form-specific parts are the form-field →
input mapping and the `is_valid()` → `form.errors` → `save()` pipeline that replaces
the model-construct + `full_clean()` heart.

## Current state

- **The flavor lives in `django_strawberry_framework/forms/`**:
  [`converter.py`][forms-converter] (`convert_form_field` + the four decode-kind
  constants), [`inputs.py`][forms-inputs] (the form-derived `<FormClass>Input` /
  `<FormClass>PartialInput` builder and its input namespace), [`sets.py`][forms-sets]
  (`DjangoModelFormMutation`, `DjangoFormMutation`, their `Meta` validation,
  `bind_form_mutations()`), and [`resolvers.py`][forms-resolvers] (the form pipeline).
  The package root [`__init__.py`][init] exports `DjangoFormMutation` /
  `DjangoModelFormMutation` beside the `036` mutation symbols.
- **It composes the `036` foundation through seams.**
  [`mutations/sets.py`][mutations-sets] `DjangoMutation` exposes the overridable
  [`_resolve_model(meta)`][spec-036], `_validate_meta(meta)`, `build_input(meta,
  primary_type)`, `input_type_name(meta)` / `input_module_path` and
  `resolve_sync` / `resolve_async` seams; `DjangoModelFormMutation` overrides each.
  [`mutations/inputs.py`][mutations-inputs] carries the public
  [`FieldError`][glossary-fielderror-envelope] type, the `build_payload_type`
  wrapper (the uniform `node` / `result` slot via `payload_object_slot`), and the
  `NON_FIELD_ERROR_KEY = "__all__"` sentinel.
  [`mutations/resolvers.py`][mutations-resolvers] carries the helpers the form
  pipeline calls rather than re-implements: `run_write_pipeline_sync` (the
  one-`transaction.atomic()` skeleton), `locate_instance`, `authorize_or_raise`,
  `refetch_optimized`, `save_or_field_errors`, `make_resolver_entries`; the
  `validation_error_to_field_errors` mapper lives in `utils/errors.py`.
  [`mutations/fields.py`][mutations-fields]'s
  [`DjangoMutationField`][glossary-djangomutationfield] accepts any class carrying
  the mutation protocol (`_has_mutation_protocol`).
  [`mutations/permissions.py`][mutations-permissions]'s
  [`DjangoModelPermission`][glossary-djangomodelpermission] checks the model the
  mutation resolved through `_resolve_model` at declaration, so the `ModelForm`
  flavor authorizes through the same default; `DenyAll` is the plain form's unset
  default.
- **The products app demonstrates both flavors** (`apps/products/forms.py` +
  `apps/products/schema.py`). The `Item` model carries the
  `unique_item_per_category` `UniqueConstraint` — a `ModelForm` over `Item` surfaces
  it as a `NON_FIELD_ERRORS` form error, the live `"__all__"`-sentinel coverage
  ([Decision 12](#decision-12--live-coverage-products-grows-a-modelform-and-a-plain-form-mutation)).

## Goals

1. **Ship `DjangoFormMutation` and `DjangoModelFormMutation` on the `class Meta`
   surface.** Both declared as a class with a nested `Meta` (`form_class` +
   optional `fields` / `exclude`), not a graphene `MutationOptions` /
   `__init_subclass_with_meta__` flow
   ([Decision 3](#decision-3--class-meta-surface-not-graphenes-mutationoptions) /
   [Decision 5](#decision-5--public-surface-djangoformmutation--djangomodelformmutation-exported-from-the-root)).
2. **Derive the input from the form's declared fields.** A `forms/converter.py`
   form-field → Strawberry-annotation registry, reusing the read-side scalar /
   enum / [`Upload`][glossary-upload-scalar] converters where the field types
   overlap, so the input shape is the form's contract — including fields a model
   does not have
   ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)).
3. **Reuse the shared `FieldError` envelope.** Map `form.errors` (and the form's
   `NON_FIELD_ERRORS` bucket) onto the one
   [`FieldError`][glossary-fielderror-envelope] envelope `036` defined
   ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)).
4. **Run the write through the form.** `form.is_valid()` → `form.save()`, sync and
   async, inside the one-`transaction.atomic()` boundary `036` set; the `ModelForm`
   payload's object is re-fetched and optimizer-planned for the response selection
   ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)
   /
   [Decision 9](#decision-9--optimizer-composition-the-modelform-payload-re-fetch-rides-the-spec-036-g2-path)).
5. **Compose with the shipped permission + visibility seams.** The `ModelForm`
   flavor inherits [`DjangoModelPermission`][glossary-djangomodelpermission]
   write-auth and the visibility-scoped `update` locate unchanged
   ([Decision 11](#decision-11--write-authorization-reuse-the-036-seam-djangomodelpermission-for-the-modelform-explicit-classes-for-the-plain-form)).
6. **Ship the products live form surface** (Slice 4).

## Non-goals

- **DRF serializer mutations and auth mutations.** [`SerializerMutation`][glossary-serializermutation]
  (`Meta.serializer_class`) and [Auth mutations][glossary-auth-mutations] are sibling
  flavors with their own specs; they reuse the same envelope
  ([Out of scope](#out-of-scope-explicitly-tracked-elsewhere)).
- **Changing the `036` model-driven generator or the `FieldError` envelope.** The
  form flavor adds no member to [`FieldError`][glossary-fielderror-envelope] and does
  not re-open [`mutations/inputs.py`][mutations-inputs]'s model-column generator
  ([Decision 2](#decision-2--card-scope-boundary-the-two-form-flavors-ship-serializer--auth-stay-out-the-frozen-036-contracts-are-reused-unchanged)).
- **The `TestClient` *ergonomic* helper, NOT file-field correctness.** The form
  flavor **owns the runtime correctness** of `forms.FileField` / `forms.ImageField`:
  the `Upload` input typing, the `data=` / `files=` decode split, and
  `form_class(data=, files=, instance=)` construction
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)),
  proven by a raw `django.test.Client` multipart live test for a form-backed
  `Upload` field (Slice 4). The *ergonomic* `TestClient` / `AsyncTestClient` wrapper
  is [`django_strawberry_framework/testing/`][testing-package]
  ([`TestClient`][glossary-testclient], [Edge cases](#edge-cases-and-constraints)).
- **Form `delete`.** graphene-django form mutations are create / update only; a
  `ModelForm` does not delete. A `delete` write stays the model-driven
  [`DjangoMutation`][glossary-djangomutation] (`Meta.operation = "delete"`)
  ([Decision 10](#decision-10--operations-create--update-for-the-modelform-no-form-delete)).
- **`Meta.return_field_name`.** graphene-django's per-mutation output-field-name
  key is **not** adopted; the `036`-frozen uniform `node` / `result` slot
  supersedes it for one cross-flavor client contract
  ([Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)).
- **A new `DjangoType` `Meta` key or settings key**
  ([Decision 13](#decision-13--finalization-seam-reuse-the-mutation-phase-25-bind-no-deferred_meta_keys-change)).

## Borrowing posture

Per the [`START.md`][start] "do both libraries provide it? → foundational" test,
form mutations are **Required `graphene-django` parity**. The borrowing splits along the package's standing line — *surface-wise* copy
`graphene-django` / DRF (the `class Meta` + `Form` / `ModelForm` shape every Django
developer already knows), *behaviorally* keep the Strawberry engine and the
package's own optimizer-composed, permission-scoped, async-capable pipeline. The
*capabilities* of graphene-django's form mutations (run the form's validation,
surface `form.errors`, `form.save()` the object) are adopted at the **outcome**
level; the graphene `MutationOptions` / `ClientIDMutation` / `__init_subclass_with_meta__`
mechanism is **explicitly rejected** — it is the decorator-adjacent
metaclass-options surface the package replaces with a nested `class Meta`.

### Reference-package parity checkpoint

| Upstream | `django-strawberry-framework` | Status |
| --- | --- | --- |
| [`graphene_django.forms.mutation.DjangoFormMutation`][upstream-forms-mutation] (plain `Form`, `MutationOptions`) | [`DjangoFormMutation`][glossary-djangoformmutation] base + nested `Meta.form_class` ([Decision 3](#decision-3--class-meta-surface-not-graphenes-mutationoptions) / [Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)) | shipped — borrow the capability, reject the `MutationOptions` surface |
| [`graphene_django.forms.mutation.DjangoModelFormMutation`][upstream-forms-mutation] (`ModelForm`, `model` from `form_class._meta.model`) | [`DjangoModelFormMutation`][glossary-djangomodelformmutation] subclassing [`DjangoMutation`][glossary-djangomutation] via the [`_resolve_model`][spec-036] seam ([Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)) | shipped — required parity |
| [`fields_for_form` + `convert_form_field`][upstream-forms-converter] (Django form field → GraphQL type) | [`forms/converter.py`][forms-converter] `convert_form_field` registry, reusing the read-side [scalar][glossary-scalar-field-conversion] / [choice-enum][glossary-choice-enum-generation] / [`Upload`][glossary-upload-scalar] converters where overlapping ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)) | shipped — required parity |
| [`ErrorType.from_errors(form.errors)`][upstream-forms-types] on the payload | `form.errors` → the shared [`FieldError` envelope][glossary-fielderror-envelope], `NON_FIELD_ERRORS` → the `"__all__"` sentinel ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)) | shipped — reuse the `036` envelope, adding no member |
| graphene-django `Meta.return_field_name` (per-mutation output field name) | not adopted — the `036` uniform `node` / `result` slot supersedes it ([Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)) | deliberate non-adoption |
| graphene-django `DjangoModelFormMutation` **full** update (a bound form over the raw input) | **partial** update via full-payload reconstruction from the located instance ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)) | deliberate divergence — matches the package's own `036` `PartialInput` contract |
| graphene-django form file fields (multipart `request.FILES` → form `files=`) | `Upload` input typing + the `data=` / `files=` decode split + `form_class(data=, files=, instance=)` ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)) | shipped — runtime correctness owned here (raw multipart live test) |
| graphene-django [`get_form` / `get_form_kwargs`][upstream-forms-mutation] (constructor-kwarg seam) | `get_form_kwargs(info, *, data, files, instance=None)` / `get_form(...)` hooks (default the package kwargs) + schema-time discovery via `form_class.base_fields` / `get_form_fields()` ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth) / [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)) | shipped — parity seam for migrated forms needing `user` / request / tenant |
| graphene-django relation visibility (none — form's own queryset only) | every relation id (Relay + raw pk) visibility-checked through the related primary `get_queryset` before the form, then `to_field_name`-converted ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)) | package security invariant beyond graphene parity (the `036` contract, raw-pk gap closed) |
| graphene `MutationOptions` / `ClientIDMutation` / `__init_subclass_with_meta__` | rejected for a nested `class Meta` base ([Decision 3](#decision-3--class-meta-surface-not-graphenes-mutationoptions)) | deliberately not borrowed |

### From `graphene-django` — borrow the user-facing shape

- **`Form` / `ModelForm` consumption.** The mutation runs the consumer's existing
  form — `form_class(data=…, files=…)` (create) / a full-payload-reconstructed
  `form_class(data=…, files=…, instance=<row>)` (update), `form.is_valid()`,
  `form.save()`. The form's `clean_<field>` / `clean()` validation and widget
  coercions are honored for free; the one deliberate divergence is **partial** update
  semantics (graphene-django's form update is full), via the
  [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)
  reconstruction, for consistency with the model-driven `036` `PartialInput`.
- **`form.errors` → field-keyed envelope.** graphene-django's
  `ErrorType.from_errors(form.errors)` is the parity shape; here it maps onto the
  shared `036` [`FieldError`][glossary-fielderror-envelope].

### From `strawberry-graphql-django` — borrow the runtime composition

- **Optimizer-composed return + permission scoping.** The `ModelForm` payload's
  object rides the same `036` optimizer re-fetch + visibility-scoped `update`
  locate the model-driven mutation uses — Strawberry-native, async-capable.

### Explicitly do not borrow

- **graphene's `MutationOptions` / `__init_subclass_with_meta__` / `ClientIDMutation`.**
  Rejected: the metaclass-options + relay-mutation surface the package's nested
  `class Meta` replaces ([Decision 3](#decision-3--class-meta-surface-not-graphenes-mutationoptions)).
- **`Meta.return_field_name`.** Rejected for the `036`-frozen uniform slot
  ([Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)).
- **A second `errors` envelope shape.** Rejected: one shared
  envelope across flavors; the `036` [`FieldError`][glossary-fielderror-envelope]
  is reused unchanged.

## User-facing API

Two new base classes, no new `DjangoType` `Meta` key. A consumer wraps a
`ModelForm` they already have:

```python
import strawberry
from django import forms

from django_strawberry_framework import (
    DjangoModelFormMutation,
    DjangoMutationField,
)

from . import models


class ItemModelForm(forms.ModelForm):
    class Meta:
        model = models.Item
        fields = ("name", "description", "category", "is_private")

    def clean_name(self):
        name = self.cleaned_data["name"]
        if name.lower() == "forbidden":
            raise forms.ValidationError("That name is reserved.")
        return name


class CreateItemViaForm(DjangoModelFormMutation):
    class Meta:
        # model resolves via form_class._meta.model
        form_class = ItemModelForm
        operation = "create"


class UpdateItemViaForm(DjangoModelFormMutation):
    class Meta:
        form_class = ItemModelForm
        operation = "update"


@strawberry.type
class Mutation:
    # Exposed through the shipped DjangoMutationField — no class-attribute
    # annotation; the <Name>Payload is materialized at finalization.
    create_item_via_form = DjangoMutationField(CreateItemViaForm)
    update_item_via_form = DjangoMutationField(UpdateItemViaForm)
```

generates:

```graphql
type Mutation {
  createItemViaForm(data: ItemModelFormInput!): CreateItemViaFormPayload!
  updateItemViaForm(id: ID!, data: ItemModelFormPartialInput!): UpdateItemViaFormPayload!
}

input ItemModelFormInput {
  name: String!
  description: String
  categoryId: ID!
  isPrivate: Boolean
}

type CreateItemViaFormPayload {
  node: ItemType
  errors: [FieldError!]!
}
```

The input fields are the **form's** declared fields (`ItemModelForm.Meta.fields`),
not the model's editable columns — `description` is optional because the form field
`required` is `False` (graphene-django parity). The relation input keeps the
cross-flavor `categoryId` GraphQL name, but the resolver decodes it to the **form
field** `category` (`{"category": pk}`) so the bound `ModelForm` validates it
natively — not via a raw model `setattr`
([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)
reverse map). On success the payload's `node` is the saved object re-fetched and
optimizer-planned for the response selection; on a `form.is_valid()` failure `node`
is `null` and `errors` carries one [`FieldError`][glossary-fielderror-envelope] per
offending field, keyed to the input field the client sent (`categoryId` for the form's
`category`), with the form's `NON_FIELD_ERRORS` (cross-field `clean()`,
model-constraint) bucket keyed to the `"__all__"` sentinel.

**`update` is a true partial update.** `updateItemViaForm` takes
`ItemModelFormPartialInput` — all-optional here because `ItemModelForm` declares only
model-backed fields (a required *non-model* extra field, were there one, stays
required, [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload));
the resolver locates the row through
`ItemType.get_queryset(...)` (a row the caller cannot see is a not-found `FieldError`
on `id`, never an existence leak), then reconstructs the **full** bound-form payload
from the located row's current values overlaid with the provided fields before
constructing the form
([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)).
So changing only `name` preserves `category` / `description` / `isPrivate` (and any
file field), while `unique_item_per_category` still validates against the unchanged
`category` — the `036` `PartialInput` contract, not graphene-django's full-update
form. Write authorization is the inherited
[`DjangoModelPermission`][glossary-djangomodelpermission] default (the `add` /
`change` model perm).

A plain `Form` (no model) wraps the same way through
[`DjangoFormMutation`][glossary-djangoformmutation], but its payload has **no
`DjangoType` object slot** — it is the pinned two-field shape
([Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)):

```graphql
type Mutation {
  subscribeToNewsletter(data: NewsletterFormInput!): SubscribeToNewsletterPayload!
}

type SubscribeToNewsletterPayload {
  ok: Boolean!
  errors: [FieldError!]!
}
```

On success `perform_mutate(self, form, info)` runs (default: `form.save()` if present,
else no-op; the consumer overrides it for the real side effect) and the payload is
`ok: true, errors: []`; on a validation failure `ok: false` with the field-keyed
`errors`. No cleaned-data is echoed (a model-less form returns a success flag, not
data — a consumer needing data back uses a `DjangoModelFormMutation`).

### Error shapes

- A `Meta` with no `form_class`; a `DjangoFormMutation` whose `form_class` is a
  `forms.ModelForm` (wrong base — checked first, the error names
  `DjangoModelFormMutation`) or is not a `forms.Form` subclass; a
  `DjangoModelFormMutation` whose `form_class` is not a `forms.ModelForm`, or whose
  `form_class._meta.model` is unresolvable; a bare-string
  / duplicate-name / unknown-name `Meta.fields` / `Meta.exclude` (validated against
  `form_class.base_fields`); or an empty effective field set — each raises
  [`ConfigurationError`][glossary-configurationerror] at mutation-class creation /
  finalization, naming the offending key.
- A `form.is_valid()` failure populates the
  [`FieldError` envelope][glossary-fielderror-envelope] (a null-object payload),
  **not** a top-level `GraphQLError`. A form field error keys to the form field
  name; a `clean()` / `NON_FIELD_ERRORS` error keys to the `"__all__"` sentinel.
- A write the caller is not authorized to perform
  ([`DjangoModelPermission`][glossary-djangomodelpermission] / `check_permission`
  denial) raises a top-level `GraphQLError`, **not** a `FieldError` entry — the same
  split [`spec-036`][spec-036] Decision 15 set.
- A sync form mutation whose target type has an `async def`
  [`get_queryset`][glossary-get_queryset-visibility-hook] raises
  [`SyncMisuseError`][glossary-syncmisuseerror] (coroutine closed first), the
  standing discipline.

## Architectural decisions

### Decision 1 — Spec filename and canonical naming

The spec file lives at **`docs/SPECS/spec-038-form_mutations-0_0_12.md`**.

Rationale companion: [Decision 1][rationale-d1].

### Decision 2 — Card-scope boundary: the two form flavors ship; serializer / auth stay out; the frozen `036` contracts are reused unchanged

The form flavor covers the **form-validated** write path end-to-end: the
[`DjangoFormMutation`][glossary-djangoformmutation] /
[`DjangoModelFormMutation`][glossary-djangomodelformmutation] bases, the
form-field → input mapping, the `is_valid()` → `form.errors` → `save()` pipeline,
and the products live form surface. The adjacent flavors are separate:

- **DRF serializer mutations** ([`SerializerMutation`][glossary-serializermutation])
  in [`django_strawberry_framework/rest_framework/`][rest-framework-package].
- **Auth mutations** ([Auth mutations][glossary-auth-mutations]) in
  [`django_strawberry_framework/auth/mutations.py`][auth-mutations].

It **reuses the contracts [`spec-036`][spec-036] defines**: the
[`FieldError` envelope][glossary-fielderror-envelope], the `<Name>Payload` wrapper
(uniform `node` / `result` slot), the
[`DjangoMutationField`][glossary-djangomutationfield] factory, the
[`DjangoModelPermission`][glossary-djangomodelpermission] / `Meta.permission_classes`
/ `check_permission` write-auth seam, and the [`_resolve_model`][spec-036] hook. The
form flavor adds **no** member to [`FieldError`][glossary-fielderror-envelope] and
does not re-open the `036` model-column input generator (the form generator is a
separate module). The envelope type itself is **additive** — a member may be added
(it carries `codes` and `path`), never removed or retyped.

Rationale companion: [Decision 2][rationale-d2].

### Decision 3 — `class Meta` surface, not graphene's `MutationOptions`

A form mutation is a **base class with a nested `class Meta`** (`form_class` +
optional `fields` / `exclude` + `operation` for the `ModelForm` flavor), declared
exactly like every other consumer surface in the package
([`DjangoType`][glossary-djangotype] / [`FilterSet`][glossary-filterset] /
[`OrderSet`][glossary-orderset]). It is **not** graphene's
`MutationOptions` / `__init_subclass_with_meta__(form_class=..., model=...,
return_field_name=...)` keyword-options flow, and **not** a `ClientIDMutation`
lineage.

Rationale companion: [Decision 3][rationale-d3].

### Decision 4 — Module and test locations: `forms/` subpackage mirroring `mutations/`

- **Source:** `django_strawberry_framework/forms/`, split in the spirit of the
  [`mutations/`][mutations-sets] subpackage: [`converter.py`][forms-converter] (the
  form-field → annotation registry), [`inputs.py`][forms-inputs] (the form-derived
  input + the namespace materialization), [`sets.py`][forms-sets]
  (`DjangoFormMutation` / `DjangoModelFormMutation` + metaclass + `Meta` validation
  + the bind hook), and [`resolvers.py`][forms-resolvers] (the form pipeline). It
  reuses [`mutations/`][mutations-fields]'s
  [`DjangoMutationField`][glossary-djangomutationfield] and
  [`FieldError`][glossary-fielderror-envelope] rather than re-declaring them.
- **Tests:** [`tests/forms/`][test-forms] mirroring the source modules
  (`test_converter.py` / `test_inputs.py` / `test_sets.py` / `test_resolvers.py`);
  live coverage in [`test_products_api.py`][test-products-api] and the library /
  scalars live suites.

Rationale companion: [Decision 4][rationale-d4].

### Decision 5 — Public surface: `DjangoFormMutation` / `DjangoModelFormMutation` exported from the root

Two public symbols, re-exported from [`__init__.py`][init] and listed in `__all__`:

- `DjangoFormMutation` — the plain-`Form` base.
- `DjangoModelFormMutation` — the `ModelForm` base.

No form-specific field factory or error type: both flavors are exposed through
[`DjangoMutationField`][glossary-djangomutationfield] and return the shared
[`FieldError`][glossary-fielderror-envelope] envelope. The factory is generic over
the write family on three axes, each an overridable seam on the mutation base (the
seam set is the spine of
[Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling);
[`SerializerMutation`][glossary-serializermutation] rides the same seams):

1. **Target check.** [`mutations/fields.py`][mutations-fields]
   `_validate_mutation_target` does not assert
   `issubclass(mutation_cls, DjangoMutation)`: the model-less plain
   `DjangoFormMutation` is not one, and importing the form bases there would close a
   load cycle ([`forms/sets.py`][forms-sets] imports [`mutations/sets.py`][mutations-sets]).
   The check is **duck-typed** over the protocol every flavor carries
   ([`mutations/fields.py`][mutations-fields]`::_has_mutation_protocol`): a
   `_mutation_meta` attribute (present even as `None` on an abstract base, so the next
   guard can tell "abstract base" from "not a mutation at all"), callable
   `resolve_sync` / `resolve_async` / `input_type_name`, and a non-`None`
   `input_module_path`. It does **not** require `_input_class` / `_payload_type_name`:
   those are **bind** outputs, and the field is constructed at import — when
   `@strawberry.type class Mutation` evaluates — before the bind runs. Concreteness
   is a separate check of the class's **own** `_mutation_meta` snapshot plus current
   membership, by identity, of a declaration ledger (`iter_mutations()` or
   `iter_form_mutations()`; equality would let a drained class equal to its
   redeclaration pass), because an MRO lookup would let an unregistered child inherit
   its parent's snapshot and a stale own snapshot can outlive a `registry.clear()`.
2. **Resolver dispatch.** `DjangoMutationField._resolve` calls
   `mutation_cls.resolve_sync` / `resolve_async`: the model base's seams delegate to
   [`mutations/resolvers.py`][mutations-resolvers]'s model pipeline, the form flavors'
   to [`forms/resolvers.py`][forms-resolvers]
   ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)).
   The plain form's seams take no `id`, so `_resolve` passes `id=` only when the
   operation is not the `"form"` sentinel.
3. **The `data:` input-ref.** `_synthesized_mutation_signature` builds the `data:`
   annotation from `_lazy_ref(mutation_cls.input_type_name(meta),
   mutation_cls.input_module_path)`. The model flavor names the model-column input in
   the `mutations.inputs` namespace (e.g. `ItemInput`); the form flavors name the
   form-derived input in the `forms.inputs` namespace (e.g. `ItemModelFormInput`)
   ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)).
   The **payload** ref always names `mutations.inputs`: the form flavors, like the
   model flavor, materialize their `<Name>Payload` there.

Rationale companion: [Decision 5][rationale-d5].

### Decision 6 — Base-class strategy: `DjangoModelFormMutation` rides the `DjangoMutation` base; the plain form is the model-less sibling

**`DjangoModelFormMutation` subclasses [`DjangoMutation`][glossary-djangomutation]**,
overriding [`_resolve_model`][spec-036] to return `Meta.form_class._meta.model`. It
reuses what the base provides — the primary [`DjangoType`][glossary-djangotype]
payload resolution (the uniform `node` / `result` slot), the
[`DjangoModelPermission`][glossary-djangomodelpermission] default (which checks the
model the class resolved through `_resolve_model` at declaration, so the override
authorizes it for free), the visibility-scoped `update` locate, the optimizer
re-fetch, and the phase-2.5
[`bind_mutations`][mutations-sets] pass — and overrides the base's four write-path
seams (the model flavor keeps every default; [`SerializerMutation`][glossary-serializermutation]
overrides the same seams):

- **Class-creation `Meta` validation.** The metaclass invokes the overridable
  `DjangoMutation._validate_meta(meta)` classmethod; the model base's body is
  `_validate_mutation_meta` (allowed keys `_ALLOWED_MUTATION_META_KEYS`, no
  `form_class`, `operation ∈ {"create", "update", "delete"}`). The `ModelForm`
  override uses its own allowed-key set — the two form flavors differ: the
  `ModelForm` set is `MODEL_BACKED_WRITE_META_KEYS | {form_class}` and the plain set
  is `COMMON_WRITE_META_KEYS | {form_class}`, so both add `form_class` and drop
  `model` / `input_class` / `partial_input_class`, and the plain set additionally has
  neither `operation` nor `select_for_update`. It restricts `operation` to
  `{"create", "update"}` (rejecting `delete` at class creation), and validates
  `Meta.form_class` presence + `forms.ModelForm`-subclass **before** delegating to
  `_resolve_model`, so a missing / wrong-type `form_class` is a clean
  [`ConfigurationError`][glossary-configurationerror] naming the key, never a raw
  `AttributeError` from `form_class._meta.model` and never the base's "set
  `Meta.model`" message.
- **Input generation (at the bind).** The bind materializes the input through the
  overridable `DjangoMutation.build_input(meta, primary_type)` hook: the model
  default builds a **model-column** `<Model>Input` via `build_mutation_input(meta.model,
  …)`; the form override builds the **form-derived** input from the
  [`forms/`][forms-inputs] generator
  ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)).
- **The `data:` input-ref name + module** (the [`DjangoMutationField`][glossary-djangomutationfield]
  seam, [Decision 5](#decision-5--public-surface-djangoformmutation--djangomodelformmutation-exported-from-the-root)).
- **Resolver dispatch** (`form.is_valid()` / `form.save()` vs `model(**attrs)` +
  `full_clean()`, [Decision 5](#decision-5--public-surface-djangoformmutation--djangomodelformmutation-exported-from-the-root)
  / [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)).

**`DjangoFormMutation` (plain `Form`) is the model-less sibling.** A plain `Form` has
no model, so it cannot resolve a primary [`DjangoType`][glossary-djangotype] payload
or inherit [`DjangoMutation`][glossary-djangomutation]'s resolvable-model contract.
It is a lighter base with its **own** metaclass —
`DjangoFormMutationMetaclass = make_meta_validating_metaclass(register_form_mutation, …)`,
the shared metaclass factory [`write_mixins.py`][write-mixins] exposes, bound over
the plain form's own disjoint declaration ledger — that shares the form pipeline
(`is_valid()` → `form.errors` → `FieldError` → `perform_mutate`) and the converter,
but its payload carries **no DjangoType object slot**. Because it is **not** a
[`DjangoMutation`][glossary-djangomutation] subclass, `register_mutation` /
[`bind_mutations`][mutations-sets] (which iterate the `DjangoMutation` declaration
registry) do not see it, so it has its **own** registration + bind machinery
([Decision 13](#decision-13--finalization-seam-reuse-the-mutation-phase-25-bind-no-deferred_meta_keys-change)):
a `forms/sets.py` declaration registry whose `clear_form_mutation_registry` runs on
`registry.clear()` + a `bind_form_mutations()` entry point wired into
[`types/finalizer.py`][types-finalizer]'s phase-2.5 window alongside `bind_mutations()`.
**Pinned plain-form payload contract.** The generated `<Name>Payload` for a plain
`DjangoFormMutation` is
**exactly two fields**: `ok: Boolean!` and `errors: [FieldError!]!`. No cleaned-data
output fields are generated. The success/failure contract: on `form.is_valid()`
success, `perform_mutate` runs and the payload is `ok: true, errors: []`; on a
validation failure, `perform_mutate` does **not** run and the payload is `ok: false`
with one `FieldError` per offending field (the form's `NON_FIELD_ERRORS` bucket under
the `"__all__"` sentinel) — the same envelope every flavor returns. A write-auth
denial is a top-level `GraphQLError`, never a payload (`036` Decision 15). The
side-effect hook is **`perform_mutate(self, form, info) -> None`**: the default calls
`form.save()` when the form exposes it (a `ModelForm` would, but the plain flavor is
for non-`ModelForm` forms) and is otherwise a no-op; a consumer overrides it for the
real action (send mail, enqueue a job) and returns `None`. The payload shape does not
mirror input narrowing (there are no output fields to narrow), has no nullable
ambiguity (`ok` is non-null, `errors` is the non-null list of non-null `FieldError`),
and needs no per-field descriptions.

**`Meta.return_field_name` is not adopted.** graphene-django lets a `ModelForm`
mutation name its output field; [`spec-036`][spec-036] Decision 7 **froze**
the uniform `node` / `result` slot precisely to keep one client contract across
flavors and to dodge model-name collisions (`Property` → `property`). The form flavor
inherits that frozen slot ([Risks and open questions][rationale-risks]).

Rationale companion: [Decision 6][rationale-d6].

### Decision 7 — Form-field → Strawberry input mapping: the form is the input source of truth

The input type derives from the **form's declared fields**
(`form_class.base_fields`, the stable class-level set — schema-time field discovery
above), not the model's editable columns: the input carries one field per form field the
operation's input keeps; a column-backed field is typed by its column and must share its
kind, except a scalar field over a relation column (below).
[`forms/converter.py`][forms-converter]
ships a `convert_form_field(field)` registry (the [graphene-django parity
shape][upstream-forms-converter]) returning each form field's Strawberry annotation +
required-ness from `field.required`:

- text-like (`CharField` / `EmailField` / `SlugField` / `URLField` / `RegexField` /
  `ChoiceField` / base `Field`) → `str`; `IntegerField` → `int`; `BooleanField` →
  `bool`; `FloatField` → `float`; `DecimalField` → `Decimal`; `UUIDField` →
  `uuid.UUID`; `JSONField` → `strawberry.scalars.JSON`; `DateField` /
  `DateTimeField` / `TimeField` → the Python-native types; `MultipleChoiceField` →
  `list[str]`. Resolution is a `type(field).__mro__` walk, so the most-specific
  registered class wins regardless of registration order — and `JSONField` **must**
  carry its own row even though it subclasses `CharField`, because otherwise the
  parent's entry types a JSON payload as `String` and rejects the object / array
  literals the form field itself accepts.
- `NullBooleanField` → `bool | None`. Its requiredness is a **three**-case rule and
  the one requiredness decision in the subsystem, single-sited in
  [`forms/converter.py`][forms-converter]`::form_field_required` and shared by the
  annotation path and [`forms/inputs.py`][forms-inputs]'s build site so the
  column-backed and column-less paths cannot drift: an **exact** `NullBooleanField` is
  forced optional (its `validate` is a no-op, so a declared `required=True` could
  never be enforced); a **subclass** keeps its declared requiredness, since it may
  override validation and genuinely reject omission (and so carries a non-null
  `bool`); and a field backed by a **non-null model column** keeps `required=True`,
  since model validation rejects `None` after the form field's no-op and the non-null
  annotation refuses it before execution instead.
- `ModelChoiceField` → the target model's id (a Relay-`GlobalID` when the target's
  primary [`DjangoType`][glossary-djangotype] is Relay-Node-shaped, else the scalar of
  the column storing the target's primary key, a one-to-one key or parent-link chain
  followed to the column it references — reusing the [`mutations/inputs.py`][mutations-inputs]
  `relation_input_annotation` strategy); `ModelMultipleChoiceField` →
  `list[<id>]`.
- `forms.FileField` / `forms.ImageField`, and any field whose widget is a `forms.FileInput`
  (`ClearableFileInput` included, the widget whose `value_from_datadict` reads `files`: a
  custom field rendered with `ClearableFileInput`, a `CharField` with `FileInput`) → the
  [`Upload`][glossary-upload-scalar] scalar ([`spec-037`][spec-037]).

**A column-backed field keeps its column's kind.** A `ModelForm` field named after a model
column is typed and decoded by that column
([`mutations/inputs.py`][mutations-inputs]`::model_column_write_kind`: a relation id, an
`Upload`, a scalar), while the bound form reads it by the field's own kind
(`django_strawberry_framework/forms/converter.py::form_field_kind`), so the two must agree. A
relation form field over a column that is no relation or over a relation of the other
cardinality, a file field (a `FileField`, or a field with a `forms.FileInput` widget) over a
column that is no file column, and a scalar field over a file column are a schema-build [`ConfigurationError`][glossary-configurationerror]
(`django_strawberry_framework/forms/inputs.py::require_column_kind_agreement`) on any field
the operation binds: every declared field for an update, whose reconstruction rebinds the
fields the input leaves out, and the input's own fields for a create. A scalar field over a
relation column agrees: it takes the relation's id input, and the decode hands it the
visible row's key, as an HTML form posts it, for the form to resolve (a `clean_<field>`
returning the row). A built-in temporal form field must also read its temporal column's
value, which the input carries as the column's own Python type: Django's `DateField`,
`DateTimeField`, `TimeField`, `DurationField` and `SplitDateTimeField` each read only the
kind they parse, so one over a `DateField`, `DateTimeField` or `TimeField` column is refused
at the same build
(`django_strawberry_framework/forms/inputs.py::_require_temporal_reader`) unless it is the
form class the column's own `formfield()` builds or admin's `SplitDateTimeField` over a
`DateTimeField`, or its class overrides `to_python` or `clean`: a `DateField` over a
`TimeField` column fails every value, one over a `DateTimeField` column stores midnight, and
a `DateTimeField` over a `DateField` column makes the date midnight in the current time zone,
so a current zone ahead of the default stores an earlier day. A `CharField` over a
temporal column reads the value's text and builds; a `DurationField` column, whose input
scalar a `SCALAR_MAP` entry decides, is not checked.

**The related model for a relation field's id basis.** A `ModelForm` relation
field has a backing column, so the related model (and its primary
[`DjangoType`][glossary-djangotype], which decides Relay-`GlobalID` vs raw pk) is
resolved through that column (`form_class._meta.model._meta.get_field(name)` →
`column.related_model`). A **plain `Form`** `ModelChoiceField` /
`ModelMultipleChoiceField` (a form-declared relation with no model column) has no
such column, so its related model is its **`field.queryset.model`**; the identical
Relay-`GlobalID`-vs-raw-pk rule and `<name>_id` / `list[<id>]` scheme then apply, so
the wire contract is uniform across the model-backed and model-less relation paths.
The [`forms/resolvers.py`][forms-resolvers] decode (the relation visibility check in
[Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload))
resolves the same related primary type by the **same basis** — `column.related_model`
for a model-backed relation, `field.queryset.model` for a model-less one — so the
input id type and the decode's visibility query agree.

**Where a form field overlaps a Django column type, reuse the read-side converters.**
A `ChoiceField` whose choices come from a model's `choices` should resolve to the
**same** generated Strawberry enum the read [`DjangoType`][glossary-djangotype] and
the `036` model-driven input synthesize (a symmetric wire contract), routing through
the [Choice enum generation][glossary-choice-enum-generation] /
[Scalar field conversion][glossary-scalar-field-conversion] registry rather than a
parallel mapping. **The reuse mechanism matters** because
[`types/converters.py`][types-converters]'s `convert_scalar` / `scalar_for_field` are keyed
on `models.Field` subclasses (an MRO walk), **not** on `forms.Field`: the overlap
reuse is reachable only for a **`ModelForm`** field that has a backing column —
resolve it via `form_class._meta.model._meta.get_field(name)` and route the column
through `convert_scalar` / `convert_choices_to_enum` (and a relation through
[`mutations/inputs.py`][mutations-inputs] `relation_input_annotation`). The form validates
the value, so a choice field whose **static choices admit fewer of the column's
values than the column lists** publishes a generated `<Input><Field>Enum` of exactly the
admitted values instead (members and values the column's, flattened from a grouped column;
`BLANK` only where the column lists `""` and the form admits it: a single-value field that is
not required, or a list field whose choices list `""`),
built by the shared `build_enum_from_choices` core
(`django_strawberry_framework/forms/inputs.py::_form_choice_narrowing`); a field admitting
every listed value (Django's generated `TypedChoiceField`, an equal set, a superset whose
extra values the column never stores) keeps the read enum. A `MultipleChoiceField` narrows
an `ArrayField`'s `base_field` elements and is a schema-build
[`ConfigurationError`][glossary-configurationerror] over a single-value choice column (it
writes a list). A field whose input shape disagrees with its column's is typed as the same
field off-column (`convert_form_field`), since the form field, not the column, reads the
value and a `clean_<field>` turns it into the column's
(`django_strawberry_framework/forms/inputs.py::_input_shape_disagrees`), in two directions:
a `MultipleChoiceField` / `TypedMultipleChoiceField` over a single-value column that lists
no choices and is neither an `ArrayField` nor a `JSONField` (a text column a
`clean_<field>` joins the list into) is `list[str]`; a built-in single-value form field over
an `ArrayField` (a `ChoiceField`, `TypedChoiceField`, `CharField`, `IntegerField`, ... a
`clean_<field>` wraps into a list) is that value's scalar. Both facts are the converter's:
whether a form field reads a list
(`django_strawberry_framework/forms/converter.py::form_field_reads_list`: a
`MultipleChoiceField`, a `JSONField`, PostgreSQL's `SimpleArrayField` and
`SplitArrayField`, subclasses included) and whether it is a built-in single-value field
(`django_strawberry_framework/forms/converter.py::form_field_reads_one_value`: a registered
scalar form field, subclasses included, reading no list). So the default `ModelForm` field
over an `ArrayField` (the `SimpleArrayField` `ArrayField.formfield` builds) keeps the
column's list, and so do a bare `forms.Field` and a consumer field no registered class
covers, whose `to_python` may read the list. A `SplitArrayField` reads its list from one
form-data key per index (its `SplitArrayWidget`), so the list is bound one element per key,
padded to `size` with `None`, and a list longer than `size` is refused
([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)
step 4). A single-value `ChoiceField` over an `ArrayField` whose `base_field` lists choices is
typed by that `base_field` (`django_strawberry_framework/forms/inputs.py::_input_typing_column`):
the element's read enum, the one the column's list carries, narrowed by the form's choices as
a single-value choice column is. The package never wraps or joins the value itself. A
value the form accepts and leaves un-wrapped reaches Django's list validation inside
`is_valid()` as a scalar and fails there with Django's own exception (`JSONDecodeError`,
`TypeError`): a top-level error, masked under the error policy; text that is itself a JSON
array is read as the list (an empty value cleaned to `""` over a `null=False`
column is that column's `null` error, Decision 8 step 5). A
create's and an update's build each log one `logger.warning` per such field it binds, naming
its direction and what the form must do to turn the input into the column's value
(`django_strawberry_framework/forms/inputs.py::_advise_shape_disagreement`); an update's also
names the initial: an omitted one binds the form's own initial (Decision 8), which must
present the stored value in the field's shape. A `JSONField` column keeps `JSON`. A field admitting no non-empty value the column lists is a
`ConfigurationError` (its input could carry at most the empty value, so no non-empty value
passes the form). The input is built once, at schema
build, from the field basis, so callable choices (re-evaluated on every read) and choices
assigned in `__init__` are request-time state: they keep the column's enum and the bound form
refuses a value outside its request-time choices. The narrowing covers the values a client
sends; a partial update validates an omitted narrowed field's stored value (reconstructed
from the row, Decision 8) against the form's choices, as Django's form does, so a row holding a value the form does not admit
cannot be partially updated through that form (a field-keyed `invalid_choice` error,
nothing written) until the request sends an admitted replacement. A **plain
`Form`** field with no model column (a `captcha`, a `confirm_email`) has no read-side
equivalent and necessarily uses the form-field → Strawberry table in
[`forms/converter.py`][forms-converter] — which is therefore genuinely net-new
machinery for the model-less case, **not** a parallel copy of the scalar table for the
model-backed case (the explicit guard against the over-DRY-into-drift trap). An
unknown form-field class raises [`ConfigurationError`][glossary-configurationerror]
naming the field and class (the graphene-django `convert_form_field`
`ImproperlyConfigured` parity, raised as the package's own exception).

**The fail-loud contract requires NOT registering a base-`forms.Field` catch-all.** A naive `functools.singledispatch` with `forms.Field` registered → `str` makes
**every** custom `forms.Field` subclass dispatch to that catch-all, so the
unknown-field raise becomes **unreachable** and a consumer's custom field silently
becomes `String`. So the registry's **fallthrough (unregistered) default RAISES**
`ConfigurationError`, and the supported classes are registered *individually*
(`CharField`, `IntegerField`, … — their subclasses, e.g. `EmailField` /
`SlugField` / `RegexField` under `CharField`, still map via the dispatch MRO, the
parity behavior). A bare **`forms.Field`** is handled as an **explicit exact-type
special case** → `str` (so the listed "base `Field` → `str`" still holds), **not** as a
catch-all registration. The upshot: a known field or a subclass of one maps; a bare
`forms.Field` maps to `str`; a custom `class CustomField(forms.Field)` with no
supported ancestor hits the raising default — proven by a `CustomField(forms.Field)`
test asserting the raise.

**Per-field metadata: the `input_attr` → `form_field_name` reverse map.** The
generated input GraphQL names follow the cross-flavor `036` convention so the wire
contract is uniform across mutation flavors — a `ModelChoiceField` named `category`
generates `categoryId` (python attr `category_id`), a scalar/`MultipleChoice`/file
field keeps its own name. But a **bound Django form is keyed by form-field name**
(`ItemModelForm(data={"category": pk})`, **not** `{"category_id": pk}` — the latter
makes the form think `category` is missing). So `forms/inputs.py` **retains, per
generated input field, a [`utils/inputs.py`][utils-inputs]`::InputFieldSpec`** that
`forms/resolvers.py` consults at decode. That is the single reverse-map record type
every write flavor shares: `input_attr` (the generated Strawberry attr) and
`graphql_name` (the camel-cased wire name) map to `target_name` — the form's own
declared field name on this path — plus a `kind ∈ {scalar, relation_single,
relation_multi, file}` and, for a relation, the `related_model` recorded at build time
so the decode never re-discovers it per request. The four `kind` constants are defined
in [`utils/inputs.py`][utils-inputs] and re-exported by
[`forms/converter.py`][forms-converter], which owns the constants and not the record
type:

- `category_id` / `categoryId` → form field `category`, kind `relation_single`
  (the form relation decoder below type-checks the id — `GlobalID` *or* raw pk —
  resolves the **visible** object through the related primary type's `get_queryset`,
  and places its `to_field_name` value (default `obj.pk`) under `category`, which the
  bound `ModelChoiceField.to_python` then resolves).
- `genres` → form field `genres`, kind `relation_multi` (each element decoded,
  visibility-checked, and `to_field_name`-converted the same way, then placed as a
  list under `genres` for `ModelMultipleChoiceField`).
- `avatar` → form field `avatar`, kind `file` (routed to `files=`, see
  [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)).
- every plain scalar → identity (`name` → `name`, kind `scalar`).

The reverse map is the single fix for the "`category_id` vs `category`" hazard: the
generated input may *expose* `categoryId` (parity), but the decode always produces a
**form-field-keyed** dict the bound form validates natively — never accidental
model-assignment semantics. Package + live tests prove the relation field validates
**through the form** (`clean_<field>` runs), not through a raw model `setattr`.

**The relation decode visibility-checks EVERY branch — Relay `GlobalID` AND raw pk.**
A default `ModelForm`'s relation queryset is `Category.objects.all()` — **not**
request-scoped — so the visibility gate must run before the form, and it must cover
the **non-Relay raw-pk branch** too: a raw-pk target has no `GlobalID` to scope, so a
decoder that visibility-checks only the Relay branch lets a writer attach a hidden
related object. The gate is therefore owned by one shared spine,
[`utils/write_values.py`][utils-write-values]`::decode_visible_relation`, which every
write flavor rides and which the form flavor only *colors*: the spine (i) skips a
clear / no-value unchanged, so the bound form's own validation decides required-ness
(the form's clear is the WHOLE relation value in the field's `empty_values`: a single
`null` or `""`, or an M2M `null` or empty list; a list element is never a clear, so an
M2M element such as a raw text pk `""` gets steps (ii)-(iv) like any id, and a hidden or
missing row is the same per-element relation error rather than an undecoded key the
`ModelMultipleChoiceField` would look up, linking a hidden row or reading a pk as
another row's `to_field_name` value),
(ii) type-checks and coerces the id (a bad `GlobalID` or an uncoercible raw pk, a text
id holding an embedded NUL included since it names no row, is the
uniform field-keyed `FieldError`; a coerced pk holding unencodable text, such as a lone
surrogate in the id of a text-keyed target, is the text preflight's field-keyed `invalid`
error, keyed to the element's index in a list, before any query), (iii) for **both**
branches **resolves the object
from the related primary [`DjangoType`][glossary-djangotype]'s
[`get_queryset`][glossary-get_queryset-visibility-hook]** (the same
`apply_type_visibility_sync(initial_queryset(...))` query every read surface applies) —
a pk not in that visible set is the same no-existence-leak field-keyed `FieldError`,
whether it arrived as a `GlobalID` or a raw pk — and (iv) projects the visible object
to the flavor's bound value. The form's colouring is the `empty_values` skip and the
`to_field_name` projection below; `decode_field_handlers` /
`decode_provided_fields` own the `UNSET` strip and the `kind` dispatch around it. The
form's own `queryset` is then a *secondary* guard, not the only one.

**`to_field_name` is honored when converting the object back to the form's key.**
A `ModelChoiceField` may set `to_field_name` (and a
`ForeignKey(to_field="slug")` generates exactly that), so `to_python` looks the object
up by the configured field, **not** `pk` — feeding a raw `pk` would make a valid
GraphQL id fail form validation. So after the visibility query yields the visible
**object**, the decoder converts it with the form field's own key:
`obj.serializable_value(field.to_field_name)` when `to_field_name` is set, else
`obj.pk`, and places that under the form field name (per element for
`ModelMultipleChoiceField`). The input build admits only a `to_field_name` that names
one row the decoded row carries: unset, `""`, `"pk"`, or a concrete field of the target,
by name or attname, that is unique on its own (`unique=True`, a one-field
`unique_together` entry, or a `UniqueConstraint` over it alone with no condition:
Django's fields.E311 test for a `ForeignKey.to_field`, extended to the declarations the
target inherits, as E311 reads only the target's own)
(`django_strawberry_framework/forms/inputs.py::require_readable_choice_keys`, run over
the fields the operation binds: the full declared field set for an update, whose
reconstruction rebinds every declared field, and the input's own fields for a create).
A lookup path, an annotation, a property, an unknown name or a column two rows may share
is a schema-build `ConfigurationError`, never a fall back to `obj.pk`: the form's
`queryset.get(<to_field_name>=key)` would resolve another row or raise
`MultipleObjectsReturned`, and a `ModelMultipleChoiceField` would link every row sharing
the key, a hidden one included; an annotation `to_field_name`, which plain Django
accepts, is refused for that reason. The bound form must look the key up the same way:
each bound model-choice field, which an `__init__` or `get_form` override may rebuild,
must query the target model or a subclass of it and resolve its choice by the same
column as the class-level field the decode read, every spelling of the primary key
counting as one column
(`django_strawberry_framework/forms/resolvers.py::_assert_bound_choice_agreement`, run
after `get_form` and before `is_valid()` over every bound name, an update's
reconstructed relations included). A disagreeing field is a `ConfigurationError` on the
request with nothing written. The bound `ModelForm`'s `instance` must likewise be a row of
the mutation's model or a subclass of it (an MTI child or a proxy subclass), the table its
save writes, never another model's, a concrete base of a proxy-backed mutation's model, a
sibling proxy or an MTI parent
(`django_strawberry_framework/forms/resolvers.py::_require_backing_row`, run after
`get_form` and before any bind or `is_valid()`, and again on the saved instance inside the
pipeline transaction); a form with no instance or an instance of another model is a
`ConfigurationError` on the request with nothing written. Reassigning the queryset over the same model and key (the
request-scoped choices idiom) agrees, and a bound field that is no longer a model-choice
field or has no queryset is left to the form. Where the bound field is certain to be the
class-level one (a `ModelForm` that resolves `__init__` and `order_fields` to Django's own,
under a mutation that keeps the default `get_form`), a column-backed model-choice field whose
class-level queryset is over a model that is neither the column's related model nor a
subclass of it would fail every request that binds it, so it is a schema-build
`ConfigurationError` instead wherever every write binds it
(`django_strawberry_framework/forms/inputs.py::require_class_choice_models`, run per
declaration over every declared field for an update, whose reconstruction binds them all,
and for a create over the input's fields the input makes required, its non-null
arguments). A create may omit an optional field and then never binds it, so such a field
builds and only a create that sends it is refused at request time; an
`__init__`, `order_fields` or `get_form` override that may reassign the queryset leaves the
field to the request-time check. A visible row
whose stored key (the column a `ForeignKey(to_field=…)` stores) is `NULL` names no row,
whatever column the form field is keyed by: the spine's visibility read admits only rows
whose key is set (`django_strawberry_framework/utils/querysets.py::linkable_rows`), so it
is the uniform relation `FieldError`, never a bound key that stores `NULL` and clears the
relation. A hidden-`Category` id (Relay or raw pk) therefore returns
the **identical** field-keyed `FieldError` the model-driven mutation returns — proven
by live + package tests over a Relay primary AND a non-Relay (raw-pk) primary, for both
single and multi relations. A single `ModelChoiceField` cannot name a visible row whose
form-key value is in the field's `empty_values` (a `to_field_name` column holding `""`):
`ModelChoiceField.to_python` answers `None` for such a value before its lookup, so
binding it would clear the relation the client named. The decoder reports it as the
form field's own `invalid_choice` error keyed to the input field, before any form is
bound (`django_strawberry_framework/forms/resolvers.py::_unrepresentable_choice`, the same check an omitted
relation passes in Decision 8 step 4). A `ModelMultipleChoiceField` looks every member
key up, `""` included, so a member keyed `""` is linked, not refused.

**Two generated inputs: create (`field.required`) + partial.** Like the `036`
`Input` / `PartialInput` split, the form flavor generates `<FormClass>Input` (create;
each field's requiredness from the form field's `field.required`) and
`<FormClass>PartialInput` (update). In the partial input, **model-backed** form fields
are forced optional — [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)'s
reconstruction supplies them from the located row — but a **non-model** extra form
field (a `confirm`, a captcha, an action flag, with no model column to reconstruct
from) keeps its declared `field.required` (see
[Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)'s
required-extra-field rule), so a required extra field stays required on update and an
optional one may be omitted.

**An update input never carries the primary key.** A `ModelForm` field whose backing
column is the model's primary key (a `OneToOneField(primary_key=True)` such as
`PatronProfile.patron`, a client-assigned text key such as `Edition.isbn_13`, a member column
of a `CompositePrimaryKey`) is a create
input (a create names its row by it) and is left out of `<FormClass>PartialInput`: the
mutation's `id` argument names the row, and `construct_instance` would assign a sent key
to the located instance so that `save()` updates or inserts a different row (an
`editable=False` key is exempt: `construct_instance` never writes it, so a declared field
named like one stays an input). Decision 8's
reconstruction rebinds the omitted field from the located row, so the bound form still
validates it at its stored value. An update `Meta.fields` naming such a field raises
[`ConfigurationError`][glossary-configurationerror] at class creation, an update
`Meta.exclude` naming it is accepted as the no-op it states, and a form whose only field
is the key has no update input (the empty-input error). The canonical
`<FormClass>PartialInput` name is the full shape minus the key
(`django_strawberry_framework/forms/inputs.py::resolve_effective_form_fields`).

**Shape identity + naming + collision (the `036` discipline).** A generated form
input's identity is **not** its name — it is the tuple **`(form_class, operation
kind, frozenset(effective field names after `Meta.fields` / `Meta.exclude`),
field-discovery basis content identity)`**, parallel to `036`'s `(model, operation kind,
effective field set)` ([`mutations/inputs.py`][mutations-inputs]
`mutation_input_shape` / `mutation_input_type_name`) plus one component the form
flavor needs. The fourth component is the **basis content** the `get_form_fields` hook
contributes, not a fifth concept: `forms/inputs.py::_form_basis_content_identity`
projects each basis field to its converter-dispatch type, its requiredness, a
column-less relation field's related model and the column values a choice field narrows
its enum to, so two mutations over one form whose hooks
produce identical bases dedupe onto one input, and any content difference builds a
separate one. The **operation kind** component is the
`DjangoModelFormMutation`'s `"create"` / `"update"`, or the fixed sentinel **`"form"`**
for a plain `DjangoFormMutation` (which has no model operation) — so a plain
form's input cache key is well-defined (`(form_class, "form", effective set, basis content)`) and two
plain mutations over the same form + effective set dedupe. Keying on the **form class object** (not its `__name__`)
captures the field *representation* — two forms with the same field names but
different field types are different `form_class`es, so they never wrongly dedupe. The
generated GraphQL **name** is the canonical `<FormClass.__name__>Input` /
`<FormClass.__name__>PartialInput` for the **full** effective shape, and a
**deterministic shape-derived name** (the model-flavor's injective sorted-field-token
scheme) for a **narrowed** (`Meta.fields` / `Meta.exclude`) shape — so two different
narrowings of one form get distinct names, and two narrowings to the *same* effective
set dedupe. **Two distinct shapes that resolve to the same generated GraphQL name
raise [`ConfigurationError`][glossary-configurationerror] at finalization** — this is
the **fail-loud fix** for the two collision cases: (a) the same
`ItemModelForm` used by two mutations with different effective field sets (distinct
shape-derived names; no clash, but if a narrowing collides with the canonical name it
raises), and (b) two **different** `ItemForm` / `NewsletterForm` classes with the same
`__name__` — both emit `<__name__>Input`, and because they are **distinct `form_class`
identities they can never dedupe** (dedupe is only within one `form_class` + effective
set), so this **always raises** regardless of whether their field shapes happen to
match; the consumer disambiguates by renaming one form (there is no name-override
`Meta` key). Only repeats of the **same** `(form_class, operation kind, effective
set, basis content)` dedupe to one materialized class. The raise comes from
[`utils/inputs.py`][utils-inputs]`::materialize_generated_input_class`, whose ledger
raises on a second *different* class under one name (the `036` raise), so the form
flavor has the early-`ConfigurationError`-not-late-Strawberry-error posture. The family ledger is per family; a name another family also derives (a model input, a `ModelForm` or serializer class whose name meets it, a filter or order input) is the cross-family type-name claim at [`utils/inputs.py::claim_generated_type_name`][utils-inputs]: identical fields merge into one type, and two shapes fail any schema serving both with Strawberry's `DuplicatedTypeName`, which [`DjangoSchema`][glossary-djangoschema] restates naming both mutations.

**`Meta.fields` / `Meta.exclude` are normalized + fail-loud against
`form_class.base_fields`.** The form base validates the narrowing at **class
creation** through the narrowing spine it shares with the serializer flavor
([`utils/inputs.py`][utils-inputs]`::resolve_effective_fields`): a bare string
(`fields = "name"`) is rejected (it
would iterate as characters; a lazy translation string (`gettext_lazy("name")`) and a bytes-like value are bare strings here, refused with the same message ([`utils/_narrowing.py::is_text_atom`][utils-narrowing]); every lazy `Promise` counts whatever result class it wraps, so a lazy list is refused too, while a `SimpleLazyObject` is judged as the object it stands for), duplicate names are rejected, a `set` / `frozenset` `fields` is rejected (its order is the generated input's field order) while a set `exclude` is accepted and stored sorted by `utils/canonical.py::canonical_sort_key` (`utils/inputs.py::normalize_field_name_sequence`'s `ordered` switch), `fields` and `exclude`
are mutually exclusive, and a name in neither `form_class.base_fields` raises
[`ConfigurationError`][glossary-configurationerror] naming the unknown field (a typo
like `fields = ("emial",)` fails loud, never silently shrinks the input). An
**empty effective field set** (a `fields = ()`, an `exclude` that drops every field,
or a form with no fields) raises [`ConfigurationError`][glossary-configurationerror]
at class creation — never a bare empty `@strawberry.input` that Strawberry rejects
only at schema build (the `036` empty-input guard, applied to `form.base_fields`).

**A `create` narrowing that drops a required form field is rejected.** A bound
form fails required-validation for any `field.required` field absent from its bound
`data=`, and `initial` is **not** a substitute for submitted data — so a `create`
whose effective field set (after `Meta.fields` / `Meta.exclude`) omits a still-declared
required form field would compile to a schema that *looks* valid but can **never**
succeed. The bind therefore raises [`ConfigurationError`][glossary-configurationerror]
([`forms/inputs.py`][forms-inputs]`::guard_create_required_fields`, run per mutation
declaration, not per cached input shape), naming the missing required field(s), when
the input is create-shaped and the narrowing excludes any `field.required` form field
(covering **both** `Meta.fields` and `Meta.exclude`). The escape hatch is an overridable
`get_form_kwargs` / `get_form` ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload))
that supplies those values before binding: when the consumer has overridden that hook,
the guard is waived (it cannot know *which* fields the override injects, so it trusts
the explicit override rather than block a legitimate scoped form).

**There are TWO narrowing guards, keyed on that one waiver.** `update` is not exempt,
only narrower: a required **model-backed** field dropped from a partial input is
harmless, because [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)'s reconstruction supplies it
from the located row — but a required **column-less** field (a declarative
`confirm = forms.CharField(required=True)`) has no row value to reconstruct from, so
dropping it finalizes a form whose bound validation fails on every request while the
schema still builds. [`forms/inputs.py`][forms-inputs]`::guard_partial_required_column_less_fields`
rejects that narrowing at bind, naming the field(s). Scoping the partial guard to
column-less fields is load-bearing: reusing the create guard here would wrongly reject
the reconstructable model-backed fields the partial path legitimately drops.

**Materialization + the `data:`-ref seam.** [`forms/inputs.py`][forms-inputs] builds
one `@strawberry.input` from the form fields — reusing
[`utils/inputs.py`][utils-inputs]'s single-sited `build_strawberry_input_class` +
`materialize_generated_input_class` core (the same machinery `mutations/inputs.py` /
`orders/inputs.py` wrap, with its own `forms` module path + `family_label` + ledger),
not a hand-rolled `setattr` — and materializes it as a module global of the **`forms`
input namespace** under a form-derived name (`<FormClass>Input`, e.g.
`ItemModelFormInput`) — a name and a shape distinct from the `036` model-column
`<Model>Input` in `mutations.inputs`. So the [`DjangoMutationField`][glossary-djangomutationfield]
`data:` lazy ref **cannot** use the shipped `_input_type_name(meta)` (model columns) +
`INPUTS_MODULE_PATH` (`mutations.inputs`): the form flavor overrides the
`input_type_name(meta)` + `input_module_path` seams
([Decision 5](#decision-5--public-surface-djangoformmutation--djangomodelformmutation-exported-from-the-root))
so the synthesized `data:` ref names the form input in the `forms` namespace, and the
bind's `build_input(meta, primary_type)` hook
([Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling))
materializes exactly that class — so the ref the field synthesizes and the class the
bind materializes are one and the same (the lifecycle discipline the set families and
`036` already follow).

**Schema-time field discovery reads `form_class.base_fields`, never an instance
(the kwarg-requiring-form case).** The input shape is derived from
**`form_class.base_fields`** — the class-level declared-fields dict Django's
`DeclarativeFieldsMetaclass` / `ModelFormMetaclass` populate at class creation (for a
`ModelForm`, `base_fields` already includes the model-derived fields). Reading it
needs **no instantiation**, so a form whose `__init__` requires constructor kwargs
(`user`, `request`, a tenant — common in migrated forms) still has a discoverable,
**request-independent stable** field shape (a form that mutates `self.fields` in
`__init__` by request could not be a stable GraphQL input anyway). An overridable
classmethod **`get_form_fields(cls) -> dict[str, forms.Field]`** (default:
`form_class.base_fields`) lets a consumer customize the discovered set; whatever it
returns must be stable across requests. A returned key is read as its text: a `StrEnum` /
`TextChoices` member names the input attribute by the exact `str` it spells, and a
non-string key is refused with a `ConfigurationError`. Instantiating `form_class()` no-arg to read
`form.fields` is **not** an option: it breaks for exactly the kwarg-requiring forms
this rule exists to serve.

Rationale companion: [Decision 7][rationale-d7].

### Decision 8 — Resolver pipeline: instantiate → `is_valid()` → `form.errors` → `save()` → optimizer re-fetch → payload

[`forms/resolvers.py`][forms-resolvers] runs one pipeline per flavor, sync and async,
swapping the model-construct + `full_clean()` heart of the
[`mutations/resolvers.py`][mutations-resolvers] pipeline for the form's own
validation and write, but **reusing the surrounding `036` steps**. The order is
**locate → authorize → decode → construct/validate → write → re-fetch → return**, and
**authorize runs BEFORE the relation decode** — the same authorize-first order the `036`
model path uses. That ordering is a security boundary, not a preference: the decode
issues visibility-scoped `get_queryset` queries, so decoding first would let an
unauthorized caller probe related-object visibility by id, and a write-auth denial
(top-level `GraphQLError`) versus an in-band relation
[`FieldError`][glossary-fielderror-envelope] is an observable distinction. Authorizing
first collapses both to the denial. Every flavor reusing this pipeline (including
[`SerializerMutation`][glossary-serializermutation]) authorizes before decoding
relations. The order is single-sited in
[`mutations/resolvers.py`][mutations-resolvers]`::run_write_pipeline_sync`,
whose own docstring pins it (#"authorize BEFORE decode") and which every
write flavor rides.

1. **Locate** (`update`, `ModelForm` only): the top-level `id:` argument is
   `strawberry.ID` (a raw GlobalID **string** the package decodes server-side via the
   reused `036` `coerce_lookup_id` — the same `node(id: ID!)` contract the shipped
   [`DjangoNodeField`][glossary-djangonodefield] uses, and the same raw `ID` string a
   Relay relation `data:` field carries into the relation decode); a malformed / wrong-model / uncoercible `id:` (a text
   id holding an embedded NUL names no row: the not-found error), or a
   raw pk holding unencodable text (a lone surrogate in a text-keyed primary's id), is an
   `id`-keyed `FieldError` **before** any lookup (no existence leak — the mutation
   surface returns the `FieldError` envelope, **not** the node field's
   `null` / `GLOBALID_INVALID`). The row is then resolved through the target type's
   [`get_queryset`][glossary-get_queryset-visibility-hook] (the `036`
   `locate_instance`); a miss (hidden or genuinely absent — indistinguishable) is a
   not-found `FieldError` on `id`. This step
   **only locates** — the form is **not** constructed here (the located row is
   carried to step 4 as the `instance=` kwarg), so the form is built exactly once, in
   step 4, from the reconstructed `data=` / `files=` payload. (graphene-django builds
   its form once too via `get_form_kwargs`, but as a *full* update; the package's
   step-4 merge is what adds true partial semantics on top of that single
   construction.)
2. **Authorize**: the inherited `check_permission` / `Meta.permission_classes`
   (before validation for `create`; after the locate for `update`). A denial raises
   a top-level `GraphQLError` ([`spec-036`][spec-036] Decision 15).
3. **Decode** the `data:` input into **two `dict`s keyed by FORM-field name** —
   `provided_data` (scalars, choice-enum raw values, and relation pks / pk-lists) and
   `provided_files` (uploaded files) — using the shared
   [`utils/inputs.py`][utils-inputs]`::InputFieldSpec` reverse-map record of
   [Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)
   (`UNSET` stripped). A
   `relation_single` / `relation_multi` field runs the **form relation decoder**
   ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)) over the
   shared [`utils/write_values.py`][utils-write-values]`::decode_visible_relation`
   spine, the single owner of the cross-flavor invariant that a writer never attaches
   a row it cannot see: it type-checks each id (`GlobalID` *or* raw pk; wrong-model /
   uncoercible / unencodable text → field-keyed `FieldError`, the `036` id-type-check contract), **resolves the
   visible object through the related primary `DjangoType.get_queryset` for BOTH
   branches** (a hidden / unseeable target is the same field-keyed `FieldError`, no
   existence leak; so is a visible target whose stored `to_field` key is `NULL`), and
   lands the object's `to_field_name` value (default `obj.pk`) under the form field name (`{form_field_name: value}` / `{form_field_name: [value,
   …]}`); a `file` field lands its uploaded value in **`provided_files`**, not
   `provided_data` (the file-routing fix below); a `scalar` choice-enum member is
   unwrapped to its raw value. The split by `kind` is the single point that keeps
   form-field names,
   visibility-checked relation pks, and file uploads each going to the right place.
4. **Construct + validate** the form **once**, through the overridable
   **`get_form_kwargs(self, info, *, data, files, instance=None) -> dict`** hook (the
   graphene-django `get_form_kwargs` parity seam, used by `create`, `update`, and
   the plain form). The default returns `{"data": data, "files": files}` (plus
   `"instance": instance` when non-`None`), and the resolver builds the form as
   `form_class(**self.get_form_kwargs(info, data=…, files=…, instance=…))`. A consumer
   overrides it to inject constructor kwargs migrated forms need — `user=…`,
   `request=…`, a tenant — or to pass the request-scoped `ModelChoiceField` queryset
   the form narrows with in its own `__init__`: `get_form_kwargs` returns
   **constructor kwargs**, so the hook is the channel and the form applies it,
   **without changing the generated input shape** (the input is derived from
   `get_form_fields()`, [Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth),
   independent of `get_form_kwargs`). A hook that injects a value the narrowed input
   cannot carry is only **observably** working if a test asserts the **written row**:
   the wire envelope of a failed write is identical whether the injection ran or not,
   because a missing non-nullable FK raises `IntegrityError` too and maps to the same
   `"__all__"` envelope. A `get_form(self, info, *, data, files,
   instance=None)` hook (default: `form_class(**self.get_form_kwargs(...))`) is the
   coarser override for full control, within the row-model rule: on the `ModelForm`
   flavor the form it returns must hold a row of the mutation's model (or a subclass) as
   its `instance`, since the save writes the instance's table, or the request is a
   `ConfigurationError` before `is_valid()` with nothing written
   (`django_strawberry_framework/forms/resolvers.py::_require_backing_row`). This **does not replace** the relation-visibility
   gate (step 3, which runs before the form regardless) — `get_form_kwargs` adds
   request-scoping on top of, not instead of, the visibility check. A form reads each
   field from the keys its widget reads under `form.add_prefix(<field>)`: a prefixed form
   reads `<prefix>-<field>` (a class-level `prefix`, a `get_form_kwargs` `prefix=`, a
   `get_form` passing the package's mapping or a copy of it with a prefix), and a widget
   reading several keys reads its parts under that name's own keys (a `MultiWidget`, such
   as `SplitDateTimeField`'s, `<field>_0` / `<field>_1` per `widgets_names`; PostgreSQL's
   `SplitArrayWidget`, `SplitArrayField`'s, `<field>_0` .. `<field>_<size - 1>`), so each
   value is bound under those keys. The rule is by content, each of the built form's
   `data` / `files` on its own: a `data` mapping holding a form field's bare name and none
   of the keys the form reads it under is re-keyed on the built form, before the package
   or `is_valid()` reads it, through the bound form's own fields: each value whole under
   `form.add_prefix(<field>)` and its parts under the widget's keys (a `MultiWidget` splits
   a value that is no list with its own `decompress`, as its `get_context` does; a
   `SplitArrayWidget` gets one element per index, padded to its `size` with `None`, so an
   empty list is bound and never read as omitted); a `files` mapping is re-keyed under the
   prefix alone. The form's own `__init__` sees the field-keyed mapping
   (`django_strawberry_framework/forms/resolvers.py::_bind_under_form_keys`; the keys a
   widget reads are `django_strawberry_framework/utils/widgets.py::widget_keys` /
   `django_strawberry_framework/utils/widgets.py::widget_entries`, the owner the filter
   side's `multi_widget_keys` lives in). A list longer than a `SplitArrayWidget`'s `size`
   (sent, reconstructed from the located row, or an omitted field's initial), whose tail
   the widget would drop, is refused before `is_valid()` as that field's error with
   Django's own `ArrayMaxLengthValidator` message and code `max_length`, keyed like every
   field error, nothing written. Only those field names move; any other key (a CSRF token,
   an extra value a consumer `clean()` reads) stays as bound, as a prefixed Django form
   leaves it. The bound mapping is never mutated: a re-keyed copy replaces it (a
   `MultiValueDict`, an immutable `QueryDict` included, as a copy of its own type, each
   part as its one entry; a files `dict` as a `MultiValueDict` whose `get` answers each
   value unchanged). A mapping already holding a key the form reads was keyed by its
   builder, wholly or partly, and is left alone, except that a multi-key widget field
   whose whole value it holds under `form.add_prefix(<field>)`, with none of the widget's
   part keys, gets those parts bound beside it (the same split and `size` refusal;
   `django_strawberry_framework/forms/resolvers.py::_bind_kept_parts`). A `disabled`
   field reads no data (Django cleans its initial), so it is bound whole, never split nor
   refused. A `MultiValueDict` holding several values for a field (`setlist`, a `doseq`
   query string) is read as the list of them, one value as that value. Every later read or write of a bound
   value (the explicit-`null` and required-file checks of step 5, an omitted list field's
   initial) goes through the same keys
   (`django_strawberry_framework/forms/resolvers.py::_bound_form_value` reads the whole
   value under `form.add_prefix`, so an explicit `null` reads as `None` whatever the
   widget; `django_strawberry_framework/forms/resolvers.py::_bind_form_values` binds whole
   and in parts), so a consumer `add_prefix` override is honoured; `form.errors` stays
   keyed by field name. The form
   is built with the `data=` / `files=` split Django requires (a bound form reads
   scalars/relations from `data=` and uploaded files from `files=` — an `UploadedFile`
   in `data=` does **not** validate):
   - **`create`** — `data = provided_data`, `files = provided_files`, then
     `form_class(**get_form_kwargs(info, data=provided_data, files=provided_files))`.
   - **`update` (the pinned partial-update contract)** — a bound `ModelForm`
     validates **every** field, so handing it only the provided fields would reject a
     valid partial update (missing-required) or clear omitted optional fields. So the
     resolver **reconstructs the complete bound payload from the located instance plus
     the provided values**, overlaid by `provided_data`, and passes
     `files = provided_files` **only** (an omitted file field is
     preserved by the bound `form_class(instance=…)` via its `initial`, never
     re-supplied and never cleared; an explicit `null` file is bound as Django's clear
     sentinel `False`, see [Edge cases](#edge-cases-and-constraints)); then
     `form_class(**get_form_kwargs(info, data=data, files=files, instance=<located row>))`.
     - **The reconstruction reads the form's FULL declared field set**
       (`get_form_fields()`), not the narrowed input: a `Meta.fields` /
       `Meta.exclude` narrowing drops fields from the GraphQL input, but the bound
       `ModelForm` still validates every field it declares, so an excluded
       model-backed field must still be supplied from the located row.
     - **Every omitted field binds in the shape a provided one decodes to**, which
       takes **three** forms, single-sited in
       [`forms/resolvers.py`][forms-resolvers]`::_reconstruct_partial_data`:
       `model_to_dict` for scalars and for a FK / one-to-one whose `ModelChoiceField`
       resolves its choice by the column the relation stores (`to_field_name or "pk"`
       names `ForeignKey.target_field`, as every generated field does), so the stored
       value is already the form key and no related row is read; the form field's
       `prepare_value` per member for a real forward M2M (the `to_field_name` value, default
       `obj.pk` — not `model_to_dict`'s list of related *instances*); and
       `prepare_value` of the related row for every other single
       `ModelChoiceField` FK / one-to-one: a `to_field_name` naming another column, or
       a `to_field_name`-**less** field over a `ForeignKey(to_field=…)`, which resolves
       by pk while the column stores the `to_field` value. Getting any of the three
       wrong makes an omitted unchanged field fail, or bind the row whose key equals
       the stored value, where a provided unchanged field passes.
     - **A single FK's form key must be one the form field looks up.** A NULL column
       still comes from `model_to_dict` (the form's empty value). Every non-null stored
       key passes one representability check
       (`django_strawberry_framework/forms/resolvers.py::_unrepresentable_choice`) before the form is bound, and a
       failure is the form field's own `invalid_choice` error mapped through
       `_form_errors_to_field_errors`: the mutation fails before the form is bound, so
       nothing is written, and the stored key is never reinterpreted or replaced by an
       empty value. Two keys fail it. A form key in the field's `empty_values` (a
       `to_field` or text key holding `""`, stored when the form key is the stored
       column, projected from the related row for the third shape) cleans to empty in
       `ModelChoiceField.to_python` before any lookup, so it would bind as a clear
       whether or not a row carries it; the stored-column case is decided by the stored
       value alone, with no query. And for the third shape a stored key whose related
       row is missing (a `db_constraint=False` key left dangling) has no form-key value:
       the stored key and the form key are different namespaces, so binding the stored
       key could resolve an unrelated row whose form key equals it. When the form key is
       the stored column and is not empty, the bound form's own lookup already refuses a
       dangling key with the same error. A provided relation passes the same check at
       its decode (Decision 7).
     - **A file field contributes no key at all.** `model_to_dict` yields the stored
       relative path, which is not a re-bindable `data=` value for a field fed from
       `files=`, so file fields are excluded from the reconstruction entirely.
     - **A field whose input shape disagrees with its column binds the form's initial.**
       A `MultipleChoiceField` over a column without choices that is neither an
       `ArrayField` nor a `JSONField` stores the single value its form made of a list, and a
       built-in single-value field over an `ArrayField` the list its form made of one value
       (Decision 7); the field refuses either stored value, except a field that accepts the
       stored list itself (a `CharField` reads its text, a `BooleanField` its truthiness).
       The reconstruction leaves it
       out, and once `get_form` has built the form its omitted value is bound from
       `form.get_initial_for_field`
       (`django_strawberry_framework/forms/resolvers.py::_bind_omitted_shape_disagreeing_initials`):
       the `ModelForm`'s row-derived `initial` after any `__init__` adjustment, so a form
       that presents the stored value in the field's shape in `self.initial[<field>]`
       (splitting the text, picking an element of the list) keeps it unchanged, and one
       that does not fails the update under full-form validation or, through a field
       that accepts the stored list itself, writes the value it makes of it. Reading the
       built form rather
       than constructing another honors `get_form` / `get_form_kwargs` overrides and adds no
       query. The initial is bound under `form.add_prefix(<field>)`, and in parts under the
       keys a multi-key widget reads, into a replacement of the bound data
       (`django_strawberry_framework/forms/resolvers.py::_bind_form_values`): a
       `MultiValueDict` (a `QueryDict`, immutable or not) is copied and the
       initial set with `setlist`, any other mapping merged into a `dict`; an initial longer
       than a `SplitArrayWidget`'s `size` is the field's `max_length` error.

     This yields true partial
     semantics — omitted scalars,
     FKs, M2Ms, and files are preserved; provided fields update — **and** the form
     validates the full merged set, so `unique_item_per_category` validates correctly
     when only `name` changes (the unchanged `category` comes from the instance). It
     matches the `036` model-driven `PartialInput` contract (consistent partial-update
     UX across both mutation flavors), not graphene-django's full-update form.
     - **Required extra (non-model) form fields.** The reconstruction only supplies
       **model-backed** fields, so a `ModelForm`'s extra declared field with no model
       column (a `confirm`, a captcha, an action flag) has **no instance value to
       reconstruct**. The pinned rule: in the `<FormClass>PartialInput`, model-backed
       fields are forced optional (reconstructed), but a **non-model form field keeps
       its declared `field.required`** ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)).
       So a **required** extra field stays required on update (the caller must supply
       it — it is in `provided_data`, never silently `None`), while an **optional**
       extra field may be omitted (and the bound form applies its own `initial` /
       empty value). This avoids both failure modes — an all-optional
       input that lets a caller omit a required extra field (then the bound form fails
       required validation confusingly) and a meaningless reconstructed `initial`.
   Then `form.is_valid()`. A failure maps `form.errors` onto the
   [`FieldError` envelope][glossary-fielderror-envelope] by **reusing the `036`
   mapper directly, not a parallel one**: `form.errors.as_data()` yields the
   `{field: [ValidationError, …]}` shape that
   [`utils/errors.py`][utils-errors]`::validation_error_to_field_errors`
   already consumes through its `error_dict` branch, so the form pipeline calls
   `validation_error_to_field_errors(ValidationError(form.errors.as_data()), key_map)`
   — the form's `NON_FIELD_ERRORS` bucket lands on the `"__all__"` sentinel
   (`NON_FIELD_ERROR_KEY`) for free, exactly as a model `full_clean()` failure does,
   and each form field name is re-keyed to the GraphQL input field the client sent
   (`category` → `categoryId`) through the key map
   `django_strawberry_framework/utils/errors.py::build_error_key_map` builds over the
   bind-stashed specs (a form spec's `target_name` is the form field name;
   `django_strawberry_framework/forms/resolvers.py::_form_errors_to_field_errors`). A
   form field the input does not expose (a `Meta.fields` narrowing) keeps its form field
   name. This is graphene-django's `ErrorType.from_errors(form.errors)` outcome (the
   error names the input the client sent), reached through a map rather than its
   `CAMELCASE_ERRORS` casing, because an input name here is not always the camel-cased
   form field name. Returns a null-object payload.
5. **Write**: for a `ModelForm`, an update, and a create whose row Django would write
   UPDATE-then-INSERT (a client-assigned key,
   `django_strawberry_framework/mutations/resolvers.py::adds_by_update_first`), split
   the save the way Django's admin does: the form's `save()` is called with
   `commit=False`, the package saves the row it returned and calls `form.save_m2m()`,
   so work a `ModelForm.save()` override does only when committing does not run there
   (an override that saves the instance itself under `commit=False` makes a plain
   `save()`). A create saves it as an INSERT through
   `django_strawberry_framework/mutations/resolvers.py::save_new_row`, whose
   `force_insert` the model's `save()` receives, per Django's override contract of
   passing keyword arguments through: a row committed under that key between
   `is_valid()` and the save is the `IntegrityError` envelope below, never
   overwritten. An update saves it as an UPDATE through
   `django_strawberry_framework/mutations/resolvers.py::save_located_row` (the model's
   `save()` receives `force_update`, plus `update_fields` naming every loaded column
   when the row spans multi-table parents, and passes them through by the same
   contract), run inside
   `django_strawberry_framework/mutations/resolvers.py::forced_save_or_field_errors`:
   a located row a concurrent transaction deleted after the locate is the `conflict`
   envelope on `id`, never re-inserted. Every other create is one `form.save()`
   (commit=True; M2M written via the internal `save_m2m()`). For a plain `Form`,
   `perform_mutate(self, form, info)` runs the form's side effect per the pinned
   plain-form contract
   ([Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)):
   the default calls `form.save()` when present, else is a no-op, and a consumer
   overrides it for a custom action. **The save is wrapped by the `036` save-time
   `IntegrityError` → `FieldError` mapper, not left to bubble.** A `form.is_valid()`
   pass can still lose a concurrent-uniqueness race or hit a residual DB constraint at
   `save()`; the write runs through the shipped
   [`mutations/resolvers.py`][mutations-resolvers]`::save_or_field_errors`, so that
   `IntegrityError` class returns the **same
   null-object + `FieldError` envelope** the model-driven path returns (the same
   message policy / `"__all__"` keying), **never** a top-level `GraphQLError` / 500 —
   preserving the cross-flavor envelope contract at write time as well as validation
   time. This wraps **both** the `ModelForm` save and the plain-form
   `perform_mutate` default save path (a `ModelForm` update through its update-side
   counterpart `forced_save_or_field_errors`, the same mappings plus `conflict`).
   Runs inside the one `transaction.atomic()` boundary (the `IntegrityError` is caught at the resolver, so the atomic block is
   exited cleanly with the envelope as the result). **A save-time Django
   `ValidationError` maps the same way.** A `ValidationError` raised by consumer
   save-time code (a `ModelForm.save()` / `Model.save()` override, a `pre_save` /
   `post_save` / `m2m_changed` receiver, a plain-form `perform_mutate`) returns the
   null-object / `{ ok: false }` envelope through the same `save_or_field_errors`
   (`forced_save_or_field_errors` on a `ModelForm` update),
   keyed to the GraphQL input names: by form field name on the plain form
   (`build_error_key_map`), by every name Django keys the backing model field by on the
   `ModelForm` (`django_strawberry_framework/utils/errors.py::save_time_error_key_map`,
   shared with the serializer flavor). The envelope rolls back whatever the save wrote
   before it raised; any other exception (a `ValueError` included) propagates. **Before
   the save, the `ModelForm` refuses an explicit `null` its form field coerced to a
   storable value** ([`forms/resolvers.py`][forms-resolvers]`::_coerced_null_fields`):
   for a form-declared, non-`disabled`, editable non-pk `null=False` column that
   `construct_instance` writes (its `Meta.fields` / `Meta.exclude` keep it) and whose
   bound `form.data` (what `get_form` bound, after any override, read under
   `form.add_prefix(<field>)`) holds `None` (an explicit
   `null`: an update reconstructs an omitted field from a row that stores no `NULL` in
   it), a cleaned value equal to the form field's own cleaning of that `None`, on the
   instance as neither `None` nor a `""` the column cannot store, means the save would
   succeed with a value the client never sent: `CheckboxInput` reads `None` as `False` on
   a `BooleanField`, and the `CharField` / `TypedChoiceField` of a text or
   text-choice column cleans it to `""` (a consumer `CharField` over a `JSONField` or an
   `HStoreField` column does too: both store `""`, the JSON string and the empty hstore,
   so neither is the `""` the save-time diagnosis names). That column is the field-keyed error with the
   field, code `null` and path the model flavor answers the same input with, and the
   column's Django `error_messages["null"]` as the message, and nothing is written. A
   cleaned value the consumer form supplies instead (a `clean_<field>` / `clean()`
   default) is written, as is a `disabled` field's initial. A `null=True` column stores
   the clear, an M2M empty value clears the relation, a file is bound through `files=`
   (an explicit `null` on an update is the clear sentinel `False`), and a form-required field fails
   `is_valid()` with its own `required` error first, so none of them is checked. **Before
   the save, the `ModelForm` also refuses a temporal or duration value the database cannot store**
   ([`forms/resolvers.py`][forms-resolvers]`::_unstorable_temporal_errors`): Django's
   `DateTimeField` / `TimeField` form fields range-check nothing past what Python parses,
   so every concrete column the cleaned data names is read from `form.instance` (the value
   the save writes; a date an `ArrayField` of datetimes still holds after
   `Model.clean_fields` is read as the midnight Django stores for it) and held to `django_strawberry_framework/utils/errors.py::unstorable_temporal`
   on the pinned alias, the rule the model flavor's decode applies (on psycopg 3 an
   `ArrayField` list is also asked of the driver as a whole, which dumps every element with
   one dumper and so can refuse a naive time beside an aware one; a `DurationField` past 64
   bits of microseconds on SQLite or MySQL, which bind it as that integer, is refused by
   the same rule, Django's own save-time preparation on that alias); a refused column is the
   form field's `invalid` error `"Enter a value the database can represent."` and nothing
   is written. **The
   `ModelForm` save also maps the one other failure a valid `ModelForm` reaches on its own**
   ([`forms/resolvers.py`][forms-resolvers]`::_modelform_save_or_field_errors`): over
   a `blank=True, null=False` column the form field is optional, so an explicit `null`
   (or an omission with no column default) cleans to an empty value and
   `Model.clean_fields` skips it; over a `blank=False, null=False` column a consumer form
   may declare the field `required=False`, and Django's
   `BaseModelForm._get_validation_exclusions` then leaves the column out of `full_clean`
   when it cleans to an empty value, so no model validation reads it either. Most form fields (`ModelChoiceField`, `IntegerField`,
   `DateField`, ...) clean it to `None`, which the database refuses with a `NOT NULL`
   `IntegrityError`; on a non-text choice column Django's form field keeps
   `TypedChoiceField(empty_value="")`, a `ChoiceField`, `TypedChoiceField` or `CharField`
   a consumer form declares over a non-text column cleans to `""` too, and `save()`
   refuses that `""` with a
   `ValueError` (e.g. an integer / float `get_prep_value`) or `ValidationError` (e.g. a
   decimal / date / UUID / boolean `to_python`); an optional single-value form field over an
   `ArrayField` (a `ChoiceField`, `TypedChoiceField` or `CharField` whose `clean_<field>`, if
   any, wraps only a non-empty value) cleans to its `empty_value` `""` too, which PostgreSQL
   refuses at the save with a `DataError` (malformed array literal). After that failed save, a form-declared
   editable non-pk column holding `None` on a `null=False` column, or `""` on a column
   that stores no empty string, that the refused save of the form's instance writes (no
   `update_fields`, or the column named there by field name or `attname`, as recorded at
   `pre_save` by `django_strawberry_framework/utils/write_values.py::attempted_saves`), is reported
   (`django_strawberry_framework/forms/resolvers.py::_unstorable_cleaned_fields`) as the
   field-keyed error with the same field, code `null` and path the model flavor answers
   the same input with (an explicit `null` on a non-nullable column or foreign key at
   decode, an omitted one after its failed INSERT, through the same column walk,
   `django_strawberry_framework/utils/write_values.py::unstorable_columns`), and the column's
   Django `error_messages["null"]` as the message, the model flavor's message too
   (`django_strawberry_framework/utils/errors.py::null_field_error`), so a custom or
   translated message is sent as is. The check reads only the in-memory instance, so no query runs on a
   connection the `IntegrityError` / `DataError` left unusable. When no column explains the
   exception (a model `save()` narrowed by `update_fields` away from the column, one
   that raised before saving the instance, or one writing the row through a path that sends
   no `pre_save`, `bulk_create` or `QuerySet.update()`, included), an `IntegrityError` is the `"__all__"` envelope above, a `ValueError` or
   `DataError` propagates unchanged and a `ValidationError` is the consumer's own, mapped as above. The check runs on the instance after the
   save attempt, never before it, so a model `save()` that fills the blank value in
   (the reason Django keeps the shape) still writes. The returned envelope rolls the
   atomic block back exactly as the `IntegrityError` envelope does.
6. **Re-fetch** (`ModelForm`): re-read the saved row by pk and optimizer-plan it for
   the response selection through the `036` `refetch_optimized`
   ([Decision 9](#decision-9--optimizer-composition-the-modelform-payload-re-fetch-rides-the-spec-036-g2-path)).
7. **Return** the `<Name>Payload` (the saved object in the uniform slot + empty
   `errors` on success; null object + populated `errors` on failure).

**Helper reuse — share, do not re-implement.** Steps 1 / 2 / 4 / 6 / 7 are not
form-local code. The seven-step sequence above is a **shared pipeline runner the form
flavor parameterizes**, not a form-local body calling helpers one by one:
[`forms/resolvers.py`][forms-resolvers] imports `make_resolver_entries` and
`run_write_pipeline_sync` from [`mutations/resolvers.py`][mutations-resolvers] and
`pipeline_write_phase` from
[`utils/write_transaction.py`][utils-write-transaction], and supplies only the
form-specific decode and write steps; the orchestration, the transaction boundary and
the authorize-before-decode ordering are owned once, in the runner. The pipeline
helpers the runner composes are public, and live in three modules:

- [`mutations/resolvers.py`][mutations-resolvers] — `locate_instance` (the
  visibility-scoped `update` locate, a security contract), `coerce_lookup_id` /
  `not_found_error` (the server-side `id` decode + not-found shape),
  `authorize_or_raise` (the write-auth gate), `refetch_optimized`
  ([Decision 9](#decision-9--optimizer-composition-the-modelform-payload-re-fetch-rides-the-spec-036-g2-path)),
  `build_payload` (the uniform-slot envelope), and `save_or_field_errors` (the
  save-time `IntegrityError` / Django `ValidationError` → `FieldError` mapper reused
  per step 5, wrapping a zero-arg save callable and a lazily built error key map; the
  `ModelForm` flavor calls it through
  `_modelform_save_or_field_errors`, which adds step 5's unstorable
  `null=False` column mapping), and `forced_save_or_field_errors` (its update-side counterpart, adding the
  disappearing-row `conflict` envelope, which the `ModelForm` update hands its
  `commit=False` split).
- [`utils/errors.py`][utils-errors] — `validation_error_to_field_errors` and
  `build_error_key_map` (the validation-error mapper and its input-name key map, reused
  per step 4), and `save_time_error_key_map` (the `ModelForm`'s step-5 key map).
- [`utils/write_values.py`][utils-write-values] — `raw_choice_value` (the choice-enum
  unwrap) alongside the relation-decode spine of step 3.

`payload_object_slot`, the uniform-slot accessor `build_payload` writes through, lives
in [`mutations/inputs.py`][mutations-inputs]. The form flavor reaches none of this by
re-implementation and none of it through another module's privates.

**How this pipeline fires.** `DjangoMutationField._resolve` calls the overridable
`resolve_sync` / `resolve_async` classmethods on the
mutation class ([Decision 5](#decision-5--public-surface-djangoformmutation--djangomodelformmutation-exported-from-the-root)), and the model
base is what delegates to [`mutations/resolvers.py`][mutations-resolvers]. Both form
flavors' pair comes from one shared factory,
[`write_mixins.py`][write-mixins]`::resolver_seams`, invoked with `with_id=False`
for the plain flavor — matching the `id`-gate
[`mutations/fields.py`][mutations-fields] applies on its #"operation != \"form\"" test,
so a model-less mutation is never given an `id:`
argument. `bind_form_mutations()` is likewise one call to the shared
`bind_write_declarations`, and the operation vocabulary the sentences above spell out
(`NON_DELETE_WRITE_OPERATIONS`, `NON_DELETE_OPERATION_INPUT_KIND`,
`non_delete_operation_error`) is owned by
[`mutations/operations.py`][mutations-operations] so no flavor re-spells it. A
`ModelForm`'s
[`form.save()`][upstream-forms-mutation] with `commit=True` writes its M2M rows
(`save_m2m()` runs inside `save()`), so a create is a single `form.save()` inside the
one `transaction.atomic()` with no separate M2M step, except the client-assigned-key
create; that create and every update use the admin-style split, which calls
`form.save_m2m()` itself inside the same block (an update inside its forced update's
savepoint).

The async path runs the whole sync body in one
`sync_to_async(thread_sensitive=True)` call, and a sync pipeline meeting an
`async def` [`get_queryset`][glossary-get_queryset-visibility-hook] raises
[`SyncMisuseError`][glossary-syncmisuseerror] — both inherited from the `036`
boundary discipline.

**The runner's boundary is more than the one `transaction.atomic()`**, and a form
mutation inherits every part of it: `check_deadline(info)` runs **before** the
pipeline's own transaction opens, so an operation already past its budget never starts a write; the
transaction is opened and pinned to one write alias
(`open_write_pipeline` / `pipeline_alias_guard` / `check_instance_write_alias`), so a
step cannot silently write through a second connection; and an immutable
`authorized_pk` snapshot is captured right after the locate, so a
later step cannot retarget the write to a row the caller was not authorized for. A
step returning a `StepFailure` (its `errors: list[FieldError]`) marks the block for rollback, so a partial write
followed by a validation failure never commits; on an update whose located row the
skeleton's probe (`django_strawberry_framework/utils/write_transaction.py::located_row_vanished`)
then finds gone, that envelope is `conflict` on `id` in place of the step's errors.

Rationale companion: [Decision 8][rationale-d8].

### Decision 9 — Optimizer composition: the `ModelForm` payload re-fetch rides the `spec-036` G2 path

The `ModelForm` payload's object (pipeline step 6) is re-fetched by pk and routed
through the **same** `036` `refetch_optimized` /
[`DjangoOptimizerExtension`][glossary-djangooptimizerextension] path the model-driven
mutation uses. Because the operation is a mutation, the [`spec-035`][spec-035] **G2**
gate keeps `select_related` / `prefetch_related` and introduces no
[`.only(...)`][glossary-only-projection] on a queryset that carries none (a projection
the target type's default manager carries is widened to the selection) — so the
re-fetched instance carries no deferred-field set of the optimizer's making. The re-fetch is **by pk without the visibility
filter** (the `036` re-fetch exception: the actor just wrote the row, so round-tripping
their own write is not an existence leak).

Rationale companion: [Decision 9][rationale-d9].

### Decision 10 — Operations: `create` / `update` for the `ModelForm`, no form `delete`

`DjangoModelFormMutation` reuses `Meta.operation` ∈ `{"create", "update"}` (the
`036` selector). A form `delete` is **not** shipped: graphene-django's form mutations
are create / update only, a `ModelForm` does not delete a row, and the model-driven
[`DjangoMutation`][glossary-djangomutation] (`Meta.operation = "delete"`) already
covers deletion. The plain `DjangoFormMutation` has no model operation — its action
is the form's `perform_mutate`, so it does not declare `Meta.operation`, and its
`_validate_meta` **rejects** any `Meta.operation` (create / update / delete alike) as
unsupported rather than silently accepting a meaningless value; its input-shape
identity uses the fixed `"form"` sentinel for the operation component
([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)).
The split is per base and total: `DjangoModelFormMutation` validates
`operation ∈ {"create", "update"}`; the plain `DjangoFormMutation` rejects `operation`
outright. No shared rule spans both.

Rationale companion: [Decision 10][rationale-d10].

### Decision 11 — Write authorization: reuse the `036` seam (`DjangoModelPermission` for the `ModelForm`, explicit classes for the plain form)

The `ModelForm` flavor inherits [`DjangoModelPermission`][glossary-djangomodelpermission]
unchanged: because `has_permission` checks the model the class resolved through the
`_resolve_model` override
([Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling))
at declaration, the `add` / `change` model-permission default works for free — an
anonymous or under-privileged caller is denied before the form runs. The visibility-scoped
`update` locate (Decision 8 step 1) and the write-auth check are the same separate
layers `036` set ("can view" ≠ "can write").

The **plain `Form`** has no model, so the model-permission default cannot apply, and
the posture is **deny by default**: an *unset* `Meta.permission_classes` on a plain
form resolves to `(DenyAll,)`
([`forms/sets.py`][forms-sets]`::DjangoFormMutation._validate_meta`), so a real gate is the
consumer's explicit `Meta.permission_classes` and a **public** plain-form write is an
explicit opt-in (`Meta.permission_classes = []`, the `036` AllowAny opt-out). An unset
key is never a configuration error.

The plain base additionally **rejects a `DjangoModelPermission` that does not override
`has_permission`** (the class itself or a subclass inheriting its hook) in
`Meta.permission_classes` at class creation. That hook checks the model the mutation
validated at declaration and maps the operation to an `add` / `change` / `delete`
codename; a model-less `DjangoFormMutation` supplies neither (its validated snapshot
carries no model, and its operation is the `"form"` sentinel), so it would surface only
as a raw error at request time, never a deny. The reject is the shared
`model_less=True` guard of
[`write_mixins.py`][write-mixins]`::_validate_permission_classes` (the model-less auth
fields pass it too); its message names the site, the class, and the remedies (override
`has_permission`, omit `permission_classes` for the deny-by-default, or set `[]` to allow
any). A subclass that overrides `has_permission` decides without the model and is
admitted; an override that calls `super().has_permission(...)` is not guarded and still
raises per request.

Rationale companion: [Decision 11][rationale-d11].

### Decision 12 — Live coverage: products grows a `ModelForm` and a plain `Form` mutation

The products app carries the primary live form surface:
`examples/fakeshop/apps/products/forms.py` declares `ItemModelForm` (`forms.ModelForm`
over `Item`, with a `clean_name` for field-level coverage and the model's
`unique_item_per_category` constraint for the `"__all__"`-sentinel coverage) and the
plain `ContactForm`, and `products/schema.py` exposes them via
[`DjangoMutationField`][glossary-djangomutationfield].
[`test_products_api.py`][test-products-api] (seeded via `seed_data` /
`create_users`) pins the create / update happy paths, the `form.errors` envelope
(field-level and `"__all__"`), write authorization, and the visibility-scoped
`update`. Products is the home because it carries the `Item` constraint and the `036`
`Mutation` wiring.

**The live form surface spans several example apps**, and each earns its place:

- **`products`** — nineteen form mutations: `createItemViaForm`, `updateItemViaForm`,
  `createItemWithFileViaForm`, `updateItemWithFileViaForm`,
  `createDefaultCategoryItemViaForm`, `createStampedItemViaForm`,
  `createItemHoldViaForm`, `submitContact`, `submitPing`, the prefixed-form pairs
  `createItemViaPrefixedForm` / `updateItemViaPrefixedForm`,
  `createItemViaKwargsPrefixedForm` / `updateItemViaKwargsPrefixedForm`,
  `createItemViaCopiedKwargsPrefixedForm` / `updateItemViaCopiedKwargsPrefixedForm` and
  `createItemViaRekeyedPrefixedForm` / `updateItemViaRekeyedPrefixedForm`, and
  `updateItemWithRequiredFileViaPrefixedForm` /
  `updateItemWithRequiredFileViaRekeyedPrefixedForm`, over `ItemModelForm` (with a
  `clean_<field>`), `ItemFileModelForm`, `DefaultCategoryItemModelForm` (the write-time
  `IntegrityError` case), `StampedItemModelForm` (kwarg-requiring, the
  `get_form_kwargs` case), `ItemHoldModelForm` (the explicit-`null` `blank=True,
  null=False` foreign key), `ItemFlagsModelForm` / `PrefixedItemFlagsModelForm` and
  `PrefixedRequiredFileItemModelForm` (a form prefix from the class, from
  `get_form_kwargs`, or from a re-keying `get_form`), `ContactForm` and `PingForm` (the
  `DenyAll` default).
- **`library`** — `CreateShelfViaForm`, `UpdateShelfViaForm`, `UpdateBookViaForm`,
  `UpdateBookAtRepairDeskViaForm`, `UpdatePatronProfileViaForm`,
  `UpdatePatronProfileByGenreNameViaForm`, `CreateBranchWithShelf` and `CreateBranchPair` over
  `ShelfRelationsForm` / `BookGenresModelForm` / `BookRepairDeskForm` /
  `PatronProfileGenreForm` / `PatronProfileGenreNameForm` / `BranchWithShelfForm` /
  `BranchPairForm`. Library carries the cases products cannot:
  the **non-Relay raw-pk** relation decode, the `to_field_name` conversion, the
  request-scoped-`queryset` idiom, the plain-form `perform_mutate` rollback, and the
  write-time blank integer choice column (`Shelf.tier`), and the narrowed form choice field
  (`UpdateBookAtRepairDeskViaForm` over `BookRepairDeskForm`, whose `circulation_status`
  admits two of the column's three values), and a declared pk-keyed `ModelChoiceField`
  over the `to_field` key `PatronProfile.favorite_genre` (`UpdatePatronProfileViaForm`) beside
  the generated name-keyed one (`UpdatePatronProfileByGenreNameViaForm`).
- **`scalars`** — `CreateMediaSpecimenImageViaForm`, the image-column flavor of the
  `Upload` routing.

The `kanban` docs-as-data app also writes through plain `DjangoFormMutation`
subclasses (its board-service mutations), outside this flavor's acceptance matrix.

Rationale companion: [Decision 12][rationale-d12].

### Decision 13 — Finalization seam: reuse the mutation phase-2.5 bind, no `DEFERRED_META_KEYS` change

**`DjangoModelFormMutation` binds through the [`bind_mutations`][mutations-sets]
pass** (it is a [`DjangoMutation`][glossary-djangomutation] subclass, so its metaclass
calls `register_mutation` and the bind resolves its primary
[`DjangoType`][glossary-djangotype] and materializes its `<Name>Payload`). The bind's
input-materialization step (`_materialize_input_for`) routes through the overridable
`build_input(meta, primary_type)` hook
([Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)),
so the form flavor materializes the **form-derived** input under its form-derived name
in the `forms` input namespace, before `strawberry.Schema(...)`, exactly as the `036`
and set-family inputs materialize (the lifecycle discipline is shared; the
*generator* differs). The payload (`build_payload_type`), primary-type resolution, and
the `registry.clear()` co-clear apply as for the model flavor.

**The plain `DjangoFormMutation` is model-less and not a
[`DjangoMutation`][glossary-djangomutation] subclass**, so `bind_mutations` never sees
it. It has its **own** machinery: a `forms/sets.py` declaration registry
(`register_form_mutation` / `iter_form_mutations` / `clear_form_mutation_registry`)
and a `bind_form_mutations()` entry point — one call to the shared
`bind_write_declarations` — that materializes each plain form's model-less input +
payload. **`registry.clear()` clears THREE form rows**, and it names none of them:
each owner **announces its own clear** via `register_subsystem_clear(...)` under a
stable owner key, and `registry.clear()` drains `iter_subsystem_clears()`. That keeps
[`registry.py`][registry] free of any per-subsystem import, and makes a reload replace
an owner's callback rather than duplicate it. The three rows are
`clear_form_input_namespace` (owner `forms.input_namespace`, registered
`before_bind=True` — the generated input/payload-globals ledger),
`clear_form_mutation_registry` (owner `forms.declarations` — the plain-form
declaration registry above), and `clear_form_shape_build_cache` (owner
`forms.shape_cache` — the form-input build cache, the twin of the model-flavor
shape cache, so two mutations over one form-shape dedupe to one materialized input
instead of tripping the materialize collision; the bind clears it at start as well,
so a stale class from a failed / re-run finalize cannot leak). `bind_form_mutations()`
is **wired into [`types/finalizer.py`][types-finalizer]'s phase-2.5 window** alongside
`bind_mutations()` and the set-family binds — no new public finalize entry point; it
hangs off the single [`finalize_django_types()`][glossary-finalize_django_types] call.

**The two ledgers stay separate; the registry *mechanics* are shared.** The
`DjangoMutation` registry and the plain-form registry are two independent ledgers —
different declaration namespaces with different `bind_*` bodies and different
`registry.clear()` rows, so merging the *storage* would be over-DRY. The mechanics
(identity-dedup append, post-`mark_finalized()` reject, `.clear()`, ordered `tuple(...)`
snapshot) are single-sourced in
[`write_mixins.py`][write-mixins]`::make_declaration_registry`, which both
`mutations/sets.py` and `forms/sets.py` instantiate over a fresh private store.

**No change to [`DEFERRED_META_KEYS`][types-base] / `ALLOWED_META_KEYS`**: a
form-mutation `Meta` is its own validation namespace
([Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)),
not a [`DjangoType`][glossary-djangotype] `Meta` key — honoring the
[Cross-subsystem invariants][glossary-cross-subsystem-invariants] rule (promote a
`DjangoType` `Meta` key only when its subsystem applies it end-to-end).

Rationale companion: [Decision 13][rationale-d13].

### Decision 14 — This card owns the `0.0.12` version bump

The form flavor first shipped in the `0.0.12` release. The release is single-sourced
in `__version__` in [`__init__.py`][init]
([`AGENTS.md`][agents] #"The release is single-sourced"); [`pyproject.toml`][pyproject]
derives its packaging metadata from it via `[tool.hatch.version]`.

Rationale companion: [Decision 14][rationale-d14].

## Implementation plan

| Slice | Files | Tests |
| --- | --- | --- |
| 1 — form-field converter + reverse map + the two form-derived inputs | [`forms/converter.py`][forms-converter] (`convert_form_field` fail-loud dispatch + the four `kind` constants, re-exported from [`utils/inputs.py`][utils-inputs]), [`forms/inputs.py`][forms-inputs] (`<FormClass>Input` + `<FormClass>PartialInput` from `base_fields`, the per-field [`utils/inputs.py`][utils-inputs]`::InputFieldSpec` reverse-map record, a choice field's narrowed column enum, shape identity, narrowing + create / partial required guards, `get_form_fields()` basis), [`forms/__init__.py`][forms-init] | [`tests/forms/test_converter.py`][test-forms] + [`tests/forms/test_inputs.py`][test-forms] — every form-field class, id mapping, `Upload`, the reverse-map + `kind` flag, custom-field raise, `base_fields` discovery, the create + partial input shapes, shape-identity collision/dedupe, `Meta.fields`/`exclude` fail-loud + empty-set + required guards |
| 2 — the two base classes + `Meta` validation + bind seams | [`forms/sets.py`][forms-sets] (the form bases, their declaration registry via the shared `make_declaration_registry`), [`mutations/sets.py`][mutations-sets] (the overridable `_validate_meta` / `build_input` / `input_type_name` / `input_module_path` / `resolve_sync` / `resolve_async` seams, model-defaulted), [`mutations/inputs.py`][mutations-inputs] (`build_payload_type` emits the model-less `{ ok errors }` plain-form payload from the same builder + materialize ledger, selected by a `resolve_object_type` returning `None`), [`types/finalizer.py`][types-finalizer] (`bind_form_mutations()` in phase 2.5), the three form clear rows announced via `register_subsystem_clear` and drained by [`registry.py`][registry]'s `iter_subsystem_clears()`, [`__init__.py`][init] (two exports) | [`tests/forms/test_sets.py`][test-forms] + [`tests/mutations/test_sets.py`][test-mutations] — `Meta` matrix incl. `delete`-rejected + `form_class`-accepted, both bind paths, no-primary error, model-flavor seam defaults |
| 3 — form relation decoder + resolver pipeline + field-factory dispatch | [`forms/resolvers.py`][forms-resolvers] (the visibility-on-every-branch form relation decoder, the `kind`-split decode, the partial-update reconstruction, the sync/async entries over `run_write_pipeline_sync`), [`forms/sets.py`][forms-sets] (`resolve_*` seams via `resolver_seams`, `get_form_kwargs` / `get_form` construction hooks on both bases, `perform_mutate` / `check_permission` on the plain base, the `guard_required` waiver, `_input_field_specs` stashed at bind for the decode reverse map), [`mutations/fields.py`][mutations-fields] (duck-typed `_has_mutation_protocol` target check, `resolve_sync` / `resolve_async` dispatch with the `operation != "form"` `id` gate, `data:` lazy-ref via `input_type_name` / `input_module_path`) | [`tests/forms/test_resolvers.py`][test-forms] + [`tests/mutations/test_fields.py`][test-mutations] — create/update, decode `data=`/`files=` split, relation visibility on Relay **and** raw-pk single+multi, `to_field_name`, `IntegrityError` envelope, `get_form_kwargs`/`get_form` hooks, partial-update preservation + required-extra rule, envelope + `"__all__"`, plain-form `ok`+`errors`, visibility locate, write-auth, sync+async, G2 plan-shape, model-flavor dispatch |
| 4 — products live form surface | [`products/forms.py`][products-forms], [`products/schema.py`][products-schema], `Item.attachment` | [`test_products_api.py`][test-products-api] — live create/update via `ModelForm`, `categoryId`-through-form, partial-update preservation, `form.errors` envelope, write-auth, a raw multipart `Upload` test, plain-form success + validation + deny-by-default |
| 5 — docs | [`docs/GLOSSARY.md`][glossary], [`docs/README.md`][docs-readme], [`README.md`][readme], [`GOAL.md`][goal], [`TODAY.md`][today], [`docs/TREE.md`][tree] | — |

## Edge cases and constraints

- **Form-only fields (no model column).** A plain `Form` field with no model column
  (a `confirm_email`, a `captcha`) becomes an input field via the form converter and
  is validated by the form; it never reaches a model write. This is exactly why the
  input derives from the form, not the model
  ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)).
- **`ModelForm` `clean()` / `NON_FIELD_ERRORS`.** A cross-field `clean()` error or a
  model-constraint error (`Item.unique_item_per_category`) surfaces in
  `form.errors[NON_FIELD_ERRORS]`, mapped to the `"__all__"` sentinel `036` defined —
  the same key a model-driven multi-field-constraint `ValidationError` uses, so the
  client contract is identical across flavors.
- **A `get_form` form over another row model.** A `ModelForm` saves the row its
  `instance` holds, so the form `get_form` returns must hold a row of the mutation's model
  or a subclass's (an MTI child, a proxy subclass); a form over another model (a coincident
  pk would otherwise answer success with another row's data), a plain `Form` with no
  instance, an MTI parent's form, and a concrete base's or a sibling proxy's form under a
  proxy-backed mutation are a request-time `ConfigurationError` before `is_valid()`, nothing
  written. A `ModelForm` over another model handed the located row writes the located row's
  table and is admitted. A `save()` that leaves another model's row on `form.instance` is the
  same refusal after the save, its write rolled back with the pipeline transaction
  (`django_strawberry_framework/forms/resolvers.py::_require_backing_row`). The message names
  the instance's class, never the row, whose `__str__` may read a relation an unsaved row
  does not hold.
- **`update` partial-update preservation.** The resolver reconstructs the full
  bound payload from the located row's values over the form's **full declared** field
  set, overlaid by the provided fields, with `files = provided_files`, before
  `form_class(data=, files=, instance=<row located via get_queryset>)` — in **three**
  shapes, so an omitted field binds exactly as a provided one decodes to
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)).
  So a `name`-only update preserves the unprovided scalar (`description`), the FK
  (`category`, as its current pk), the M2M (`genres`, as the current pk list), and any
  file field (omitted → kept via the bound form's `initial`); a provided **non-file**
  optional field the consumer wants emptied is sent explicitly (e.g. `""` for a
  `CharField`). A hidden row is not-found before the form runs.
- **File / image form fields: upload, preserve, clear.**
  `forms.FileField` / `forms.ImageField` map to the
  [`Upload`][glossary-upload-scalar] scalar ([`spec-037`][spec-037]) on input, and the
  resolver routes uploaded values into the form's **`files=`** argument (a bound Django
  form reads files from `files=`, never `data=`), so `form_class(data=…, files=…,
  instance=…)` validates them — proven by a raw `django.test.Client` multipart live
  test (Slice 4). The three file actions are **upload** (provide an `Upload`),
  **preserve** (omit it on partial update → kept via the bound
  `ModelForm(instance=…)`'s `initial`) and **clear** (an explicit `null` on update).
  Django's `FileField` reads `None` as "no change" and `False` as "clear" (the value
  `ClearableFileInput` returns for its checked clear box), so the update binds an
  explicit `null` through `files=` as `False`
  ([`forms/resolvers.py`][forms-resolvers]`::_file_clears`): an optional form field
  cleans it to `False` and the model field's `save_form_data` stores the empty name,
  whether the column is `null=True` or not. A required form field cannot clear
  (`clean(False, initial)` validates it as `None` and returns the stored file), so
  that `null` is the field's own `required` error, the create's answer to it
  (`_required_file_clears`, reading `form.files` under `form.add_prefix(<field>)`), and
  nothing is written. A create has no stored file, so
  its `null` stays `None`.
- **A `ModelForm` whose `Meta.fields` omits an editable column.** The omitted column
  is simply not an input field — the form's contract governs the write surface
  (graphene-django parity), and the model's column default applies on `save()`.
- **A `ChoiceField` over model `choices`.** Resolves to the same generated enum the
  read side uses ([Choice enum generation][glossary-choice-enum-generation]); the
  decode unwraps the enum member to its raw choice value before the form sees it
  (through the shared [`utils/write_values.py`][utils-write-values]`::raw_choice_value`).
  A declared field whose static choices admit fewer of the column's values publishes the
  generated enum of the admitted values ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth));
  one admitting none of the column's non-empty values, or a `MultipleChoiceField` over a
  single-value choice column,
  is a schema-build `ConfigurationError`.
  A partial update validates an omitted narrowed field's stored value against the form's
  choices, as Django's form does: a row holding a value the form does not admit (a
  `checked_out` book through `BookRepairDeskForm`) is refused field-keyed with nothing
  written unless the request sends an admitted value.
- **A `MultipleChoiceField` over a single-value column without choices.** A
  `MultipleChoiceField` (or `TypedMultipleChoiceField`) over `Branch.city`, a `TextField`
  listing no choices, joined in `clean_city`: the input types it `[String!]!` on create and
  `[String!]` on update (the field off-column), and a create's and an update's build each log
  a warning naming the form, the field and the column. An update omitting it binds the form's
  initial (named in the update's warning): kept
  when the form splits the stored value into `self.initial`, refused "Enter a list of
  values." with nothing written otherwise. The initial is bound under the form's prefixed
  name (`form.add_prefix`) and the keys the field's widget reads, and a `QueryDict` a `get_form` override binds is copied and given
  the initial as its list of values, every other field keeping its own. A widget that splits a
  comma string on such a field (e.g. `django_filters.widgets.CSVWidget`) takes a list, not a
  `String`: the field types as a list like the same field off-column. A `JSONField` column
  keeps `JSON`; an `ArrayField` column keeps its list; a relation column keeps its id.
- **A built-in single-value form field over an `ArrayField`.** A `ChoiceField`,
  `TypedChoiceField`, `CharField`, `IntegerField` or `DecimalField` (any of the converter's
  registered scalar form fields) over an `ArrayField` (e.g. "pick one tag", wrapped into a
  one-element list in `clean_tags`) is typed as the same field off-column, a required scalar
  on create and an optional one on update, never the column's list, and a create's and an
  update's build each log a warning naming the list column. A `ChoiceField` over an
  `ArrayField` whose
  `base_field` lists choices takes the element's read enum, or the generated enum of the
  element values its choices admit. A create and an update naming the field store the list
  `clean_<field>` makes; an omitted one binds the form's initial (its `__init__` or
  `get_form_kwargs`): kept when it presents one stored element, otherwise the stored list is
  bound and the update is refused field-keyed with nothing written (`invalid_choice` for a
  choice field, `invalid` for a number field), except through a field that accepts the
  stored list itself (a `CharField` binds its text, a `BooleanField` its truthiness), whose
  value is then written. A value the form accepts and leaves un-wrapped (no `clean_<field>`)
  reaches Django's list validation inside `is_valid()` as a scalar and fails there with
  Django's own exception (`JSONDecodeError`, `TypeError`): a top-level error, masked under
  the error policy; text that is itself a JSON array is read as the list, and an empty
  value over a `null=False` column is that column's `null` error. The default `ModelForm` field
  (`SimpleArrayField`), a `SplitArrayField`, a `MultipleChoiceField`, a `JSONField` and their
  subclasses read the list and keep the column's list type, and a bare `forms.Field` or a
  consumer field no registered class covers keeps the column's type, since nothing states
  it reads one value.
- **A form field whose widget reads several keys.** A `SplitArrayField` over an
  `ArrayField` (required or optional, `remove_trailing_nulls` either way, text or integer
  elements, a nullable-element column, a column default, a prefixed form) writes exactly
  the list sent, created or updated (Django's own `required` rule stands: a required one sent a list with no truthy element, `[0]` included, answers "This field is required."): the list is bound one element per
  `<field>_<index>` key, padded to `size` with `None`, so `[]` is a value (the column
  default fills only a create omitting the field) and an update omitting it keeps the
  stored list. A list longer than `size`, sent or reconstructed from the stored row, is
  the field's `max_length` error with `ArrayMaxLengthValidator`'s message, nothing
  written; a shorter one keeps Django's own semantics (`remove_trailing_nulls` drops the
  padding, otherwise each padded `None` is cleaned by the base field). A
  `SplitDateTimeField` over a `DateTimeField` and a consumer `MultiValueField` over a
  `MultiWidget` write the value sent, split by the widget's `decompress` into its
  `<field>_0` / `<field>_1` keys, and keep the stored value when omitted. An explicit
  `null` is bound whole beside its parts, so the explicit-`null` check answers it as for
  any field. A field whose widget reads one key binds under that key alone. A list a
  `get_form_kwargs` hook binds as a `QueryDict` value list, or under its own prefixed copy
  of the data, is read whole and split the same way; a `disabled` field is bound whole,
  so an omitted update keeps a stored list longer than `size`.
- **A declared field of another kind than its column.** A `ModelChoiceField` over a text
  column would store the `str()` of any row its queryset holds, one the target's
  visibility query hides included, and a file field over a text column reads `files`, so
  it never receives the text the input carries;
  every such pairing, other than a scalar field over a relation column, is a schema-build
  [`ConfigurationError`][glossary-configurationerror], a narrowed-out field included on an
  update ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)).
  A built-in temporal field over a temporal column whose value it cannot read is refused
  the same way: a `DateField` over a `TimeField` column is handed a `time` it cannot parse.
  A field is a file field by its class (`FileField` / `ImageField`) or by its widget's real
  type (a `forms.FileInput`, `ClearableFileInput` included, read without running consumer
  widget code): a custom field rendered with `ClearableFileInput` agrees with a file
  column, and with no column it takes an `Upload`, since its form reads it from `files`,
  which a `String` input never reaches. `needs_multipart_form` is not read: it only asks
  for a multipart form, and a text widget setting it still reads `data` and stays a
  `String`. A custom widget that reads `files` without subclassing `forms.FileInput` reads
  as a scalar field; subclass `forms.FileInput` for it.
- **Relation visibility is not delegated to the form's queryset.** A
  `ModelChoiceField`'s default queryset is `Category.objects.all()` (not
  request-scoped), so the decode type- and visibility-checks the id through the
  related primary `DjangoType.get_queryset` **before** the form sees it; a hidden /
  unseeable target is a field-keyed `FieldError`, identical to the model-mutation
  path. The form's own queryset remains a secondary guard
  ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)).
- **A `ModelForm` placed on the plain `DjangoFormMutation` base.** Rejected at
  class creation with a [`ConfigurationError`][glossary-configurationerror] naming
  `DjangoModelFormMutation`. `forms.ModelForm` is **not** a `forms.Form` subclass (a
  sibling under `forms.BaseForm`), so the plain base checks
  `issubclass(form_class, forms.ModelForm)` **first** to emit the targeted message —
  otherwise a `ModelForm` would silently write with no object slot / no
  `DjangoModelPermission` default / no optimizer re-fetch
  ([Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)).
- **A required extra (non-model) `ModelForm` field on `update`.** It has no
  instance value to reconstruct, so it keeps its `field.required` in the partial
  input (the caller must supply it); an optional extra field may be omitted
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)).
- **A relation field with `to_field_name`.** A `ModelChoiceField` /
  `ModelMultipleChoiceField` whose `to_field_name` (or backing `ForeignKey(to_field=…)`)
  looks the object up by a non-pk field: after the visibility query resolves the
  object, the decoder feeds the form `obj.serializable_value(field.to_field_name)`
  (else `obj.pk`), so a valid GraphQL id does not fail form validation
  ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)).
  A `to_field_name` that is not `pk` or a concrete field of the target unique on its own
  (a lookup path, an annotation, a property, a column two rows may share) is a
  schema-build `ConfigurationError`, on an update even on a field the input leaves out; a
  create never binds such a field and builds. A bound form whose `__init__` or `get_form`
  rebuilt a relation field over another model (a subclass of the target agrees) or another
  key column is a request-time `ConfigurationError` before `is_valid()`, nothing written,
  on a provided relation and on one an update rebinds from the stored key alike. A row whose stored `to_field` key is `NULL` is the relation error,
  whatever the field is keyed by, including a field keyed by the stored column itself;
  a key `""` stays the field's `invalid_choice` error (below). An `update` that omits the field rebinds the located row's related object the same
  way whenever the form's key is not the column the relation stores, including a
  `to_field_name`-less field over a `ForeignKey(to_field=…)`
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)).
  An omitted field whose stored key names no row is that field's `invalid_choice` error
  with nothing written, never a rebind by the stored key or a clear. So is a single
  relation, omitted or provided, whose form-key value the field cleans to empty (a
  `to_field_name` or text key holding `""`), whether or not a row carries it; an M2M
  member keyed `""` is looked up like any member and linked. An M2M list element is never
  a clear: a raw-pk element `""` is decoded through the related type's visibility like
  any id, so a hidden or missing row it names is the relation error, never bound.
- **A form whose `__init__` requires constructor kwargs.** Schema-time discovery
  reads `form_class.base_fields` (no instantiation), and runtime construction goes
  through `get_form_kwargs(info, *, data, files, instance=None)` — the consumer
  overrides it to inject `user` / `request` / tenant, or to pass the request-scoped
  queryset a form narrows a `ModelChoiceField` with in its own `__init__` — the hook
  returns constructor kwargs, so the form applies it — without changing the generated
  input shape
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)).
- **A narrowing that drops a required form field.** Two guards keyed on one waiver
  ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)): a **create**
  narrowing that drops any required form field is rejected at bind with a
  [`ConfigurationError`][glossary-configurationerror] naming the missing field(s) — a
  bound form cannot succeed without it and `initial` is no substitute; an **update**
  narrowing that drops a required **column-less** field is rejected at bind for the
  same reason, since the reconstruction can only supply model-backed fields. Both are
  waived when `get_form_kwargs` / `get_form` is overridden to supply the values.
- **Write-time `IntegrityError`.** A valid `ModelForm` save (or the plain-form
  `perform_mutate` save) that loses a concurrent-uniqueness race or hits a residual DB
  constraint returns the null-object + `FieldError` envelope via the `036`
  `save_or_field_errors` mapper (`forced_save_or_field_errors` on a `ModelForm`
  update) — never a top-level `GraphQLError`
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)).
  On a `ModelForm` update, and a create over a client-assigned key, the form's `save()`
  is called with `commit=False` and the package saves the row it returned and calls
  `save_m2m()`, as Django's admin does, so work an override does only when committing
  does not run there. On the create the model's `save()` receives `force_insert`, and a
  row committed under that key after `is_valid()` is this envelope, never overwritten.
- **Write-time disappearing row.** On a `ModelForm` update the model's `save()`
  receives `force_update` (plus `update_fields` naming every loaded column when the row
  spans multi-table parents), so a located row a concurrent transaction deleted after
  the locate (reachable under `Meta.select_for_update = False` or on a backend without
  `FOR UPDATE`) matches no row on some table and returns the null-object + `conflict`
  `FieldError` envelope on `id` with the transaction rolled back, never a re-inserted
  row reported as updated.
- **Validation-time disappearing row.** A located row removed before the bound form
  validated (deleted, or cascaded away with a row it references) fails the form on data
  rebuilt from a row that no longer exists: an omitted M2M re-read from the database as
  empty (`required`), an omitted relation whose stored key's target vanished with the row
  (`invalid_choice`), a named relation that vanished with it. That failure is the same
  `conflict` envelope on `id`, never `form.errors`: on a step failure over a located row
  the shared skeleton (`django_strawberry_framework/mutations/resolvers.py::run_write_pipeline_sync`)
  probes it (`django_strawberry_framework/utils/write_transaction.py::located_row_vanished`)
  and answers `conflict` when it is gone. A row still present keeps `form.errors`: a
  partial update after the only kept genre was deleted is `genres` `required`, true about
  the row.
- **Write-time unstorable `null=False` column.** A `ModelForm` over a
  `blank=True, null=False` column, or a `blank=False, null=False` column whose form field
  the consumer form declares `required=False`, cleans an explicit `null` (or an omission
  with no column default) to `None` (a foreign key, a plain integer, ...) or, on a choice
  column of any non-text type (e.g. integer, decimal, date) or through an optional
  single-value form field over a non-text column or an `ArrayField`, to `""`, which only
  `save()` or the database (`NOT NULL`, PostgreSQL's malformed array literal) refuses; the
  failure returns the null-object envelope keyed by that column with code `null`,
  nothing written. A consumer `save()` that fills the value in writes; any other
  `ValueError` or `DataError` out of `save()` propagates and any other `IntegrityError` is the
  `"__all__"` envelope, among them a refused save whose `update_fields` leaves the `None`
  column out
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)
  step 5).
- **Explicit `null` coerced to a storable value on a `null=False` column.** A
  `BooleanField`'s `CheckboxInput` reads an explicit `null` as `False`, and a
  `blank=True` text or text-choice column's form field, or a consumer `CharField` over a
  `JSONField` column, cleans it to `""`; each is a value the column stores, so the save
  would succeed. The valid form's instance is
  checked before the save, and such a column returns the null-object envelope keyed by
  it with code `null` and the column's `error_messages["null"]`, nothing written, on
  create and update alike, as the model and serializer flavors answer the same input.
  Only the form field's own cleaning of the `null` is refused: a value a `clean_<field>`
  / `clean()` supplies, a `get_form` / `get_form_kwargs` override binding a value in
  place of the `null`, a `disabled` field, and a declared field `Meta.fields` /
  `Meta.exclude` keeps out of `construct_instance` all write as the form resolves them. A
  `null=True` column, an M2M, a file and a form-required field are never checked
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)
  step 5).
- **A prefixed form.** A form whose prefix comes from its class, a `get_form_kwargs`
  `prefix=`, or a `get_form` passing the package's mapping or a copy of it with a prefix
  reads every value the client sent: each bound `data` / `files` mapping holding bare
  field names and none of the keys the form reads them under is re-keyed under
  `form.add_prefix` (and, in `data`, under a multi-key widget's own keys), and one already
  holding such a key, keyed by a `get_form` override, is left as bound. The explicit-`null` and required-file checks read the bound value under
  the same key, so a prefixed form answers every input as the unprefixed one does
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)
  step 4).
- **Write-time consumer `ValidationError`.** A `ValidationError` raised by consumer
  save-time code (a `ModelForm.save()` / `Model.save()` override, a model signal
  receiver, a plain-form `perform_mutate`) after `is_valid()` passed returns the
  null-object / `{ ok: false }` envelope keyed to the GraphQL input names (a bare
  message or a `NON_FIELD_ERRORS` key to `"__all__"`, a key no input exposes kept as
  raised), with whatever the save wrote rolled back
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)
  step 5).
- **Two distinct generated form inputs colliding on one GraphQL name.** Two
  **different** form classes with the same `__name__` both emit `<__name__>Input` and
  **always** raise a finalize-time [`ConfigurationError`][glossary-configurationerror]
  (distinct `form_class` identities never dedupe — the reused
  `materialize_generated_input_class` ledger raise); only repeats of the **same**
  `(form_class, operation kind, effective set, basis content)` dedupe to one
  materialized class, and
  two different narrowings of one form get distinct shape-derived names
  ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)).
- **Plain-form write authorization.** With no model, the
  [`DjangoModelPermission`][glossary-djangomodelpermission] default cannot apply, so an
  unset `Meta.permission_classes` resolves to `(DenyAll,)` — deny by default, with a
  public write the explicit `Meta.permission_classes = []` opt-in. An entry that is a
  [`DjangoModelPermission`][glossary-djangomodelpermission] that does not override
  `has_permission` is **rejected** at class creation, since that hook resolves its
  codename from a model a model-less mutation never supplies ([Decision 11](#decision-11--write-authorization-reuse-the-036-seam-djangomodelpermission-for-the-modelform-explicit-classes-for-the-plain-form)).
- **No `DjangoType` `Meta` key added.** [`DEFERRED_META_KEYS`][types-base] /
  `ALLOWED_META_KEYS` carry no form key
  ([Decision 13](#decision-13--finalization-seam-reuse-the-mutation-phase-25-bind-no-deferred_meta_keys-change)).

## Test plan

Test placement follows the [`AGENTS.md`][agents] mirror rule; the live surface owns
behavior reachable through `/graphql/`, package tests own internals.

- **Live, over `/graphql/`** (Slice 4, [`test_products_api.py`][test-products-api],
  seeded via `seed_data` / `create_users`): `createItemViaForm` / `updateItemViaForm`
  happy paths; the `form.errors` envelope (a `clean_<field>` error keyed to the form
  field's input name, an explicit `null` `categoryId` the form's own `required` error
  on `categoryId`, the `unique_item_per_category` `clean()` error keyed to `"__all__"`);
  **`categoryId` validates and writes through the `ModelForm`'s `category` field**
  (not via model `setattr` — proving the reverse map); **partial-update
  preservation** — a `name`-only `updateItemViaForm` preserves `description` and
  `category` (FK), and `unique_item_per_category` still fires when only `name` changes
  to a value already taken under the unchanged `category` (the partial-update
  contract); a non-colliding partial update whose reconstruction reads no category (the
  one real `products_category` SELECT is the bound form's choice lookup); write
  authorization (anonymous denied, a
  caller missing the model perm denied, a permitted caller succeeds); the
  visibility-scoped `update` (a caller who cannot see a private `Item` gets
  not-found); **relation visibility** — a permitted writer submitting a **hidden**
  `Category` `GlobalID` as `categoryId` gets the same field-keyed `FieldError` the
  model-driven mutation returns (the `036` relation-visibility invariant, proving the form's
  default `Category.objects.all()` queryset is not the only guard); **a raw
  `django.test.Client` multipart upload** to a form-backed `Upload` field, proving the
  `data=` / `files=` split validates and writes the file (the file-routing
  contract); **a `get_form_kwargs` override injecting `user`** drives a form whose
  `__init__` requires it (the construction-hook migration case); the plain `Form`
  mutation's **success** (`ok: true`, empty `errors`) **and** validation-failure
  (`ok: false`, field-keyed `errors`) shapes, and the deny-by-default plain form
  (`submitPing`, top-level denial). **Narrowed choice field** — `updateBookAtRepairDeskViaForm`
  publishes only the two `circulationStatus` members `BookRepairDeskForm` admits, `repair`
  writes, and `checked_out` is an enum-coercion error with no write; an input omitting
  `circulationStatus` on a stored `checked_out` book is the form's field-keyed
  `invalid_choice` error with no `UPDATE`, and on a stored `available` book it saves. **Omitted
  relation over a `to_field` key** — an `updatePatronProfileViaForm` that omits
  `favoriteGenreId` keeps the stored genre name, including when that name is another
  genre's id; an unset genre stays unset, a genre replaces it and `null` clears it. A
  stored name no genre carries (the genre row deleted under disabled constraint checks)
  is the `favoriteGenreId`-keyed `invalid_choice` error with nothing written, including
  when that name is another genre's id, while a supplied genre or `null` still writes;
  over the pk-keyed `updateItemViaForm` a dangling `category` is the form's own
  `categoryId`-keyed `invalid_choice` error. **A relation keyed `""`** — over the
  name-keyed `updatePatronProfileByGenreNameViaForm`, an omitted stored name `""` (no
  genre carrying it, or a genre named `""`) and a supplied genre named `""` are each the
  `favoriteGenreId`-keyed `invalid_choice` error with nothing written, never a clear,
  the stored name refused without reading the genre table, while an omitted genre keeps
  its name, an unset genre stays unset, and a supplied genre or `null` over a stored
  `""` still writes; over `updateShelfViaForm` / `createShelfViaForm`, whose `branch`
  resolves by name over the pk-stored column, an omitted or supplied branch named `""`
  is the `branchId`-keyed `invalid_choice` error; over `updatePrintingViaForm` a stored
  edition ISBN `""` is the `editionId`-keyed `invalid_choice` error decided without
  reading the edition by its key, while a `boundWith` member keyed `""` stays linked,
  omitted or supplied, and a `boundWith` element `""` naming no edition is the
  `boundWith`-keyed relation error with nothing written. **A `to_field` key that may be
  `NULL`** — `createInterlibraryLoanViaForm` / `updateInterlibraryLoanViaForm`, whose
  declared `lender` resolves a branch by id while `InterlibraryLoan.lender` stores
  `Branch.isil`, link a branch with an ISIL and store it, and answer a branch with no ISIL
  like a hidden or missing one: the `lenderId` relation error with nothing written and the
  prior ISIL kept; `null` clears
  (`test_library_api.py::test_loan_lender_that_names_no_linkable_branch_is_the_relation_error`).
  **A list over a single-value column** — under the default-off
  `FAKESHOP_TEST_BRANCH_CITY_PICKS` flag, `createBranchCityPicksViaForm` /
  `updateBranchCityPicksViaForm` / `updateBranchCityPicksSplitViaForm` write `Branch.city`
  through a `MultipleChoiceField` joined in `clean_city`: the inputs type `city` as a list,
  a create stores the joined picks, a provided list replaces them, and an omitted `city`
  keeps them through the form splitting the stored text into its initial (bound as given, to
  an immutable `QueryDict`, or under the form prefix `p`:
  `updateBranchCityPicksQueryDictViaForm` / `updateBranchCityPicksPrefixedViaForm`) and is refused
  "Enter a list of values." with nothing written through the one that does not, at the
  statements a provided `city` runs
  (`test_library_api.py::test_branch_city_picks_update_binds_an_omitted_city_from_the_form_initial_over_http`).
  **A prefixed form** — over a class-level prefix (`createItemViaPrefixedForm` /
  `updateItemViaPrefixedForm`), a `get_form_kwargs` `prefix=` over the package's data
  (`...KwargsPrefixedForm`) or `dict(data)` copies (`...CopiedKwargsPrefixedForm`) and
  a re-keying `get_form` (`...RekeyedPrefixedForm`), a create stores every value sent, a
  one-field update writes it and keeps the rest, and an explicit `description: null` /
  `isPrivate: null` on create and update is the column-keyed `null` error with nothing
  written; an explicit `attachment: null` on the required file of
  `updateItemWithRequiredFileViaPrefixedForm` / `...RekeyedPrefixedForm` is its `required`
  error with the file kept, and an update omitting it renames the row and keeps the file
  (`test_products_api.py::test_create_item_via_prefixed_form_explicit_null_is_a_field_error`).
  **Write-time `IntegrityError`** — a valid
  `ModelForm.save()` that hits a constraint the form's validation excluded
  (`createDefaultCategoryItemViaForm`) surfaces the **`FieldError` envelope**, not a
  top-level GraphQL error. **Client-assigned key create** — `createPatronProfileViaForm`
  over `PatronProfileGenreForm` creates a free patron's profile with no `UPDATE` of the
  table, a taken patron is the `unique` error on `patronId`, and a profile a competing
  writer saves after `is_valid()` (a `pre_save` receiver inserting it) is the `"__all__"`
  `constraint` envelope with nothing written
  (`examples/fakeshop/test_query/test_library_api.py::test_form_create_patron_profile_names_its_patron_by_the_key_over_http`).
  **Write-time disappearing row** — an `updateBookViaForm` over a full input naming
  `genres` and an `updatePatronProfileViaForm` over the client-assigned `patron` key whose
  located row is deleted after authorization return the `conflict` envelope on `id` with
  no `INSERT` and the stored state rolled back
  (`examples/fakeshop/test_query/test_library_api.py::test_form_update_of_a_row_deleted_after_authorization_is_conflict_over_http`),
  as do `updateItemViaForm` and the multi-table `updateLendingDeskViaForm`, deleted whole
  or only from the desk's own table, whose no-race update names `update_fields`
  (`test_products_api.py`, `test_library_inheritance_api.py`). **Validation-time
  disappearing row** — `updateItemViaForm` / `updateItemWithFileViaForm`
  (`test_products_api.py::test_item_update_whose_category_delete_cascaded_to_the_row_is_conflict_over_http`),
  `updateBookViaForm`, `updatePrintingViaForm`, `updatePatronProfileViaForm` and
  `updateShelfViaForm`
  (`test_library_api.py::test_update_whose_row_vanished_before_validation_failed_is_conflict_over_http`)
  whose located row vanished before the form validated return `conflict` with the probe as
  the last read, rolled back; the row-present control keeps `genres` `required`
  (`test_library_api.py::test_form_partial_update_after_a_kept_genre_was_deleted_keeps_required_over_http`).
  **Write-time consumer `ValidationError`** — `Item.save()`
  refusing `SAVE_REJECTED_ITEM_NAME` on `createItemViaForm` / `updateItemViaForm`
  returns the `name`-keyed envelope with nothing written (the create also over the
  async view), and the kanban `setCardStatus` illegal transition (a `pre_save`
  receiver under `perform_mutate`) returns `{ ok: false }` with one `"__all__"`
  error. **Write-time unstorable `blank=True, null=False` column** — an explicit
  `tier: null` on `createShelfViaForm` (`Shelf.tier` is a `blank=True` integer choice
  column with a default) returns the `tier` / `null` envelope with no row written, while
  a member writes and an omission keeps the default; an omitted or explicit `null`
  `itemId` on `createItemHoldViaForm` (`ItemHold.item` is a `blank=True, null=False`
  foreign key with no default) returns the `itemId` / `null` envelope `createItemHold`
  returns, with no row written (the omission also over the async view).
  **Explicit `null` coerced to a storable value** — `description: null` on
  `createItemViaForm` / `updateItemViaForm` (`Item.description` is a `blank=True,
  null=False` text column) returns the `description` / `null` envelope `createItem` /
  `updateItem` return, with no row written and the stored description unchanged.
- **Package-internal** ([`tests/forms/`][test-forms]):
  - `test_converter.py` — each supported form-field class → annotation +
    required-ness; `ModelChoiceField` / `ModelMultipleChoiceField` id mapping
    (Relay-`GlobalID` vs raw pk); `forms.FileField`, and a field rendered with a
    `forms.FileInput`, → [`Upload`][glossary-upload-scalar];
    **the [`utils/inputs.py`][utils-inputs]`::InputFieldSpec` reverse-map record**
    (`category_id` / `categoryId` → `category` / `relation_single`; a `file`-kind flag for an
    `Upload` field); field discovery from **`form_class.base_fields`** (a form whose
    `__init__` requires kwargs still yields a shape); and **the fail-loud dispatch:
    a bare `forms.Field` → `str`, a known subclass (`EmailField`) maps, but a
    custom `class CustomField(forms.Field)` raises [`ConfigurationError`][glossary-configurationerror]**
    (the catch-all-shadowing regression test); `form_field_kind` classifies by class and
    widget's real type and never raises, a field the converter refuses included, and a
    text widget asking for a multipart form is no file widget.
  - `test_inputs.py` — the **two generated inputs** (`<FormClass>Input` with
    `field.required` requiredness for create; `<FormClass>PartialInput` — model-backed
    fields optional, **a required non-model extra field still required**); fields
    from `form_class.base_fields` (no instantiation; an overridable `get_form_fields()`
    honored), narrowed by `Meta.fields` / `Meta.exclude`; materialization as
    a module global; a form-only (non-model) field included. **Narrowed choice
    fields:** a subset (typed, optional, grouped, declared empty option) publishes the
    admitted values on both inputs, an equal / superset / callable / per-request set keeps
    the read enum, `BLANK` follows `required`, an integer column keeps its `int` values, an
    `ArrayField` narrows its elements, a grouped column binds a narrowed field and refuses
    one admitting every value, and a disjoint field and a `MultipleChoiceField` over a
    single-value choice column are refused, while a `TypedMultipleChoiceField` over a text
    column without choices is typed `list[str]` (optional on update), a
    `MultipleChoiceField` over a `JSONField` keeps `JSON`, and an update build, an
    excluding one included, and a create build binding the field each warn once of the text
    column (the update's naming the initial), a create excluding it or a `JSONField` column
    not at all, and a form serving two creates and an update once per input it builds; a
    `ChoiceField` / `TypedChoiceField` / `CharField` / `IntegerField` /
    `DecimalField` over an `ArrayField` is typed by the field's scalar (optional on update), a
    `ChoiceField` over a `base_field` listing choices by the element enum (narrowed by a
    subset), a `MultipleChoiceField`, a `JSONField`, a bare `forms.Field` and a consumer
    `forms.Field` subclass keep the column's list, and a create build and an update build
    each warn of the list column and a list-reading field not at all (`tests/forms/test_inputs.py`;
    `form_field_reads_list` and `form_field_reads_one_value` in
    `tests/forms/test_converter.py`);
    on the Postgres tier the default `ModelForm` `SimpleArrayField`, a subclass of it and a
    `MultipleChoiceField` over a real `ArrayField` keep `[String!]!` while a `ChoiceField` is
    `String!`, and a built-in single-value field over an `ArrayField` creates, updates and keeps an
    omitted value through the form's initial, refused field-keyed without one
    (`tests/forms/test_resolvers.py::test_single_value_fields_over_array_columns_update`). **Column kind agreement:** a relation field over a
    scalar, file or other-cardinality relation column, a file field over a scalar or
    relation column and a scalar field over a file column are refused on both inputs, a
    narrowed-out field on an update but not on a create, while a scalar field over a
    relation column takes the relation's id input, a custom field with a `FileInput`
    widget builds over a file column, or as an `Upload` with no column, and a text widget
    asking for a multipart form stays a `String`
    (`tests/forms/test_inputs.py::test_field_of_another_kind_than_its_column_is_refused`,
    `::test_update_input_refuses_a_kind_mismatch_on_a_narrowed_out_field`,
    `::test_create_input_admits_a_kind_mismatch_on_a_narrowed_out_field`,
    `::test_scalar_field_over_relation_column_takes_the_relation_id`,
    `::test_field_with_a_file_widget_over_a_file_column_builds`,
    `::test_field_with_a_file_widget_maps_to_upload`,
    `::test_field_with_a_multipart_text_widget_stays_a_string`,
    `::test_field_with_a_multipart_text_widget_over_a_text_column_builds`). **Temporal
    readers:** a built-in temporal field over a temporal column it cannot read, a subclass
    overriding neither `to_python` nor `clean` included, is refused on both inputs, a
    narrowed-out one on an update but not on a create, a `DateTimeField` over a `DateField`
    included, while the column's own form class, `SplitDateTimeField` over a `DateTimeField`,
    a `CharField` and a subclass overriding `to_python` build, and each column's first reader
    is the class its `formfield()` builds
    (`tests/forms/test_inputs.py::test_temporal_field_over_a_temporal_column_it_cannot_read_is_refused`,
    `::test_temporal_refusal_names_the_form_the_column_and_the_remedy`,
    `::test_datetime_over_date_refusal_names_the_zone_shift_and_the_remedy`,
    `::test_update_input_refuses_an_unreadable_temporal_field_on_a_narrowed_out_field`,
    `::test_temporal_field_reading_its_column_builds`,
    `::test_temporal_readers_open_with_the_form_class_django_builds_for_the_column`). **Shape identity:**
    the same form with two different `Meta.fields` narrowings → two **distinct**
    generated names; two repeats of the **same** `(form_class, op, effective set)` →
    **dedupe** (one materialized class); two **different** form classes with the
    **same `__name__`** → a finalize-time [`ConfigurationError`][glossary-configurationerror]
    collision **always** (distinct `form_class` identities never dedupe, even with
    matching field shapes); an **empty effective field set** → `ConfigurationError`.
  - `test_sets.py` — the `Meta` validation matrix (missing `form_class`; a `ModelForm`
    on **`DjangoFormMutation`** rejected naming `DjangoModelFormMutation`; a
    non-`ModelForm` on `DjangoModelFormMutation` rejected; `ModelForm`-with-no-model;
    `DjangoModelFormMutation` `operation = "delete"` rejected; **any `Meta.operation`
    on the plain base rejected**; **a `create` narrowing (`Meta.fields` *or*
    `Meta.exclude`) that drops a required form field → `ConfigurationError` naming the
    missing field(s), waived when `get_form_kwargs` is overridden**;
    **`Meta.fields` bare-string / duplicate-name / unknown-name against
    `form.base_fields`**; `fields` + `exclude` both set; unknown key); **plain-form
    input dedupe via the `"form"` sentinel**; a stateful `get_form_fields` hook narrowing a
    choice field differently per class → the materialize collision (the narrowed values are
    part of the basis content identity); registration; phase-2.5 binding (both
    paths); the no-registered-primary-type error for `DjangoModelFormMutation`; an update
    leaving out a field of another kind than its column fails `finalize_django_types()`,
    and a create leaving it out binds without reading its queryset.
  - `test_resolvers.py` — create / update happy paths; `form.is_valid()` failure →
    envelope (null object), incl. a `NON_FIELD_ERRORS` `clean()` error → `"__all__"`;
    **the decode split** — `categoryId` → `{"category": pk}` in `data=`, an `Upload`
    → `files=` (never `data=`); **relation visibility on EVERY branch** — a hidden
    target → field-keyed `FieldError` before the form, for **both** a Relay-`GlobalID`
    primary AND a **non-Relay raw-pk** primary, and for **both** `ModelChoiceField` and
    `ModelMultipleChoiceField`; **a raw-pk /
    wrong-model relation id** → `FieldError`; **`to_field_name`** — a `ModelChoiceField`
    / `ModelMultipleChoiceField` with `to_field_name` set validates the decoded value
    by the target field, not pk, and a path, annotation, unknown, reverse-relation, M2M
    or non-unique `to_field_name` is refused at build, a narrowed-out field included on an
    update but not on a create, which never binds it, while a column unique alone
    (`unique=True`, a one-field `unique_together`, a total `UniqueConstraint`) is admitted
    (`tests/forms/test_inputs.py::test_require_readable_choice_keys_refuses_a_key_naming_no_one_row`,
    `::test_require_readable_choice_keys_refuses_a_column_unique_only_with_others`,
    `::test_require_readable_choice_keys_admits_a_column_unique_on_its_own`,
    `::test_update_input_refuses_an_unreadable_key_on_a_narrowed_out_field`,
    `::test_create_input_admits_an_unreadable_key_on_a_narrowed_out_field`); a bound
    form whose `__init__` or `get_form` sets, clears or misnames a relation's key, single,
    M2M or omitted from an update, or swaps its queryset to another model, is a
    request-time `ConfigurationError` with nothing written, while a same-model queryset,
    any pk spelling, a name-for-attname respelling and a subclass queryset bind the
    decoded row, and a bound field whose queryset `get_form` clears is left to the form's
    own validation
    (`tests/forms/test_resolvers.py::test_bound_choice_disagreeing_with_the_decode_is_refused_before_validation`,
    `::test_bound_choice_agreeing_with_the_decode_links_the_decoded_row`,
    `::test_queryset_less_bound_choice_is_left_to_the_form`);
    a `get_form` form whose instance is no row of the mutation's model (another model on a
    coincident-pk create and update, a plain `Form`, an MTI parent, a concrete base and a
    sibling proxy under a proxy-backed mutation, an unsaved instance whose `__str__` reads a
    relation) is a request-time `ConfigurationError` with no table written, a `save()` that
    swaps `form.instance` rolls its write back, and an MTI child's form, a proxy subclass's
    form and another model's form handed the located row write
    (`tests/forms/test_resolvers.py::test_create_through_a_form_over_another_model_with_a_coincident_pk_is_refused`,
    `::test_get_form_over_another_row_model_is_refused_before_validation`,
    `::test_save_that_swaps_the_form_instance_rolls_its_write_back`,
    `::test_get_form_whose_instance_is_a_row_of_the_model_writes`);
    a row whose stored key is `NULL` is the relation error, single and multi
    (`tests/forms/test_resolvers.py::test_decode_form_relation_refuses_a_row_whose_stored_key_is_null`);
    **write-time `IntegrityError`** — a valid
    `form.save()` raising `IntegrityError` (and the plain-form `perform_mutate` save
    path) → `FieldError` envelope, not a top-level error (via `save_or_field_errors`;
    `forced_save_or_field_errors` on a `ModelForm` update);
    **write-time consumer `ValidationError`** — a save-time `ValidationError` on the
    `ModelForm` and plain-form paths keys through each flavor's key map (form field
    name, model field name, forward-relation `attname`, `NON_FIELD_ERRORS`, an
    unexposed key kept as raised);
    **write-time unstorable `null=False` column** — an integer choice column
    omitted with no default, decimal and date choice columns sent `null`, an update sent
    `null`, a plain integer column sent `null`, omitted or updated to `null`, and an
    `ItemHold` update sending `itemId: null` each return the column-keyed `null` envelope
    with nothing written, as does a consumer form's optional `TypedChoiceField` or
    `CharField` over a `blank=False` integer column omitted on a create or sent `null` on
    a create and an update, sync and async
    (`tests/forms/test_resolvers.py::test_modelform_optional_field_over_required_column_cleaned_to_empty_string_is_null_error`),
    and, on PostgreSQL, an optional single-value `ChoiceField`,
    `TypedChoiceField` or `CharField` (also one whose `clean_tags` wraps only a non-empty
    value) over a `blank=True` or `blank=False`, `null=False` `ArrayField` sent `""` or `null` on a create, a
    client-assigned-key create and an update, or omitted on either create, sync and async
    (`tests/forms/test_resolvers.py::test_modelform_blank_array_cleaned_to_empty_string_is_field_keyed_null_error`);
    a model `save()` filling the value in (`""` or `None`) writes; a
    consumer `save()` `ValueError`, or a `DataError` PostgreSQL raises for it, with no such
    column propagates; a model `save()` narrowing an update's `update_fields` away from a
    `None` column answers the `"__all__"` `constraint` envelope for the other column it
    refuses
    (`tests/forms/test_resolvers.py::test_modelform_save_time_null_skips_a_column_outside_update_fields`),
    one naming the cleared foreign key by field name or `attname` keeps its `null` error,
    a consumer `ValidationError` raised before the row saves maps as raised, a refused
    save of a sibling row and a failure after the row saved (`save_m2m()`) name no column
    of the form's row (the `"__all__"` envelope), and a retried save is read at its latest
    attempt
    (`tests/forms/test_resolvers.py::test_modelform_save_time_null_is_read_from_the_refused_row_only`,
    `tests/forms/test_resolvers.py::test_modelform_failure_after_the_row_saved_names_no_column`,
    `tests/forms/test_resolvers.py::test_modelform_save_time_null_reads_the_latest_attempt_of_the_row`);
    **explicit `null` coerced to a storable value** — `isPrivate: null` on create and on
    update over a `True` row, a `blank=True` text choice column sent `null` on create
    and update, and a consumer `CharField` over a `blank=True` or `blank=False`
    `JSONField` sent `null` on create and update
    (`tests/forms/test_resolvers.py::test_modelform_optional_char_field_over_json_column_explicit_null_is_null_error`),
    each return the column-keyed `null` envelope with nothing written; a
    form-required `name: null` keeps the form's `required` error, and a `null=True`
    column sent `null` stores `NULL`; an `isPrivate: null` the consumer form resolves (a
    `clean_is_private`, a `get_form_kwargs` override, a `disabled` field, a declared field
    `Meta.fields` / `Meta.exclude` leaves out) writes with empty `errors`
    (`::test_modelform_null_the_consumer_form_resolves_is_written`); a consumer
    `add_prefix` override names the key the package binds and reads
    (`::test_modelform_create_binds_and_reads_through_the_form_add_prefix`), and a
    `get_form_kwargs` binding its own prefixed copy of `data` or of `files` (a plain
    `dict`) keeps it while the package re-keys the other, a bare immutable `QueryDict` and
    `MultiValueDict` are re-keyed into copies, data holding a prefixed key beside a bare
    one is left as bound, a `source` key no field names stays bare for the form's
    `clean()`, and a files `dict` the hook keeps a reference to reads unchanged after the
    write (`::test_update_under_a_prefix_never_mutates_the_bound_files_mapping`)
    (`::test_update_under_a_half_rekeyed_prefix_binds_both_mappings`);
    **a field whose widget reads several keys** (package-only: fakeshop declares no such
    form field and runs on SQLite, which has no `ArrayField`) — on PostgreSQL a
    `SplitArrayField` (text and integer elements, required and optional,
    `remove_trailing_nulls` both ways, a nullable-element column, a column default,
    unprefixed and prefixed) writes the list sent on create and update, `[]` included
    (`::test_modelform_split_array_field_writes_the_list_sent`), keeps the stored list on
    an update omitting it and the column default on a create omitting it
    (`::test_modelform_split_array_field_omitted_keeps_the_stored_list`), refuses a list
    longer than `size`, sent or reconstructed, as `max_length` with nothing written
    (`::test_modelform_split_array_field_longer_than_size_is_refused`), and answers an
    explicit `null` with the column's `null` error
    (`::test_modelform_split_array_field_explicit_null_is_the_column_null_error`), sync
    and async, reads the whole list a `doseq` `QueryDict` or a hook's own prefixed copy
    holds (`::test_modelform_split_array_field_reads_a_hook_bound_mapping`), and a
    `disabled` one keeps a stored list longer than `size`
    (`::test_modelform_disabled_split_array_field_keeps_a_stored_list_past_size`); live, a
    `SplitDateTimeField` over `ScalarSpecimen.occurred_at` writes the datetime sent and
    keeps it when omitted, unprefixed, under the form's prefix and beside a `get_form`'s
    own prefixed copy
    (`examples/fakeshop/test_query/test_scalars_mutation_api.py::test_split_datetime_form_field_writes_the_datetime_sent`);
    a consumer `MultiValueField` over a text column (no fakeshop form declares one) does
    the same unprefixed, prefixed, from a `MultiValueDict` a `get_form_kwargs` binds and
    beside a hook's own prefixed copy
    (`::test_modelform_multi_widget_field_writes_the_compressed_value`); the padding, the
    refusal (also from a `MultiValueDict`, a `doseq` `QueryDict` and a hook's prefixed
    copy), a `disabled` field's stored value and an omitted field's initial bound under a
    split widget's keys run on SQLite through a driver-free `SplitArrayWidget` double
    (`::test_modelform_split_array_widget_binds_each_element_padded_to_size`,
    `::test_modelform_split_array_widget_value_past_size_is_refused`,
    `::test_disabled_split_widget_field_keeps_its_stored_value_past_size`,
    `::test_omitted_initial_binds_under_the_split_widget_keys`), and the key and entry
    walk on its own in `tests/utils/test_widgets.py`;
    **the `get_form_kwargs` / `get_form` hook** — an override injecting `user` and one
    scoping a `ModelChoiceField.queryset` (input shape unchanged); **partial-update
    reconstruction at the unit tier** — omitted scalar / FK / M2M preserved from the
    located instance (an omitted FK reads its related row only when the form's key is
    not the column the relation stores: no query for a pk-keyed field over `Book.shelf`,
    one for a `code`-keyed one), omitted file preserved via the bound form's `initial`, a
    **required extra non-model field omitted → required error** while an optional one
    may be omitted), and `unique_item_per_category` validating on a one-field
    change; the **plain-form `ok` + `errors` payload** and the `perform_mutate(self,
    form, info)` default (calls `form.save()` if present, else no-op) + a consumer
    override; the visibility-scoped `update` locate (hidden row → not-found); write-auth
    denial vs success; sync + async (the async path runs the body in one
    `sync_to_async(thread_sensitive=True)` call); the
    [`SyncMisuseError`][glossary-syncmisuseerror] async-hook-from-sync path; the G2
    re-fetch plan-shape (`select_related` / `prefetch_related` kept, no `.only(...)`
    introduced): `tests/forms/test_resolvers.py::test_modelform_refetch_keeps_select_related_and_introduces_no_projection`.
  - [`tests/mutations/test_fields.py`][test-mutations] — the
    [`DjangoMutationField`][glossary-djangomutationfield] target check accepts a
    `DjangoModelFormMutation` and the plain-form flavor
    ([Decision 5](#decision-5--public-surface-djangoformmutation--djangomodelformmutation-exported-from-the-root)).
- **Cross-cutting.** The full suite is green at the 100% coverage gate
  (`fail_under = 100`); the `036` model-driven mutation surface and the read side keep
  their contracts.

## Doc updates

- **GLOSSARY** ([`docs/GLOSSARY.md`][glossary]):
  [`DjangoFormMutation`][glossary-djangoformmutation] /
  [`DjangoModelFormMutation`][glossary-djangomodelformmutation] carry the shipped
  contract — the `Meta.form_class` surface, the form-derived input, the `form.errors`
  → [`FieldError`][glossary-fielderror-envelope] mapping, the `036` reuse. The
  `DjangoFormMutation` entry states the sibling shape
  ([Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)):
  only `DjangoModelFormMutation` subclasses `DjangoMutation` (returns the post-save
  object in the uniform `node` / `result` slot), while the plain `DjangoFormMutation`
  is a model-less sibling accepted by the generalized mutation-field family, returning
  the pinned `ok: Boolean!` + `errors: [FieldError!]!` payload (no object slot). Both
  symbols are in **Public exports**, the **Index**, and the **Mutations**
  browse-by-category row.
- **Package docs**: [`docs/README.md`][docs-readme] / [`README.md`][readme] list form
  mutations; [`GOAL.md`][goal] criterion 6 names the `ModelForm` flavor;
  [`TODAY.md`][today] notes the products `ModelForm` write surface;
  [`docs/TREE.md`][tree] carries the `forms/` / [`tests/forms/`][test-forms] summary
  lines (rendered from the module docstrings).

## Risks and open questions

Every question the form flavor raised is answered by a Decision above; the
deliberation, including the `Meta.return_field_name` tension, is in the rationale
companion under [Risks and open questions][rationale-risks].

## Out of scope (explicitly tracked elsewhere)

- **DRF serializer mutations** ([`SerializerMutation`][glossary-serializermutation])
  — the sibling flavor in
  [`django_strawberry_framework/rest_framework/`][rest-framework-package]; it reuses the
  same [`FieldError` envelope][glossary-fielderror-envelope] and a serializer-field
  converter, not the form converter.
- **Auth mutations** ([Auth mutations][glossary-auth-mutations]) — the sibling flavor in
  [`django_strawberry_framework/auth/mutations.py`][auth-mutations].
- **The ergonomic `TestClient` / `AsyncTestClient` helper** —
  [`TestClient`][glossary-testclient] in
  [`django_strawberry_framework/testing/`][testing-package]. File-field correctness is
  the form flavor's own: the `forms.FileField` / `forms.ImageField` →
  [`Upload`][glossary-upload-scalar] typing **and** the runtime `data=` / `files=`
  decode split + `form_class(data=, files=, instance=)` construction, proven by a raw
  `django.test.Client` multipart live test (Slice 4,
  [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)).
- **Form `delete`** — not shipped; the model-driven
  [`DjangoMutation`][glossary-djangomutation] (`Meta.operation = "delete"`) covers
  deletion ([Decision 10](#decision-10--operations-create--update-for-the-modelform-no-form-delete)).
- **Field-level read gates** ([`FieldSet`][glossary-fieldset] /
  [Per-field permission hooks][glossary-per-field-permission-hooks]) — composing on top
  of (not replacing) write authorization.
- **A new `DjangoType` `Meta` key or settings key**
  ([Decision 13](#decision-13--finalization-seam-reuse-the-mutation-phase-25-bind-no-deferred_meta_keys-change)).

## Definition of done

The completion contract.

**Spec + companion CSV**

1. `docs/SPECS/spec-038-form_mutations-0_0_12.md` and its companion
   `appx/spec-038-form_mutations-0_0_12-terms.csv` exist;
   `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-038-form_mutations-0_0_12.md`
   reports `OK: <N> terms`.

**Slice 1 — form-field converter + form-derived input**

2. [`forms/converter.py`][forms-converter] ships `convert_form_field` (every
   supported form-field class → its Strawberry annotation + required-ness — including
   `JSONField` → `strawberry.scalars.JSON` on its own row, and the three-case
   `NullBooleanField` requiredness rule single-sited in `form_field_required` — reusing
   the read-side [scalar][glossary-scalar-field-conversion] /
   [choice-enum][glossary-choice-enum-generation] /
   [`Upload`][glossary-upload-scalar] converters where overlapping; a choice field
   admitting fewer of its column's values publishes the generated enum of the values it
   admits, and a field whose input shape disagrees with its column, a `MultipleChoiceField`
   over a single-value column without choices or a built-in single-value field over an
   `ArrayField`,
   is typed as the same field off-column, with a create- and update-build warning) with a
   **fail-loud
   dispatch — no base-`forms.Field` catch-all**: a bare `forms.Field` → `str` (exact
   special case), a known subclass maps via MRO, but a custom `forms.Field` subclass
   hits the **raising** default → [`ConfigurationError`][glossary-configurationerror]
   — plus the four `kind` constants it re-exports from
   [`utils/inputs.py`][utils-inputs] and does not itself define.
   [`forms/inputs.py`][forms-inputs] records, per generated input field, the shared
   [`utils/inputs.py`][utils-inputs]`::InputFieldSpec` the resolver consults at decode
   (`category_id` / `categoryId` → `category` / `relation_single`; an `Upload` field
   flagged `file`), and builds **both** the form-derived `<FormClass>Input`
   (create, `field.required` requiredness) and `<FormClass>PartialInput` (update;
   model-backed fields optional, **a required non-model extra field still required**)
   from **`form_class.base_fields`** (no instantiation — kwarg-requiring forms work;
   overridable `get_form_fields()`), under the `036`-parallel **shape identity**
   `(form_class, operation kind, effective field set, basis content identity)` — the
   operation component is the `DjangoModelFormMutation` verb or the plain `"form"`
   sentinel, and the fourth component is
   `forms/inputs.py::_form_basis_content_identity` (each basis field's dispatch type,
   requiredness, column-less related model and narrowed choice values) — with canonical /
   shape-derived names, dedupe, and a finalize-time **collision
   [`ConfigurationError`][glossary-configurationerror]** for two distinct shapes on one
   name (incl. different forms sharing a `__name__`, which always collide);
   `Meta.fields` / `Meta.exclude` are normalized + fail-loud against
   `form_class.base_fields` (bare string / duplicate / unknown name / empty set →
   `ConfigurationError`), and a narrowing that drops a required form field
   **raises** — any required field on `create`, a required **column-less** field on
   `update` — unless `get_form_kwargs` / `get_form` is overridden; a field the operation
   binds whose kind disagrees with its column's, other than a scalar field over a relation
   column, **raises**; all materialized as module
   globals ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)).

**Slice 2 — the two base classes**

3. [`mutations/sets.py`][mutations-sets] carries the class-creation validation as
   the overridable `DjangoMutation._validate_meta(meta)` beside the
   `build_input` / `input_type_name` / `input_module_path` / `resolve_sync` /
   `resolve_async` seams (each model-defaulted);
   [`forms/sets.py`][forms-sets] ships `DjangoModelFormMutation` (subclasses
   [`DjangoMutation`][glossary-djangomutation], overriding
   [`_resolve_model`][spec-036] → `Meta.form_class._meta.model` plus those seams) and
   `DjangoFormMutation` (the model-less sibling — its own metaclass + declaration
   registry + `bind_form_mutations()` wired into [`types/finalizer.py`][types-finalizer]'s
   phase-2.5 window, with a `registry.clear()` co-clear). The form-flavor
   `_validate_meta` override enforces the matrix (missing `form_class`; **a
   `ModelForm` on the plain `DjangoFormMutation` base rejected naming
   `DjangoModelFormMutation`**, and a non-`ModelForm` on `DjangoModelFormMutation`
   rejected — validated **before** `_resolve_model`; `ModelForm`-with-no-model;
   **`operation` split by base** — `DjangoModelFormMutation` validates `∈ {"create",
   "update"}` (reject `"delete"`), plain `DjangoFormMutation` **rejects any
   `Meta.operation`** and uses the `"form"` shape sentinel; `form_class` a known
   key; mutually exclusive / normalized / fail-loud `fields` / `exclude`;
   unknown key → [`ConfigurationError`][glossary-configurationerror]); the model
   flavor's seam defaults validate + bind its model-column input;
   [`DEFERRED_META_KEYS`][types-base] / `ALLOWED_META_KEYS` carry no form key; both
   symbols export from [`__init__.py`][init]
   ([Decision 5](#decision-5--public-surface-djangoformmutation--djangomodelformmutation-exported-from-the-root)
   / [Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)
   / [Decision 13](#decision-13--finalization-seam-reuse-the-mutation-phase-25-bind-no-deferred_meta_keys-change)).

**Slice 3 — resolver pipeline + field exposure**

4. [`forms/resolvers.py`][forms-resolvers] runs the locate → authorize → decode →
   `is_valid()` → write → re-fetch → payload pipeline (sync + async, one
   `transaction.atomic()` / one `sync_to_async(thread_sensitive=True)`), **authorizing
   before the decode** so an unauthorized caller cannot probe relation visibility.
   Decode produces a **form-field-keyed** `provided_data` over the shared
   `decode_visible_relation` spine: every relation id — `GlobalID`
   *or* **raw pk** — is type-checked, resolved to the **visible** object through the
   related primary `DjangoType.get_queryset` (both branches), and converted by
   `to_field_name`
   (`obj.serializable_value(field.to_field_name)`, or `obj.pk` when the field sets
   none) before landing under the form field name; a hidden target, or a visible one
   whose stored `to_field` key is `NULL`, → field-keyed `FieldError`; a `to_field_name`
   that is not `pk` or a concrete field of the target is a schema-build
   `ConfigurationError` on any field the operation binds (every declared field for an
   update) + a **separate `provided_files`** (uploaded `Upload` values, never in
   `data=`); construction goes through the overridable `get_form_kwargs(info, *, data,
   files, instance=None)` hook — `create` builds `form_class(**get_form_kwargs(…,
   data=provided_data, files=provided_files))`, `update` reconstructs the **full partial
   payload** from the located row over the form's full declared field set, overlaid by
   `provided_data` and in the three shapes a provided field decodes to (an omitted field
   whose input shape disagrees with its column binds the built form's initial), with
   `files = provided_files`, then `form_class(**get_form_kwargs(…, instance=<located
   row>))` — so omitted scalar / FK / M2M / file values are preserved and
   `unique_item_per_category` validates on a one-field change. The built form's data is
   re-keyed under the keys each field's widget reads (`form.add_prefix`, and a
   `MultiWidget`'s or `SplitArrayWidget`'s own keys, a split list padded to `size`), a list
   longer than a `SplitArrayWidget`'s `size` being that field's `max_length` error before
   `is_valid()`. `form.errors` maps
   onto the [`FieldError` envelope][glossary-fielderror-envelope] (each form field keyed
   to its input name, `NON_FIELD_ERRORS` → `"__all__"`, via the reused
   `validation_error_to_field_errors(ValidationError(form.errors.as_data()), key_map)`); **the write is wrapped by the `036` `save_or_field_errors`
   save-time mapper** (`forced_save_or_field_errors` on a `ModelForm` update) (no top-level error on a save-time race or a consumer save-time
   `ValidationError`), and
   a `ModelForm` save refused over a `null=False` column cleaned to a value
   it cannot store (`None`, or `""` on a column that stores no empty string: a non-text choice column, an `ArrayField`) returns that column's
   field-keyed `null` error, as does, before the save, an explicit `null` its own form
   field cleaned to a value such a `null=False` column stores (`False`, `""`);
   the `ModelForm` payload object is re-fetched through the
   `036` optimizer path (G2: `select_related` / `prefetch_related` kept, no
   [`.only(...)`][glossary-only-projection] introduced); the **plain `DjangoFormMutation`
   returns the pinned `ok: Boolean!` + `errors: [FieldError!]!` payload** with
   `perform_mutate(self, form, info)` (default `form.save()`-if-present else no-op);
   [`mutations/fields.py`][mutations-fields]'s
   [`DjangoMutationField`][glossary-djangomutationfield] is generic along three axes
   (target check, `_resolve` dispatch → `mutation_cls.resolve_sync` /
   `resolve_async`, and the `data:` lazy-ref → `mutation_cls.input_type_name` +
   `input_module_path`), so it exposes both flavors through their own pipelines
   ([Decision 5](#decision-5--public-surface-djangoformmutation--djangomodelformmutation-exported-from-the-root)
   / [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)
   / [Decision 9](#decision-9--optimizer-composition-the-modelform-payload-re-fetch-rides-the-spec-036-g2-path)).

**Slice 4 — products live form surface**

5. Products exposes `DjangoModelFormMutation`s (create + update over `Item`) and
   plain `DjangoFormMutation`s, and [`test_products_api.py`][test-products-api]
   (seeded via `seed_data` / `create_users`) proves the create / update happy paths,
   `categoryId` validating through the form's `category` field, **a hidden-`Category`
   `GlobalID` → field-keyed `FieldError`** (the relation-visibility invariant),
   **partial-update preservation** (a `name`-only update preserves
   `category` / `description`, and `unique_item_per_category` fires on a one-field
   change), the `form.errors` envelope (field-level + the `unique_item_per_category`
   `"__all__"` case), write authorization, the visibility-scoped `update`, **a raw
   `django.test.Client` multipart upload to a form-backed `Upload` field** (the
   file-routing contract), **a write-time `IntegrityError` returning the
   `FieldError` envelope**, **a `get_form_kwargs` override injecting `user`** for a
   kwarg-requiring form, and the plain `Form` mutation's **success** (`ok: true`),
   validation-failure and deny-by-default shapes
   ([Decision 12](#decision-12--live-coverage-products-grows-a-modelform-and-a-plain-form-mutation)).

**Cross-cutting**

6. The full suite is green at the 100% coverage gate (`fail_under = 100`); the `036`
   model-driven mutation surface and the read side keep their contracts.

**Slice 5 — docs**

7. [`docs/GLOSSARY.md`][glossary] carries
   [`DjangoFormMutation`][glossary-djangoformmutation] /
   [`DjangoModelFormMutation`][glossary-djangomodelformmutation] as shipped (with
   Public-exports + Index + Mutations-category rows); [`docs/README.md`][docs-readme] /
   [`README.md`][readme] list form mutations; [`GOAL.md`][goal] / [`TODAY.md`][today] /
   [`docs/TREE.md`][tree] reflect the flavor. The two public symbols
   (`DjangoFormMutation`, `DjangoModelFormMutation`) are in `__all__` and the export
   pin.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[contributing]: ../../CONTRIBUTING.md
[goal]: ../../GOAL.md
[kanban]: ../../KANBAN.md
[pyproject]: ../../pyproject.toml
[readme]: ../../README.md
[start]: ../../START.md
[today]: ../../TODAY.md

<!-- docs/ -->
[docs-readme]: ../README.md
[glossary]: ../GLOSSARY.md
[glossary-apply_cascade_permissions]: ../GLOSSARY.md#apply_cascade_permissions
[glossary-auth-mutations]: ../GLOSSARY.md#auth-mutations
[glossary-choice-enum-generation]: ../GLOSSARY.md#choice-enum-generation
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-cross-subsystem-invariants]: ../GLOSSARY.md#cross-subsystem-invariants
[glossary-djangoformmutation]: ../GLOSSARY.md#djangoformmutation
[glossary-djangomodelformmutation]: ../GLOSSARY.md#djangomodelformmutation
[glossary-djangomodelpermission]: ../GLOSSARY.md#djangomodelpermission
[glossary-djangomutation]: ../GLOSSARY.md#djangomutation
[glossary-djangomutationfield]: ../GLOSSARY.md#djangomutationfield
[glossary-djangonodefield]: ../GLOSSARY.md#djangonodefield
[glossary-djangooptimizerextension]: ../GLOSSARY.md#djangooptimizerextension
[glossary-djangoschema]: ../GLOSSARY.md#djangoschema
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-fielderror-envelope]: ../GLOSSARY.md#fielderror-envelope
[glossary-fieldset]: ../GLOSSARY.md#fieldset
[glossary-filterset]: ../GLOSSARY.md#filterset
[glossary-finalize_django_types]: ../GLOSSARY.md#finalize_django_types
[glossary-get_queryset-visibility-hook]: ../GLOSSARY.md#get_queryset-visibility-hook
[glossary-input-type-generation]: ../GLOSSARY.md#input-type-generation
[glossary-metaexclude]: ../GLOSSARY.md#metaexclude
[glossary-metafields]: ../GLOSSARY.md#metafields
[glossary-metamodel]: ../GLOSSARY.md#metamodel
[glossary-metaprimary]: ../GLOSSARY.md#metaprimary
[glossary-only-projection]: ../GLOSSARY.md#only-projection
[glossary-orderset]: ../GLOSSARY.md#orderset
[glossary-per-field-permission-hooks]: ../GLOSSARY.md#per-field-permission-hooks
[glossary-scalar-field-conversion]: ../GLOSSARY.md#scalar-field-conversion
[glossary-serializermutation]: ../GLOSSARY.md#serializermutation
[glossary-syncmisuseerror]: ../GLOSSARY.md#syncmisuseerror
[glossary-testclient]: ../GLOSSARY.md#testclient
[glossary-upload-scalar]: ../GLOSSARY.md#upload-scalar
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[rationale-d10]: appx/spec-038-form_mutations-0_0_12-rationale.md#decision-10--operations-create--update-for-the-modelform-no-form-delete
[rationale-d11]: appx/spec-038-form_mutations-0_0_12-rationale.md#decision-11--write-authorization-reuse-the-036-seam-djangomodelpermission-for-the-modelform-explicit-classes-for-the-plain-form
[rationale-d12]: appx/spec-038-form_mutations-0_0_12-rationale.md#decision-12--live-coverage-products-grows-a-modelform-and-a-plain-form-mutation
[rationale-d13]: appx/spec-038-form_mutations-0_0_12-rationale.md#decision-13--finalization-seam-reuse-the-mutation-phase-25-bind-no-deferred_meta_keys-change
[rationale-d14]: appx/spec-038-form_mutations-0_0_12-rationale.md#decision-14--this-card-owns-the-0012-version-bump
[rationale-d1]: appx/spec-038-form_mutations-0_0_12-rationale.md#decision-1--spec-filename-and-canonical-naming
[rationale-d2]: appx/spec-038-form_mutations-0_0_12-rationale.md#decision-2--card-scope-boundary-the-two-form-flavors-ship-serializer--auth-stay-out-the-frozen-036-contracts-are-reused-unchanged
[rationale-d3]: appx/spec-038-form_mutations-0_0_12-rationale.md#decision-3--class-meta-surface-not-graphenes-mutationoptions
[rationale-d4]: appx/spec-038-form_mutations-0_0_12-rationale.md#decision-4--module-and-test-locations-forms-subpackage-mirroring-mutations
[rationale-d5]: appx/spec-038-form_mutations-0_0_12-rationale.md#decision-5--public-surface-djangoformmutation--djangomodelformmutation-exported-from-the-root
[rationale-d6]: appx/spec-038-form_mutations-0_0_12-rationale.md#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling
[rationale-d7]: appx/spec-038-form_mutations-0_0_12-rationale.md#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth
[rationale-d8]: appx/spec-038-form_mutations-0_0_12-rationale.md#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload
[rationale-d9]: appx/spec-038-form_mutations-0_0_12-rationale.md#decision-9--optimizer-composition-the-modelform-payload-re-fetch-rides-the-spec-036-g2-path
[rationale-risks]: appx/spec-038-form_mutations-0_0_12-rationale.md#risks-and-open-questions
[spec-010]: spec-010-foundation-0_0_4.md
[spec-027]: spec-027-filters-0_0_8.md
[spec-028]: spec-028-orders-0_0_8.md
[spec-034]: spec-034-permissions-0_0_10.md
[spec-035]: spec-035-optimizer_hardening-0_0_10.md
[spec-036]: spec-036-mutations-0_0_11.md
[spec-037]: spec-037-upload_file_image_mapping-0_0_11.md
[spec-038-rationale]: appx/spec-038-form_mutations-0_0_12-rationale.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[auth-mutations]: ../../django_strawberry_framework/auth/mutations.py
[forms-converter]: ../../django_strawberry_framework/forms/converter.py
[forms-init]: ../../django_strawberry_framework/forms/__init__.py
[forms-inputs]: ../../django_strawberry_framework/forms/inputs.py
[forms-resolvers]: ../../django_strawberry_framework/forms/resolvers.py
[forms-sets]: ../../django_strawberry_framework/forms/sets.py
[init]: ../../django_strawberry_framework/__init__.py
[mutations-fields]: ../../django_strawberry_framework/mutations/fields.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[mutations-operations]: ../../django_strawberry_framework/mutations/operations.py
[mutations-permissions]: ../../django_strawberry_framework/mutations/permissions.py
[mutations-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[mutations-sets]: ../../django_strawberry_framework/mutations/sets.py
[registry]: ../../django_strawberry_framework/registry.py
[rest-framework-package]: ../../django_strawberry_framework/rest_framework/
[testing-package]: ../../django_strawberry_framework/testing/
[types-base]: ../../django_strawberry_framework/types/base.py
[types-converters]: ../../django_strawberry_framework/types/converters.py
[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py
[utils-errors]: ../../django_strawberry_framework/utils/errors.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py
[utils-narrowing]: ../../django_strawberry_framework/utils/_narrowing.py
[utils-write-transaction]: ../../django_strawberry_framework/utils/write_transaction.py
[utils-write-values]: ../../django_strawberry_framework/utils/write_values.py
[write-mixins]: ../../django_strawberry_framework/write_mixins.py

<!-- tests/ -->
[test-forms]: ../../tests/forms/
[test-mutations]: ../../tests/mutations/

<!-- examples/ -->
[products-forms]: ../../examples/fakeshop/apps/products/forms.py
[products-schema]: ../../examples/fakeshop/apps/products/schema.py
[test-products-api]: ../../examples/fakeshop/test_query/test_products_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[upstream-forms-converter]: ../../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/forms/converter.py
[upstream-forms-mutation]: ../../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/forms/mutation.py
[upstream-forms-types]: ../../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/forms/types.py
