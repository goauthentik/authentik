use clap::{Parser, Subcommand};
use miette::Result;

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
}

fn main() -> Result<()> {
    let cli = Cli::parse();

    match cli.command {
        Command::Server(args) => authentik_server::run(args),
    }
}
