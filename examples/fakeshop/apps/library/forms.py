"""Forms for the library app's live form-mutation surface.

These exist to earn framework branches over a LIVE ``/graphql`` request (the
``examples/fakeshop/test_query/README.md`` discipline - any coverage line reachable
from a real query must be earned there): the raw-pk relation decode (single + multi)
and the ``to_field_name`` conversion, including a request-scoped FK queryset.
``Shelf.branch`` / ``Shelf.alt_branches``
relate to the NON-Relay ``BranchType`` primary, so their generated inputs are raw pk
scalars (not ``GlobalID``); the ``branch`` field sets ``to_field_name="name"``
(``Branch.name`` is unique) and declares ``queryset=None`` before assigning the
request-time queryset in ``__init__``, so schema construction and relation decoding
cannot re-derive the target model from the class-level field. ``BookGenresModelForm`` adds the live FORM
partial-update M2M-preservation case over the Relay-Node ``BookType``: an omitted
required ``genres`` M2M is reconstructed from the located row rather than cleared.
``BookRepairDeskForm`` declares a ``circulation_status`` ``ChoiceField`` narrower than
the column, so its generated input publishes only the values the form admits.
``PatronProfileGenreForm`` declares a genre-id-keyed ``favorite_genre`` over the ``to_field``
key ``PatronProfile.favorite_genre``, so a partial update omitting it rebinds the stored
genre by its id; it also names the primary-key relation ``patron``, which the create input
carries and the update input leaves out. ``PatronProfileGenreNameForm`` keeps the generated
name-keyed field over the same key, so the stored name is the form key.
``PrintingForm`` relates to the text-keyed ``Edition`` (FK + M2M), so its raw-pk
inputs carry ISBN text; ``EditionImprintForm`` updates an ``Edition`` located by that text.
``LendingDeskForm`` updates a multi-table ``LendingDesk`` through a column of its ``Venue``
parent table and one of its own, so the update writes both tables.
``KioskFaultForm`` names a ``SelfServeDesk``, whose primary key is a parent-link chain.
``InterlibraryLoanForm`` declares a branch-id-keyed ``lender`` over the ``to_field`` key
``InterlibraryLoan.lender`` (``Branch.isil``, which may be ``NULL``).
``BranchWithShelfForm`` and ``BranchPairForm`` add model-less plain-form
``perform_mutate`` write-hook and transaction-rollback cases.
``BranchCityPicksForm`` picks several cities into the single ``Branch.city`` text column, so
its input types ``city`` as a list; ``BranchCityPicksSplitForm`` also presents the stored
text as a list, so an update omitting ``city`` keeps it; ``as_query_dict`` re-encodes the
data a mutation binds as the immutable ``QueryDict`` an HTML form post arrives as.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django import forms
from django.http import QueryDict

from apps.library import models

if TYPE_CHECKING:
    from collections.abc import Mapping

    from django.core.files.uploadedfile import UploadedFile
    from django.utils.datastructures import MultiValueDict
    from typing_extensions import TypeIs


class ShelfRelationsForm(forms.ModelForm[models.Shelf]):
    """A ``Shelf`` ``ModelForm`` whose relations target the non-Relay ``BranchType``.

    ``branch`` (FK) and ``alt_branches`` (M2M) both point at ``Branch``, a non-Relay
    primary with a visibility ``get_queryset`` (it hides ``city="restricted"`` from
    non-staff), so the generated inputs are raw pk - exercising the single + multi
    raw-pk decode arms and the visibility-on-the-raw-pk-branch fix over a live query.
    ``branch`` declares ``queryset=None`` and assigns its real queryset in
    ``__init__`` (the standard request-scoped-choices idiom), and declares
    ``to_field_name="name"`` so the decode binds the resolved Branch by its unique
    name rather than its pk. The generated input and relation decoder must therefore
    retain the backing model column's related model instead of consulting the
    class-level form field's absent queryset. ``tier`` is the ``blank=True`` integer
    choice column: an explicit ``null`` cleans to ``""``, which only ``save()``
    refuses, so it earns the save-time field-keyed ``null`` error live.
    """

    branch: forms.ModelChoiceField[models.Branch] = forms.ModelChoiceField(
        queryset=None,
        to_field_name="name",
    )

    class Meta:
        model = models.Shelf
        fields = (
            "code",
            "topic",
            "condition",
            "tier",
            "branch",
            "alt_branches",
        )

    def __init__(self, *args: object, **kwargs: object) -> None:
        """Point the ``branch`` choice field at every branch."""
        # basedpyright: verbatim forward; ModelForm.__init__ checks each argument when it runs
        super().__init__(*args, **kwargs)  # pyright: ignore[reportArgumentType]
        branch = self.fields["branch"]
        if not isinstance(branch, forms.ModelChoiceField):
            raise TypeError("ShelfRelationsForm.branch must be the declared ModelChoiceField.")
        branch.queryset = models.Branch.objects.all()


class BookGenresModelForm(forms.ModelForm[models.Book]):
    """A ``Book`` ``ModelForm`` with a required ``genres`` M2M and an optional ``subtitle``.

    It serves the live FORM partial-update preservation cases.

    ``Book`` is the Relay-Node ``BookType`` primary (so the update ``id`` is a
    decodable ``GlobalID`` - unlike the non-Relay ``Shelf``, which supports create
    only). On a ``title``-only partial update two omitted shapes are reconstructed from
    the located row by ``forms/resolvers.py::_reconstruct_partial_data`` rather than
    cleared: the required ``genres`` M2M (no ``to_field_name``; the bound form would
    otherwise fail required-validation - the M2M branch) and the genuinely-optional,
    nullable ``subtitle`` scalar (``blank=True, null=True`` - distinct from a
    ``default=""`` field). ``shelf`` is intentionally NOT a form field, so the located
    row's shelf is preserved untouched by ``save()``.
    """

    class Meta:
        model = models.Book
        fields = ("title", "subtitle", "genres")


class BookRepairDeskForm(forms.ModelForm[models.Book]):
    """A ``Book`` ``ModelForm`` for the repair desk, which shelves a book or sends it to repair.

    Checking a book out is the loan desk's job, so ``circulation_status`` declares a
    ``ChoiceField`` admitting two of the column's three ``CirculationStatus`` values. The
    generated input publishes a generated enum of exactly those two values rather than the
    column's read enum, so every member the schema offers is one the form accepts.
    """

    circulation_status = forms.ChoiceField(
        choices=[
            (
                models.Book.CirculationStatus.AVAILABLE,
                models.Book.CirculationStatus.AVAILABLE.label,
            ),
            (models.Book.CirculationStatus.REPAIR, models.Book.CirculationStatus.REPAIR.label),
        ],
    )

    class Meta:
        model = models.Book
        fields = ("circulation_status",)


class PatronProfileGenreForm(forms.ModelForm[models.PatronProfile]):
    """A ``PatronProfile`` ``ModelForm`` whose ``favorite_genre`` choices are keyed by genre id.

    ``favorite_genre`` is a ``ForeignKey(Genre, to_field="name")``: the column stores the
    genre name. The form declares the field itself to list the genres alphabetically and
    sets no ``to_field_name``, so it resolves a choice by genre id, not by the name the
    column stores (the generated field passes ``to_field_name="name"``). A partial update
    that omits ``favoriteGenreId`` therefore has to rebind the stored genre by its id.
    The form also names the primary-key relation ``patron``: a create takes it as the
    client-assigned key, while the update input leaves it out (an update never carries the
    row's primary key), so the bound form validates the stored patron.
    """

    favorite_genre: forms.ModelChoiceField[models.Genre] = forms.ModelChoiceField(
        queryset=models.Genre.objects.order_by("name"),
        required=False,
    )

    class Meta:
        model = models.PatronProfile
        fields = ("patron", "address_2", "favorite_genre")


class PatronProfileGenreNameForm(forms.ModelForm[models.PatronProfile]):
    """A ``PatronProfile`` ``ModelForm`` whose generated ``favorite_genre`` is keyed by genre name.

    ``favorite_genre`` is a ``ForeignKey(Genre, to_field="name")`` and the form keeps the
    generated field, which resolves a choice by ``to_field_name="name"``: the key the column
    stores, so an omitted genre rebinds the stored name as is. The field is optional
    (``blank=True``), so a name the field cleans to empty (``""``) would clear the relation
    instead of naming the genre that carries it.
    """

    class Meta:
        model = models.PatronProfile
        fields = ("address_2", "favorite_genre")


class PrintingForm(forms.ModelForm[models.Printing]):
    """A ``Printing`` ``ModelForm`` over two relations into the text-keyed ``Edition``.

    ``Edition``'s primary key is its ISBN text column and ``EditionType`` is not
    Relay-Node, so ``edition`` (FK) and ``bound_with`` (M2M) generate raw-pk inputs that
    name each edition by its ISBN. ``Printing`` is the Relay-Node ``PrintingType``
    primary, so the update ``id`` is a ``GlobalID``.
    """

    class Meta:
        model = models.Printing
        fields = ("edition", "run_size", "bound_with")


class EditionImprintForm(forms.ModelForm[models.Edition]):
    """An ``Edition`` ``ModelForm`` over its ``imprint``, for updates by the text pk.

    ``EditionType`` is non-Relay, so the update ``id`` is the raw ISBN text.
    """

    class Meta:
        model = models.Edition
        fields = ("imprint",)


class LendingDeskForm(forms.ModelForm[models.LendingDesk]):
    """A ``LendingDesk`` ``ModelForm`` over a parent column and a local one.

    ``name`` lives on the ``Venue`` parent table and ``window_count`` on the desk's own, so
    an update writes both tables of the multi-table row, each as an UPDATE that a deleted
    row fails instead of re-inserting. ``LendingDeskType`` is non-Relay, so the update
    ``id`` is the raw pk.
    """

    class Meta:
        model = models.LendingDesk
        fields = ("name", "window_count")


class KioskFaultForm(forms.ModelForm[models.KioskFault]):
    """A ``KioskFault`` ``ModelForm`` over its ``kiosk`` key and ``note``.

    The generated ``kiosk`` choice field resolves a ``SelfServeDesk`` by primary key, the
    ``lendingdesk_ptr`` parent link.
    """

    class Meta:
        model = models.KioskFault
        fields = ("kiosk", "note")


class InterlibraryLoanForm(forms.ModelForm[models.InterlibraryLoan]):
    """An ``InterlibraryLoan`` ``ModelForm`` whose ``lender`` choices are keyed by branch id.

    ``lender`` is a ``ForeignKey(Branch, to_field="isil")``: the column stores the branch's
    ISIL. The form declares the field itself to list the branches by name and sets no
    ``to_field_name``, so it resolves a choice by branch id, not by the ISIL the column
    stores. A branch with no ISIL is a choice the field accepts, but storing its key would
    clear the relation.
    """

    lender: forms.ModelChoiceField[models.Branch] = forms.ModelChoiceField(
        queryset=models.Branch.objects.order_by("name"),
        required=False,
    )

    class Meta:
        model = models.InterlibraryLoan
        fields = ("lender", "title")


class BranchWithShelfForm(forms.Form):
    """A model-less plain ``forms.Form`` whose mutation overrides ``perform_mutate``.

    Backs ``CreateBranchWithShelf`` (a plain ``DjangoFormMutation``). A plain form has no
    ``Meta.model`` and no ``form.save()``, so the default ``perform_mutate`` is a no-op.
    The mutation overrides it to run a real multi-row ORM write - a ``Branch`` plus a
    starter ``Shelf`` under it from these two ``CharField`` values - the model-less write
    the hook exists for (a single ``ModelForm.save()`` cannot create two related rows).
    """

    branch_name = forms.CharField(max_length=200)
    shelf_code = forms.CharField(max_length=200)


class BranchPairForm(forms.Form):
    """A plain form whose mutation creates two uniquely named ``Branch`` rows.

    The second name can race with an existing row after the first branch has
    already been inserted. That gives the live mutation surface a natural
    partial-write ``IntegrityError`` case for proving that an ``ok: false``
    envelope rolls the entire plain-form transaction back.
    """

    first_name = forms.CharField(max_length=200)
    second_name = forms.CharField(max_length=200)


def _is_list(value: object) -> TypeIs[list[object]]:
    """Whether a cleaned value is a list, its items still unvalidated."""
    return isinstance(value, list)


#: The cities ``BranchCityPicksForm.city`` offers.
BRANCH_CITY_PICKS = (("north", "North"), ("south", "South"), ("east", "East"))


class BranchCityPicksForm(forms.ModelForm[models.Branch]):
    """A ``Branch`` form picking several cities into the single ``city`` text column.

    ``city`` is a ``MultipleChoiceField`` over ``Branch.city``, a ``TextField`` listing no
    choices: the field reads a list, which ``clean_city`` joins with ``,`` into the stored
    text, so the generated input types ``city`` as a list. The form presents the stored
    text as it is, so an update omitting ``city`` binds that text and the field refuses it
    ("Enter a list of values.").
    """

    city = forms.MultipleChoiceField(choices=BRANCH_CITY_PICKS)

    class Meta:
        model = models.Branch
        fields = ("name", "city")

    def clean_city(self) -> str:
        """Join the picked cities into the text ``Branch.city`` stores."""
        picks: object = self.cleaned_data.get("city")
        if not _is_list(picks):
            # Django runs ``clean_city`` only once the ``city`` field cleaned to a list.
            raise TypeError(f"expected the cleaned picks, got {type(picks).__name__}")
        return ",".join(str(pick) for pick in picks)


class BranchCityPicksSplitForm(BranchCityPicksForm):
    """``BranchCityPicksForm`` presenting the stored ``city`` text as the list it was joined from.

    ``__init__`` splits a located branch's ``city`` into ``initial["city"]``, so an update
    omitting ``city`` binds the stored picks and keeps them.
    """

    def __init__(
        self,
        data: Mapping[str, object] | None = None,
        files: MultiValueDict[str, UploadedFile[bytes]] | None = None,
        *,
        instance: models.Branch | None = None,
        prefix: str | None = None,
    ) -> None:
        """Split a located branch's stored ``city`` into the initial picks."""
        super().__init__(data, files, instance=instance, prefix=prefix)
        if self.instance.pk is not None:
            self.initial["city"] = self.instance.city.split(",") if self.instance.city else []


def as_query_dict(data: Mapping[str, object]) -> QueryDict:
    """Re-encode form data as the immutable ``QueryDict`` an HTML form post binds.

    A list value becomes the key's list of values, as a multi-select posts it.
    """
    query = QueryDict(mutable=True)
    for key, value in data.items():
        values = value if _is_list(value) else [value]
        query.setlist(key, [str(item) for item in values])
    return QueryDict(query.urlencode())
