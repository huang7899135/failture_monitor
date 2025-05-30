from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from config.setting import DATABASE_URL
from contextlib import contextmanager


engine = create_engine(
    DATABASE_URL, 
    pool_size=10, 
    max_overflow=20, 
    pool_recycle=3600, 
    pool_pre_ping=True,
    connect_args={
        "charset": "utf8mb4",
        "use_unicode": True
    }
)


SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=True, bind=engine))


# engine = create_engine('mysql+pymysql://username:password@localhost/dbname')
@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()