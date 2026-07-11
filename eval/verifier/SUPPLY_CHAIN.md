# Verifier / Grader Supply Chain

The verifier and grader images run code inside the evaluation boundary — the
grader in particular executes the model's own code. Their base image is
therefore part of the trust boundary, and shipping one with known Critical/High
CVEs is not acceptable.

## The gate

`eval/verifier/scan_images.sh` builds both images and **fails on any Critical or
High CVE**, writing an SPDX SBOM per image to `eval/verifier/sbom/`. It uses
`docker scout` when present, otherwise `trivy`. The `image-scan` GitHub workflow
runs the same gate on any change under `eval/verifier/**`.

```bash
# Requires Docker + (docker scout | trivy)
bash eval/verifier/scan_images.sh
```

A green run means: 0 Critical, 0 High, and an SBOM exists for each image.

## Choosing a clean base

The Dockerfiles take an overridable `ARG BASE_IMAGE`. The default is a pinned
`python:3.12-slim` digest, which historically carried Perl-related Critical/High
Debian CVEs; the scan gate exists precisely so that state cannot ship silently.
To release:

1. Pick a base with 0 Critical/High (a scanned `python:3.12-alpine` digest has
   been observed clean; distroless is another option). Confirm your task
   fixtures run on it — Alpine uses musl, so tasks needing glibc-only wheels may
   need a different base.
2. Pin it by digest and scan:

   ```bash
   BASE_IMAGE="python:3.12-alpine@sha256:<digest>" bash eval/verifier/scan_images.sh
   ```

3. Set that `BASE_IMAGE` digest as the Dockerfile default, rebuild, and pin the
   built verifier/grader images by digest for `VERIFICATION_IMAGE` /
   `GRADER_IMAGE` (see [README.md](README.md)).

## Release evidence

Attach the two SBOMs from `eval/verifier/sbom/` and the passing `image-scan`
run to the release. Image provenance and periodic re-scanning remain a
deployment responsibility: a base that is clean today can regress as new CVEs
are published, so re-run the gate before each release.
