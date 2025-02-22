{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    systems.url = "github:nix-systems/default";
  };

  outputs =
    { systems, nixpkgs, ... }:
    let
      eachSystem = f: nixpkgs.lib.genAttrs (import systems) (system: f nixpkgs.legacyPackages.${system});
    in
    {
      devShells = eachSystem (pkgs: {
        default = pkgs.mkShell {
          packages = [
            (pkgs.python3.withPackages (python-pkgs: [
              python-pkgs.fastapi
              python-pkgs.python-dotenv
              python-pkgs.pydantic
              python-pkgs.ruff
              python-pkgs.fastapi-cli
              python-pkgs.jinja2
              python-pkgs.httpx
              python-pkgs.requests
              python-pkgs.apscheduler
              python-pkgs.python-multipart
            ]))
            pkgs.vscode-langservers-extracted
          ];
        };
      });

      formatter = eachSystem (pkgs: pkgs.nixfmt-rfc-style);
    };
}
