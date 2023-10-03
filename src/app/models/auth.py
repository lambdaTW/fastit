import sqlalchemy

from app.db import bases as model_bases


class User(model_bases.Base):
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, index=True)
    username = sqlalchemy.Column(sqlalchemy.String, index=True)
    password = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    is_superuser = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
