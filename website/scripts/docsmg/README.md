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
3. In the `/____` directory, create a file named `docsmg.env` with the entry of `MIGRATE_FILE=./docs`.

## Steps to use

1. Navigate to the `authentik/website` dir.
2. Generate a migratefile with `docsmg generate | sort  >> migratefile`.
   You can also just run `docsmg generate | sort` to see the output in the terminal, before writing it to a file.
3. Edit the `migratefile` to add the target directory paths for each entry.
   Find the files you want to move in `migratefile` and insert the path you want to move them to after the arrow; ex `path/to/move/from/file.md -> path/to/move/to/file.md` Note: make sure to put spaces on either side of the arrow or that line won't be recognized.
4. Once you have entered all the paths you want to move, migrate the files with `docsmg migrate`.
5. To revert the migration, use `docsmg unmigrate`; Note: DO NOT edit the migrate file in between steps 3 and 4.
6. Repeat steps 2-4 until you are satisfied with the result.
