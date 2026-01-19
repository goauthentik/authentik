use argh::FromArgs;
use authentik_config::{Config, get_config};
use eyre::Result;

#[derive(Debug, FromArgs, PartialEq)]
/// The authentication glue you need
struct Cli {
    #[argh(subcommand)]
    command: Command,
}

#[derive(Debug, FromArgs, PartialEq)]
#[argh(subcommand)]
enum Command {
    Server(authentik_server::Cli),
    Worker(authentik_worker::Cli),
}

fn install_tracing() {}

fn main() -> Result<()> {
    color_eyre::install()?;
    Config::setup()?;
    let cli: Cli = argh::from_env();

    match cli.command {
        Command::Server(args) => authentik_server::run(args),
        Command::Worker(args) => authentik_worker::run(args),
    }
}
