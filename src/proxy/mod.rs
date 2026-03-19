use argh::FromArgs;
use axum::extract::Request;
use eyre::Result;

use crate::arbiter::{Arbiter, Tasks};

#[derive(Debug, FromArgs, PartialEq)]
/// Run the authentik proxy outpost.
#[argh(subcommand, name = "proxy")]
#[expect(
    clippy::empty_structs_with_brackets,
    reason = "argh doesn't support unit structs"
)]
pub(crate) struct Cli {}

pub(crate) mod tls {
    use std::sync::Arc;

    use rustls::{server::ClientHello, sign::CertifiedKey};

    #[derive(Debug)]
    pub(crate) struct CertResolver;

    impl CertResolver {
        #[expect(clippy::unused_self, reason = "still WIP")]
        pub(crate) fn resolve(&self, _client_hello: &ClientHello<'_>) -> Option<Arc<CertifiedKey>> {
            None
        }
    }
}

pub(crate) fn can_handle(_request: &Request) -> bool {
    false
}

pub(crate) async fn ignore_me(arbiter: Arbiter) -> Result<()> {
    arbiter.shutdown().await;
    Ok(())
}

pub(super) fn run(_cli: Cli, tasks: &mut Tasks) -> Result<()> {
    let arbiter = tasks.arbiter();
    tasks
        .build_task()
        .name(&format!("{}::ignore_me", module_path!(),))
        .spawn(ignore_me(arbiter))?;
    Ok(())
}
