use eyre::Result;
use reqwest::{Method, StatusCode};
use testcontainers::{
    compose::DockerCompose,
    core::{WaitFor, wait::HttpWaitStrategy},
};

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
            HttpWaitStrategy::new("/setup")
                .with_port(9000_u16.into())
                .with_method(Method::HEAD)
                .with_expected_status_code(StatusCode::OK),
        ),
    );

    dbg!(&compose);

    compose.up().await?;

    dbg!(&compose);

    assert_eq!(1, 1);

    Ok(())
}
