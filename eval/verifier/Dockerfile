# Base image is overridable so a release can pin a scanned 0-Critical/0-High
# digest (see eval/verifier/SUPPLY_CHAIN.md). The default remains a pinned slim
# digest; the image-scan gate fails on Critical/High CVEs, so shipping requires
# bumping this to a clean digest.
ARG BASE_IMAGE=python:3.12-slim@sha256:423ed6ab25b1921a477529254bfeeabf5855151dc2c3141699a1bfc852199fbf
FROM ${BASE_IMAGE}

RUN python -m pip install --no-cache-dir pytest==9.1.1

COPY uv-shim /usr/local/bin/uv

RUN chmod +x /usr/local/bin/uv && mkdir -p /workspace

WORKDIR /workspace
