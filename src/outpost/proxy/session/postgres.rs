//! PostgreSQL-backed session store, used by the embedded outpost.

use std::time::Duration;

use eyre::Result;
use sqlx::types::Json;
use sqlx::types::chrono::{DateTime, Utc};
use uuid::Uuid;

use crate::outpost::proxy::claims::Claims;
use crate::outpost::proxy::session::SessionData;

/// Stores sessions in the shared `authentik_providers_proxy_proxysession` table.
#[derive(Debug, Clone)]
pub(crate) struct PgSessionStore;

impl PgSessionStore {
    pub(crate) async fn load(&self, sid: &str) -> Result<Option<SessionData>> {
        let row: Option<(Json<SessionData>, DateTime<Utc>)> = sqlx::query_as(
            "
            SELECT session_data, expires
            FROM authentik_providers_proxy_proxysession
            WHERE session_key = $1
            ",
        )
        .bind(sid)
        .fetch_optional(ak_common::db::get())
        .await?;

        let Some((data, expires)) = row else {
            return Ok(None);
        };
        if expires <= Utc::now() {
            self.delete(sid).await?;
            return Ok(None);
        }
        Ok(Some(data.0))
    }

    pub(crate) async fn save(
        &self,
        sid: &str,
        data: &SessionData,
        max_age: Duration,
    ) -> Result<()> {
        let user_id = data
            .claims
            .as_ref()
            .and_then(|claims| Uuid::parse_str(&claims.sub).ok());
        let ttl = i64::try_from(max_age.as_secs()).unwrap_or(i64::MAX);
        let expires = DateTime::from_timestamp(Utc::now().timestamp().saturating_add(ttl), 0)
            .unwrap_or_else(Utc::now);

        sqlx::query(
            "
            INSERT INTO authentik_providers_proxy_proxysession
                (uuid, session_key, user_id, session_data, expires, expiring)
            VALUES ($1, $2, $3, $4, $5, true)
            ON CONFLICT (session_key) DO UPDATE SET
                user_id = EXCLUDED.user_id,
                session_data = EXCLUDED.session_data,
                expires = EXCLUDED.expires
            ",
        )
        .bind(Uuid::new_v4())
        .bind(sid)
        .bind(user_id)
        .bind(Json(data))
        .bind(expires)
        .execute(ak_common::db::get())
        .await?;
        Ok(())
    }

    async fn delete(&self, sid: &str) -> Result<()> {
        sqlx::query("DELETE FROM authentik_providers_proxy_proxysession WHERE session_key = $1")
            .bind(sid)
            .execute(ak_common::db::get())
            .await?;
        Ok(())
    }

    pub(crate) async fn logout(
        &self,
        filter: &(dyn Fn(&Claims) -> bool + Send + Sync),
    ) -> Result<()> {
        let rows: Vec<(String, Json<SessionData>)> = sqlx::query_as(
            "
            SELECT session_key, session_data
            FROM authentik_providers_proxy_proxysession
            ",
        )
        .fetch_all(ak_common::db::get())
        .await?;

        let stale: Vec<String> = rows
            .into_iter()
            .filter(|(_, data)| data.0.claims.as_ref().is_some_and(filter))
            .map(|(session_key, _)| session_key)
            .collect();

        if !stale.is_empty() {
            sqlx::query(
                "DELETE FROM authentik_providers_proxy_proxysession WHERE session_key = ANY($1)",
            )
            .bind(&stale)
            .execute(ak_common::db::get())
            .await?;
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use std::time::Duration;

    use ak_common::{Tasks, config, db};

    use super::PgSessionStore;
    use crate::outpost::proxy::claims::{Claims, ProxyClaims};
    use crate::outpost::proxy::session::SessionData;

    /// Truncates the session table when dropped, cleaning up after the test.
    struct TruncateGuard;

    impl Drop for TruncateGuard {
        fn drop(&mut self) {
            tokio::task::block_in_place(|| {
                tokio::runtime::Handle::current().block_on(async {
                    let _ = sqlx::query("TRUNCATE authentik_providers_proxy_proxysession")
                        .execute(db::get())
                        .await;
                });
            });
        }
    }

    /// Initialise config + the global database pool (see `ak_common::db` tests).
    async fn setup() {
        std::env::set_current_dir(env!("CARGO_MANIFEST_DIR")).expect("chdir to crate root");
        config::init().expect("init config");
        let mut tasks = Tasks::new().expect("create tasks");
        db::init(&mut tasks).await.expect("init db");
    }

    fn session(sub: &str) -> SessionData {
        SessionData {
            claims: Some(Claims {
                sub: sub.to_owned(),
                sid: "session-id".to_owned(),
                ak_proxy: Some(ProxyClaims::default()),
                ..Claims::default()
            }),
            redirect: None,
        }
    }

    #[tokio::test(flavor = "multi_thread")]
    async fn save_load_expire_logout() {
        setup().await;
        let _guard = TruncateGuard;
        sqlx::query("TRUNCATE authentik_providers_proxy_proxysession")
            .execute(db::get())
            .await
            .expect("truncate");

        let store = PgSessionStore;
        let sub = "1d8f8d4e-2b2a-4f1e-9c3a-000000000001";
        let data = session(sub);

        // Save then load round-trips the data.
        store
            .save("live", &data, Duration::from_mins(1))
            .await
            .expect("save");
        assert_eq!(store.load("live").await.expect("load"), Some(data));

        // An already-expired session loads as None.
        store
            .save("expired", &session(sub), Duration::from_secs(0))
            .await
            .expect("save expired");
        assert_eq!(store.load("expired").await.expect("load expired"), None);

        // Logout deletes only the sessions whose claims match the filter.
        store
            .save(
                "other",
                &session("2d8f8d4e-2b2a-4f1e-9c3a-000000000002"),
                Duration::from_mins(1),
            )
            .await
            .expect("save other");
        let owner = sub.to_owned();
        store
            .logout(&move |claims| claims.sub == owner)
            .await
            .expect("logout");
        assert_eq!(store.load("live").await.expect("load after logout"), None);
        assert!(store.load("other").await.expect("load other").is_some());
    }
}
