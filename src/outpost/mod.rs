use std::{sync::Arc, time::Duration};

use ak_client::{
    apis::{configuration::Configuration, outposts_api::outposts_instances_list},
    models::Outpost as OutpostModel,
};
use ak_common::{Tasks, VERSION, api, authentik_build_hash};
use arc_swap::ArcSwap;
use eyre::{Result, eyre};
use tracing::{debug, info, instrument};
use uuid::Uuid;

pub(crate) mod event;
#[cfg(feature = "proxy")]
pub(crate) mod proxy;

pub(crate) trait Outpost: Send + Sync + Sized {
    const OUTPOST_TYPE: &'static str;
    type Cli: Send + Sync;

    async fn new(controller: Arc<OutpostController>) -> Result<Self>;

    fn start(&self, tasks: &mut Tasks) -> Result<()>;
    fn refresh(&self) -> impl Future<Output = Result<()>> + Send;

    fn end_session(&self, event: event::EventSessionEnd)
    -> impl Future<Output = Result<()>> + Send;
}

#[derive(Debug)]
pub(crate) struct OutpostController {
    api_config: Configuration,
    outpost: ArcSwap<OutpostModel>,
    instance_uuid: Uuid,
    reload_offset: Duration,
    m_info: metrics::Gauge,
    m_last_update: metrics::Gauge,
    m_connection: metrics::Gauge,
}

impl OutpostController {
    #[instrument(skip_all)]
    async fn get_outpost(api_config: &Configuration) -> Result<OutpostModel> {
        let outposts = outposts_instances_list(
            api_config, None, None, None, None, None, None, None, None, None, None, None, None,
        )
        .await?;

        let Some(outpost) = outposts.results.into_iter().next() else {
            return Err(eyre!(
                "No outposts found with given token, ensure the given token corresponds to an \
                 authentik Outpost"
            ));
        };
        debug!(name = outpost.name, "fetched outpost configuration");

        Ok(outpost)
    }

    #[instrument(skip_all)]
    async fn new<O: Outpost>() -> Result<Self> {
        let api_config = api::make_config()?;
        let outpost = Self::get_outpost(&api_config).await?;
        let instance_uuid = Uuid::new_v4();

        let m_labels = [
            ("outpost_name", outpost.name.clone()),
            ("outpost_type", O::OUTPOST_TYPE.to_owned()),
            ("uuid", instance_uuid.to_string()),
            ("version", VERSION.to_owned()),
            ("build", authentik_build_hash(None)),
        ];
        metrics::describe_gauge!("authentik_outpost_info", "Outpost info");
        let m_info = metrics::gauge!("authentik_outpost_info", &m_labels);
        metrics::describe_gauge!("authentik_outpost_last_update", "Time of last update");
        let m_last_update = metrics::gauge!("authentik_outpost_last_update", &m_labels);
        metrics::describe_gauge!("authentik_outpost_connection", "Connection status");
        let m_connection = metrics::gauge!("authentik_outpost_connection", &m_labels);

        let reload_offset = Duration::from_secs(rand::random_range(0..10));
        let controller = Self {
            api_config,
            outpost: ArcSwap::from_pointee(outpost),
            instance_uuid,
            reload_offset,
            m_info,
            m_last_update,
            m_connection,
        };

        info!(embedded = controller.is_embedded(), "outpost mode");
        debug!(?reload_offset, "HA Reload offset");

        Ok(controller)
    }

    fn is_embedded(&self) -> bool {
        self.outpost
            .load()
            .managed
            .as_ref()
            .and_then(|m| m.as_deref())
            .is_some_and(|m| m == "goauthentik.io/outposts/embedded")
    }

    async fn refresh(&self) -> Result<()> {
        let outpost = Self::get_outpost(&self.api_config).await?;
        self.outpost.swap(Arc::new(outpost));
        Ok(())
    }
}

#[instrument(skip_all)]
pub(crate) async fn start<O: Outpost + 'static>(_cli: O::Cli, tasks: &mut Tasks) -> Result<()> {
    let controller = Arc::new(OutpostController::new::<O>().await?);
    let outpost = Arc::new(O::new(Arc::clone(&controller)).await?);

    event::start(tasks, Arc::clone(&controller), Arc::clone(&outpost))?;
    outpost.start(tasks)?;
    controller.m_info.set(1_u8);

    Ok(())
}
