use clap::{Parser, Subcommand};
use color_eyre::eyre::Result;

shadow_rs::shadow!(build);

#[derive(Parser)]
#[command(version, about, long_about = None)]
#[command(propagate_version = true)]
struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(Subcommand)]
enum Command {
    Server(authentik_server::Cli),
    Worker(authentik_worker::Cli),
}

fn main() -> Result<()> {
    color_eyre::install()?;
    let cli = Cli::parse();

    match cli.command {
        Command::Server(args) => authentik_server::run(args),
        Command::Worker(args) => authentik_worker::run(args),
    }
}
