//! Utilities for working with the authentik API client.

use ak_client::apis::configuration::Configuration;
use eyre::{Result, eyre};
use url::Url;

use crate::{config, user_agent_outpost};

pub struct ServerConfig {
    pub host: Url,
    pub token: String,
    pub insecure: bool,
}

impl ServerConfig {
    pub fn new() -> Result<Self> {
        let host = config::get()
            .host
            .clone()
            .ok_or_else(|| eyre!("environment variable `AUTHENTIK_HOST` not set"))?;
        let mut host: Url = host.parse()?;
        let token = config::get()
            .token
            .clone()
            .ok_or_else(|| eyre!("environment variable `AUTHENTIK_TOKEN` not set"))?;
        let insecure = config::get().insecure.unwrap_or(false);

        if !host.path().ends_with('/') {
            host.path_segments_mut()
                .map_err(|()| eyre!("URL cannot be a base"))?
                .push("");
        }

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

    let base_path = server_config.host.join("api/v3")?.into();

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

#[cfg(test)]
mod tests {
    use serde_json::json;

    use super::{ServerConfig, make_config};
    use crate::config;

    #[test]
    fn server_config_no_trailing_slash() {
        config::init().expect("failed to init config");
        config::set(json!({
            "host": "http://localhost:9000",
            "token": "token",
        }))
        .expect("failed to set config");

        let server_config = ServerConfig::new().expect("failed to create server config");

        assert_eq!(server_config.host.as_str(), "http://localhost:9000/");
    }

    #[test]
    fn server_config_with_trailing_slash() {
        config::init().expect("failed to init config");
        config::set(json!({
            "host": "http://localhost:9000/",
            "token": "token",
        }))
        .expect("failed to set config");

        let server_config = ServerConfig::new().expect("failed to create server config");

        assert_eq!(server_config.host.as_str(), "http://localhost:9000/");
    }

    #[test]
    fn server_config_with_path_no_trailing_slash() {
        config::init().expect("failed to init config");
        config::set(json!({
            "host": "http://localhost:9000/authentik",
            "token": "token",
        }))
        .expect("failed to set config");

        let server_config = ServerConfig::new().expect("failed to create server config");

        assert_eq!(
            server_config.host.as_str(),
            "http://localhost:9000/authentik/"
        );
    }

    #[test]
    fn server_config_with_path_and_trailing_slash() {
        config::init().expect("failed to init config");
        config::set(json!({
            "host": "http://localhost:9000/authentik/",
            "token": "token",
        }))
        .expect("failed to set config");

        let server_config = ServerConfig::new().expect("failed to create server config");

        assert_eq!(
            server_config.host.as_str(),
            "http://localhost:9000/authentik/"
        );
    }

    #[test]
    fn make_config_no_trailing_slash() {
        config::init().expect("failed to init config");
        config::set(json!({
            "host": "http://localhost:9000",
            "token": "token",
        }))
        .expect("failed to set config");

        let api_config = make_config().expect("failed to make config");

        assert_eq!(api_config.base_path, "http://localhost:9000/api/v3");
    }

    #[test]
    fn make_config_with_trailing_slash() {
        config::init().expect("failed to init config");
        config::set(json!({
            "host": "http://localhost:9000/",
            "token": "token",
        }))
        .expect("failed to set config");

        let api_config = make_config().expect("failed to make config");

        assert_eq!(api_config.base_path, "http://localhost:9000/api/v3");
    }

    #[test]
    fn make_config_with_path_no_trailing_slash() {
        config::init().expect("failed to init config");
        config::set(json!({
            "host": "http://localhost:9000/authentik",
            "token": "token",
        }))
        .expect("failed to set config");

        let api_config = make_config().expect("failed to make config");

        assert_eq!(
            api_config.base_path,
            "http://localhost:9000/authentik/api/v3"
        );
    }

    #[test]
    fn make_config_with_path_and_trailing_slash() {
        config::init().expect("failed to init config");
        config::set(json!({
            "host": "http://localhost:9000/authentik/",
            "token": "token",
        }))
        .expect("failed to set config");

        let api_config = make_config().expect("failed to make config");

        assert_eq!(
            api_config.base_path,
            "http://localhost:9000/authentik/api/v3"
        );
    }
}
