"""Fetch official UCI archives, verify SHA-256, and extract allowlisted files only."""

import argparse
import hashlib
import json
import ssl
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import certifi

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "sources.json"
MAX_DOWNLOAD_BYTES = 60 * 1024 * 1024
MAX_MEMBER_BYTES = 100 * 1024 * 1024


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fetch_archive(url: str, destination: Path) -> None:
    """Bound download size and retry transient network errors; no TLS bypass."""
    partial = destination.with_suffix(".part")
    request = urllib.request.Request(
        url, headers={"User-Agent": "DataGuardAI/1.0 (public UCI dataset downloader)"}
    )
    for attempt in range(3):
        try:
            with (
                urllib.request.urlopen(
                    request, timeout=45, context=ssl.create_default_context(cafile=certifi.where())
                ) as response,
                partial.open("wb") as output,
            ):
                total = 0
                while block := response.read(1024 * 1024):
                    total += len(block)
                    if total > MAX_DOWNLOAD_BYTES:
                        raise ValueError("Archive exceeds the 60 MB download limit.")
                    output.write(block)
            partial.replace(destination)
            return
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt == 2:
                raise
            time.sleep(attempt + 1)


def extract_verified(archive: Path, spec: dict, directory: Path) -> list[Path]:
    """Never extract arbitrary ZIP paths or execute downloaded content."""
    expected = spec["sha256"]
    observed = sha256(archive)
    if expected and observed != expected:
        raise ValueError(
            f"Checksum mismatch for {archive.name}: {observed}. Review upstream changes; do not bypass verification."
        )
    outputs = []
    with zipfile.ZipFile(archive) as bundle:
        for member in spec["members"]:
            info = bundle.getinfo(member)
            if info.file_size > MAX_MEMBER_BYTES or Path(member).name != member:
                raise ValueError("Unsafe or oversized archive member.")
            destination = directory / member
            with bundle.open(info) as source:
                content = source.read(MAX_MEMBER_BYTES + 1)
            if len(content) > MAX_MEMBER_BYTES:
                raise ValueError("Archive member exceeds the extraction limit.")
            destination.write_bytes(content)
            outputs.append(destination)
    return outputs


def download(
    datasets: list[str], data_dir: Path, *, offline: bool = False, force: bool = False
) -> dict:
    """Cache archives locally; offline mode still verifies hashes and re-extracts."""
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    results = {}
    for name in datasets:
        spec = catalog[name]
        if not spec["sha256"]:
            raise ValueError("Dataset archive must have a reviewed checksum in data/sources.json.")
        directory = data_dir / "raw" / name
        directory.mkdir(parents=True, exist_ok=True)
        archive = directory / f"{name}.zip"
        if force and offline:
            raise ValueError("--force and --offline cannot be used together.")
        if not archive.exists() or force:
            if offline:
                raise FileNotFoundError(
                    f"Missing cached archive {archive}. Run once without --offline."
                )
            try:
                fetch_archive(spec["download_url"], archive)
            except urllib.error.URLError:
                # UCI's official beta host serves the same archives with its own TLS certificate.
                mirror = spec["download_url"].replace(
                    "https://archive.ics.uci.edu/", "https://archive-beta.ics.uci.edu/"
                )
                print(
                    "Primary host unavailable; retrying the official UCI beta host with TLS verification."
                )
                fetch_archive(mirror, archive)
        files = extract_verified(archive, spec, directory)
        results[name] = {
            "archive_sha256": sha256(archive),
            "files": {p.name: sha256(p) for p in files},
        }
        print(
            f"{name}: SHA-256 {results[name]['archive_sha256']}; {len(files)} source files verified"
        )
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset", choices=["all", "online_retail", "wine_quality"], default="all"
    )
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    names = ["online_retail", "wine_quality"] if args.dataset == "all" else [args.dataset]
    try:
        download(names, args.data_dir, offline=args.offline, force=args.force)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        parser.exit(
            1, f"Download failed: {exc}\nSee docs/DATASETS.md for manual-download recovery.\n"
        )


if __name__ == "__main__":
    main()
