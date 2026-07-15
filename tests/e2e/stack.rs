#![expect(dead_code, reason = "Not every test uses every feature.")]
use std::time::Duration;

use ak_client::{
    apis::{configuration::Configuration, core_api::core_tokens_view_key_retrieve},
    models::Outpost,
};
use eyre::Result;
use reqwest::{Method, StatusCode};
use serde_json::Value;
use testcontainers::{
    compose::DockerCompose,
    core::{ExecCommand, WaitFor, wait::HttpWaitStrategy},
};
use thirtyfour::prelude::*;
use tokio::time::{Instant, sleep};

#[derive(Default)]
pub(crate) struct AuthentikStackBuilder {
    blueprint_paths: Vec<String>,
    selenium: bool,
    mailpit: bool,
    whoami: bool,
}

impl AuthentikStackBuilder {
    pub(crate) fn with_blueprint(mut self, blueprint_path: &str) -> Self {
        self.blueprint_paths.push(blueprint_path.to_owned());
        self
    }

    pub(crate) fn with_selenium(mut self, selenium: bool) -> Self {
        self.selenium = selenium;
        self
    }

    pub(crate) fn with_mailpit(mut self, mailpit: bool) -> Self {
        self.mailpit = mailpit;
        self
    }

    pub(crate) fn with_whoami(mut self, whoami: bool) -> Self {
        self.whoami = whoami;
        self
    }

    pub(crate) async fn run(self) -> Result<AuthentikStack> {
        let mut compose_profiles = Vec::with_capacity(3);

        let compose = {
            let mut compose = DockerCompose::with_local_client(&[concat!(
                env!("CARGO_MANIFEST_DIR"),
                "/tests/e2e/compose.yml"
            )])
            .with_env("PG_PASS", "password")
            .with_env("AUTHENTIK_SECRET_KEY", "secret_key")
            .with_env("AUTHENTIK_TAG", "gh-next")
            .with_wait_for_service(
                "server",
                WaitFor::http(
                    HttpWaitStrategy::new("/if/flow/default-authentication-flow/")
                        .with_port(9000_u16.into())
                        .with_method(Method::GET)
                        .with_expected_status_code(StatusCode::OK),
                ),
            );

            if self.selenium {
                compose_profiles.push("selenium".to_owned());
            }
            if self.mailpit {
                compose_profiles.push("mailpit".to_owned());
            }
            if self.whoami {
                compose_profiles.push("whoami".to_owned());
            }

            compose = compose.with_env("COMPOSE_PROFILES", compose_profiles.join(","));

            compose.up().await?;

            compose
        };

        let driver = if self.selenium {
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
            Some(WebDriver::new(driver_url, caps).await?)
        } else {
            None
        };

        let api_config = Configuration {
            base_path: format!(
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
            ),
            bearer_access_token: Some("akadmin".to_owned()),
            ..Default::default()
        };

        let mut stack = AuthentikStack {
            compose_profiles,
            compose: Some(compose),
            driver,
            api_config,
        };

        for blueprint_path in self.blueprint_paths {
            stack.apply_blueprint(&blueprint_path).await?;
        }

        sleep(Duration::from_secs(5)).await;

        Ok(stack)
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
    compose_profiles: Vec<String>,
    compose: Option<DockerCompose>,
    driver: Option<WebDriver>,
    api_config: Configuration,
}

impl AuthentikStack {
    pub(crate) fn builder() -> AuthentikStackBuilder {
        AuthentikStackBuilder::default()
    }

    pub(crate) fn api_config(&self) -> &Configuration {
        &self.api_config
    }

    pub(crate) fn compose(&mut self) -> &mut DockerCompose {
        self.compose
            .as_mut()
            .expect("a docker compose instance to be present")
    }

    pub(crate) fn driver(&self) -> &WebDriver {
        self.driver
            .as_ref()
            .expect("with_selenium must be set to true to use the selenium driver")
    }

    pub(crate) async fn start_outpost(&mut self, outpost: &Outpost) -> Result<()> {
        self.compose_profiles.push(outpost.r#type.to_string());

        let token =
            core_tokens_view_key_retrieve(self.api_config(), &outpost.token_identifier).await?;

        self.compose = Some(
            self.compose
                .take()
                .expect("compose")
                .with_env(
                    format!(
                        "AUTHENTIK_{}_TOKEN",
                        outpost.r#type.to_string().to_uppercase()
                    ),
                    token.key,
                )
                .with_env("COMPOSE_PROFILES", self.compose_profiles.join(",")),
        );

        self.compose().up().await?;

        Ok(())
    }

    pub(crate) async fn apply_blueprint(&mut self, blueprint_path: &str) -> Result<()> {
        let mut res = self
            .compose()
            .service("worker")
            .expect("a worker to be started")
            .exec(ExecCommand::new(&[
                "ak".to_owned(),
                "apply_blueprint".to_owned(),
                blueprint_path.to_owned(),
            ]))
            .await?;
        Ok(())
    }

    pub(crate) async fn goto(&self, url: &str) -> Result<()> {
        self.driver().goto(url).await?;
        Ok(())
    }

    pub(crate) async fn wait_for_url(&self, url: &str) -> Result<()> {
        let start = Instant::now();
        loop {
            if self.driver().current_url().await?.as_str() == url {
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
                .driver()
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
                .driver()
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
            .driver()
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
        let Self {
            compose, driver, ..
        } = self;

        let driver = if let Some(driver) = driver {
            driver.quit().await
        } else {
            Ok(())
        };
        let compose = if let Some(compose) = compose {
            compose.down().await
        } else {
            Ok(())
        };

        compose?;
        driver?;

        Ok(())
    }
}
