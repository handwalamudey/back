import csv
import re
import uuid
from io import TextIOWrapper
from typing import List, Tuple

from .models import Voter, PollingStation


CSV_HEADERS = [
    "name",
    "id_number",
    "phone_number",
    "dob",
    "r_g",
    "clan",
    "polling_station_name",
    "location",
    "age_group",
    "football_club",
    "tribe",
    "ward",
    "polling_center",
    "stream",
    "mobilized_by",
    "status",
    "notes",
]


def parse_bool(value: str) -> bool:
    if value is None:
        return False
    value = str(value).strip().lower()
    return value in ["1", "true", "yes", "y"]


def import_voters_from_csv(file) -> Tuple[int, List[str]]:
    """
    Import voters from a CSV file-like object.

    Expected headers (case-insensitive):
    name,id_number,phone_number,dob,r_g,clan,polling_station_name,location,age_group,football_club,status,notes
    """
    # Ensure we have a text wrapper around uploaded file (which is usually bytes).
    # Some Excel-generated CSVs are not strict UTF-8, so we ignore invalid bytes instead of crashing.
    if isinstance(file, TextIOWrapper):
        text_file = file
    else:
        # Django's UploadedFile exposes a .file attribute which is a raw file-like object.
        raw = getattr(file, "file", file)
        text_file = TextIOWrapper(raw, encoding="utf-8", errors="ignore")

    reader = csv.DictReader(text_file)
    created_count = 0
    errors: List[str] = []

    # Normalize fieldnames to lower-case for case-insensitive matching
    if reader.fieldnames:
        reader.fieldnames = [h.lower().strip() for h in reader.fieldnames]

    for idx, row in enumerate(reader, start=2):  # start=2 -> account for header row
        try:
            # Normalise header keys very aggressively:
            # - lowercase
            # - replace any non-alphanumeric with underscore
            # - collapse multiple underscores
            # This lets "ID Number", "id-number", "Id.Number" all map to "id_number".
            data = {}
            for raw_key, raw_value in row.items():
                if raw_key is None:
                    continue
                key = raw_key.lower().strip()
                key = re.sub(r"[^a-z0-9]+", "_", key)
                key = re.sub(r"_+", "_", key).strip("_")
                value = raw_value.strip() if isinstance(raw_value, str) else raw_value
                data[key] = value

            # Normalise some specific common variants that might still slip through
            # e.g. "r_g" from "R.G" or "RG" etc.
            if "rg" in data and "r_g" not in data:
                data["r_g"] = data["rg"]

            # Map common ID column variants into id_number so the sheet
            # can use headers like "ID", "National ID", "ID No", etc.
            if "id_number" not in data or not data.get("id_number"):
                for alt_key in ["id", "id_no", "idno", "national_id", "nationalid"]:
                    if alt_key in data and data.get(alt_key):
                        data["id_number"] = data[alt_key]
                        break

            # Map common phone column variants into phone_number so the sheet
            # can use headers like "Phone", "Phone No", "Mobile", etc.
            if "phone_number" not in data or not data.get("phone_number"):
                for alt_key in ["phone", "phone_no", "phoneno", "mobile", "mobile_no", "tel", "telephone"]:
                    if alt_key in data and data.get(alt_key):
                        data["phone_number"] = data[alt_key]
                        break

            name = data.get("name")
            id_number = data.get("id_number")
            age_group = data.get("age_group")

            # Ultra-flexible: only skip truly empty rows (no useful info at all).
            if not any([
                name,
                id_number,
                age_group,
                data.get("phone_number"),
                data.get("location"),
            ]):
                errors.append(f"Row {idx}: Completely empty or invalid row - skipped")
                continue

            # Fill sensible defaults so missing boxes don't block import.
            if not name:
                name = f"Unknown Voter {idx}"
            if not id_number:
                id_number = f"AUTO-{idx}-{uuid.uuid4().hex[:8]}"
            if not age_group:
                age_group = "unspecified"

            clan = data.get("clan") or "N/A"
            polling_station_name = data.get("polling_station_name") or "GENERAL"
            location = data.get("location") or "N/A"

            # Get or create polling station
            station, _ = PollingStation.objects.get_or_create(
                name=polling_station_name,
                defaults={"registered_voters": 0, "zone_type": "swing"},
            )

            dob_raw = data.get("dob")
            try:
                dob = int(dob_raw) if dob_raw else None
            except (TypeError, ValueError):
                dob = None

            voter = Voter.objects.create(
                name=name,
                id_number=id_number,
                phone_number=data.get("phone_number") or None,
                clan=clan,
                polling_station=station,
                location=location,
                dob=dob,
                r_g=parse_bool(
                    data.get("r_g")
                    or data.get("r.g")
                    or data.get("rg")
                    or data.get("registered")
                    or ""
                ),
                age_group=age_group,
                football_club=data.get("football_club") or None,
                tribe=data.get("tribe") or None,
                ward=data.get("ward") or None,
                polling_center=data.get("polling_center") or None,
                stream=data.get("stream") or None,
                mobilized_by=data.get("mobilized_by") or None,
                status=data.get("status") or "undecided",
                notes=data.get("notes") or "",
            )

            created_count += 1
        except Exception as e:
            errors.append(f"Row {idx}: {str(e)}")

    return created_count, errors


