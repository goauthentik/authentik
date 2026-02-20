use argh::FromArgs;
use axum::extract::Request;

#[derive(Debug, FromArgs, PartialEq)]
/// Run the authentik proxy outpost.
#[argh(subcommand, name = "proxy")]
pub(crate) struct Cli {}

pub(crate) fn can_handle(_request: &Request) -> bool {
    false
}
