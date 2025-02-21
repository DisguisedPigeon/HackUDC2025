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
          buildInputs =
            with pkgs;
            (
              [
                nixd
                nil
                python313
                python313Packages.flask
              ]
              ++ lib.optional stdenv.isLinux inotify-tools
            );
        };
      });

      formatter = eachSystem (pkgs: pkgs.nixfmt-rfc-style);
    };
}
