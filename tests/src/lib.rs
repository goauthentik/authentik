use regex::Regex;
use std::{env, time::Duration};

use ak_client::{
    apis::{configuration::Configuration, core_api::core_tokens_view_key_retrieve},
    models::Outpost,
};
use eyre::{Result, eyre};
use reqwest::{Method, StatusCode};
use serde_json::Value;
use testcontainers::{
    compose::DockerCompose,
    core::{ExecCommand, WaitFor, wait::HttpWaitStrategy},
};
use thirtyfour::prelude::*;
use tokio::{
    runtime::{Handle, RuntimeFlavor},
    task::block_in_place,
    time::{Instant, sleep},
};

#[derive(Default)]
pub struct AuthentikStackBuilder {
    blueprint_paths: Vec<String>,
    selenium: bool,
    mailpit: bool,
    whoami: bool,
}

impl AuthentikStackBuilder {
    #[must_use]
    pub fn with_blueprint(mut self, blueprint_path: &str) -> Self {
        self.blueprint_paths.push(blueprint_path.to_owned());
        self
    }

    #[must_use]
    pub fn with_selenium(mut self, selenium: bool) -> Self {
        self.selenium = selenium;
        self
    }

    #[must_use]
    pub fn with_mailpit(mut self, mailpit: bool) -> Self {
        self.mailpit = mailpit;
        self
    }

    #[must_use]
    pub fn with_whoami(mut self, whoami: bool) -> Self {
        self.whoami = whoami;
        self
    }

    #[expect(
        clippy::future_not_send,
        reason = "So this future cannot be sent between threads, but we don't care in tests."
    )]
    pub async fn run(self) -> Result<AuthentikStack> {
        assert_eq!(
            RuntimeFlavor::MultiThread,
            Handle::current().runtime_flavor()
        );

        let tag = {
            let branch_name = if let Ok(env_pr_branch) = env::var("GITHUB_HEAD_REF")
                && !env_pr_branch.is_empty()
            {
                env_pr_branch
            } else {
                env::var("GITHUB_REF").unwrap_or_else(|_| "main".to_owned())
            };
            let branch_name = branch_name.replace("refs/heads/", "");
            let branch_name = Regex::new("[^a-zA-Z0-9-]")
                .expect("regex")
                .replace_all(&branch_name, "-");

            format!("gh-{branch_name}")
        };

        let mut compose_profiles = Vec::with_capacity(3);

        let compose = {
            let mut compose = DockerCompose::with_local_client(&[concat!(
                env!("CARGO_MANIFEST_DIR"),
                "/src/compose.yml"
            )])
            .with_env("PG_PASS", "password")
            .with_env("AUTHENTIK_SECRET_KEY", "secret_key")
            .with_env("AUTHENTIK_TAG", &tag)
            .with_wait_for_service("worker", WaitFor::healthcheck())
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
pub enum Dom {
    #[default]
    Shadow,
    Shady,
}

#[derive(Default)]
pub struct LoginOptions {
    pub dom: Dom,
    pub skip_stages: Vec<String>,
}

pub struct AuthentikStack {
    compose_profiles: Vec<String>,
    compose: Option<DockerCompose>,
    driver: Option<WebDriver>,
    api_config: Configuration,
}

impl AuthentikStack {
    pub fn builder() -> AuthentikStackBuilder {
        AuthentikStackBuilder::default()
    }

    pub fn api_config(&self) -> &Configuration {
        &self.api_config
    }

    pub fn compose(&mut self) -> &mut DockerCompose {
        self.compose
            .as_mut()
            .expect("a docker compose instance to be present")
    }

    pub fn driver(&self) -> &WebDriver {
        self.driver
            .as_ref()
            .expect("with_selenium must be set to true to use the selenium driver")
    }

    pub async fn start_outpost(&mut self, outpost: &Outpost) -> Result<()> {
        self.compose_profiles.push(outpost.r#type.to_string());

        sleep(Duration::from_secs(3)).await;
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
                .with_env("COMPOSE_PROFILES", self.compose_profiles.join(","))
                .with_wait_for_service(outpost.r#type.to_string(), WaitFor::healthcheck()),
        );

        self.compose().up().await?;
        sleep(Duration::from_secs(3)).await;

        Ok(())
    }

    #[expect(
        clippy::future_not_send,
        reason = "So this future cannot be sent between threads, but we don't care in tests."
    )]
    pub async fn apply_blueprint(&mut self, blueprint_path: &str) -> Result<()> {
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
        eprintln!("::group::apply_blueprint logs - {blueprint_path} - stdout");
        let _ = tokio::io::copy(&mut res.stdout(), &mut tokio::io::stderr()).await;
        eprintln!("::endgroup::");
        eprintln!("::group::apply_blueprint logs - {blueprint_path} - stderr");
        let _ = tokio::io::copy(&mut res.stderr(), &mut tokio::io::stderr()).await;
        eprintln!("::endgroup::");
        if let Some(exit_code) = res.exit_code().await?
            && exit_code != 0
        {
            return Err(eyre!(
                "Apply blueprint {blueprint_path} failed with exit code {exit_code}"
            ));
        }
        Ok(())
    }

    pub async fn goto(&self, url: &str) -> Result<()> {
        self.driver().goto(url).await?;
        Ok(())
    }

    pub async fn wait_for_url(&self, url: &str) -> Result<()> {
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

    pub async fn get_shadow_root(
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

    pub async fn get_shady_dom(&self, selector: &str) -> Result<WebElement> {
        let start = Instant::now();
        loop {
            let res = self
                .driver()
                .execute(
                    "return document.__shady_native_querySelector(arguments[0])",
                    vec![Value::String(selector.to_owned())],
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

    pub async fn login(&self, options: LoginOptions) -> Result<()> {
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

    pub async fn parse_json_content(&self) -> Result<Value> {
        let body = self
            .driver()
            .query(By::Tag("pre"))
            .single()
            .await?
            .text()
            .await?;
        Ok(serde_json::from_str(&body)?)
    }

    pub async fn assert_user(&self, username: &str, name: &str, email: &str) -> Result<()> {
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

    pub async fn quit(&mut self) -> Result<()> {
        let driver = if let Some(driver) = self.driver.take() {
            driver.quit().await
        } else {
            Ok(())
        };
        let compose = if let Some(compose) = self.compose.take() {
            for service in compose.services() {
                if let Some(svc) = compose.service(service) {
                    eprintln!("::group::Container logs - {service} - stdout");
                    let _ = tokio::io::copy(&mut svc.stdout(false), &mut tokio::io::stderr()).await;
                    eprintln!("::endgroup::");
                    eprintln!("::group::Container logs - {service} - stderr");
                    let _ = tokio::io::copy(&mut svc.stderr(false), &mut tokio::io::stderr()).await;
                    eprintln!("::endgroup::");
                }
            }

            compose.down().await
        } else {
            Ok(())
        };

        compose?;
        driver?;

        Ok(())
    }
}

#[expect(clippy::missing_trait_methods, reason = "We don't use pin_drop")]
impl Drop for AuthentikStack {
    fn drop(&mut self) {
        let rt = Handle::current();
        if let Err(err) = block_in_place(move || rt.block_on(async { self.quit().await })) {
            eprintln!("Failed to cleanly shutdown stack: {err}");
        }
    }
}
