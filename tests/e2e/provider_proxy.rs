#![expect(
    clippy::tests_outside_test_module,
    reason = "e2e tests don't need a test module"
)]

use std::time::Duration;

use ak_client::{
    apis::{
        core_api::{core_applications_create, core_users_list, core_users_partial_update},
        flows_api::flows_instances_list,
        outposts_api::outposts_instances_create,
        providers_api::providers_proxy_create,
    },
    models::{
        ApplicationRequest, OutpostRequest, OutpostTypeEnum, PatchedUserRequest,
        ProxyProviderRequest,
    },
};
use eyre::Result;

mod stack;
use stack::AuthentikStack;
use testcontainers::{GenericImage, ImageExt as _, runners::AsyncRunner as _};
use tokio::time::sleep;

#[tokio::test]
async fn proxy_simple() -> Result<()> {
    let mut stack = AuthentikStack::builder()
        .with_blueprint("default/flow-authentication-flow.yaml")
        .with_blueprint("default/flow-default-invalidation-flow.yaml")
        .with_blueprint("default/flow-default-provider-authorization-implicit-consent.yaml")
        .with_blueprint("default/flow-default-provider-invalidation.yaml")
        .with_blueprint("system/providers-oauth2.yaml")
        .with_blueprint("system/providers-proxy.yaml")
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

    let outpost = outposts_instances_create(
        stack.api_config(),
        OutpostRequest {
            name: "test".to_owned(),
            r#type: OutpostTypeEnum::Proxy,
            providers: vec![provider.pk],
            ..Default::default()
        },
    )
    .await?;

    sleep(Duration::from_secs(3)).await;

    stack.start_outpost(&outpost).await?;

    dbg!("DO THE THING");
    sleep(Duration::from_secs(30)).await;

    // flows_instances_partial_update(
    //     stack.api_config(),
    //     "default-authentication-flow",
    //     Some(PatchedFlowRequest {
    //         compatibility_mode: Some(true),
    //         ..Default::default()
    //     }),
    // )
    // .await?;
    //
    // stack
    //     .goto("http://server:9000/if/flow/default-authentication-flow/")
    //     .await?;
    //
    // stack
    //     .login(LoginOptions {
    //         dom: Dom::Shady,
    //         ..Default::default()
    //     })
    //     .await?;
    //
    // stack
    //     .wait_for_url("http://server:9000/if/user/#/library")
    //     .await?;
    //
    // stack
    //     .assert_user("akadmin", "authentik Default Admin", "root@example.com")
    //     .await?;

    stack.quit().await
}
