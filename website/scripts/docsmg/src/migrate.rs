use std::{
    collections::{HashMap, HashSet, VecDeque}, env::consts::OS, ffi::OsStr, fs::{create_dir_all, read_to_string, remove_file, write, File}, path::{Component, PathBuf}, process::Command
};

use colored::Colorize;
use regex::{Captures, Regex};

use crate::{hackyfixes::add_extra_dot_dot_to_expression_mdx, migratefile::read_migrate_file, recurse_directory, Cli};

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
    //shorten_all_external_links(migrate_path);
    add_extra_dot_dot_to_expression_mdx(migrate_path.clone());
    let _ = Command::new("sh")
        .arg("-c")
        .arg("find . -empty -type d -delete")
        .current_dir(migrate_path)
        .output();
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
    remove_redirects(successful_moves, migrate_path.clone());
    //shorten_all_external_links(migrate_path);
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

fn replace_links(migrate_path: PathBuf, moves: Vec<(PathBuf, PathBuf)>) {
    let files = recurse_directory(migrate_path.clone());
    let mut moved = HashSet::new();

    let mut absolute_moves = vec![];
    for r#move in &moves {
        let r#move = (
            migrate_path.join(r#move.0.clone()),
            migrate_path.join(r#move.1.clone()),
        );
        let absolute_move_0 = r#move
            .0
            .canonicalize()
            .expect(&format!("{}", r#move.0.display()));

        let _ = create_dir_all(r#move.1.parent().unwrap());
        let tmp_file = File::create_new(&r#move.1);
        let absolute_move_1 = r#move.1.clone().canonicalize().expect(&format!(
            "{} {:?}",
            r#move.1.display(),
            tmp_file
        ));
        // delete file if it didnt already exist
        if let Ok(_) = tmp_file {
            let _ = remove_file(&r#move.1);
        };
        absolute_moves.push((absolute_move_0, absolute_move_1));
    }
    let absolute_moves = absolute_moves
        .iter()
        .map(|x| x.clone())
        .collect::<HashMap<PathBuf, PathBuf>>();

    for file in files {
        let absolute_file = file.canonicalize().unwrap();
        println!("{}", absolute_file.display());
        let mut contents = match read_to_string(file.clone()) {
            Ok(i) => i,
            Err(_) => continue,
        };

        // replace old absolute file with the new absolute file
        let old_absolute_file = absolute_file.clone();
        let absolute_file = match absolute_moves.get(&absolute_file) {
            Some(file) => {
                println!("    new file: {}", file.display());
                moved.insert(absolute_file);
                file.clone()
            }
            None => absolute_file.clone(),
        };

        // get all links in file and remove web links and link to self
        let re = Regex::new(r"\[(?<name>[\w \-\*'`]*)\]\((?<link>[\w\-\\/\\.#]*)\)").unwrap();
        let tmp_contents = contents.clone();
        let captures: Vec<Captures> = re
            .captures_iter(&tmp_contents)
            .filter(|x| {
                let link = &x["link"];

                !["http", "#", "/"]
                    .iter()
                    .fold(false, |acc, x| acc || link.starts_with(x))
            })
            .collect();
        println!("    captures: {}\n", captures.len());

        for capture in captures {
            let mut capture_log = String::new();
            let link = capture["link"].to_owned();
            let link_path;

            let link_postfix_index = link.find('#');

            let link_postfix = match link_postfix_index {
                Some(i) => {
                    let link_postfix = link[i..].to_owned();
                    link_path = link[..i].to_owned();
                    Some(link_postfix)
                }
                None => {
                    link_path = link.clone();
                    None
                },
            };

            let absolute_link = old_absolute_file.parent().unwrap().join(link_path.clone());
            //let _ = create_dir_all(absolute_link.parent().unwrap());
            //let tmp_file = File::create_new(&absolute_link);

            let absolute_link = match absolute_link
                .canonicalize()
                .or(absolute_link.with_extension("md").canonicalize())
                .or(absolute_link.with_extension("mdx").canonicalize())
            {
                Ok(link) => link,
                _ => {
                    println!(
                        "    {}: {} -> {}",
                        "failed".red(),
                        absolute_file.to_string_lossy().to_string().red(),
                        absolute_link.to_string_lossy().to_string().red()
                    );
                    continue;
                }
            };
            let absolute_link = if absolute_link.is_file() {
                absolute_link
            } else if absolute_link.join("index.md").is_file() {
                absolute_link.join("index.md")
            } else if absolute_link.join("index.mdx").is_file() {
                absolute_link.join("index.mdx")
            } else {
                println!(
                    "    {}: {} -> {}",
                    "failed".red(),
                    absolute_file.to_string_lossy().to_string().red(),
                    absolute_link.to_string_lossy().to_string().red()
                );
                continue;
            };
            // delete file if it didnt already exist
            //if let Ok(_) = tmp_file {
            //    let _ = remove_file(&absolute_link);
            //};
            capture_log.push_str(&format!("    oldalink: {}\n", absolute_link.display()));

            // replace old absolute link with the new absolute link
            let absolute_link = match absolute_moves.get(&absolute_link) {
                Some(link) => link.clone(),
                None => absolute_link.clone(),
            };

            capture_log.push_str(&format!("    newalink: {}\n", absolute_link.display()));

            // create tmp absolutes and make them into components
            let tmp_absolute_file = absolute_file.clone();
            let mut tmp_absolute_file = tmp_absolute_file.components().collect::<VecDeque<_>>();
            let tmp_absolute_link = absolute_link.clone();
            let mut tmp_absolute_link = tmp_absolute_link.components().collect::<VecDeque<_>>();
            // remove the shared path components
            loop {
                if tmp_absolute_file.front() != tmp_absolute_link.front()
                    || tmp_absolute_file.front() == None
                {
                    break;
                }
                tmp_absolute_file.pop_front();
                tmp_absolute_link.pop_front();
            }
            capture_log.push_str(&format!(
                "    shrtfile: {}\n",
                tmp_absolute_file.iter().collect::<PathBuf>().display()
            ));
            capture_log.push_str(&format!(
                "    shrtlink: {}\n",
                tmp_absolute_link.iter().collect::<PathBuf>().display()
            ));

            if tmp_absolute_file.len() <= 0 {
                println!(
                    "    {}: {} -> {}",
                    "failed".red(),
                    absolute_file.to_string_lossy().to_string().red(),
                    absolute_link.to_string_lossy().to_string().red()
                );
                continue;
            }
            let escapes = (0..tmp_absolute_file.len() - 1)
                .map(|_| Component::Normal("..".as_ref()))
                .collect::<PathBuf>();

            let new_link = escapes.join(tmp_absolute_link.iter().collect::<PathBuf>());
            // add a . to the begining if it doesnt already start with . or ..
            let new_link = match new_link
                .components()
                .collect::<Vec<_>>()
                .first()
                .iter()
                .collect::<PathBuf>()
                .to_str()
            {
                Some(".") => new_link,
                Some("..") => new_link,
                _ => PathBuf::from(".").join(new_link),
            };
            let mut new_link = new_link.to_string_lossy().to_string();
            match link_postfix {
                Some(i) => new_link.push_str(&i),
                None => {}
            }
            capture_log.push_str(&format!("    old link: {}\n", link));
            capture_log.push_str(&format!("    new link: {}\n", new_link));
            print!("{}", capture_log);
            //println!("{} {} {}", absolute_file.display(), absolute_link.display(), new_link.display());
            let tmp_contents = contents.replace(&format!("({})", link), &format!("({})", new_link));
            if tmp_contents == contents {
                println!("{}", "    nothing replaced".yellow());
            } else {
                contents = tmp_contents;
            };
            println!("");
        }

        write(file, contents).unwrap();
    }
}

fn fix_internal_links_in_file(migrate_path: PathBuf, move_from: PathBuf, move_to: PathBuf) {
    let move_from = migrate_path.join(move_from);
    let move_to = migrate_path.join(move_to);
    let contents = read_to_string(&move_from);
    let mut contents = match contents {
        Ok(ok) => ok,
        Err(_) => return,
    };
    let re = Regex::new(r"\[(?<name>.*)\]\((?<link>.*)\)").unwrap();
    let captures: Vec<Captures> = re.captures_iter(&contents).collect();
    let mut changes = vec![];
    for capture in captures {
        //let name = &capture["name"];
        let link = &capture["link"];
        if link.starts_with('#') || link.starts_with("http") {
            continue;
        }
        let link = PathBuf::from(link);
        //println!("{} {}", move_from.display(), link.display());
        let absolute_link = move_from
            .parent()
            .unwrap()
            .canonicalize()
            .unwrap()
            .join(&link);
        if move_to.components().collect::<Vec<_>>().len() > 1 {
            let _ = create_dir_all(move_to.parent().unwrap());
        }
        let tmp_file = File::create_new(move_to.clone());
        //println!("{} {} {} {}", name, link.display(), absolute_link.display(), make_path_relative(absolute_link.clone(), move_to.canonicalize().unwrap().clone()).display());
        let new_link = make_path_relative(
            absolute_link.clone(),
            move_to.canonicalize().unwrap().clone(),
        );
        if let Ok(_) = tmp_file {
            remove_file(move_to.clone()).unwrap()
        };
        changes.push((link.clone(), new_link.clone()));
    }
    for i in changes {
        contents = contents.replace(
            &format!("({})", i.0.display()),
            &format!("({})", i.1.display()),
        );
    }
    write(move_from, contents).unwrap();
}

fn make_path_relative(path: PathBuf, relative_to: PathBuf) -> PathBuf {
    let mut subdirs = 0;
    let path_components = path.components().collect::<Vec<_>>();
    let relative_to_components = relative_to.components().collect::<Vec<_>>();
    loop {
        if path_components.len() <= subdirs {
            break;
        } else if path_components[subdirs] != relative_to_components[subdirs] {
            break;
        }
        subdirs += 1;
    }
    let new_path = &path_components[subdirs..].iter().collect::<PathBuf>();
    let backouts = (0..relative_to_components.len() - subdirs - 1)
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

    let new_path = if new_path.file_name() == Some(OsStr::new("index.md"))
        || new_path.file_name() == Some(OsStr::new("index.mdx"))
    {
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
