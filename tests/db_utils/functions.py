from datetime import datetime
from sqlalchemy.sql.expression import func
from database import init as init_db, new_session, Period


def get_max_end_time(db: str) -> datetime:
    init_db(db)

    with new_session() as session:
        return session.query(func.max(Period.end)).one()[0]
