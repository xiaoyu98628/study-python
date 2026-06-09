import argparse

from day1.agent import build_system_prompt


def main() -> None:
    parser = argparse.ArgumentParser(description="Preview the final system prompt.")
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Print prompt length after the prompt content.",
    )
    args = parser.parse_args()

    prompt = build_system_prompt()
    print(prompt)

    if args.stats:
        print()
        print("--- stats ---")
        print(f"characters: {len(prompt)}")


if __name__ == "__main__":
    main()
