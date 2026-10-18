"""Import processed CSV rows into the transactions table.

Run create-tables first, then seed-transactions from the project root.
Existing transaction IDs are skipped, and errors roll back the entire import.
"""

import argparse
import csv
import os
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from sqlalchemy import Boolean, Date, Numeric, create_engine
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Connection

from app.models import Transaction


def parse_row(raw: dict[str, str], line_number: int) -> dict[str, object]:
    """Convert CSV strings to the types declared in the model."""
    if None in raw or any(value is None for value in raw.values()):
        raise ValueError(f"CSV line {line_number}: incorrect number of fields")

    row = {}
    for column in Transaction.__table__.columns:
        value = raw[column.name].strip()
        try:
            if value == "":
                if not column.nullable:
                    raise ValueError("a value is required")
                row[column.name] = None
            elif isinstance(column.type, Boolean):
                if value not in {"0", "1"}:
                    raise ValueError("expected 0 or 1")
                row[column.name] = value == "1"
            elif isinstance(column.type, Date):
                row[column.name] = date.fromisoformat(value)
            elif isinstance(column.type, Numeric):
                number = Decimal(value)
                if not number.is_finite():
                    raise ValueError("expected a finite number")
                scale = column.type.scale
                if number != number.quantize(Decimal(1).scaleb(-scale)):
                    raise ValueError(f"expected at most {scale} decimal places")
                if abs(number) >= Decimal(10) ** (column.type.precision - scale):
                    raise ValueError("number is too large for this column")
                row[column.name] = number
            else:
                max_length = getattr(column.type, "length", None)
                if max_length and len(value) > max_length:
                    raise ValueError(f"expected at most {max_length} characters")
                row[column.name] = value
        except (ValueError, InvalidOperation) as error:
            raise ValueError(
                f"CSV line {line_number}, column '{column.name}': {error}"
            ) from error
    return row


def seed_transactions(
    connection: Connection, csv_path: Path, batch_size: int = 1000
) -> tuple[int, int]:
    """Return (processed, inserted) counts; the caller manages the transaction."""
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")

    table = Transaction.__table__
    # RETURNING counts only newly inserted rows, excluding duplicate IDs.
    statement = (
        insert(table)
        .on_conflict_do_nothing(index_elements=[table.c.transaction_id])
        .returning(table.c.transaction_id)
    )
    processed = inserted = 0
    batch = []

    with csv_path.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        expected = set(table.columns.keys())
        headers = reader.fieldnames or []
        if set(headers) != expected or len(headers) != len(expected):
            raise ValueError("CSV headers must match the transactions table columns")

        for raw in reader:
            batch.append(parse_row(raw, reader.line_num))
            processed += 1
            if len(batch) == batch_size:
                inserted += len(connection.execute(statement, batch).all())
                batch.clear()

        if batch:
            inserted += len(connection.execute(statement, batch).all())

    return processed, inserted


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "csv_path",
        nargs="?",
        type=Path,
        default=Path("data/processed/processed_data.csv"),
        help="CSV file to import (default: data/processed/processed_data.csv)",
    )
    parser.add_argument("--batch-size", type=int, default=1000)
    args = parser.parse_args()
    if args.batch_size <= 0:
        parser.error("--batch-size must be greater than zero")

    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://realtor:realtor@localhost:5432/transactions",
    )
    engine = create_engine(database_url)
    try:
        print(f"Importing {args.csv_path}...", flush=True)
        # All batches commit together on success, or roll back on an error.
        with engine.begin() as connection:
            processed, inserted = seed_transactions(
                connection, args.csv_path, args.batch_size
            )
        print(
            f"Processed {processed:,} rows: inserted {inserted:,}, "
            f"skipped {processed - inserted:,} existing transaction IDs."
        )
    except (OSError, ValueError) as error:
        parser.exit(1, f"Import failed: {error}. No rows were committed.\n")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
