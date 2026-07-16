#![expect(
    clippy::tests_outside_test_module,
    reason = "e2e tests don't need a test module"
)]

use std::time::Duration;

use ak_client::{
    apis::{
        core_api::core_applications_create,
        flows_api::flows_instances_list,
        outposts_api::{
            outposts_instances_create, outposts_instances_default_settings_retrieve,
            outposts_instances_health_list,
        },
        providers_api::providers_proxy_create,
    },
    models::{ApplicationRequest, OutpostRequest, OutpostTypeEnum, ProxyProviderRequest},
};
use eyre::{Result, eyre};
use tokio::time::sleep;

mod stack;
use stack::AuthentikStack;

#[tokio::test(flavor = "multi_thread")]
async fn proxy_connectivity() -> Result<()> {
    let mut stack = AuthentikStack::builder()
        .with_blueprint("default/flow-default-provider-authorization-implicit-consent.yaml")
        .with_blueprint("default/flow-default-provider-invalidation.yaml")
        .with_whoami(true)
        .run()
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

    let mut retries = 0_usize;
    loop {
        if retries > 50 {
            let _ = stack.quit().await;
            return Err(eyre!("Failed to check outpost state."));
        }
        let states = outposts_instances_health_list(
            stack.api_config(),
            &outpost.pk.to_string(),
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
        )
        .await?;

        if let Some(state) = states.first()
            && !state.version.is_empty()
        {
            break;
        }

        retries += 1;
        sleep(Duration::from_millis(500)).await;
    }

    stack.quit().await
}
