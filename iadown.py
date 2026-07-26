from __future__ import annotations

import argparse
import os
import re
import zipfile
from pathlib import Path
from typing import Iterable

SAFE_IDENTIFIER = re.compile(r"[A-Za-z0-9._-]+")


def required_environment(name: str) -> str:
    value = os.environ.get(name)
    if value is None:
        raise SystemExit(f"Required environment variable is missing: {name}")
    return value


def write_github_outputs(values: Iterable[tuple[str, object]]) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return

    with Path(output_path).open("a", encoding="utf-8") as output:
        for name, value in values:
            output.write(f"{name}={value}\n")


def resolve_items() -> None:
    from internetarchive import search_items

    query = required_environment("SEARCH_QUERY").strip()
    if not query:
        raise SystemExit("search_query cannot be empty")

    try:
        max_items = int(required_environment("MAX_ITEMS"))
    except ValueError as exc:
        raise SystemExit("max_items must be a whole number") from exc

    if max_items < 0:
        raise SystemExit("max_items must be 0 or greater")

    identifiers: list[str] = []
    seen: set[str] = set()
    results = search_items(
        query,
        fields=["identifier"],
        sorts=["identifier asc"],
        max_retries=5,
    )

    for result in results:
        identifier = str(result.get("identifier", "")).strip()
        if not identifier or identifier in seen:
            continue
        if identifier in {".", ".."} or not SAFE_IDENTIFIER.fullmatch(identifier):
            raise SystemExit(f"Unsafe or invalid item identifier: {identifier!r}")

        seen.add(identifier)
        identifiers.append(identifier)
        if max_items and len(identifiers) >= max_items:
            break

    if not identifiers:
        raise SystemExit("The search query returned no items")

    identifiers_path = Path(required_environment("IA_IDENTIFIERS_FILE"))
    identifiers_path.parent.mkdir(parents=True, exist_ok=True)
    identifiers_path.write_text(
        "".join(f"{identifier}\n" for identifier in identifiers),
        encoding="utf-8",
    )

    download_root = Path(required_environment("IA_DOWNLOAD_DIR"))
    download_root.mkdir(parents=True, exist_ok=True)
    for identifier in identifiers:
        (download_root / identifier).mkdir(exist_ok=True)

    write_github_outputs([("item_count", len(identifiers))])
    print(f"Found {len(identifiers)} item(s).")


def package_downloads() -> None:
    requested_name = required_environment("REQUESTED_ARTIFACT_NAME").strip()
    if requested_name.lower().endswith(".zip"):
        requested_name = requested_name[:-4]

    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "-", requested_name)
    safe_name = safe_name.strip("._-")[:100] or "internet-archive-items"

    download_root = Path(required_environment("IA_DOWNLOAD_DIR")).resolve()
    if not download_root.is_dir():
        raise SystemExit(f"Download directory does not exist: {download_root}")

    zip_path = (Path.cwd() / f"{safe_name}.zip").resolve()
    paths = sorted(download_root.rglob("*"), key=lambda path: path.as_posix())

    file_count = 0
    with zipfile.ZipFile(
        zip_path,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=1,
        allowZip64=True,
    ) as archive:
        for path in paths:
            if path.is_symlink():
                raise SystemExit(f"Refusing to archive symlink: {path}")

            archive_name = path.relative_to(download_root).as_posix()
            if path.is_dir():
                archive.writestr(f"{archive_name.rstrip('/')}/", b"")
            elif path.is_file():
                archive.write(path, archive_name)
                file_count += 1

    if file_count == 0:
        zip_path.unlink(missing_ok=True)
        raise SystemExit("No files were downloaded")

    write_github_outputs(
        [
            ("artifact_name", safe_name),
            ("zip_path", zip_path),
            ("zip_name", zip_path.name),
            ("file_count", file_count),
        ]
    )
    print(f"Created {zip_path.name} with {file_count} file(s).")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resolve an Internet Archive search or package downloaded items."
    )
    parser.add_argument(
        "command",
        choices=("resolve", "package"),
        help="Operation to perform.",
    )
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    if arguments.command == "resolve":
        resolve_items()
    else:
        package_downloads()


if __name__ == "__main__":
    main()
