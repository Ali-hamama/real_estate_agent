"""Save CSV statistics for every column as a PDF without charts.

Usage:
    python data/scripts/inspect_data.py
    python data/scripts/inspect_data.py --input data/raw/combined_raw_data.csv
    python data/scripts/inspect_data.py --top-values 20

Requires pandas and reportlab. Missing means null or whitespace-only.
Invalid prices/sizes are nonnumeric, infinite, zero, or negative.
Dates default to YYYY-MM-DD; use --date-format for other formats.
"""

from __future__ import annotations

import argparse
from contextlib import redirect_stdout
import io
import textwrap
from pathlib import Path

import pandas as pd
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

DATA_DIR = Path(__file__).resolve().parents[1]


def missing_mask(series: pd.Series) -> pd.Series:
    return series.isna() | series.astype("string").str.strip().eq("").fillna(False)


def print_table(title: str, frame: pd.DataFrame) -> None:
    print(f"\n{title}\n{'=' * len(title)}")
    print("No values." if frame.empty else frame.to_string(index=False))


def print_counts(title: str, series: pd.Series, limit: int | None = None) -> None:
    # Nulls stay separate from literal strings such as '(Missing)'.
    values = series.astype("string").str.strip().mask(missing_mask(series))
    counts = values.value_counts(dropna=False)
    shown = counts if limit is None else counts.head(limit)
    print_table(title, shown.rename_axis("Value").reset_index(name="Rows"))
    if limit is not None and len(counts) > limit:
        print(f"Showing {limit} of {len(counts):,} values (including missing); use --top-values 0 for all.")


def generate_report(input_path: Path, date_format: str = "%Y-%m-%d",
                    top_values: int = 10) -> None:
    """Read a CSV and print statistics; optional domain columns may be absent."""
    df = pd.read_csv(input_path, low_memory=False, dtype={"transaction_id": "string"})
    print("CSV data inspection report")
    print(f"Source: {input_path.resolve()}")
    print(f"Total rows: {len(df):,}")
    print(f"Total columns: {len(df.columns):,}")
    print(f"Fully duplicated rows beyond the first: {df.duplicated().sum():,}")
    print("Statistics include all rows; duplicates are not removed.")

    summary = []
    for column in df.columns:
        missing = missing_mask(df[column])
        present = df.loc[~missing, column]
        summary.append({
            "Column": column, "Data type": str(df[column].dtype),
            "Present": len(present), "Missing": int(missing.sum()),
            "Missing %": round(100 * missing.mean(), 2) if len(df) else 0.0,
            "Unique nonmissing": present.nunique(),
        })
    print_table("All columns: types, completeness, and unique values", pd.DataFrame(summary))

    if "transaction_id" in df:
        missing = missing_mask(df["transaction_id"])
        ids = df.loc[~missing, "transaction_id"].str.strip()
        counts = ids.value_counts()
        duplicates = counts[counts > 1]
        print_table("Transaction IDs", pd.DataFrame([
            ["Unique nonmissing IDs", ids.nunique()],
            ["Missing IDs", int(missing.sum())],
            ["Distinct repeated IDs", len(duplicates)],
            ["Rows belonging to repeated IDs", int(duplicates.sum())],
            ["Extra rows beyond first occurrence", int(ids.duplicated().sum())],
        ], columns=["Metric", "Rows / IDs"]))
        print("IDs are compared after trimming whitespace; missing IDs are excluded.")
        print_table("Duplicate transaction IDs", duplicates.rename_axis("Transaction ID").reset_index(name="Occurrences"))
    else:
        print("\nTransaction ID checks unavailable: transaction_id column is absent.")

    quality = []
    if "instance_date" in df:
        missing = missing_mask(df["instance_date"])
        dates = pd.to_datetime(df["instance_date"].astype("string").str.strip(),
                               format=date_format, errors="coerce")
        valid = dates.dropna()
        print("\nDate range: " + (f"{valid.min():%Y-%m-%d} to {valid.max():%Y-%m-%d}"
                                   if not valid.empty else "No valid dates"))
        quality.append(["instance_date", int(missing.sum()), int((~missing & dates.isna()).sum()), int(dates.notna().sum())])
        years = dates.dt.year.astype("Int64").astype("string").fillna("Missing/invalid date")
        print_table("Transactions per year", years.value_counts().sort_index().rename_axis("Year").reset_index(name="Rows"))
    else:
        print("\nDate range and yearly counts unavailable: instance_date column is absent.")

    details = []
    for column in ["actual_worth", "procedure_area"]:
        if column not in df:
            print(f"\nNumeric validation unavailable: {column} column is absent.")
            continue
        missing = missing_mask(df[column])
        values = pd.to_numeric(df[column], errors="coerce")
        nonnumeric = ~missing & values.isna()
        infinite = values.isin([float("inf"), float("-inf")])
        nonpositive = values.le(0) & ~infinite
        invalid = ~missing & (nonnumeric | infinite | nonpositive)
        quality.append([column, int(missing.sum()), int(invalid.sum()), int((~missing & ~invalid).sum())])
        details.extend([[column, "Nonnumeric", int(nonnumeric.sum())],
                        [column, "Infinite", int(infinite.sum())],
                        [column, "Zero or negative (finite)", int(nonpositive.sum())]])
    print_table("Missing and invalid dates, prices, and property sizes",
                pd.DataFrame(quality, columns=["Column", "Missing", "Invalid", "Valid"]))
    print(f"Invalid dates do not match {date_format}; future dates are allowed.")
    print("Invalid prices/sizes are nonnumeric, infinite, zero, or negative; missing and invalid counts are separate.")
    print_table("Numeric validation details", pd.DataFrame(details, columns=["Column", "Issue", "Rows"]))

    full_counts = {
        "area_name_en": "Transactions per community",
        "rooms_en": "Transactions per bedroom count (original labels)",
        "property_type_en": "Unique property types",
        "property_sub_type_en": "Unique property subtypes",
        "procedure_name_en": "Unique transaction categories",
        "trans_group_en": "Unique transaction groups",
        "reg_type_en": "Unique Ready/Off-Plan values (original labels)",
    }
    for column, title in full_counts.items():
        if column in df:
            print_counts(f"{title}: {column}", df[column])

    # Every column gets its own statistics, including fields beyond the domain checks.
    for column in df.columns:
        series = df[column].mask(missing_mask(df[column]))
        print_table(f"Column statistics: {column}", series.describe().rename_axis("Statistic").reset_index(name="Value"))
        print_counts(f"Value counts: {column}", series, limit=top_values or None)


