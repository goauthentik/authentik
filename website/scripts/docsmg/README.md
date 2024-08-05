# Docsmg

This CLI tool is used to generate a mapping file (`migratefile`) that is then used by the tool to migrate `.md`, `.mdx`, and images file from their current structure into a new structure.

Use this migration tool to:

-   generate the mapping file with the current structure
-   read the completed (manual process to define target structure) and create the directories and move the files.
-   modify the internal, cross-reference links to point to new location
-   write to the `netlify.toml` file to add redirect entries for all migrated files.

## Steps to install

1. Verify that you have the latest version of rust installed
    - Install [rust](rustup.rs) or update rust to the latest version with `rustup update`
    - If installing rust from scratch, you may need to run `. $HOME/.cargo/env`
2. Install the cli tool with `cargo install --git https://github.com/goauthentik/authentik --bin docsmg`

## Steps to use

1. Generate a migratefile with `docsmg generate >> migratefile`
2. Find the files you want to move in `migratefile` and insert the path you want to move them to after the arrow; ex `path/to/move/from/file.md -> path/to/move/to/file.md` Note: make sure to put spaces on either side of the arrow or that line won't be recognized
3. Once you have entered all the paths you want to move, migrate the files with `docsmg migrate`
4. To revert the migration, use `docsmg unmigrate`; Note: DO NOT edit the migrate file inbetween steps 3 and 4
5. Repeat steps 2-4 until you are satified with the result

