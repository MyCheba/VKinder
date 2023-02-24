import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Users(Base):
    __tablename__ = "users"  # список пользователей сообщества

    id = sq.Column(sq.Integer, primary_key=True)
    bdate = sq.Column(sq.Integer)
    sex = sq.Column(sq.Integer)
    first_name = sq.Column(sq.String)
    last_name = sq.Column(sq.String)
    city_id = sq.Column(sq.Integer)
    city_name = sq.Column(sq.String)


class Params(Base):  # параметры поиска для каждого пользователя сообщества
    __tablename__ = "params"

    param_id = sq.Column(sq.Integer, primary_key=True)
    sex = sq.Column(sq.Integer)
    age_from = sq.Column(sq.Integer)
    age_to = sq.Column(sq.Integer)
    city_id = sq.Column(sq.Integer)

    user_id = sq.Column(sq.Integer, sq.ForeignKey("users.id"), nullable=False)

    users = relationship(Users, backref="params")


class Profiles(Base):  # найденные профили в разрезе параметров поиска
    __tablename__ = "profiles"

    id = sq.Column(sq.Integer, primary_key=True)
    photo_id = sq.Column(sq.String)
    track_code = sq.Column(sq.String)
    first_name = sq.Column(sq.String)
    last_name = sq.Column(sq.String)
    can_access_closed = sq.Column(sq.Boolean)
    is_closed = sq.Column(sq.Boolean)
    favorite = sq.Column(sq.Boolean,  default=False)
    blacklist = sq.Column(sq.Boolean, default=False)

    param_id = sq.Column(sq.Integer, sq.ForeignKey("params.param_id"), primary_key=True)

    params = relationship(Params, backref="profiles")


def create_tables(engine):  # создание новых таблиц в БД
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
