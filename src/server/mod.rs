use std::{env::temp_dir, path::PathBuf, sync::Arc, time::Duration};

use argh::FromArgs;
use axum::body::Body;
use eyre::Result;
use hyper_unix_socket::UnixSocketConnector;
use hyper_util::{client::legacy::Client, rt::TokioExecutor};

use crate::arbiter::Tasks;

#[derive(Debug, Default, FromArgs, PartialEq, Eq)]
/// Run the authentik server.
#[argh(subcommand, name = "server")]
#[expect(
    clippy::empty_structs_with_brackets,
    reason = "argh doesn't support unit structs"
)]
pub struct Cli {}

pub struct Server {
    pub(crate) metrics_client: Client<UnixSocketConnector<PathBuf>, Body>,
}

impl Server {
    fn new() -> Self {
        let metrics_client = Client::builder(TokioExecutor::new())
            .pool_idle_timeout(Duration::from_secs(60))
            .set_host(false)
            .build(UnixSocketConnector::new(
                temp_dir().join("authentik-server-metrics.sock"),
            ));

        Self { metrics_client }
    }
}

pub fn run(_cli: Cli, _tasks: &mut Tasks) -> Result<Arc<Server>> {
    let server = Arc::new(Server::new());
    Ok(server)
}
