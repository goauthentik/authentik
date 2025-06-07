use std::{fs, path::PathBuf};

use clap::{Parser, Subcommand};

mod generate;
mod links;
mod migrate;
mod migratefile;
mod r#move;
mod hackyfixes;

#[derive(Parser)]
struct Cli {
    #[arg(long, env, default_value = "./")]
    migrate_path: PathBuf,

    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    Move {
        old_path: PathBuf,
        new_path: PathBuf,
    },
    Migrate {
        #[arg(long, name = "FILE", default_value = "./migratefile")]
        migratefile: PathBuf,

        #[arg(short, long)]
        quiet: bool,
    },
    Unmigrate {
        #[arg(long, name = "FILE", default_value = "./migratefile")]
        migratefile: PathBuf,

        #[arg(short, long)]
        quiet: bool,
    },
    Generate {
        #[arg(long, name = "FILE")]
        migratefile: Option<PathBuf>,
    },
}

fn main() {
    let _ = dotenv::from_filename("./docsmg.env");
    let cli = Cli::parse();

    match cli.command {
        Commands::Move { old_path, new_path } => r#move::r#move(old_path, new_path),
        Commands::Migrate { migratefile, quiet } => {
            migrate::migrate(quiet, migratefile, cli.migrate_path)
        }
        Commands::Unmigrate { migratefile, quiet } => {
            migrate::unmigrate(quiet, migratefile, cli.migrate_path)
        }
        Commands::Generate { migratefile } => generate::generate(migratefile, cli.migrate_path),
    }
}

fn recurse_directory(path: PathBuf) -> Vec<PathBuf> {
    let paths = fs::read_dir(path).expect("path to exist");
    let mut final_paths = vec![];
    for path in paths {
        match path {
            Ok(path) => {
                if !path.path().is_file() && !path.path().is_dir() {
                    continue;
                } // dont go any further if not a file or directory
                let is_dir = path.path().is_dir();
                let path = path.path();

                if is_dir {
                    let mut paths = recurse_directory(path);
                    final_paths.append(&mut paths);
                } else {
                    final_paths.push(path);
                }
            }
            _ => {}
        }
    }
    final_paths
}
