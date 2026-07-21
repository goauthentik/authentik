#![expect(clippy::tests_outside_test_module, reason = "we don't care here")]

use std::time::Duration;

use ak_client::{
    apis::{
        core_api::core_applications_create,
        flows_api::flows_instances_list,
        outposts_api::{outposts_instances_create, outposts_instances_default_settings_retrieve},
        providers_api::providers_proxy_create,
    },
    models::{
        ApplicationRequest, OutpostRequest, OutpostTypeEnum, ProxyMode, ProxyProviderRequest,
    },
};
use authentik_tests::{AuthentikStack, ComposeProfile, LoginOptions};
use eyre::Result;
use thirtyfour::prelude::*;
use tokio::time::sleep;

async fn prepare(stack: &mut AuthentikStack, mode: ProxyMode, external_host: &str) -> Result<()> {
    let authorization_flows = flows_instances_list(
        stack.api_config(),
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        Some("default-provider-authorization-implicit-consent"),
    )
    .await?;
    let authorization_flow = authorization_flows
        .results
        .first()
        .expect("unable to find authorization flow");
    let invalidation_flows = flows_instances_list(
        stack.api_config(),
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        Some("default-provider-invalidation-flow"),
    )
    .await?;
    let invalidation_flow = invalidation_flows
        .results
        .first()
        .expect("unable to find invalidation flow");

    let provider = providers_proxy_create(
        stack.api_config(),
        ProxyProviderRequest {
            name: "test".to_owned(),
            mode: Some(mode),
            authorization_flow: authorization_flow.pk,
            invalidation_flow: invalidation_flow.pk,
            internal_host: Some("http://whoami".to_owned()),
            external_host: format!("http://{external_host}"),
            ..Default::default()
        },
    )
    .await?;
    core_applications_create(
        stack.api_config(),
        ApplicationRequest {
            name: "test".to_owned(),
            slug: "test".to_owned(),
            provider: Some(Some(provider.pk)),
            ..Default::default()
        },
    )
    .await?;

    let outpost_config = {
        let mut config = outposts_instances_default_settings_retrieve(stack.api_config())
            .await?
            .config;
        config.insert(
            "authentik_host".to_owned(),
            serde_json::Value::String("http://server:9000".to_owned()),
        );
        config.insert(
            "log_level".to_owned(),
            serde_json::Value::String("debug".to_owned()),
        );
        config
    };

    let outpost = outposts_instances_create(
        stack.api_config(),
        OutpostRequest {
            name: "test".to_owned(),
            r#type: OutpostTypeEnum::Proxy,
            providers: vec![provider.pk],
            config: outpost_config,
            ..Default::default()
        },
    )
    .await?;

    stack.start_outpost(&outpost).await
}

async fn test_single(stack: &AuthentikStack, external_host: &str) -> Result<()> {
    stack.goto(&format!("http://{external_host}/api")).await?;
    sleep(Duration::from_secs(2)).await;
    stack.login(LoginOptions::default()).await?;

    let json = stack.parse_json_content().await?;
    let headers = &json["headers"];

    assert_eq!(
        headers["X-Authentik-Username"],
        serde_json::Value::Array(vec![stack.akadmin_username().into()])
    );

    stack
        .goto(&format!(
            "http://{external_host}/outpost.goauthentik.io/sign_out"
        ))
        .await?;
    sleep(Duration::from_secs(2)).await;

    let flow_executor = stack.get_shadow_root("ak-flow-executor", None).await?;
    let session_end_stage = stack
        .get_shadow_root("ak-stage-session-end", Some(flow_executor))
        .await?;
    let flow_card = stack
        .get_shadow_root("ak-flow-card", Some(session_end_stage))
        .await?;
    let title = flow_card
        .query(By::Css(".pf-c-title.pf-m-3xl"))
        .single()
        .await?
        .text()
        .await?;

    assert!(title.contains("You've logged out of"));

    Ok(())
}

