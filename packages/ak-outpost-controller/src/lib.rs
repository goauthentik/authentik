use std::{path::PathBuf, sync::Arc, time::Duration};

use ak_client::{
    apis::{configuration::Configuration, outposts_api::outposts_instances_list},
    models::Outpost as OutpostModel,
};
use ak_common::{Tasks, VERSION, api, authentik_build_hash, tracing::LogFilterHandle};
use arc_swap::ArcSwap;
use eyre::{Error, Result, eyre};
use tokio_retry2::{Retry, RetryError, strategy::LinearBackoff};
use tracing::{debug, info, instrument, warn};
use uuid::Uuid;

pub mod event;

pub trait Outpost: Send + Sync + Sized {
    const OUTPOST_TYPE: &'static str;
    type Cli: Send + Sync;

    fn new(controller: Arc<OutpostController>) -> impl Future<Output = Result<Self>> + Send;

    fn start(self: Arc<Self>, tasks: &mut Tasks) -> Result<()>;
    fn refresh(&self) -> impl Future<Output = Result<()>> + Send;

    fn end_session(&self, event: event::EventSessionEnd)
    -> impl Future<Output = Result<()>> + Send;
}

#[derive(Debug)]
pub struct OutpostController {
    pub api_config: Configuration,
    pub outpost: ArcSwap<OutpostModel>,
    /// Socket of the core server, set only when running as the embedded outpost.
    pub(crate) embedded_socket: Option<PathBuf>,
    pub(crate) instance_uuid: Uuid,
    pub(crate) reload_offset: Duration,
    pub(crate) m_info: metrics::Gauge,
    pub(crate) m_last_update: metrics::Gauge,
    pub(crate) m_connection: metrics::Gauge,
}

impl OutpostController {
    #[instrument(skip_all)]
    pub async fn get_outpost(api_config: &Configuration) -> Result<OutpostModel> {
        let retry_strategy = LinearBackoff::from_millis(500).max_delay(Duration::from_secs(5));
        let retrieve_outposts = async || {
            outposts_instances_list(
                api_config, None, None, None, None, None, None, None, None, None, None, None, None,
            )
            .await
            .map_err(Error::new)
            .map_err(RetryError::transient)
        };
        let retry_notify = |err: &Error, _duration| {
            warn!(
                ?err,
                "Failed to fetch outpost from API, retrying in 3 seconds"
            );
        };

        let outposts = Retry::spawn_notify(retry_strategy, retrieve_outposts, retry_notify).await?;

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
    pub async fn new<O: Outpost>(embedded_socket: Option<PathBuf>) -> Result<Self> {
        let api_config = match embedded_socket.clone() {
            Some(socket) => api::make_config_embedded(socket)?,
            None => api::make_config()?,
        };

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
            embedded_socket,
            instance_uuid,
            reload_offset,
            m_info,
            m_last_update,
            m_connection,
        };

        if controller.embedded_socket.is_some() && !controller.is_embedded() {
            return Err(eyre!(
                "We think we are running as embedded, but the outpost returned by the API is not \
                 the embedded outpost."
            ));
        }

        info!(embedded = controller.is_embedded(), "outpost mode");
        debug!(?reload_offset, "HA Reload offset");

        Ok(controller)
    }

    pub fn is_embedded(&self) -> bool {
        self.outpost
            .load()
            .managed
            .as_ref()
            .and_then(|m| m.as_deref())
            .is_some_and(|m| m == "goauthentik.io/outposts/embedded")
    }

    pub async fn refresh(&self) -> Result<()> {
        let outpost = Self::get_outpost(&self.api_config).await?;
        self.outpost.swap(Arc::new(outpost));
        Ok(())
    }
}

#[instrument(skip_all)]
pub async fn start<O: Outpost + 'static>(
    _cli: O::Cli,
    tasks: &mut Tasks,
    log_filter_handle: Option<LogFilterHandle>,
    embedded_socket: Option<PathBuf>,
) -> Result<Arc<O>> {
    let controller = Arc::new(OutpostController::new::<O>(embedded_socket).await?);
    let outpost = Arc::new(O::new(Arc::clone(&controller)).await?);

    if let Some(handle) = log_filter_handle
        && let Some(new_log_level) = controller.outpost.load().config.get("log_level")
        && let Some(new_log_level) = new_log_level.as_str()
    {
        handle.set_log_level(new_log_level)?;
    }

    event::start(tasks, Arc::clone(&controller), Arc::clone(&outpost))?;
    Arc::clone(&outpost).start(tasks)?;
    controller.m_info.set(1_u8);

    Ok(outpost)
}
