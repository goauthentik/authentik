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

# Copy uv package manager (same as production)
COPY --from=ghcr.io/astral-sh/uv:0.9.7@sha256:ba4857bf2a068e9bc0e64eed8563b065908a4cd6bfb66b531a9c424c8e25e142 /uv /uvx /bin/

# Install build dependencies (matching production python-deps stage)
# These are kept in devcontainer since we need to build/rebuild packages during development
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
    libltdl-dev && \
    # Install Rust (required for cryptography and other native packages)
    curl https://sh.rustup.rs -sSf | sh -s -- -y && \
    rm -rf /var/lib/apt/lists/*

# Add Rust to PATH
ENV PATH="/root/.cargo/bin:$PATH"

# Environment for building native Python packages (matching production)
ENV UV_NO_BINARY_PACKAGE="cryptography lxml python-kadmin-rs xmlsec" \
    RUSTUP_PERMIT_COPY_RENAME="true"

# Install Go 1.25 (matching production)
RUN apt-get update && \
    apt-get install -y --no-install-recommends wget && \
    ARCH=$(dpkg --print-architecture) && \
    wget -q "https://go.dev/dl/go1.25.4.linux-${ARCH}.tar.gz" && \
    tar -C /usr/local -xzf "go1.25.4.linux-${ARCH}.tar.gz" && \
    rm "go1.25.4.linux-${ARCH}.tar.gz" && \
    rm -rf /var/lib/apt/lists/*

# Install Node.js 24 (matching production)
RUN curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    rm -rf /var/lib/apt/lists/*

# Install Docker CLI and runit (for chpst command used by lifecycle/ak)
RUN curl -fsSL https://get.docker.com | sh && \
    apt-get update && \
    apt-get install -y --no-install-recommends runit && \
    rm -rf /var/lib/apt/lists/*

# Create authentik user (matching production, required by lifecycle/ak script)
RUN adduser --system --no-create-home --uid 1000 --group --home /authentik authentik && \
    mkdir -p /certs /media /authentik/.ssh && \
    chown authentik:authentik /certs /media /authentik/.ssh

# Add Go to PATH and set GOPATH
ENV PATH="/usr/local/go/bin:/root/go/bin:${PATH}" \
    GOPATH="/root/go"

# Install golangci-lint for Go linting using official install script
RUN curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b /usr/local/go/bin v2.6.1

# FIPS configuration for Go development
# Don't set GOFIPS/GOFIPS140 globally to avoid breaking Go tools like docker-compose
# These will be set when building/running authentik Go code (see lifecycle/ak and Makefile)
ENV CGO_ENABLED=1

# Set TMPDIR for PID files and temp data
# Use /tmp instead of /dev/shm for development because go run needs to execute binaries
ENV TMPDIR=/tmp

# Note: Python dependencies will be installed via `uv sync` after container starts
# Note: Source code is mounted at runtime from docker-compose for live editing
