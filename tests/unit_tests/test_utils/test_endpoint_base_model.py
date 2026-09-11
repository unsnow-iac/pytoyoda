"""Tests for CustomEndpointBaseModel field defaulting and wrapping."""

from typing import Any

import pytest
from pydantic import Field, ValidationError

from pytoyoda.utils.models import CustomEndpointBaseModel


class _Sample(CustomEndpointBaseModel):
    """Sample model exercising the field-handling rules."""

    required: int
    optional_no_default: str | None = Field(alias="optionalNoDefault")
    explicit_default: str | None = Field(alias="explicitDefault", default="x")
    plain_default: str | None = None
    any_field: Any = Field(alias="anyField")


def test_nullable_without_default_is_optional():  # noqa: D103
    model = _Sample.model_validate({"required": 1})
    assert model.optional_no_default is None
    assert model.any_field is None
    assert model.explicit_default == "x"
    assert model.plain_default is None


def test_alias_is_preserved():  # noqa: D103
    model = _Sample.model_validate({"required": 1, "optionalNoDefault": "hi"})
    assert model.optional_no_default == "hi"


def test_invalid_value_becomes_none():  # noqa: D103
    model = _Sample.model_validate({"required": 1, "optionalNoDefault": 123})
    assert model.optional_no_default is None


def test_non_nullable_field_still_required():  # noqa: D103
    with pytest.raises(ValidationError):
        _Sample.model_validate({})
