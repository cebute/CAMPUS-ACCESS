import json
import os
import re
import tempfile

from pathlib import Path


# -----------------------------
# CONFIGURATION
# -----------------------------

DATA_FILE = Path(__file__).parent / "data" / "requests.json"

VALID_CARD_TYPES = {
    "visitor",
    "student",
    "staff",
}

VALID_STATUSES = {
    "requested",
    "approved",
    "issued",
    "returned",
}

REQUIRED_FIELDS = {
    "request_id",
    "fellow_id",
    "card_type",
    "status",
    "approved_by",
}


# -----------------------------
# CUSTOM EXCEPTIONS
# -----------------------------

class RequestError(Exception):
    """Base exception for request-related errors."""


class ValidationError(RequestError):
    """Raised when request data is invalid."""


class DataFileError(RequestError):
    """Raised when saved data is invalid or unreadable."""


# -----------------------------
# VALIDATION
# -----------------------------

def validate_fellow_id(fellow_id):
    """
    Validate the fellow ID.

    Expected format: F followed by three digits.
    Examples: F001, F002, F123
    """

    if not isinstance(fellow_id, str):
        raise ValidationError(
            "Fellow ID must be text."
        )

    fellow_id = fellow_id.strip().upper()

    if not fellow_id:
        raise ValidationError(
            "Fellow ID cannot be blank."
        )

    if not re.fullmatch(r"F\d{3}", fellow_id):
        raise ValidationError(
            "Invalid fellow ID. Use a format such as F001."
        )

    return fellow_id


def validate_card_type(card_type):
    """
    Accept only the supported card types.
    """

    if not isinstance(card_type, str):
        raise ValidationError(
            "Card type must be text."
        )

    card_type = card_type.strip().lower()

    if card_type not in VALID_CARD_TYPES:
        raise ValidationError(
            "Invalid card type. Choose visitor, student, or staff."
        )

    return card_type


def validate_request_record(record):
    """
    Validate the structure and values of a complete request.
    """

    if not isinstance(record, dict):
        raise DataFileError(
            "Each request must be a dictionary."
        )

    if set(record.keys()) != REQUIRED_FIELDS:
        raise DataFileError(
            "Request contains missing or unexpected fields."
        )

    request_id = record["request_id"]

    if (
        not isinstance(request_id, str)
        or not re.fullmatch(r"A\d{3,}", request_id)
    ):
        raise DataFileError(
            "Invalid request ID."
        )

    try:
        validate_fellow_id(record["fellow_id"])
        validate_card_type(record["card_type"])
    except ValidationError as error:
        raise DataFileError(str(error)) from error

    status = record["status"]

    if (
        not isinstance(status, str)
        or status not in VALID_STATUSES
    ):
        raise DataFileError(
            "Invalid request status."
        )

    approved_by = record["approved_by"]

    if status == "requested":
        if approved_by is not None:
            raise DataFileError(
                "A requested card must not have an approver."
            )

    else:
        if (
            not isinstance(approved_by, str)
            or not approved_by.strip()
        ):
            raise DataFileError(
                "Approved, issued, and returned cards "
                "must have a valid approver."
            )

    return True


# -----------------------------
# LOAD REQUESTS
# -----------------------------

def load_requests(file_path=DATA_FILE):
    """
    Load and validate saved requests.

    A missing file means there are no saved requests yet.
    An existing empty or corrupted file is rejected.
    """

    file_path = Path(file_path)

    if not file_path.exists():
        return []

    try:
        with file_path.open("r", encoding="utf-8") as file:
            requests = json.load(file)

    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise DataFileError(
            "The request file contains invalid JSON."
        ) from error

    except OSError as error:
        raise DataFileError(
            "Could not read the request file."
        ) from error

    if not isinstance(requests, list):
        raise DataFileError(
            "The request file must contain a JSON list."
        )

    seen_ids = set()

    for record in requests:
        validate_request_record(record)

        request_id = record["request_id"]

        if request_id in seen_ids:
            raise DataFileError(
                f"Duplicate request ID: {request_id}"
            )

        seen_ids.add(request_id)

    return requests


# -----------------------------
# SAVE REQUESTS SAFELY
# -----------------------------

def save_requests(requests, file_path=DATA_FILE):
    """
    Validate and save requests using an atomic file replacement.

    The original file is not replaced until the new JSON
    has been written successfully.
    """

    file_path = Path(file_path)

    if not isinstance(requests, list):
        raise ValidationError(
            "Requests must be stored in a list."
        )

    seen_ids = set()

    for record in requests:
        try:
            validate_request_record(record)
        except (ValidationError, DataFileError) as error:
            raise ValidationError(str(error)) from error

        request_id = record["request_id"]

        if request_id in seen_ids:
            raise ValidationError(
                f"Duplicate request ID: {request_id}"
            )

        seen_ids.add(request_id)

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = None

    try:
        # Create the temporary file in the same directory.
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=file_path.parent,
            delete=False,
        ) as temporary_file:

            temporary_path = Path(temporary_file.name)

            json.dump(
                requests,
                temporary_file,
                indent=4,
            )

            temporary_file.flush()
            os.fsync(temporary_file.fileno())

        # Replace the old file only after writing succeeds.
        os.replace(temporary_path, file_path)

    except (OSError, TypeError, ValueError) as error:
        raise DataFileError(
            "Could not save requests. "
            "The previous data file has not been replaced."
        ) from error

    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass


# -----------------------------
# GENERATE UNIQUE REQUEST IDs
# -----------------------------

def generate_request_id(requests):
    """
    Generate the next request ID.

    Examples:
    A001, A002, A003

    Uses the largest existing numeric ID, not just the
    number of records in the list.
    """

    highest_number = 0

    for record in requests:
        validate_request_record(record)

        request_id = record["request_id"]

        number = int(request_id[1:])

        if number > highest_number:
            highest_number = number

    return f"A{highest_number + 1:03d}"


# -----------------------------
# CREATE A REQUEST
# -----------------------------

def create_request(
    fellow_id,
    card_type,
    file_path=DATA_FILE,
):
    """
    Validate, create, and save a new card request.

    Returns the newly created request dictionary.
    """

    # Validate user input before making changes.
    fellow_id = validate_fellow_id(fellow_id)
    card_type = validate_card_type(card_type)

    # Load existing records before generating an ID.
    requests = load_requests(file_path)

    request_id = generate_request_id(requests)

    new_request = {
        "request_id": request_id,
        "fellow_id": fellow_id,
        "card_type": card_type,
        "status": "requested",
        "approved_by": None,
    }

    # Validate the complete record before saving.
    validate_request_record(new_request)

    # Build a new list rather than changing the loaded list.
    updated_requests = requests + [new_request]

    # If saving fails, the original file remains untouched
    # by the atomic replacement operation.
    save_requests(updated_requests, file_path)

    return new_request


# -----------------------------
# FIND A REQUEST
# -----------------------------

def find_request(request_id, file_path=DATA_FILE):
    """
    Find a request by ID without modifying saved records.
    """

    if not isinstance(request_id, str):
        raise ValidationError(
            "Request ID must be text."
        )

    request_id = request_id.strip().upper()

    if not re.fullmatch(r"A\d{3,}", request_id):
        raise ValidationError(
            "Invalid request ID format."
        )

    requests = load_requests(file_path)

    for record in requests:
        if record["request_id"] == request_id:
            return record

    return None