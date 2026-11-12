import pytest
from pydantic import ValidationError

from ggs_genealogy import Person


def test_person_roundtrip() -> None:
    person = Person(given_name="Ada", family_name="Lovelace")
    assert person.model_dump() == {
        "given_name": "Ada",
        "family_name": "Lovelace",
    }
    assert person.display_name() == "Ada Lovelace"


def test_person_rejects_empty_given_name() -> None:
    with pytest.raises(ValidationError):
        Person(given_name="", family_name="Lovelace")
