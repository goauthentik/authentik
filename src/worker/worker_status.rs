use ak_common::{arbiter::Arbiter, authentik_full_version, db};
use eyre::Result;
use nix::unistd::gethostname;
use tokio::time::{Duration, interval, sleep};
use tracing::warn;
use uuid::Uuid;

async fn keep(arbiter: Arbiter, id: Uuid, hostname: &str, version: &str) -> Result<()> {
    let query = "
        INSERT INTO authentik_tasks_workerstatus (id, hostname, version, last_seen)
            VALUES ($1, $2, $3, NOW())
            ON CONFLICT (id) DO UPDATE SET last_seen = NOW()
    ";
    let mut keep_interval = interval(Duration::from_secs(30));
    loop {
        tokio::select! {
            _ = keep_interval.tick() => {
                sqlx::query(query)
                .bind(id)
                .bind(hostname)
                .bind(version)
                .execute(db::get())
                .await?;
            },
            () = arbiter.shutdown() => return Ok(()),
        }
    }
}

pub(super) async fn run(arbiter: Arbiter) -> Result<()> {
    let id = Uuid::new_v4();
    let raw_hostname = gethostname()?;
    let hostname = raw_hostname.to_string_lossy();
    let version = authentik_full_version();

    loop {
        if let Err(err) = keep(arbiter.clone(), id, hostname.as_ref(), &version).await {
            warn!(?err, "failed to update worker status in database");
        }
        // `keep` returned. It's either an error in which case we wait 10s before
        // retrying.
        // Or we actually need to exit, which will happen here.
        tokio::select! {
            () = sleep(Duration::from_secs(10)) => {},
            () = arbiter.shutdown() => return Ok(()),
        }
    }
}
