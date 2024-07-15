---
title: Docs migration script
---

This repository contains the source code for the authentik Docs Migration Script.

## How to Run

- use branch
- run the script
- ?
- test
- ?

### Prerequisites

- ?
- git

## What does it do, and how does it work?

The script does the following:
- migrates all doc files and images from their old file path structure into their new structure
    - creates new directories (name read from the `migratefile.txt` TO column.)
    - files moved into new directories
    - internal links within each file are rewritten to use new location
    - tbd


### Setup

- tbd

### Run the Script

`docsmg migrate`

### Commands:

- `docsmg move`

    Examples:

    `docsmg move + <current path file name> <target path and file name>`

    or for moving all files within a folder, use:

    `docsmg move testing/testing2 newtesting/newtesting2/puthere >> migratefile`

- `docsmg migrate`

    This will read the the `migratefile.txt`, creates the dirs (gets the names from the `migratefile.txt` file), and then migrates the files.

- `docsmg unmigrate`

    This command will undo the most recent move.

#### Flags

Flags include

Use `-r` if we are keeping the exact same structure in any place, we can use this flag to move that specified dir to a new place while keeping the sub-structure exactly the same.

Using `-m` flag that allows tab-completion of the OLD file path.

Use `-q` flag with `docsmg migrate` to not show the successful lines but will show any failures.

### Steps:

1. tbw
    * sub-tbw
    * sub-tbq
2. tbw
3. tbw
4. tbw

## Verify the migration
