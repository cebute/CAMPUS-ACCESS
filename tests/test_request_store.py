import json
import tempfile
import unittest

from pathlib import Path
from unittest.mock import patch

from request_store import (
    create_request,
    load_requests,
    save_requests,
    generate_request_id,
    validate_request_record,
    ValidationError,
    DataFileError,
)


class TestRequestStore(unittest.TestCase):

    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.data_file = (
            Path(self.temp_directory.name) / "requests.json"
        )

    def tearDown(self):
        self.temp_directory.cleanup()

    def test_create_valid_request(self):
        request = create_request(
            "F001",
            "visitor",
            self.data_file,
        )

        self.assertEqual(request["request_id"], "A001")
        self.assertEqual(request["fellow_id"], "F001")
        self.assertEqual(request["card_type"], "visitor")
        self.assertEqual(request["status"], "requested")
        self.assertIsNone(request["approved_by"])

        saved = load_requests(self.data_file)
        self.assertEqual(len(saved), 1)

    def test_reject_blank_fellow_id(self):
        with self.assertRaises(ValidationError):
            create_request(
                "   ",
                "visitor",
                self.data_file,
            )

        self.assertFalse(self.data_file.exists())

    def test_reject_invalid_card_type(self):
        with self.assertRaises(ValidationError):
            create_request(
                "F001",
                "gold",
                self.data_file,
            )

        self.assertFalse(self.data_file.exists())

    def test_reject_wrong_input_type(self):
        with self.assertRaises(ValidationError):
            create_request(
                123,
                "visitor",
                self.data_file,
            )

        self.assertFalse(self.data_file.exists())

    def test_reject_malformed_fellow_id(self):
        with self.assertRaises(ValidationError):
            create_request(
                "F12",
                "visitor",
                self.data_file,
            )

        self.assertFalse(self.data_file.exists())

    def test_unique_ids_after_reload(self):
        first = create_request(
            "F001",
            "visitor",
            self.data_file,
        )

        # Simulate a new program session by loading the file again.
        loaded = load_requests(self.data_file)

        second_id = generate_request_id(loaded)

        self.assertEqual(first["request_id"], "A001")
        self.assertEqual(second_id, "A002")

        second = create_request(
            "F002",
            "student",
            self.data_file,
        )

        self.assertEqual(second["request_id"], "A002")

    def test_reject_corrupted_json(self):
        self.data_file.write_text(
            '{"request_id": ',
            encoding="utf-8",
        )

        with self.assertRaises(DataFileError):
            load_requests(self.data_file)

    def test_reject_empty_existing_file(self):
        self.data_file.write_text(
            "",
            encoding="utf-8",
        )

        with self.assertRaises(DataFileError):
            load_requests(self.data_file)

    def test_reject_missing_fields(self):
        invalid_request = {
            "request_id": "A001",
            "fellow_id": "F001",
        }

        with self.assertRaises(DataFileError):
            validate_request_record(invalid_request)

    def test_reject_duplicate_ids(self):
        request = {
            "request_id": "A001",
            "fellow_id": "F001",
            "card_type": "visitor",
            "status": "requested",
            "approved_by": None,
        }

        self.data_file.write_text(
            json.dumps([request, request]),
            encoding="utf-8",
        )

        with self.assertRaises(DataFileError):
            load_requests(self.data_file)

    def test_reject_invalid_status(self):
        request = {
            "request_id": "A001",
            "fellow_id": "F001",
            "card_type": "visitor",
            "status": "cancelled",
            "approved_by": None,
        }

        with self.assertRaises(DataFileError):
            validate_request_record(request)

    def test_failed_save_preserves_original_file(self):
        original_request = {
            "request_id": "A001",
            "fellow_id": "F001",
            "card_type": "visitor",
            "status": "requested",
            "approved_by": None,
        }

        save_requests(
            [original_request],
            self.data_file,
        )

        original_contents = self.data_file.read_bytes()

        another_request = {
            "request_id": "A002",
            "fellow_id": "F002",
            "card_type": "student",
            "status": "requested",
            "approved_by": None,
        }

        with patch(
            "request_store.os.replace",
            side_effect=OSError("Simulated save failure"),
        ):
            with self.assertRaises(DataFileError):
                save_requests(
                    [original_request, another_request],
                    self.data_file,
                )

        self.assertEqual(
            self.data_file.read_bytes(),
            original_contents,
        )

        # Verify that the original file is still readable.
        loaded = load_requests(self.data_file)

        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["request_id"], "A001")


if __name__ == "__main__":
       unittest.main()