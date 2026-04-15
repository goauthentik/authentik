//! Utilities for working with the authentik API client.

use ak_client::apis::configuration::Configuration;
use eyre::{Result, eyre};

use crate::{config, user_agent_outpost};

struct ServerConfig {
    host: String,
    token: String,
    insecure: bool,
}

impl ServerConfig {
    fn new() -> Result<Self> {
        let host = config::get()
            .host
            .clone()
            .ok_or_else(|| eyre!("environment variable `AUTHENTIK_HOST` not set"))?;
        let host = if host.ends_with('/') {
            host
        } else {
            format!("{host}/")
        };
        let token = config::get()
            .token
            .clone()
            .ok_or_else(|| eyre!("environment variable `AUTHENTIK_TOKEN` not set"))?;
        let insecure = config::get().insecure.unwrap_or(false);

        Ok(Self {
            host,
            token,
            insecure,
        })
    }
}

/// Return a [`Configuration`] object based on external environment variables.
pub fn make_config() -> Result<Configuration> {
    let server_config = ServerConfig::new()?;

    let base_path = format!("{}api/v3", server_config.host);

    let client = reqwest::ClientBuilder::new()
        .tls_danger_accept_invalid_hostnames(server_config.insecure)
        .tls_danger_accept_invalid_certs(server_config.insecure)
        .build()?;
    let client = reqwest_middleware::ClientBuilder::new(client).build();

    Ok(Configuration {
        base_path,
        client,
        bearer_access_token: Some(server_config.token),
        user_agent: Some(user_agent_outpost()),
        ..Default::default()
    })
}
