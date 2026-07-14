use std::path::{Path, PathBuf};

use crate::{migratefile::read_migrate_file_left_side, recurse_directory};

pub(crate) fn generate(migratefile: Option<&Path>, migrate_path: &Path) {
    // if there is a migrate file, read it and get the paths from the left side
    let paths: Vec<PathBuf> = match migratefile {
        Some(i) => read_migrate_file_left_side(i).unwrap_or_default(),
        None => {
            vec![]
        }
    };
    // get rid of paths already in the specified migrate file
    let paths: Vec<PathBuf> = recurse_directory(migrate_path)
        .iter()
        .filter_map(|x| x.strip_prefix(migrate_path).ok())
        .filter(|x| !paths.contains(&x.to_path_buf()))
        .map(|x| x.to_path_buf())
        .collect();

    for path in paths {
        eprintln!("{} ->", path.display());
    }
}