#[tokio::test(flavor = "multi_thread")]
async fn caddy_single() -> Result<()> {
    let mut stack = AuthentikStack::builder()
        .with_blueprint("default/flow-default-authentication-flow.yaml")
        .with_blueprint("default/flow-default-invalidation-flow.yaml")
        .with_blueprint("default/flow-default-provider-authorization-implicit-consent.yaml")
        .with_blueprint("default/flow-default-provider-invalidation.yaml")
        .with_blueprint("system/providers-oauth2.yaml")
        .with_blueprint("system/providers-proxy.yaml")
        .with_profile(ComposeProfile::Selenium)?
        .with_profile(ComposeProfile::Whoami)?
        .with_profile(ComposeProfile::CaddySingle)?
        .run()
        .await?;

    let external_host = "caddy-single";

    prepare(&mut stack, ProxyMode::ForwardSingle, external_host).await?;

    test_single(&stack, external_host).await?;

    stack.quit().await
}

#[tokio::test(flavor = "multi_thread")]
async fn envoy_single() -> Result<()> {
    let mut stack = AuthentikStack::builder()
        .with_blueprint("default/flow-default-authentication-flow.yaml")
        .with_blueprint("default/flow-default-invalidation-flow.yaml")
        .with_blueprint("default/flow-default-provider-authorization-implicit-consent.yaml")
        .with_blueprint("default/flow-default-provider-invalidation.yaml")
        .with_blueprint("system/providers-oauth2.yaml")
        .with_blueprint("system/providers-proxy.yaml")
        .with_profile(ComposeProfile::Selenium)?
        .with_profile(ComposeProfile::Whoami)?
        .with_profile(ComposeProfile::EnvoySingle)?
        .run()
        .await?;

    let external_host = "envoy-single";

    prepare(&mut stack, ProxyMode::ForwardSingle, external_host).await?;

    test_single(&stack, external_host).await?;

    stack.quit().await
}

#[tokio::test(flavor = "multi_thread")]
async fn nginx_single() -> Result<()> {
    let mut stack = AuthentikStack::builder()
        .with_blueprint("default/flow-default-authentication-flow.yaml")
        .with_blueprint("default/flow-default-invalidation-flow.yaml")
        .with_blueprint("default/flow-default-provider-authorization-implicit-consent.yaml")
        .with_blueprint("default/flow-default-provider-invalidation.yaml")
        .with_blueprint("system/providers-oauth2.yaml")
        .with_blueprint("system/providers-proxy.yaml")
        .with_profile(ComposeProfile::Selenium)?
        .with_profile(ComposeProfile::Whoami)?
        .with_profile(ComposeProfile::NginxSingle)?
        .run()
        .await?;

    let external_host = "nginx-single";

    prepare(&mut stack, ProxyMode::ForwardSingle, external_host).await?;

    test_single(&stack, external_host).await?;

    stack.quit().await
}

#[tokio::test(flavor = "multi_thread")]
async fn traefik_single() -> Result<()> {
    let mut stack = AuthentikStack::builder()
        .with_blueprint("default/flow-default-authentication-flow.yaml")
        .with_blueprint("default/flow-default-invalidation-flow.yaml")
        .with_blueprint("default/flow-default-provider-authorization-implicit-consent.yaml")
        .with_blueprint("default/flow-default-provider-invalidation.yaml")
        .with_blueprint("system/providers-oauth2.yaml")
        .with_blueprint("system/providers-proxy.yaml")
        .with_profile(ComposeProfile::Selenium)?
        .with_profile(ComposeProfile::Whoami)?
        .with_profile(ComposeProfile::TraefikSingle)?
        .run()
        .await?;

    let external_host = "traefik-single";

    prepare(&mut stack, ProxyMode::ForwardSingle, external_host).await?;

    test_single(&stack, external_host).await?;

    stack.quit().await
}
