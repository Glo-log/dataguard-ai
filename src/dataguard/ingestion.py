"""Bounded CSV ingestion without silently skipping malformed records."""

import csv
import io
import re
from dataclasses import dataclass

import pandas as pd

MAX_BYTES = 25 * 1024 * 1024
MAX_ROWS = 200_000
MAX_COLUMNS = 250


class IngestionError(ValueError):
    """A readable, actionable input error."""


def is_identifier_column(name: str) -> bool:
    """Recognize conventional IDs without misclassifying measurements like acid."""
    return bool(
        re.search(r"(^id$|_id$|code$|invoiceno$|customerid$)", name, flags=re.IGNORECASE)
    ) or name.endswith(("ID", "Id"))


@dataclass
class LoadedDataset:
    frame: pd.DataFrame
    encoding: str
    delimiter: str


def read_csv(
    content: bytes,
    *,
    encoding: str = "utf-8-sig",
    delimiter: str = ",",
    max_bytes: int = MAX_BYTES,
    max_rows: int = MAX_ROWS,
) -> LoadedDataset:
    """Parse an explicit encoding/delimiter; retain identifier columns as strings.

    Empty fields are missing; literals such as 'NA' remain data. Row positions are
    zero-based in all downstream reports. Source bytes are never changed.
    """
    if not content or len(content) > max_bytes:
        raise IngestionError(f"Choose a nonempty CSV of at most {max_bytes // 1024**2} MB.")
    if encoding not in {"utf-8-sig", "cp1252", "latin-1"}:
        raise IngestionError("Choose UTF-8, Windows-1252, or Latin-1 explicitly.")
    if delimiter not in {",", ";", "\t", "|"}:
        raise IngestionError("Unsupported delimiter.")
    try:
        decoded = content.decode(encoding, errors="strict")
    except UnicodeDecodeError as exc:
        raise IngestionError("Cannot decode this file. Select its encoding and retry.") from exc
    if "\x00" in decoded:
        raise IngestionError("NUL bytes detected; provide a text CSV, not an Excel/binary file.")
    try:
        reader = csv.reader(io.StringIO(decoded, newline=""), delimiter=delimiter, strict=True)
        header = next(reader, [])
        if not header or any(not c.strip() for c in header):
            raise IngestionError("The CSV needs a header with nonempty column names.")
        if len(set(header)) != len(header) or len(header) > MAX_COLUMNS:
            raise IngestionError(f"Use unique headers and at most {MAX_COLUMNS} columns.")
        count = 0
        for row in reader:
            if not row:
                continue
            count += 1
            if len(row) != len(header):
                raise IngestionError(
                    f"Record {count} has {len(row)} fields; expected {len(header)}."
                )
            if count > max_rows:
                raise IngestionError(f"Demo limit: {max_rows:,} rows. Use a smaller CSV.")
        if count == 0:
            raise IngestionError("The CSV contains a header but no records.")
        identifiers = {c: "string" for c in header if is_identifier_column(c)}
        frame = pd.read_csv(
            io.StringIO(decoded),
            sep=delimiter,
            dtype=identifiers,
            keep_default_na=False,
            na_values=[""],
            on_bad_lines="error",
        )
    except (csv.Error, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
        raise IngestionError(f"Malformed CSV: {exc}") from exc
    return LoadedDataset(frame.reset_index(drop=True), encoding, delimiter)
