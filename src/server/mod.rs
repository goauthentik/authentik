use argh::FromArgs;
use eyre::Result;

use crate::arbiter::Tasks;

#[derive(Debug, Default, FromArgs, PartialEq)]
/// Run the authentik server.
#[argh(subcommand, name = "server")]
#[expect(
    clippy::empty_structs_with_brackets,
    reason = "argh doesn't support unit structs"
)]
pub struct Cli {}

pub fn run(_cli: Cli, _tasks: &mut Tasks) -> Result<()> {
    Ok(())
}
