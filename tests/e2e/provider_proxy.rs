#![expect(
    clippy::tests_outside_test_module,
    reason = "e2e tests don't need a test module"
)]
#![expect(clippy::panic_in_result_fn, reason = "We need assert! in tests")]

use std::time::Duration;

use ak_client::{
    apis::{
        core_api::{core_applications_create, core_users_list, core_users_partial_update},
        flows_api::flows_instances_list,
        outposts_api::{outposts_instances_create, outposts_instances_default_settings_retrieve},
        providers_api::providers_proxy_create,
    },
    models::{
        ApplicationRequest, OutpostRequest, OutpostTypeEnum, PatchedUserRequest,
        ProxyProviderRequest,
    },
};
use base64::prelude::*;
use eyre::Result;
use thirtyfour::prelude::*;
use tokio::time::sleep;

use authentik_tests::{AuthentikStack, LoginOptions};
use jsonwebtoken::dangerous::insecure_decode;
use serde::Deserialize;

#[derive(Debug, Clone, Deserialize)]
struct ProxyClaims {
    sid: Option<String>,
    ak_proxy: Option<serde_json::Value>,
}

#[tokio::test(flavor = "multi_thread")]
async fn proxy_simple() -> Result<()> {
    let mut stack = AuthentikStack::builder()
        .with_blueprint("default/flow-default-authentication-flow.yaml")
        .with_blueprint("default/flow-default-invalidation-flow.yaml")
        .with_blueprint("default/flow-default-provider-authorization-implicit-consent.yaml")
        .with_blueprint("default/flow-default-provider-invalidation.yaml")
        .with_blueprint("system/providers-oauth2.yaml")
        .with_blueprint("system/providers-proxy.yaml")
        .with_selenium(true)
        .with_whoami(true)
        .run()
        .await?;

    let users = core_users_list(
        stack.api_config(),
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        Some("akadmin"),
        None,
    )
    .await?;
    let me = users.results.first().expect("unable to find akadmin");
    let mut attributes = me.attributes.clone().unwrap_or_default();
    let mut additional_headers = serde_json::Map::new();
    additional_headers.insert(
        "X-Foo".to_owned(),
        serde_json::Value::String("bar".to_owned()),
    );
    attributes.insert(
        "additionalHeaders".to_owned(),
        serde_json::Value::Object(additional_headers),
    );
    core_users_partial_update(
        stack.api_config(),
        me.pk,
        Some(PatchedUserRequest {
            attributes: Some(attributes),
            ..Default::default()
        }),
    )
    .await?;

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
            authorization_flow: authorization_flow.pk,
            invalidation_flow: invalidation_flow.pk,
            internal_host: Some("http://whoami".to_owned()),
            external_host: "http://proxy:9000".to_owned(),
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

    stack.start_outpost(&outpost).await?;

    stack.goto("http://proxy:9000/api").await?;

    stack.login(LoginOptions::default()).await?;

    let json = stack.parse_json_content().await?;
    let headers = &json["headers"];

    assert_eq!(
        headers["X-Authentik-Username"],
        serde_json::Value::Array(vec!["akadmin".into()])
    );
    assert_eq!(
        headers["X-Foo"],
        serde_json::Value::Array(vec!["bar".into()])
    );
    let jwt = headers["X-Authentik-Jwt"][0].clone();
    let serde_json::Value::String(jwt) = jwt else {
        panic!("No jwt found");
    };

    let jwt_header = insecure_decode::<ProxyClaims>(jwt)?;
    assert!(jwt_header.claims.sid.is_some());
    assert!(jwt_header.claims.ak_proxy.is_some());

    stack
        .goto("http://proxy:9000/outpost.goauthentik.io/sign_out")
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

    stack.quit().await
}

#[tokio::test(flavor = "multi_thread")]
async fn proxy_basic_auth() -> Result<()> {
    let mut stack = AuthentikStack::builder()
        .with_blueprint("default/flow-default-authentication-flow.yaml")
        .with_blueprint("default/flow-default-invalidation-flow.yaml")
        .with_blueprint("default/flow-default-provider-authorization-implicit-consent.yaml")
        .with_blueprint("default/flow-default-provider-invalidation.yaml")
        .with_blueprint("system/providers-oauth2.yaml")
        .with_blueprint("system/providers-proxy.yaml")
        .with_selenium(true)
        .with_whoami(true)
        .run()
        .await?;

    let users = core_users_list(
        stack.api_config(),
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        Some("akadmin"),
        None,
    )
    .await?;
    let me = users.results.first().expect("unable to find akadmin");
    let mut attributes = me.attributes.clone().unwrap_or_default();
    attributes.insert(
        "basic-username".to_owned(),
        serde_json::Value::String("akadmin-cred".to_owned()),
    );
    attributes.insert(
        "basic-password".to_owned(),
        serde_json::Value::String("akadmin-password".to_owned()),
    );
    core_users_partial_update(
        stack.api_config(),
        me.pk,
        Some(PatchedUserRequest {
            attributes: Some(attributes),
            ..Default::default()
        }),
    )
    .await?;
    let expected_base64_header = BASE64_STANDARD.encode("akadmin-cred:akadmin-password");

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
            authorization_flow: authorization_flow.pk,
            invalidation_flow: invalidation_flow.pk,
            internal_host: Some("http://whoami".to_owned()),
            external_host: "http://proxy:9000".to_owned(),
            basic_auth_enabled: Some(true),
            basic_auth_user_attribute: Some("basic-username".to_owned()),
            basic_auth_password_attribute: Some("basic-password".to_owned()),
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

    stack.start_outpost(&outpost).await?;

    stack.goto("http://proxy:9000/api").await?;

    stack.login(LoginOptions::default()).await?;

    let json = stack.parse_json_content().await?;
    let headers = &json["headers"];

    assert_eq!(
        headers["X-Authentik-Username"],
        serde_json::Value::Array(vec!["akadmin".into()])
    );
    assert_eq!(
        headers["Authorization"],
        serde_json::Value::Array(vec![format!("Basic {expected_base64_header}").into()])
    );

    stack
        .goto("http://proxy:9000/outpost.goauthentik.io/sign_out")
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

    stack.quit().await
}
