from day1.skills.validator import validate_skills


def main() -> None:
    issues = validate_skills()
    if not issues:
        print("OK")
        return

    for issue in issues:
        print(f"{issue.severity.upper()} {issue.path}: {issue.message}")

    if any(issue.severity == "error" for issue in issues):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
