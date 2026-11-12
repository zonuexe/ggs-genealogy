from pydantic import BaseModel, Field


class Person(BaseModel):
    """A person identified by given and family names."""

    given_name: str = Field(min_length=1)
    family_name: str = Field(min_length=1)

    def display_name(self) -> str:
        return f"{self.given_name} {self.family_name}"
