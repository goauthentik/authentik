# Docsmg

## Steps to install

1. Verify that you have the latest version of rust installed
    - Install [rust](rustup.rs) or update rust to the latest version with `rustup update`
    - If installing rust from scratch, you may need to run `. $HOME/.cargo/env`
2. Install the cli tool with `cargo install --git https://github.com/goauthentik/authentik --bin docsmg`

## Steps to use

1. Navigate to the /website dir.
2. Generate a migratefile with `docsmg generate | sort  >> migratefile`.
3. Edit the `migratefile` to add the target directory paths for each entry.
   Find the files you want to move in `migratefile` and insert the path you want to move them to after the arrow; ex `path/to/move/from/file.md -> path/to/move/to/file.md` Note: make sure to put spaces on either side of the arrow or that line won't be recognized.
4. Once you have entered all the paths you want to move, migrate the files with `docsmg migrate`.
5. To revert the migration, use `docsmg unmigrate`; Note: DO NOT edit the migrate file in between steps 3 and 4.
6. Repeat steps 2-4 until you are satisfied with the result.
