from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from config.setting import DATABASE_URL

engine = create_engine(DATABASE_URL, pool_size=5, max_overflow=1, pool_recycle=3600, pool_pre_ping=True)


SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))


# engine = create_engine('mysql+pymysql://username:password@localhost/dbname')
