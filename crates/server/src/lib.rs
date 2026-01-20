use argh::FromArgs;
use eyre::Result;
use tracing::info;

#[derive(Debug, FromArgs, PartialEq)]
/// Run the authentik server.
#[argh(subcommand, name = "server")]
pub struct Cli {}

pub fn run(_cli: Cli) -> Result<()> {
    info!("from server");
    Ok(())
}
