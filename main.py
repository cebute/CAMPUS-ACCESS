from request_store import (
    create_request,
    load_requests,
    find_request,
    RequestError,
)


def main():
    while True:
        print("\n=== CARD REQUEST SYSTEM ===")
        print("1. Create card request")
        print("2. View all requests")
        print("3. Find a request")
        print("4. Exit")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            fellow_id = input("Enter fellow ID: ")
            card_type = input(
                "Enter card type (visitor/student/staff): "
            )

            try:
                request = create_request(
                    fellow_id,
                    card_type,
                )

                print("\nRequest created successfully.")
                print(f"Request ID: {request['request_id']}")

                for field, value in request.items():
                    print(f"{field}: {value}")

            except RequestError as error:
                print(f"Error: {error}")
        elif choice == "2":
            try:
                requests = load_requests()

                if not requests:
                    print("No requests found.")
                else:
                    for request in requests:
                        print(request)

            except RequestError as error:
                print(f"Error: {error}")

        elif choice == "3":
            request_id = input("Enter request ID: ")

            try:
                request = find_request(request_id)

                if request is None:
                    print("Request not found.")
                else:
                    for field, value in request.items():
                        print(f"{field}: {value}")

            except RequestError as error:
                print(f"Error: {error}")

        elif choice == "4":
            print("Goodbye!")
            break

        else:
            print(
                "Invalid option. Please choose 1, 2, 3, or 4."
            )


if __name__ == "__main__":
    main()
    