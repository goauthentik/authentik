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
                (session_key, user_id, session_data, expires, expiring)
            VALUES ($1, $2, $3, $4, true)
            ON CONFLICT (session_key) DO UPDATE SET
                user_id = EXCLUDED.user_id,
                session_data = EXCLUDED.session_data,
                expires = EXCLUDED.expires
            ",
        )
        .bind(sid)
        .bind(user_id)
        .bind(Json(data))
        .bind(expires)
        .execute(ak_common::db::get())
        .await?;
        Ok(())
    }

    pub(crate) async fn delete(&self, sid: &str) -> Result<()> {
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
            .filter(|(_, data)| data.0.claims.as_ref().is_some_and(|claims| filter(claims)))
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
