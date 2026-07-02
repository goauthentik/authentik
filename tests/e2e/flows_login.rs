use std::time::Duration;

use eyre::Result;
use reqwest::{Method, StatusCode};
use testcontainers::{
    compose::DockerCompose,
    core::{WaitFor, wait::HttpWaitStrategy},
};
use thirtyfour::prelude::*;
use tokio::time::Instant;

async fn wait_for_url(
    driver: &WebDriver,
    target: &str,
    timeout: Duration,
    poll: Duration,
) -> WebDriverResult<()> {
    let start = Instant::now();
    loop {
        if driver.current_url().await?.as_str() == target {
            return Ok(());
        }

        if start.elapsed() > timeout {
            return Err(WebDriverError::Timeout(format!(
                "URL did not become {target}"
            )));
        }

        tokio::time::sleep(poll).await;
    }
}

#[tokio::test]
async fn trying_stuff_out() -> Result<()> {
    let mut compose = DockerCompose::with_local_client(&[concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/tests/e2e/compose.authentik.yml"
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

    dbg!(&compose);

    compose.up().await?;

    dbg!(&compose);

    let caps = DesiredCapabilities::chrome();
    let driver_url = format!(
        "http://{}:{}",
        compose
            .service("selenium")
            .expect("selenium")
            .get_host()
            .await?,
        compose
            .service("selenium")
            .expect("selenium")
            .get_host_port_ipv4(4444)
            .await?,
    );
    dbg!(&driver_url);
    let driver = WebDriver::new(driver_url, caps).await?;

    let url = format!(
        "http://{}:{}/if/flow/default-authentication-flow/",
        // compose
        //     .service("server")
        //     .expect("server")
        //     .get_host()
        //     .await?,
        // compose
        //     .service("server")
        //     .expect("server")
        //     .get_host_port_ipv4(9000)
        //     .await?
        "server",
        "9000",
    );

    dbg!(&url);

    driver.goto(url).await?;

    dbg!("we're there");

    let flow_executor = driver.query(By::Css("ak-flow-executor")).single().await?;
    dbg!(&flow_executor);

    let identification_stage = flow_executor
        .get_shadow_root()
        .await?
        .query(By::Css("ak-stage-identification"))
        .single()
        .await?;
    dbg!(&identification_stage);

    let username_field = identification_stage
        .get_shadow_root()
        .await?
        .query(By::Css("input[name=uidField]"))
        .single()
        .await?;
    dbg!(&username_field);

    username_field.click().await?;
    username_field.send_keys("akadmin").await?;
    username_field.send_keys(Key::Enter).await?;

    let flow_executor = driver.query(By::Css("ak-flow-executor")).single().await?;
    dbg!(&flow_executor);

    let password_stage = flow_executor
        .get_shadow_root()
        .await?
        .query(By::Css("ak-stage-password"))
        .single()
        .await?;
    dbg!(&password_stage);

    let password_field = password_stage
        .get_shadow_root()
        .await?
        .query(By::Css("input[name=password]"))
        .single()
        .await?;
    dbg!(&password_field);

    password_field.click().await?;
    password_field.send_keys("akadmin").await?;
    password_field.send_keys(Key::Enter).await?;

    tokio::time::sleep(Duration::from_secs(1)).await;

    wait_for_url(
        &driver,
        "http://server:9000/if/user/#/library",
        Duration::from_secs(20),
        Duration::from_millis(500),
    )
    .await?;

    driver.quit().await?;

    Ok(())
}
