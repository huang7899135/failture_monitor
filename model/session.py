from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from config.setting import DATABASE_URL

engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20, pool_recycle=3600, pool_pre_ping=True)


SessionLocal = scoped_session(sessionmaker(autocommit=True, autoflush=True, bind=engine))


# engine = create_engine('mysql+pymysql://username:password@localhost/dbname')
