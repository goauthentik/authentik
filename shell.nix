let
  nixpkgs = builtins.fetchTarball {
    name = "nixos-unstable-2026-02-04";
    url = "https://github.com/nixos/nixpkgs/archive/e6eae2ee2110f3d31110d5c222cd395303343b08.tar.gz";
    # Hash obtained using `nix-prefetch-url --unpack <url>`
    sha256 = "1mqwcpjyq690m9m52njw0dr9baw715s4j9sh7s8nq5wf8psm6w98";
  };
  pkgs = import nixpkgs {
    config = {
      allowUnfree = true;
    };
  };
in
  (pkgs.mkShell.override {stdenv = pkgs.gcc13Stdenv;}) {
    nativeBuildInputs = with pkgs; [
      rustup
      rustPlatform.bindgenHook
    ];
    buildInputs = with pkgs; [
      clang
      cmake
      go
      nodejs_24
      pkg-config
      python314

      gettext
      glibc
      krb5.dev
      krb5.out
      libbacktrace
      libev
      libgcc
      libtool
      libunwind
      libuv
      libxml2
      libxslt
      libclang
      lz4
      openssl
      postgresql
      postgresql.pg_config
      xmlsec
      zlib

      cargo-audit
      cargo-deny
      cargo-expand
      cargo-machete
      cargo-outdated
      cargo-workspaces
      docker-compose
      git
      gnumake
      golangci-lint
      k6
      sccache
      tokio-console
      uv
      valgrind
      watchexec
    ];

    UV_NO_BINARY_PACKAGE = "ruff psycopg gevent python-kadmin-rs memray maturin";

    GSSAPI_COMPILER_ARGS = "-I${pkgs.krb5.dev}/include -DHAS_GSSAPI_EXT_H";
    KADMIN_HEIMDAL_CLIENT_INCLUDES = "${pkgs.heimdal.dev}/include";
    KADMIN_HEIMDAL_CLIENT_KRB5_CONFIG = "${pkgs.heimdal.dev}/bin/krb5-config";
    KADMIN_HEIMDAL_SERVER_INCLUDES = "${pkgs.heimdal.dev}/include";
    KADMIN_HEIMDAL_SERVER_KRB5_CONFIG = "${pkgs.heimdal.dev}/bin/krb5-config";
    KADMIN_MIT_CLIENT_INCLUDES = "${pkgs.krb5.dev}/include";
    KADMIN_MIT_CLIENT_KRB5_CONFIG = "${pkgs.krb5.dev}/bin/krb5-config";
    KADMIN_MIT_SERVER_INCLUDES = "${pkgs.krb5.dev}/include";
    KADMIN_MIT_SERVER_KRB5_CONFIG = "${pkgs.krb5.dev}/bin/krb5-config";
    RUSTC_WRAPPER = "sccache";
    RUST_BACKTRACE = 1;

    # LD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib/";
    # LIBCLANG_PATH = "${pkgs.libclang}/lib";
    # NIX_CFLAGS_COMPILE = "-Wno-error=incompatible-pointer-types";
    # RUST_SRC_PATH = "${pkgs.rust.packages.stable.rustPlatform.rustLibSrc}";

    shellHook = ''
      export PATH="''${CARGO_HOME:-~/.cargo}/bin":"$PATH"
      export PATH="''${RUSTUP_HOME:-~/.rustup}/toolchains/$RUSTC_VERSION-${pkgs.stdenv.hostPlatform.rust.rustcTarget}/bin":"$PATH"
    '';
  }
