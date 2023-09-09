import typing

from sqlalchemy import orm


@orm.as_declarative()
class Base:
    id: typing.Any
    __name__: str

    # Generate __tablename__ automatically
    @orm.declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