def save_pdf(input_path: Path, output_path: Path,
             date_format: str = "%Y-%m-%d", top_values: int = 10) -> Path:
    """Render the complete printed report as paginated text, preserving tables."""
    output = io.StringIO()
    with redirect_stdout(output):
        generate_report(input_path, date_format, top_values)

    # A monospaced font keeps the printed table columns aligned.
    font = "Courier"
    font_path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")
    if font_path.is_file():
        font = "ReportMono"
        pdfmetrics.registerFont(TTFont(font, str(font_path)))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    page_width, page_height = landscape(A4)
    document = canvas.Canvas(str(output_path), pagesize=(page_width, page_height))
    document.setTitle("CSV data inspection report")
    margin, font_size, line_height = 36, 8, 11
    line_width = int((page_width - 2 * margin) / pdfmetrics.stringWidth("M", font, font_size))
    page_number = 1
    y = page_height - margin
    document.setFont(font, font_size)

    def footer() -> None:
        document.setFont(font, font_size)
        document.drawRightString(page_width - margin, 20, f"Page {page_number}")

    for line in output.getvalue().splitlines():
        # Wrap unusually wide tables/values instead of clipping their contents.
        lines = textwrap.wrap(line, width=line_width, expand_tabs=False,
                              replace_whitespace=False, drop_whitespace=False) or [""]
        for wrapped in lines:
            if y < margin + line_height:
                footer()
                document.showPage()
                page_number += 1
                document.setFont(font, font_size)
                y = page_height - margin
            document.drawString(margin, y, wrapped)
            y -= line_height
    footer()
    document.save()
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", type=Path, default=DATA_DIR / "processed" / "processed_data.csv")
    parser.add_argument("--output", type=Path, default=DATA_DIR / "reports" / "data_inspection_report.pdf")
    parser.add_argument("--date-format", default="%Y-%m-%d", help="Date parsing format (default: ISO YYYY-MM-DD)")
    parser.add_argument("--top-values", type=int, default=10, help="Value counts per column (default: 10; 0 prints all)")
    args = parser.parse_args()
    if args.top_values < 0:
        parser.error("--top-values must be zero or greater")
    try:
        report = save_pdf(args.input, args.output, args.date_format, args.top_values)
        print(f"Report saved to {report.resolve()}")
    except (OSError, ValueError, pd.errors.ParserError) as error:
        parser.exit(1, f"Report generation failed: {error}\n")


if __name__ == "__main__":
    main()
