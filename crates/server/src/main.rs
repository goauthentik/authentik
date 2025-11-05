use authentik_server::{Cli, run};
use clap::Parser;
use miette::Result;

fn main() -> Result<()> {
    let cli = Cli::parse();
    run(cli)
}
