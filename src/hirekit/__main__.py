"""Allow running HireKit via `python -m hirekit`."""

import sys


def main() -> None:
    from hirekit.cli.app import app
    try:
        app()
    except KeyboardInterrupt:
        sys.exit(130)  # 128 + SIGINT(2)


if __name__ == "__main__":
    main()
