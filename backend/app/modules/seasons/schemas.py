from datetime import date

from pydantic import BaseModel, Field, model_validator


class SeasonCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    starts_on: date | None = None
    ends_on: date | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.starts_on and self.ends_on and self.ends_on < self.starts_on:
            raise ValueError("La fecha de finalización no puede ser anterior a la fecha de inicio")
        self.name = self.name.strip()
        return self


class SeasonUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    starts_on: date | None = None
    ends_on: date | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.starts_on and self.ends_on and self.ends_on < self.starts_on:
            raise ValueError("La fecha de finalización no puede ser anterior a la fecha de inicio")
        if self.name is not None:
            self.name = self.name.strip()
        return self


class SeasonResponse(BaseModel):
    id: int
    name: str
    starts_on: date | None
    ends_on: date | None
    is_active: bool


class CollectionCreateRequest(BaseModel):
    season_id: int = Field(gt=0)
    name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=5000)

    @model_validator(mode="after")
    def clean_name(self):
        self.name = self.name.strip()
        return self


class CollectionUpdateRequest(BaseModel):
    season_id: int | None = Field(default=None, gt=0)
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=5000)

    @model_validator(mode="after")
    def clean_name(self):
        if self.name is not None:
            self.name = self.name.strip()
        return self


class CollectionResponse(BaseModel):
    id: int
    season_id: int
    season_name: str
    name: str
    description: str | None
    is_active: bool


class SeasonPage(BaseModel):
    items: list[SeasonResponse]
    page: int
    page_size: int
    total: int
    total_pages: int


class CollectionPage(BaseModel):
    items: list[CollectionResponse]
    page: int
    page_size: int
    total: int
    total_pages: int
