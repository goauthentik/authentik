use std::time::Duration;

use ak_client::{
    apis::stages_api::{
        stages_authenticator_validate_list, stages_authenticator_validate_partial_update,
    },
    models::{
        DeviceClassesEnum, NotConfiguredActionEnum, PatchedAuthenticatorValidateStageRequest,
    },
};
use eyre::Result;
use thirtyfour::prelude::*;

use authentik_tests::{AuthentikStack, LoginOptions};
use tokio::time::sleep;

async fn login_sfe(&self) -> Result<()> {
    let flow_executor = self
        .driver
        .query(By::Id("flow-sfe-container"))
        .single()
        .await?;

    let identification_stage = flow_executor.query(By::Id("ident-form")).single().await?;

    let username_field = identification_stage
        .query(By::Css("input[name=uid_field]"))
        .single()
        .await?;
    username_field.click().await?;
    username_field.send_keys("akadmin").await?;
    username_field.send_keys(Key::Enter).await?;

    let password_stage = flow_executor
        .query(By::Id("password-form"))
        .single()
        .await?;
    let password_field = password_stage
        .query(By::Css("input[name=password]"))
        .single()
        .await?;
    password_field.click().await?;
    password_field.send_keys("akadmin").await?;
    password_field.send_keys(Key::Enter).await?;

    sleep(Duration::from_secs(1)).await;

    Ok(())
}

#[tokio::test(flavor = "multi_thread")]
async fn login_sfe() -> Result<()> {
    let stack = AuthentikStack::builder()
        .with_blueprint("default/flow-default-authentication-flow.yaml")
        .with_blueprint("default/flow-default-invalidation-flow.yaml")
        .with_selenium(true)
        .run()
        .await?;

    stack
        .goto("http://server:9000/if/flow/default-authentication-flow/?sfe=true")
        .await?;

    login_sfe(&stack).await?;

    stack
        .wait_for_url("http://server:9000/if/user/#/library")
        .await?;

    stack
        .assert_user("akadmin", "authentik Default Admin", "root@example.com")
        .await?;

    stack.quit().await
}

#[tokio::test(flavor = "multi_thread")]
async fn login_sfe_mfa_static_deny() -> Result<()> {
    let stack = AuthentikStack::builder()
        .with_blueprint("default/flow-default-authentication-flow.yaml")
        .with_blueprint("default/flow-default-invalidation-flow.yaml")
        .with_selenium(true)
        .run()
        .await?;

    let authenticator_validate_stages = stages_authenticator_validate_list(
        stack.api_config(),
        None,
        Some("default-authentication-mfa-validation"),
        None,
        None,
        None,
        None,
        None,
    )
    .await?;

    let authenticator_validate_stage = authenticator_validate_stages
        .results
        .first()
        .expect("no mfa validate stage found");

    stages_authenticator_validate_partial_update(
        stack.api_config(),
        &authenticator_validate_stage.pk.to_string(),
        Some(PatchedAuthenticatorValidateStageRequest {
            not_configured_action: Some(NotConfiguredActionEnum::Deny),
            device_classes: Some(vec![DeviceClassesEnum::Static]),
            ..Default::default()
        }),
    )
    .await?;

    stack
        .goto("http://server:9000/if/flow/default-authentication-flow/?sfe=true")
        .await?;

    login_sfe(&stack).await?;

    let msg = stack
        .driver()
        .query(By::Css("#access-denied > p"))
        .single()
        .await?;
    let msg_text = msg.text().await?;
    assert_eq!(msg_text, "No (allowed) MFA authenticator configured.");

    stack.quit().await
}
