from model.session import engine


def create_tables():
    from model.base import Base
    from model import models
    Base.metadata.create_all(bind=engine)