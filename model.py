from typing import Protocol, TypeVar, cast

from mopyx import model

C = TypeVar('C', bound=type)


class IdentityProto(Protocol):
    def __call__(self, val: C) -> C:
        ...


model = cast(IdentityProto, model)
