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


from django.db import transaction

def import_voters_from_csv(file) -> Tuple[int, List[str]]:
    """
    Import voters from a CSV file-like object.

    Expected headers (case-insensitive):
    name,id_number,phone_number,dob,r_g,clan,polling_station_name,location,age_group,football_club,status,notes
    """
    # Ensure we have a text wrapper around uploaded file (which is usually bytes).
    if isinstance(file, TextIOWrapper):
        text_file = file
    else:
        raw = getattr(file, "file", file)
        text_file = TextIOWrapper(raw, encoding="utf-8", errors="ignore")

    reader = csv.DictReader(text_file)
    created_count = 0
    errors: List[str] = []

    # Normalize fieldnames to lower-case for case-insensitive matching
    if reader.fieldnames:
        reader.fieldnames = [h.lower().strip() for h in reader.fieldnames]

    # Pre-fetch existing polling stations to minimize DB hits
    stations_cache = {s.name.strip(): s for s in PollingStation.objects.all()}
    # Pre-fetch existing ID numbers to prevent duplicates
    existing_ids = set(Voter.objects.values_list('id_number', flat=True))
    voters_to_create = []

    with transaction.atomic():
        for idx, row in enumerate(reader, start=2):  # start=2 -> account for header row
            try:
                # Normalise header keys very aggressively:
                data = {}
                for raw_key, raw_value in row.items():
                    if raw_key is None:
                        continue
                    key = raw_key.lower().strip()
                    key = re.sub(r"[^a-z0-9]+", "_", key)
                    key = re.sub(r"_+", "_", key).strip("_")
                    value = raw_value.strip() if isinstance(raw_value, str) else raw_value
                    data[key] = value

                if "rg" in data and "r_g" not in data:
                    data["r_g"] = data["rg"]

                if "id_number" not in data or not data.get("id_number"):
                    for alt_key in ["id", "id_no", "idno", "national_id", "nationalid"]:
                        if alt_key in data and data.get(alt_key):
                            data["id_number"] = data[alt_key]
                            break

                if "phone_number" not in data or not data.get("phone_number"):
                    for alt_key in ["phone", "phone_no", "phoneno", "mobile", "mobile_no", "tel", "telephone"]:
                        if alt_key in data and data.get(alt_key):
                            data["phone_number"] = data[alt_key]
                            break

                name = data.get("name")
                id_number = data.get("id_number")

                if not any([name, id_number, data.get("phone_number"), data.get("location")]):
                    continue

                if not name:
                    name = f"Unknown Voter {idx}"
                if not id_number:
                    id_number = f"AUTO-{idx}-{uuid.uuid4().hex[:8]}"
                
                # Skip if ID number already exists
                if id_number in existing_ids:
                    errors.append(f"Row {idx}: Voter with ID {id_number} already exists. Skipped.")
                    continue
                
                # Add to existing_ids set to catch duplicates within the same CSV
                existing_ids.add(id_number)

                clan = data.get("clan") or data.get("tribe") or "N/A"
                polling_station_name = data.get("polling_station_name") or "GENERAL"
                location = data.get("location") or "N/A"

                if polling_station_name == "GENERAL" and data.get("polling_center"):
                    polling_station_name = data.get("polling_center")

                # Get or create polling station from cache/DB
                station_name = polling_station_name.strip()
                if station_name not in stations_cache:
                    station, _ = PollingStation.objects.get_or_create(
                        name=station_name,
                        defaults={"registered_voters": 0, "zone_type": "swing"},
                    )
                    stations_cache[station_name] = station
                else:
                    station = stations_cache[station_name]

                dob_raw = data.get("dob")
                try:
                    dob = int(float(dob_raw)) if dob_raw else None
                except (TypeError, ValueError):
                    dob = None

                voter = Voter(
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
                    football_club=data.get("football_club") or None,
                    tribe=data.get("tribe") or None,
                    ward=data.get("ward") or None,
                    polling_center=data.get("polling_center") or None,
                    stream=data.get("stream") or None,
                    mobilized_by=data.get("mobilized_by") or None,
                    status=data.get("status") or "undecided",
                    notes=data.get("notes") or "",
                )
                voters_to_create.append(voter)
                created_count += 1

                # Bulk create in batches to keep memory usage sane
                if len(voters_to_create) >= 500:
                    Voter.objects.bulk_create(voters_to_create)
                    voters_to_create = []

            except Exception as e:
                errors.append(f"Row {idx}: {str(e)}")

        # Final batch
        if voters_to_create:
            Voter.objects.bulk_create(voters_to_create)

    return created_count, errors


