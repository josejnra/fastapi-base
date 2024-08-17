from sqlalchemy.engine.base import Engine
from sqlmodel import SQLModel, create_engine


def get_engine(db_url: str) -> Engine:
    """Get SQLAlchemy engine from database URL.

    Args:
        db_url (str): database URL

    Returns:
        Engine: object that handles the communication with the database.
    """
    return create_engine(db_url, echo=True)


def init_db(engine: Engine):
    """It takes an engine and uses it to create the database
        and all the tables registered in this MetaData object.

    Args:
        engine (Engine): object that holds all network information to the database.
    """
    SQLModel.metadata.create_all(engine)
