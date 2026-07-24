//! Session storage.

use std::time::Duration;

use eyre::Result;
use serde::{Deserialize, Serialize};

use crate::outpost::proxy::claims::Claims;

pub(crate) mod filesystem;
#[cfg(feature = "core")]
pub(crate) mod postgres;

use filesystem::FsSessionStore;

/// Data persisted for a session.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub(crate) struct SessionData {
    pub(crate) claims: Option<Claims>,
}

/// A session store backend.
#[derive(Debug)]
pub(crate) enum SessionStore {
    Filesystem(FsSessionStore),
    #[cfg(feature = "core")]
    Postgres(postgres::PgSessionStore),
}

impl SessionStore {
    pub(crate) async fn load(&self, sid: &str) -> Result<Option<SessionData>> {
        match self {
            Self::Filesystem(store) => store.load(sid).await,
            #[cfg(feature = "core")]
            Self::Postgres(store) => store.load(sid).await,
        }
    }

    pub(crate) async fn save(
        &self,
        sid: &str,
        data: &SessionData,
        max_age: Duration,
    ) -> Result<()> {
        match self {
            Self::Filesystem(store) => store.save(sid, data, max_age).await,
            #[cfg(feature = "core")]
            Self::Postgres(store) => store.save(sid, data, max_age).await,
        }
    }

    /// Delete every stored session whose claims match `filter`.
    pub(crate) async fn logout(
        &self,
        filter: &(dyn Fn(&Claims) -> bool + Send + Sync),
    ) -> Result<()> {
        match self {
            Self::Filesystem(store) => store.logout(filter).await,
            #[cfg(feature = "core")]
            Self::Postgres(store) => store.logout(filter).await,
        }
    }
}
