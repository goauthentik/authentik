# syntax=docker/dockerfile:1

# Start from the same FIPS Python base as production (python-base stage)
FROM ghcr.io/goauthentik/fips-python:3.13.9-slim-trixie-fips@sha256:700fc8c1e290bd14e5eaca50b1d8e8c748c820010559cbfb4c4f8dfbe2c4c9ff

USER root

# Setup environment matching production python-base stage
ENV VENV_PATH="/ak-root/.venv" \
    PATH="/lifecycle:/ak-root/.venv/bin:$PATH" \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NATIVE_TLS=1 \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /ak-root

# Copy uv package manager
COPY --from=ghcr.io/astral-sh/uv:0.9.7@sha256:ba4857bf2a068e9bc0e64eed8563b065908a4cd6bfb66b531a9c424c8e25e142 /uv /uvx /bin/

# Install build dependencies
RUN rm -f /etc/apt/apt.conf.d/docker-clean && \
    echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    # Build essentials
    build-essential pkg-config libffi-dev git binutils \
    # cryptography
    curl \
    # libxml
    libxslt-dev zlib1g-dev \
    # postgresql
    libpq-dev \
    # python-kadmin-rs and kerberos testing
    clang libkrb5-dev sccache krb5-kdc krb5-admin-server \
    # xmlsec
    libltdl-dev \
    # runit (for chpst command used by lifecycle/ak)
    runit \
    # sudo (required by devcontainer features)
    sudo && \
    rm -rf /var/lib/apt/lists/*

# Environment for building native Python packages
ENV UV_NO_BINARY_PACKAGE="cryptography lxml python-kadmin-rs xmlsec" \
    RUSTUP_PERMIT_COPY_RENAME="true"

# Create authentik user with proper home directory (required for devcontainer features)
RUN adduser --disabled-password --gecos "" --uid 1000 --home /home/authentik authentik && \
    mkdir -p /certs /media /ak-root && \
    chown -R authentik:authentik /certs /media /ak-root /home/authentik && \
    echo "authentik ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/authentik

# FIPS configuration for Go development
# Don't set GOFIPS/GOFIPS140 globally to avoid breaking Go tools like docker-compose
# These will be set when building/running authentik Go code (see lifecycle/ak and Makefile)
ENV CGO_ENABLED=1

# Set TMPDIR for PID files and temp data
# Use /tmp instead of /dev/shm for development because go run needs to execute binaries
ENV TMPDIR=/tmp

# Switch to authentik user
USER authentik

# Note: Go, Node.js, Rust, and Docker are installed via devcontainer features
# Note: Python dependencies will be installed via `uv sync` after container starts
# Note: Source code is mounted at runtime from docker-compose for live editing
