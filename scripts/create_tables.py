"""Create the tables defined in app/models.py.

Install the project with: python -m pip install -e .
Then run: create-tables
Set DATABASE_URL to use a different database connection.
"""

import os

from sqlalchemy import create_engine

from app.models import Base, Transaction


def main() -> None:
    # localhost connects through the PostgreSQL port exposed by compose.yaml.
    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://realtor:realtor@localhost:5432/transactions",
    )
    engine = create_engine(database_url)

    try:
        # Importing Base also loads Transaction and registers its table.
        # create_all creates missing tables; existing tables are left intact.
        Base.metadata.create_all(engine)
        # Transaction.__table__.create(engine, checkfirst=True)
        print("Database tables are ready.")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
