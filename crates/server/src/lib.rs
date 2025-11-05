use clap::Parser;
use miette::Result;

shadow_rs::shadow!(build);

#[derive(Parser)]
#[command(version = build::CLAP_LONG_VERSION, about, long_about = None)]
pub struct Cli {}

pub fn run(_cli: Cli) -> Result<()> {
    Ok(())
}
