class WorkflowError(Exception):
    """Raised when a card workflow operation is invalid."""
    pass


def approve_request(requests, request_id, approved_by):
    """
    Approve a card request.

    Expected initial status: requested
    New status: approved
    """
    if request_id not in requests:
        raise WorkflowError(f"Request '{request_id}' was not found.")

    if not isinstance(approved_by, str) or not approved_by.strip():
        raise WorkflowError("Approver ID cannot be blank.")

    request = requests[request_id]

    if request["status"] != "requested":
        raise WorkflowError(
            f"Cannot approve request with status '{request['status']}'."
        )

    # Validate before modifying the record.
    request["approved_by"] = approved_by.strip()
    request["status"] = "approved"

    return request


def issue_card(requests, request_id):
    """
    Issue a card only after approval.

    Expected initial status: approved
    New status: issued
    """
    if request_id not in requests:
        raise WorkflowError(f"Request '{request_id}' was not found.")

    request = requests[request_id]

    if request["status"] != "approved":
        raise WorkflowError(
            f"Cannot issue card. Current status: '{request['status']}'. "
            "The request must be approved first."
        )

    # Change the status only after validation succeeds.
    request["status"] = "issued"

    return request


def return_card(requests, request_id):
    """
    Return an issued card.

    Expected initial status: issued
    New status: returned
    """
    if request_id not in requests:
        raise WorkflowError(f"Request '{request_id}' was not found.")

    request = requests[request_id]

    if request["status"] != "issued":
        raise WorkflowError(
            f"Cannot return card. Current status: '{request['status']}'. "
            "Only issued cards can be returned."
        )

    # Change the status only after validation succeeds.
    request["status"] = "returned"

    return request


def display_request(request):
    """Display all fields of a request."""
    print("\n--- Card Request ---")
    for field, value in request.items():
        print(f"{field}: {value}")
    print("--------------------")


def run_menu(requests):
    """
    CLI menu for approving, issuing, returning,
    and viewing card requests.

    'requests' is the dictionary managed by Engineer A.
    """
    while True:
        print("\n===== CARD MANAGEMENT MENU =====")
        print("1. View a request")
        print("2. Approve a request")
        print("3. Issue a card")
        print("4. Return a card")
        print("5. List all requests")
        print("0. Exit")

        choice = input("Choose an option: ").strip()

        if choice == "0":
            print("Exiting card management system.")
            break

        elif choice == "1":
            request_id = input("Enter request ID: ").strip()

            try:
                if request_id not in requests:
                    raise WorkflowError(
                        f"Request '{request_id}' was not found."
                    )

                display_request(requests[request_id])

            except WorkflowError as error:
                print(f"Error: {error}")

        elif choice == "2":
            request_id = input("Enter request ID: ").strip()
            approved_by = input("Enter approver ID: ").strip()

            try:
                request = approve_request(
                    requests, request_id, approved_by
                )
                print("Request approved successfully.")
                display_request(request)

            except (WorkflowError, KeyError) as error:
                print(f"Error: {error}")

        elif choice == "3":
            request_id = input("Enter request ID: ").strip()

            try:
                request = issue_card(requests, request_id)
                print("Card issued successfully.")
                display_request(request)

            except (WorkflowError, KeyError) as error:
                print(f"Error: {error}")

        elif choice == "4":
            request_id = input("Enter request ID: ").strip()

            try:
                request = return_card(requests, request_id)
                print("Card returned successfully.")
                display_request(request)

            except (WorkflowError, KeyError) as error:
                print(f"Error: {error}")

        elif choice == "5":
            if not requests:
                print("No requests are available.")
            else:
                for request in requests.values():
                    display_request(request)

        else:
            print(
                "Invalid option. Please enter 0, 1, 2, 3, 4, or 5."
            )