use std::path::Path;

use crate::recurse_directory;

pub(crate) fn r#move(old_path: &Path, new_path: &Path) {
    let is_dir = old_path.is_dir();
    if is_dir {
        let paths = recurse_directory(old_path);
        for path in paths {
            let raw_path = path
                .strip_prefix(old_path)
                .expect("path to be within old path");
            let new_path = new_path.join(raw_path);
            eprintln!("{} -> {}", path.display(), new_path.display());
        }
    } else {
        eprintln!(
            "{} -> {}",
            old_path.to_string_lossy(),
            new_path.to_string_lossy()
        );
    }
}
