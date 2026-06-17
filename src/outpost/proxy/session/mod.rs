//! Session storage.

use std::time::Duration;

use eyre::Result;
use serde::{Deserialize, Serialize};

use crate::outpost::proxy::claims::Claims;

pub(crate) mod filesystem;

use filesystem::FsSessionStore;

/// Data persisted for a session.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub(crate) struct SessionData {
    pub(crate) claims: Option<Claims>,
    pub(crate) redirect: Option<String>,
}

/// A session store backend.
#[derive(Debug)]
pub(crate) enum SessionStore {
    Filesystem(FsSessionStore),
}

impl SessionStore {
    pub(crate) async fn load(&self, sid: &str) -> Result<Option<SessionData>> {
        match self {
            Self::Filesystem(store) => store.load(sid).await,
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
        }
    }

    pub(crate) async fn delete(&self, sid: &str) -> Result<()> {
        match self {
            Self::Filesystem(store) => store.delete(sid).await,
        }
    }

    /// Delete every stored session whose claims match `filter`.
    pub(crate) async fn logout(
        &self,
        filter: &(dyn Fn(&Claims) -> bool + Send + Sync),
    ) -> Result<()> {
        match self {
            Self::Filesystem(store) => store.logout(filter).await,
        }
    }
}
