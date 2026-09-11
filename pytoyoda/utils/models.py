"""Utilities for manipulating or extending pydantic models."""

import logging
from collections.abc import Callable
from typing import Annotated, Any, Generic, TypeVar, get_args, get_origin

from pydantic import BaseModel, ConfigDict, Field, ValidationError, WrapValidator
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

T = TypeVar("T")

_LOGGER = logging.getLogger(__name__)


def invalid_to_none(v: Any, handler: Callable[[Any], Any], info: Any) -> Any:  # noqa : ANN401
    """Return None for failed validations otherwise original value.

    Args:
        v: Value to validate
        handler: Original validation handler
        info: Pydantic validation info, used to name the failing field

    Returns:
        Validated value or None if validation fails

    """
    try:
        return handler(v)
    except ValidationError as err:
        _LOGGER.debug(
            "Ignoring invalid value for field %r: %s",
            getattr(info, "field_name", None),
            err.errors()[:1],
        )
        return None


class CustomEndpointBaseModel(BaseModel):
    """Enhanced BaseModel that automatically sets invalid values to None.

    This model extends Pydantic's BaseModel to provide more graceful handling
    of invalid data by converting fields that fail validation to None instead
    of raising exceptions.

    Example:
        >>> class User(CustomBaseModel):
        ...     name: str
        ...     age: int
        >>> # This won't raise an error, age will be None
        >>> user = User(name="John", age="not-a-number")
        >>> print(user.age)
        None

    """

    def __init_subclass__(cls, **kwargs: dict) -> None:
        """Default nullable fields to None and wrap every field's validation.

        Each field is wrapped with :func:`invalid_to_none` so a value that
        fails validation becomes None instead of invalidating the response.

        Nullable fields (``X | None``) without an explicit default are also
        given ``default=None``. Pydantic otherwise treats ``X | None`` as
        *required*, so a field Toyota stops sending (response schema drift)
        fails validation of the whole model. Because collection fields are
        wrapped too, one such omission would silently collapse e.g. an entire
        vehicle list to None instead of dropping just the missing value.
        Treating nullable fields as optional matches this base model's lenient
        contract and keeps a single drifted field from invalidating a payload.
        """
        for name, annotation in list(cls.__annotations__.items()):
            # Skip private/protected attributes
            if name.startswith("_"):
                continue

            # Split any existing Annotated metadata from the underlying type
            # so it is preserved when the field is re-wrapped below.
            is_annotated = get_origin(annotation) is Annotated
            inner = get_args(annotation)[0] if is_annotated else annotation
            metadata = list(get_args(annotation)[1:]) if is_annotated else []

            field_info = cls.__dict__.get(name)
            has_explicit_default = (
                isinstance(field_info, FieldInfo)
                and (
                    field_info.default is not PydanticUndefined
                    or field_info.default_factory is not None
                )
            ) or (field_info is not None and not isinstance(field_info, FieldInfo))
            is_nullable = inner is Any or type(None) in get_args(inner)
            if is_nullable and not has_explicit_default:
                metadata.insert(0, Field(default=None))

            # Apply the validator wrapper (nesting keeps this valid on 3.10)
            metadata.append(WrapValidator(invalid_to_none))
            combined = inner
            for item in metadata:
                combined = Annotated[combined, item]
            cls.__annotations__[name] = combined


class CustomAPIBaseModel(BaseModel, Generic[T]):
    """Base class for all API models."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(self, data: T, **kwargs: dict) -> None:
        """Initialize with data object.

        Args:
            data (T): The underlying data object
            **kwargs: Additional keyword arguments passed to the parent class

        """
        super().__init__(**kwargs)
        self._data = data

    def __repr__(self) -> str:
        """Generate string representation based on properties."""
        return " ".join(
            [
                f"{k}={getattr(self, k)!s}"
                for k, v in type(self).__dict__.items()
                if isinstance(v, property)
            ],
        )


class Temperature(BaseModel):
    """Temperature value with unit."""

    value: float | None
    unit: str | None

    def __str__(self) -> str:
        """Represent Temperature model as string."""
        return f"{self.value}{self.unit}"


class Distance(BaseModel):
    """Distance value with unit."""

    value: float | None
    unit: str | None

    def __str__(self) -> str:
        """Represent Distance model as string."""
        return f"{self.value} {self.unit}"
