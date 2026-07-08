use ak_client::{apis::flows_api::flows_instances_partial_update, models::PatchedFlowRequest};
use eyre::Result;

mod stack;
use stack::{AuthentikStack, Dom, LoginOptions};

#[tokio::test]
async fn login() -> Result<()> {
    let stack = AuthentikStack::builder()
        .wait_for_flow("default-authentication-flow")
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

#[tokio::test]
async fn login_compatibility_mode() -> Result<()> {
    let stack = AuthentikStack::builder()
        .wait_for_flow("default-authentication-flow")
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
