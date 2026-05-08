#!/usr/bin/env python3
"""Pin the validator image digest in envs/deployed/docker-compose.yml after a CI build.

Examples:
    python tools/update_compose_digest.py
    python tools/update_compose_digest.py --environment staging
    python tools/update_compose_digest.py --compose-path path/to/docker-compose.yml

FIXME(template): replace <OWNER_LOWER>/<REPO_LOWER> in REPOSITORY_PREFIX with your fork after cloning the template.
The placeholder is intentionally invalid so an unpinned digest fetch fails fast.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPOSITORY_PREFIX = "ghcr.io/<OWNER_LOWER>/<REPO_LOWER>"
TAG = "v0-latest"


def run(cmd: list[str]) -> str:
    """Run command and return stdout or raise on failure."""
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return result.stdout


def fetch_digest_buildx(image: str) -> str | None:
    """Return top-level image/index digest using docker buildx imagetools inspect."""
    try:
        output = run(["docker", "buildx", "imagetools", "inspect", image])
    except subprocess.CalledProcessError:
        return None

    match = re.search(r"(?m)^Digest:\s+(\S+)\s*$", output)
    if match:
        return match.group(1)
    return None


def fetch_digest(image: str) -> str:
    """Return manifest digest for the given image tag."""
    digest = fetch_digest_buildx(image)
    if digest:
        return digest

    try:
        output = run(["docker", "manifest", "inspect", "--verbose", image])
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"docker manifest inspect failed: {exc.stderr or exc}") from exc

    try:
        data = json.loads(output)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Cannot parse docker manifest output: {exc}") from exc

    if isinstance(data, dict):
        digest = data.get("Descriptor", {}).get("digest")
        if digest:
            return digest
    elif isinstance(data, list):
        digests = [item.get("Descriptor", {}).get("digest") for item in data if isinstance(item, dict)]
        digests = [digest for digest in digests if digest]
        if len(digests) == 1:
            return digests[0]
        raise SystemExit(
            "Unable to determine a single digest from docker manifest output. "
            "Install/enable docker buildx or use an image with a single manifest."
        )

    raise SystemExit("Unable to find digest in docker manifest output.")


def update_compose(compose_path: Path, env: str, digest: str) -> int:
    """Replace `<prefix>-<env>` image references with the same prefix pinned by digest."""
    text = compose_path.read_text()
    pattern = re.compile(rf"({re.escape(REPOSITORY_PREFIX)}-{re.escape(env)})(?:[:@][^\s]+)")
    new_text, count = pattern.subn(rf"\1@{digest}", text)
    if count > 0:
        compose_path.write_text(new_text)
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-e",
        "--environment",
        choices=["prod", "staging"],
        default="prod",
        help="target environment (determines image namespace, default: prod)",
    )
    default_path = Path(__file__).resolve().parents[1] / "envs" / "deployed" / "docker-compose.yml"
    parser.add_argument(
        "--compose-path",
        type=Path,
        default=default_path,
        help=f"path to validator docker-compose.yml (default: {default_path})",
    )
    args = parser.parse_args()

    if not args.compose_path.exists():
        raise SystemExit(f"docker-compose file not found: {args.compose_path}")

    image_tag = f"{REPOSITORY_PREFIX}-{args.environment}:{TAG}"
    digest = fetch_digest(image_tag)
    replacements = update_compose(args.compose_path, args.environment, digest)

    if replacements == 0:
        raise SystemExit(f"No image references for {image_tag} found in {args.compose_path}")
    print(f"Validator: pinned {replacements} reference(s) to {image_tag}@{digest}")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as exc:
        if exc.code not in (None, 0):
            print(exc, file=sys.stderr)
        raise
