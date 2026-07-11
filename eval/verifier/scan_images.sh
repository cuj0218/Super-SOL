#!/usr/bin/env bash
# Build the verifier + grader images and gate them on vulnerabilities.
# Fails (nonzero) if any Critical or High CVE is present, and writes an SBOM
# for each image as release evidence. Requires Docker. Uses `docker scout` when
# available, else `trivy`. This is the supply-chain gate referenced by
# SUPPLY_CHAIN.md; it is NOT run by the offline Python quality gate.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="${HERE}/sbom"
mkdir -p "$OUT"

VERIFIER_TAG="${VERIFIER_TAG:-super-sol-verifier:scan}"
GRADER_TAG="${GRADER_TAG:-super-sol-grader:scan}"
BASE_IMAGE="${BASE_IMAGE:-}"   # override to pin a scanned 0C/0H base

build() {
  local dockerfile="$1" tag="$2"
  echo "==> Building $tag"
  if [ -n "$BASE_IMAGE" ]; then
    docker build --build-arg "BASE_IMAGE=${BASE_IMAGE}" -f "$dockerfile" -t "$tag" "$HERE"
  else
    docker build -f "$dockerfile" -t "$tag" "$HERE"
  fi
}

scan() {
  local tag="$1" name="$2"
  echo "==> Scanning $tag (fail on Critical/High)"
  if docker scout version >/dev/null 2>&1; then
    docker scout sbom --format spdx --output "${OUT}/${name}.spdx.json" "$tag"
    docker scout cves --only-severity critical,high --exit-code "$tag"
  elif command -v trivy >/dev/null 2>&1; then
    trivy image --format spdx-json --output "${OUT}/${name}.spdx.json" "$tag"
    trivy image --severity CRITICAL,HIGH --exit-code 1 "$tag"
  else
    echo "ERROR: need 'docker scout' or 'trivy' to scan images." >&2
    exit 3
  fi
  echo "    SBOM: ${OUT}/${name}.spdx.json"
}

build "${HERE}/Dockerfile" "$VERIFIER_TAG"
build "${HERE}/Dockerfile.grader" "$GRADER_TAG"
scan "$VERIFIER_TAG" "verifier"
scan "$GRADER_TAG" "grader"

echo "==> Supply-chain gate passed: 0 Critical, 0 High. SBOMs in ${OUT}/"
