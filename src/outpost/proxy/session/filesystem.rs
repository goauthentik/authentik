//! Filesystem-backed session store: one JSON file per session.

use std::io::ErrorKind;
use std::path::PathBuf;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use eyre::Result;
use serde::{Deserialize, Serialize};

use crate::outpost::proxy::claims::Claims;
use crate::outpost::proxy::session::SessionData;

const SESSION_FILE_PREFIX: &str = "session_";

#[derive(Debug, Clone)]
pub(crate) struct FsSessionStore {
    dir: PathBuf,
}

#[derive(Serialize, Deserialize)]
struct StoredSession {
    expires: i64,
    data: SessionData,
}

fn now_unix() -> i64 {
    let secs = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_or(0, |d| d.as_secs());
    i64::try_from(secs).unwrap_or(i64::MAX)
}

impl FsSessionStore {
    pub(crate) fn new(dir: PathBuf) -> Self {
        Self { dir }
    }

    fn path(&self, sid: &str) -> PathBuf {
        self.dir.join(format!("{SESSION_FILE_PREFIX}{sid}"))
    }

    pub(crate) async fn load(&self, sid: &str) -> Result<Option<SessionData>> {
        let path = self.path(sid);
        let bytes = match tokio::fs::read(&path).await {
            Ok(bytes) => bytes,
            Err(err) if err.kind() == ErrorKind::NotFound => return Ok(None),
            Err(err) => return Err(err.into()),
        };
        let record: StoredSession = serde_json::from_slice(&bytes)?;
        if record.expires <= now_unix() {
            let _ = tokio::fs::remove_file(&path).await;
            return Ok(None);
        }
        Ok(Some(record.data))
    }

    pub(crate) async fn save(
        &self,
        sid: &str,
        data: &SessionData,
        max_age: Duration,
    ) -> Result<()> {
        let ttl = i64::try_from(max_age.as_secs()).unwrap_or(i64::MAX);
        let record = StoredSession {
            expires: now_unix().saturating_add(ttl),
            data: data.clone(),
        };
        let json = serde_json::to_vec(&record)?;
        tokio::fs::write(self.path(sid), json).await?;
        Ok(())
    }

    pub(crate) async fn delete(&self, sid: &str) -> Result<()> {
        match tokio::fs::remove_file(self.path(sid)).await {
            Ok(()) => Ok(()),
            Err(err) if err.kind() == ErrorKind::NotFound => Ok(()),
            Err(err) => Err(err.into()),
        }
    }

    pub(crate) async fn logout(
        &self,
        filter: &(dyn Fn(&Claims) -> bool + Send + Sync),
    ) -> Result<()> {
        let mut entries = tokio::fs::read_dir(&self.dir).await?;
        while let Some(entry) = entries.next_entry().await? {
            let name = entry.file_name();
            let Some(name) = name.to_str() else {
                continue;
            };
            if !name.starts_with(SESSION_FILE_PREFIX) {
                continue;
            }
            let path = entry.path();
            let Ok(bytes) = tokio::fs::read(&path).await else {
                continue;
            };
            let Ok(record) = serde_json::from_slice::<StoredSession>(&bytes) else {
                continue;
            };
            if let Some(claims) = &record.data.claims
                && filter(claims)
            {
                let _ = tokio::fs::remove_file(&path).await;
            }
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use std::time::Duration;

    use tempfile::tempdir;

    use super::FsSessionStore;
    use crate::outpost::proxy::claims::Claims;
    use crate::outpost::proxy::session::SessionData;

    fn data(sub: &str) -> SessionData {
        SessionData {
            claims: Some(Claims {
                sub: sub.to_owned(),
                sid: "sid".to_owned(),
                ..Claims::default()
            }),
            redirect: Some("/dashboard".to_owned()),
        }
    }

    #[tokio::test]
    async fn save_and_load() {
        let dir = tempdir().expect("tempdir");
        let store = FsSessionStore::new(dir.path().to_path_buf());
        let session = data("user");

        store
            .save("abc", &session, Duration::from_mins(1))
            .await
            .expect("save");
        let loaded = store.load("abc").await.expect("load");

        assert_eq!(loaded, Some(session));
    }

    #[tokio::test]
    async fn load_missing_returns_none() {
        let dir = tempdir().expect("tempdir");
        let store = FsSessionStore::new(dir.path().to_path_buf());

        assert_eq!(store.load("nope").await.expect("load"), None);
    }

    #[tokio::test]
    async fn expired_returns_none() {
        let dir = tempdir().expect("tempdir");
        let store = FsSessionStore::new(dir.path().to_path_buf());

        store
            .save("e", &data("user"), Duration::from_secs(0))
            .await
            .expect("save");

        assert_eq!(store.load("e").await.expect("load"), None);
    }

    #[tokio::test]
    async fn delete_removes_session() {
        let dir = tempdir().expect("tempdir");
        let store = FsSessionStore::new(dir.path().to_path_buf());

        store
            .save("abc", &data("user"), Duration::from_mins(1))
            .await
            .expect("save");
        store.delete("abc").await.expect("delete");

        assert_eq!(store.load("abc").await.expect("load"), None);
        // Deleting a missing session is not an error.
        store.delete("abc").await.expect("delete missing");
    }

    #[tokio::test]
    async fn logout_deletes_matching_only() {
        let dir = tempdir().expect("tempdir");
        let store = FsSessionStore::new(dir.path().to_path_buf());

        store
            .save("a", &data("target"), Duration::from_mins(1))
            .await
            .expect("save");
        store
            .save("b", &data("other"), Duration::from_mins(1))
            .await
            .expect("save");

        let filter: &(dyn Fn(&Claims) -> bool + Send + Sync) = &|claims| claims.sub == "target";
        store.logout(filter).await.expect("logout");

        assert_eq!(store.load("a").await.expect("load"), None);
        assert!(store.load("b").await.expect("load").is_some());
    }
}
