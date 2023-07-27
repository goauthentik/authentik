{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    futils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, futils } @ inputs:
    let
      inherit (nixpkgs) lib;
      inherit (lib) recursiveUpdate;
      inherit (futils.lib) eachDefaultSystem defaultSystems;

      nixpkgsFor = lib.genAttrs defaultSystems (system: import nixpkgs {
        inherit system;
      });
    in
    (eachDefaultSystem (system:
      let
        pkgs = nixpkgsFor.${system};
      in
      {
        devShell = pkgs.mkShell {
          buildInputs = with pkgs; [
            docker-compose
            gcc
            git
            go
            gnumake
            krb5
            libkrb5
            nodejs_20
            openssl
            pkg-config
            poetry
            postgresql
            zlib
            python311
            xmlsec
            libxml2
            libtool
            libxslt
            yarn
            golangci-lint
            ruff
          ];
        };
      }
    ));
}
