use std::path::PathBuf;

use crate::recurse_directory;

pub fn r#move(old_path: PathBuf, new_path: PathBuf) {
    let is_dir = old_path.is_dir();
    if is_dir {
        let paths = recurse_directory(old_path.clone());
        for path in paths {
            let raw_path = path
                .strip_prefix(old_path.clone())
                .expect("path to be within old path");
            let new_path = new_path.join(raw_path);
            println!("{} -> {}", path.display(), new_path.display());
        }
    } else {
        println!(
            "{} -> {}",
            old_path.to_string_lossy(),
            new_path.to_string_lossy()
        );
    }
}
