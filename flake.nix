{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    futils.url = "github:numtide/flake-utils";
  };

  outputs = {
    self,
    nixpkgs,
    futils,
  } @ inputs: let
    inherit (nixpkgs) lib;
    inherit (futils.lib) eachDefaultSystem defaultSystems;

    nixpkgsFor = lib.genAttrs defaultSystems (system:
      import nixpkgs {
        inherit system;
      });
  in
    eachDefaultSystem (system: let
      pkgs = nixpkgsFor.${system};
    in {
      devShell = pkgs.mkShell {
        buildInputs = with pkgs; [
          clang
          cmake
          docker-compose
          gettext
          git
          glibc
          gnumake
          go
          golangci-lint
          krb5.dev
          krb5.out
          libclang
          libev
          libgcc
          libtool
          libunwind
          libuv
          libxml2
          libxslt
          lz4
          nodejs_24
          openssl
          pkg-config
          postgresql
          postgresql.pg_config
          python313
          sccache
          uv
          xmlsec
          zlib
        ];
      };
    });
}
