use std::time::Duration;

use ak_client::apis::configuration::Configuration;
use eyre::Result;
use reqwest::{Method, StatusCode};
use serde_json::Value;
use testcontainers::{
    compose::DockerCompose,
    core::{WaitFor, wait::HttpWaitStrategy},
};
use thirtyfour::prelude::*;
use tokio::time::{Instant, sleep};

pub(crate) struct AuthentikStackBuilder {
    wait_for_flows: Vec<String>,
}

impl AuthentikStackBuilder {
    pub(crate) fn wait_for_flow(mut self, flow: &str) -> Self {
        self.wait_for_flows.push(flow.to_string());
        self
    }

    pub(crate) async fn run(self) -> Result<AuthentikStack> {
        let compose = {
            let mut compose = DockerCompose::with_local_client(&[concat!(
                env!("CARGO_MANIFEST_DIR"),
                "/tests/e2e/compose.yml"
            )])
            .with_env("PG_PASS", "password")
            .with_env("AUTHENTIK_SECRET_KEY", "secret_key")
            .with_env("AUTHENTIK_TAG", "gh-next");

            for flow in self.wait_for_flows {
                compose = compose.with_wait_for_service(
                    "server",
                    WaitFor::http(
                        HttpWaitStrategy::new(format!("/if/flow/{flow}/"))
                            .with_port(9000_u16.into())
                            .with_method(Method::GET)
                            .with_expected_status_code(StatusCode::OK),
                    ),
                )
            }

            compose.up().await?;

            compose
        };

        let driver = {
            let mut caps = DesiredCapabilities::chrome();
            caps.set_browser_log_level(thirtyfour::LoggingPrefsLogLevel::All)?;
            let driver_url = format!(
                "http://{}:{}",
                compose
                    .service("selenium")
                    .expect("a selenium to be started")
                    .get_host()
                    .await?,
                compose
                    .service("selenium")
                    .expect("a selenium to be started")
                    .get_host_port_ipv4(4444)
                    .await?,
            );
            WebDriver::new(driver_url, caps).await?
        };

        let api_config = {
            let mut api_config = Configuration::default();
            api_config.base_path = format!(
                "http://{}:{}/api/v3",
                compose
                    .service("server")
                    .expect("a server to be started")
                    .get_host()
                    .await?,
                compose
                    .service("server")
                    .expect("a server to be started")
                    .get_host_port_ipv4(9000)
                    .await?,
            );
            api_config.bearer_access_token = Some("akadmin".to_owned());
            api_config
        };

        Ok(AuthentikStack {
            compose,
            driver,
            api_config,
        })
    }
}

impl Default for AuthentikStackBuilder {
    fn default() -> Self {
        Self {
            wait_for_flows: vec![],
        }
    }
}

#[derive(Default)]
pub(crate) enum Dom {
    #[default]
    Shadow,
    Shady,
}

#[derive(Default)]
pub(crate) struct LoginOptions {
    pub(crate) dom: Dom,
    pub(crate) skip_stages: Vec<String>,
}

pub(crate) struct AuthentikStack {
    pub(crate) compose: DockerCompose,
    pub(crate) driver: WebDriver,
    api_config: Configuration,
}

impl AuthentikStack {
    pub(crate) fn builder() -> AuthentikStackBuilder {
        Default::default()
    }

    pub(crate) fn api_config(&self) -> &Configuration {
        &self.api_config
    }

    pub(crate) async fn goto(&self, url: &str) -> Result<()> {
        self.driver.goto(url).await?;
        Ok(())
    }

    pub(crate) async fn wait_for_url(&self, url: &str) -> Result<()> {
        let start = Instant::now();
        loop {
            if self.driver.current_url().await?.as_str() == url {
                return Ok(());
            }

            if start.elapsed() > Duration::from_secs(20) {
                return Err(WebDriverError::Timeout(format!("URL did not become {url}")).into());
            }

            sleep(Duration::from_millis(500)).await;
        }
    }

    pub(crate) async fn get_shadow_root(
        &self,
        selector: &str,
        container: Option<WebElement>,
    ) -> Result<WebElement> {
        if let Some(container) = container {
            Ok(container
                .query(By::Css(selector))
                .single()
                .await?
                .get_shadow_root()
                .await?)
        } else {
            Ok(self
                .driver
                .query(By::Css(selector))
                .single()
                .await?
                .get_shadow_root()
                .await?)
        }
    }

    pub(crate) async fn get_shady_dom(&self, selector: &str) -> Result<WebElement> {
        let start = Instant::now();
        loop {
            let res = self
                .driver
                .execute(
                    "return document.__shady_native_querySelector(arguments[0])",
                    vec![Value::String(selector.to_string())],
                )
                .await?;

            if !res.json().is_null() {
                return Ok(res.element()?);
            }

            if start.elapsed() > Duration::from_secs(20) {
                return Err(WebDriverError::Timeout(format!(
                    "shady element {selector} did not appear"
                ))
                .into());
            }

            sleep(Duration::from_millis(500)).await;
        }
    }

    pub(crate) async fn login(&self, options: LoginOptions) -> Result<()> {
        if !options
            .skip_stages
            .iter()
            .any(|s| s == "ak-stage-identification")
        {
            let username_field = match options.dom {
                Dom::Shadow => {
                    let flow_executor = self.get_shadow_root("ak-flow-executor", None).await?;
                    let identification_stage = self
                        .get_shadow_root("ak-stage-identification", Some(flow_executor))
                        .await?;
                    identification_stage
                        .query(By::Css("input[name=uidField]"))
                        .single()
                        .await?
                }
                Dom::Shady => self.get_shady_dom("input[name=uidField]").await?,
            };

            username_field.click().await?;
            username_field.send_keys("akadmin").await?;
            username_field.send_keys(Key::Enter).await?;
        }

        if !options.skip_stages.iter().any(|s| s == "ak-stage-password") {
            let password_field = match options.dom {
                Dom::Shadow => {
                    let flow_executor = self.get_shadow_root("ak-flow-executor", None).await?;
                    let password_stage = self
                        .get_shadow_root("ak-stage-password", Some(flow_executor))
                        .await?;
                    password_stage
                        .query(By::Css("input[name=password]"))
                        .single()
                        .await?
                }
                Dom::Shady => self.get_shady_dom("input[name=password]").await?,
            };

            password_field.click().await?;
            password_field.send_keys("akadmin").await?;
            password_field.send_keys(Key::Enter).await?;
        }

        sleep(Duration::from_secs(1)).await;

        Ok(())
    }

    pub(crate) async fn parse_json_content(&self) -> Result<Value> {
        let body = self
            .driver
            .query(By::Tag("pre"))
            .single()
            .await?
            .text()
            .await?;
        Ok(serde_json::from_str(&body)?)
    }

    pub(crate) async fn assert_user(&self, username: &str, name: &str, email: &str) -> Result<()> {
        self.goto("http://server:9000/api/v3/core/users/me/")
            .await?;
        self.wait_for_url("http://server:9000/api/v3/core/users/me/")
            .await?;

        let user_data = self.parse_json_content().await?;

        assert!(user_data.get("user").is_some());
        assert_eq!(user_data["user"]["username"], username);
        assert_eq!(user_data["user"]["name"], name);
        assert_eq!(user_data["user"]["email"], email);

        Ok(())
    }

    pub(crate) async fn quit(self) -> Result<()> {
        let AuthentikStack {
            compose, driver, ..
        } = self;

        let driver = driver.quit().await;
        let compose = compose.down().await;

        compose?;
        driver?;

        Ok(())
    }
}
