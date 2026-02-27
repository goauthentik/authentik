use std::{fs::read_to_string, path::PathBuf};

use regex::{Captures, Regex};

use crate::recurse_directory;

#[expect(unused)]
pub(crate) fn shorten_all_external_links(migrate_path: PathBuf) {
    let files = recurse_directory(migrate_path.clone());
    let re = Regex::new(r"\[(?<name>.*)\]\((?<link>.*)\)").unwrap();
    for file in files {
        let file = migrate_path.join(file);
        let absolute_file = file.clone().canonicalize().unwrap();
        let contents = if let Ok(x) = read_to_string(file) {
            x
        } else {
            continue;
        };
        let captures: Vec<Captures> = re.captures_iter(&contents).collect();
        for capture in captures {
            let link = &capture["link"];
            let link = PathBuf::from(link);
            let absolute_link = absolute_file
                .clone()
                .parent()
                .unwrap()
                .join(link)
                .canonicalize()
                .unwrap();
            shorten_link_relative_to(absolute_link.clone(), absolute_file.clone());
        }
    }
}

fn shorten_link_relative_to(_link_to_shorten: PathBuf, _relative_to: PathBuf) {}
