use std::{fs::read_to_string, path::PathBuf};

use eyre::Result;

pub(crate) fn read_migrate_file(file: PathBuf) -> Result<Vec<(PathBuf, PathBuf)>> {
    let contents = read_to_string(file)?;
    let lines: Vec<String> = contents
        .split('\n')
        .map(|x| x.to_owned())
        .filter(|x| !x.is_empty())
        .collect();
    let migrations = lines
        .iter()
        .filter_map(|x| x.split_once(" -> "))
        .filter(|x| x.0 != x.1)
        .map(|x| {
            (
                x.0.parse().expect("a valid path"),
                x.1.parse().expect("a valid path"),
            )
        })
        .collect::<Vec<_>>();
    Ok(migrations)
}

pub(crate) fn read_migrate_file_left_side(file: PathBuf) -> Result<Vec<PathBuf>> {
    let contents = read_to_string(file)?;
    let lines: Vec<String> = contents
        .split('\n')
        .map(|x| x.to_owned())
        .filter(|x| !x.is_empty())
        .collect();
    let migrations = lines
        .iter()
        .map(|x| x.split(" -> ").collect::<Vec<&str>>()[0].into())
        .collect::<Vec<_>>();
    Ok(migrations)
}
