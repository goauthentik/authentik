use authentik_worker::{Cli, run};
use clap::Parser;
use color_eyre::eyre::Result;

fn main() -> Result<()> {
    color_eyre::install()?;
    let cli = Cli::parse();
    run(cli)
}
