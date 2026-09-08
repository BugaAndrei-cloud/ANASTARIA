import argparse

from app.database.session import SessionLocal
from app.services.marketplace_executor import process_next_command


def main() -> None:
    parser = argparse.ArgumentParser(description="Process due ANASTARIA Marketplace commands")
    parser.add_argument("--worker-id", default="marketplace-worker-cli")
    parser.add_argument("--max-commands", type=int, default=1)
    args = parser.parse_args()
    if args.max_commands < 1:
        parser.error("--max-commands must be positive")

    processed = 0
    while processed < args.max_commands:
        with SessionLocal.begin() as session:
            command_id = process_next_command(session, args.worker_id)
        if command_id is None:
            break
        processed += 1
    print(f"processed={processed}")


if __name__ == "__main__":
    main()
