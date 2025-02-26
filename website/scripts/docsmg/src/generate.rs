use std::path::PathBuf;

use crate::{migratefile::read_migrate_file_left_side, recurse_directory};

pub fn generate(migratefile: Option<PathBuf>, migrate_path: PathBuf) {
    // if there is a migrate file, read it and get the paths from the left side
    let paths: Vec<PathBuf> = match migratefile {
        Some(i) => {
            let contents = read_migrate_file_left_side(i);
            if let Ok(contents) = contents {
                contents
            } else {
                vec![]
            }
        }
        None => {
            vec![]
        }
    };
    // get rid of paths already in the specified migrate file
    let paths: Vec<PathBuf> = recurse_directory(migrate_path.clone())
        .iter()
        .filter_map(|x| x.strip_prefix(migrate_path.clone()).ok())
        .filter(|x| !paths.contains(&x.to_path_buf()))
        .map(|x| x.to_path_buf())
        .collect();

    for path in paths {
        println!("{} ->", path.display());
    }
}
