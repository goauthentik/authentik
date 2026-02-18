use std::{
    fs::{read_to_string, write},
    path::PathBuf,
};

use crate::recurse_directory;

pub(crate) fn add_extra_dot_dot_to_expression_mdx(migrate_path: PathBuf) {
    let binding = recurse_directory(migrate_path);
    let files = binding.iter().filter(|x| {
        if let Some(i) = x.file_name() {
            Some("expression.mdx") == i.to_str() || Some("expressions.md") == i.to_str()
        } else {
            false
        }
    });

    for file in files {
        let content = match read_to_string(file) {
            Ok(i) => i,
            _ => continue,
        };
        let _ = write(file, content.replace("../expressions", "../../expressions"));
    }
}
