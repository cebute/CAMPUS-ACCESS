import unittest

from workflow import (
    approve_request,
    issue_card,
    return_card,
    WorkflowError,
)


def make_request(status="requested", approved_by=None):
    return {
        "A001": {
            "request_id": "A001",
            "fellow_id": "F001",
            "card_type": "visitor",
            "status": status,
            "approved_by": approved_by,
        }
    }


class TestWorkflow(unittest.TestCase):

    def test_new_request_starts_as_requested(self):
        requests = make_request()

        self.assertEqual(requests["A001"]["status"], "requested")
        self.assertIsNone(requests["A001"]["approved_by"])

    def test_cannot_issue_before_approval(self):
        requests = make_request()
        original = requests["A001"].copy()

        with self.assertRaises(WorkflowError):
            issue_card(requests, "A001")

        self.assertEqual(requests["A001"], original)

    def test_blank_approver_is_rejected(self):
        requests = make_request()
        original = requests["A001"].copy()

        with self.assertRaises(WorkflowError):
            approve_request(requests, "A001", "   ")

        self.assertEqual(requests["A001"], original)

    def test_approval_records_approver(self):
        requests = make_request()

        approve_request(requests, "A001", "M01")

        self.assertEqual(requests["A001"]["status"], "approved")
        self.assertEqual(requests["A001"]["approved_by"], "M01")

    def test_complete_workflow(self):
        requests = make_request()

        approve_request(requests, "A001", "M01")
        issue_card(requests, "A001")
        return_card(requests, "A001")

        self.assertEqual(requests["A001"]["status"], "returned")
        self.assertEqual(requests["A001"]["approved_by"], "M01")

    def test_cannot_return_twice(self):
        requests = make_request(status="issued", approved_by="M01")

        return_card(requests, "A001")
        original = requests["A001"].copy()

        with self.assertRaises(WorkflowError):
            return_card(requests, "A001")

        self.assertEqual(requests["A001"], original)

    def test_cannot_issue_returned_card(self):
        requests = make_request(status="returned", approved_by="M01")
        original = requests["A001"].copy()

        with self.assertRaises(WorkflowError):
            issue_card(requests, "A001")

        self.assertEqual(requests["A001"], original)

    def test_unknown_request_is_rejected(self):
        requests = make_request()

        with self.assertRaises(WorkflowError):
            approve_request(requests, "A999", "M01")

        with self.assertRaises(WorkflowError):
            issue_card(requests, "A999")

        with self.assertRaises(WorkflowError):
            return_card(requests, "A999")

    def test_cannot_approve_twice(self):
        requests = make_request()

        approve_request(requests, "A001", "M01")
        original = requests["A001"].copy()

        with self.assertRaises(WorkflowError):
            approve_request(requests, "A001", "M02")

        self.assertEqual(requests["A001"], original)


if __name__ == "__main__":
    unittest.main()
