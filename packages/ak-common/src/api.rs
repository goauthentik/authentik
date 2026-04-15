//! Utilities for working with the authentik API client.

use ak_client::apis::configuration::Configuration;
use eyre::{Result, eyre};

use crate::{config, user_agent_outpost};

/// Return a [`Configuration`] object based on external environment variables.
pub fn make_config() -> Result<Configuration> {
    let ak_host = config::get()
        .host
        .clone()
        .ok_or_else(|| eyre!("environment variable `AUTHENTIK_HOST` not set"))?;
    let ak_token = config::get()
        .token
        .clone()
        .ok_or_else(|| eyre!("environment variable `AUTHENTIK_TOKEN` not set"))?;
    let ak_insecure = config::get().insecure.unwrap_or(false);

    let base_path = if ak_host.ends_with('/') {
        format!("{ak_host}api/v3")
    } else {
        format!("{ak_host}/api/v3")
    };

    let client = reqwest::ClientBuilder::new()
        .tls_danger_accept_invalid_hostnames(ak_insecure)
        .tls_danger_accept_invalid_certs(ak_insecure)
        .build()?;
    let client = reqwest_middleware::ClientBuilder::new(client).build();

    Ok(Configuration {
        base_path,
        client,
        bearer_access_token: Some(ak_token),
        user_agent: Some(user_agent_outpost()),
        ..Default::default()
    })
}
