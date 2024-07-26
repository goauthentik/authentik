use std::{
    collections::HashMap, ffi::OsStr, fmt::format, fs::{read_to_string, write}, path::{Component, Path, PathBuf}
};

use colored::Colorize;
use lazy_static::lazy_static;

use crate::{migratefile::read_migrate_file, recurse_directory};

pub fn migrate(quiet: bool, migratefile: PathBuf, migrate_path: PathBuf) {
    if !quiet {
        println!("Reading migrate file");
    }
    let files = read_migrate_file(migratefile);

    let files = match files {
        Ok(i) => {
            if !quiet {
                println!("{}", "Success".green());
            }
            i
        }
        Err(_) => {
            println!("{}: Could not read migrate file", "Error".red());
            return;
        }
    };

    replace_links(migrate_path.clone(), files.clone());
    let successful_moves = move_files(quiet, migrate_path.clone(), files);
    add_redirects(successful_moves.clone(), migrate_path.clone());
}

pub fn unmigrate(quiet: bool, migratefile: PathBuf, migrate_path: PathBuf) {
    if !quiet {
        println!("Reading migrate file");
    }
    let files = read_migrate_file(migratefile);

    let files = match files {
        Ok(i) => {
            if !quiet {
                println!("{}", "Success".green());
            }
            i
        }
        Err(_) => {
            println!("{}: Could not read migrate file", "Error".red());
            return;
        }
    };

    let files: Vec<(PathBuf, PathBuf)> = files.iter().map(|x| (x.1.clone(), x.0.clone())).collect(); //switch files to reverse a migration
    replace_links(migrate_path.clone(), files.clone());
    let successful_moves = move_files(quiet, migrate_path.clone(), files);
    let successful_moves: Vec<(PathBuf, PathBuf)> = successful_moves
        .iter()
        .map(|x| (x.1.clone(), x.0.clone()))
        .collect(); //switch files to reverse a migration
    remove_redirects(successful_moves, migrate_path);
}

fn move_files(
    quiet: bool,
    migrate_path: PathBuf,
    files: Vec<(PathBuf, PathBuf)>,
) -> Vec<(PathBuf, PathBuf)> {
    let mut successful_moves = vec![];
    for file in files {
        if !quiet {
            print!("{} -> {} : ", file.0.display(), file.1.display());
        }
        let rename: anyhow::Result<()> = (|| {
            let old_file = migrate_path.join(&file.0);
            let new_file = migrate_path.join(&file.1);
            std::fs::create_dir_all(&new_file.parent().expect("files to have a parent"))?;
            std::fs::rename(&old_file, &new_file)?;
            Ok(())
        })();
        match rename {
            Ok(_) => {
                if !quiet {
                    println!("{}", "Success".green());
                }
                successful_moves.push(file);
            }
            Err(_) => println!(
                "{}: Could not move file {}",
                "Error".red(),
                file.0.display()
            ),
        };
    }
    successful_moves
}

fn replace_links(migrate_path: PathBuf, successful_moves: Vec<(PathBuf, PathBuf)>) {
    lazy_static! {
        static ref find_link: regex::Regex =
            regex::Regex::new(r"\[(?<a>.*)\]\((?<b>.*)\)").unwrap();
    }
    let files = recurse_directory(migrate_path.clone());

    for file in files {
        let relative_file = file.strip_prefix(migrate_path.clone()).unwrap().to_path_buf();
        let mut contents = match read_to_string(file.clone()) {
            Ok(i) => i,
            Err(_) => continue,
        };
        let mut replace = vec![];
        for successful_move in &successful_moves {
            if migrate_path.join(successful_move.0.clone()).canonicalize().unwrap() 
                == file.clone().canonicalize().unwrap() {
                continue;
            }
            let new_successful_move_from = make_path_relative(successful_move.0.clone(), relative_file.clone());
            let new_successful_move_to = make_path_relative(successful_move.1.clone(), relative_file.clone());
            replace.push((new_successful_move_from, new_successful_move_to));
        }
        for i in replace {
            println!("{} : {} -> {}", file.display(), i.0.display(), i.1.display());
            contents = contents.replace(&format!("({})", i.0.display()), &format!("({})", i.1.display()));
        }
        write(file, contents).unwrap();
    }
}

fn make_path_relative(path: PathBuf, relative_to: PathBuf) -> PathBuf {
    let mut subdirs = 0;
    let path_components = path.components().collect::<Vec<_>>();
    let relative_to_components = relative_to.components().collect::<Vec<_>>();
    loop {
        if path_components.len() <= subdirs {
            break;
        } else if path_components[subdirs]
            != relative_to_components[subdirs]
        {
            break;
        }
        subdirs += 1;
    }
    let new_path = &path_components[subdirs..]
        .iter()
        .collect::<PathBuf>();
    let backouts =
        (0..relative_to_components.len() - subdirs - 1)
            .map(|_| PathBuf::from(".."))
            .reduce(|acc, e| acc.join(e))
            .unwrap_or(PathBuf::from(""));
    //println!("{}, {}", relative_to_components.len() - subdirs - 1, backouts.display());
    let new_path = backouts.join(new_path);
    let new_path = if new_path
        .to_string_lossy()
        .to_string()
        .chars()
        .next()
        .unwrap()
        != '.'
    {
        PathBuf::from(".").join(new_path)
    } else {
        new_path
    };

    let new_path = if new_path.file_name() == Some(OsStr::new("index.md")) || new_path.file_name() == Some(OsStr::new("index.mdx")) {
        new_path.parent().unwrap().to_path_buf()
    } else {
        new_path
    };
        

    new_path
}

fn add_redirects(successful_moves: Vec<(PathBuf, PathBuf)>, migrate_path: PathBuf) {
    let redirects = generate_redirects(successful_moves);
    let netlify_path = migrate_path.parent().unwrap().join("netlify.toml");
    let mut netlify_contents = read_to_string(netlify_path.clone()).unwrap();
    for redirect in redirects {
        netlify_contents.push_str(&redirect);
    }
    std::fs::write(netlify_path, netlify_contents).unwrap();
}

fn remove_redirects(successful_moves: Vec<(PathBuf, PathBuf)>, migrate_path: PathBuf) {
    let redirects = generate_redirects(successful_moves);
    let netlify_path = migrate_path.parent().unwrap().join("netlify.toml");
    let mut netlify_contents = read_to_string(netlify_path.clone()).unwrap();
    for redirect in redirects {
        netlify_contents = netlify_contents.replace(&redirect, "");
    }
    std::fs::write(netlify_path, netlify_contents).unwrap();
}

fn generate_redirects(successful_moves: Vec<(PathBuf, PathBuf)>) -> Vec<String> {
    successful_moves
        .iter()
        .map(|x| {
            format!(
                "
[[redirects]]
  from = \"{}\"
  to = \"{}\"
  status = 301
  force = true
",
                x.0.display(),
                x.1.display()
            )
        })
        .collect()
}
