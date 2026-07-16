#![expect(clippy::tests_outside_test_module, reason = "we don't care here")]
use ak_client::{apis::flows_api::flows_instances_partial_update, models::PatchedFlowRequest};
use authentik_tests::{AuthentikStack, Dom, LoginOptions};
use eyre::Result;

#[tokio::test(flavor = "multi_thread")]
async fn login() -> Result<()> {
    let mut stack = AuthentikStack::builder()
        .with_blueprint("default/flow-default-authentication-flow.yaml")
        .with_blueprint("default/flow-default-invalidation-flow.yaml")
        .with_selenium(true)
        .run()
        .await?;

    stack
        .goto("http://server:9000/if/flow/default-authentication-flow/")
        .await?;

    stack.login(LoginOptions::default()).await?;

    stack
        .wait_for_url("http://server:9000/if/user/#/library")
        .await?;

    stack
        .assert_user("akadmin", "authentik Default Admin", "root@example.com")
        .await?;

    stack.quit().await
}

#[tokio::test(flavor = "multi_thread")]
async fn login_compatibility_mode() -> Result<()> {
    let mut stack = AuthentikStack::builder()
        .with_blueprint("default/flow-default-authentication-flow.yaml")
        .with_blueprint("default/flow-default-invalidation-flow.yaml")
        .with_selenium(true)
        .run()
        .await?;

    flows_instances_partial_update(
        stack.api_config(),
        "default-authentication-flow",
        Some(PatchedFlowRequest {
            compatibility_mode: Some(true),
            ..Default::default()
        }),
    )
    .await?;

    stack
        .goto("http://server:9000/if/flow/default-authentication-flow/")
        .await?;

    stack
        .login(LoginOptions {
            dom: Dom::Shady,
            ..Default::default()
        })
        .await?;

    stack
        .wait_for_url("http://server:9000/if/user/#/library")
        .await?;

    stack
        .assert_user("akadmin", "authentik Default Admin", "root@example.com")
        .await?;

    stack.quit().await
}
