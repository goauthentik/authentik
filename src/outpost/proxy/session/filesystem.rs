//! Filesystem-backed session store: one JSON file per session.

use std::{
    fs::{File, TryLockError},
    io::ErrorKind,
    os::unix::fs::OpenOptionsExt as _,
    path::{Path, PathBuf},
    time::{Duration, SystemTime, UNIX_EPOCH},
};

use ak_common::Arbiter;
use eyre::Result;
use serde::{Deserialize, Serialize};
use tokio::{io::AsyncWriteExt as _, time::interval};
use tracing::{debug, warn};
use uuid::Uuid;

use crate::outpost::proxy::{claims::Claims, session::SessionData};

/// How often expired session files are swept from disk.
const CLEANUP_INTERVAL: Duration = Duration::from_mins(5);

const SESSION_FILE_PREFIX: &str = "session_";

/// Lock file ensuring a single process sweeps a shared session directory at once.
const CLEANUP_LOCK_FILE: &str = "session-cleanup.lock";

/// Session files hold the user's claims and raw token, so restrict them to the
/// owner.
const SESSION_FILE_MODE: u32 = 0o600;

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

/// Atomically write `json` to `target` with owner-only permissions: stage it in
/// `tmp` (created exclusively) then rename over `target`. The rename is atomic,
/// so concurrent readers never observe a partial write. The caller removes `tmp`
/// if this returns an error.
async fn write_atomic(tmp: &Path, target: &Path, json: &[u8]) -> Result<()> {
    let mut file = tokio::fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .mode(SESSION_FILE_MODE)
        .open(tmp)
        .await?;
    file.write_all(json).await?;
    drop(file);
    tokio::fs::rename(tmp, target).await?;
    Ok(())
}

impl FsSessionStore {
    /// Create a store, verifying the directory is writable.
    pub(crate) fn new(dir: PathBuf) -> Result<Self> {
        let probe = dir.join(format!("{SESSION_FILE_PREFIX}write_test"));
        std::fs::OpenOptions::new()
            .write(true)
            .create(true)
            .truncate(true)
            .mode(SESSION_FILE_MODE)
            .open(&probe)?;
        let _ = std::fs::remove_file(&probe);
        Ok(Self { dir })
    }

    fn path(&self, sid: &str) -> PathBuf {
        self.dir.join(format!("{SESSION_FILE_PREFIX}{sid}"))
    }

    /// A unique temporary path used to stage an atomic write. The leading dot
    /// keeps it out of the `session_` namespace scanned by cleanup/logout.
    fn tmp_path(&self, sid: &str) -> PathBuf {
        self.dir.join(format!(
            ".{SESSION_FILE_PREFIX}{sid}.{}.tmp",
            Uuid::new_v4()
        ))
    }

    pub(crate) async fn load(&self, sid: &str) -> Result<Option<SessionData>> {
        let path = self.path(sid);
        let bytes = match tokio::fs::read(&path).await {
            Ok(bytes) => bytes,
            Err(err) if err.kind() == ErrorKind::NotFound => return Ok(None),
            Err(err) => return Err(err.into()),
        };
        // Unreadable data (e.g. a session written by the old Go proxy) is treated
        // as absent and removed, so the user simply re-authenticates.
        let Ok(record) = serde_json::from_slice::<StoredSession>(&bytes) else {
            let _ = tokio::fs::remove_file(&path).await;
            return Ok(None);
        };
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

        let tmp = self.tmp_path(sid);
        if let Err(err) = write_atomic(&tmp, &self.path(sid), &json).await {
            let _ = tokio::fs::remove_file(&tmp).await;
            return Err(err);
        }
        Ok(())
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

    /// Remove expired session files from the store directory.
    pub(crate) async fn cleanup(&self) -> Result<()> {
        // Hold an advisory `flock` so that, when several processes share a
        // session directory, only one sweeps at a time. `lock` is kept in scope
        // for the whole sweep and releases when dropped. The lock lives on the
        // kernel's open file description, so a crash releases it automatically;
        // the leftover lock file is harmless and reused on the next run (do NOT
        // delete it as "stale" — that would defeat the locking).
        let lock = File::create(self.dir.join(CLEANUP_LOCK_FILE))?;
        match lock.try_lock() {
            Ok(()) => {}
            Err(TryLockError::WouldBlock) => {
                debug!("session cleanup already running elsewhere, skipping");
                return Ok(());
            }
            Err(TryLockError::Error(err)) => return Err(err.into()),
        }

        let now = now_unix();
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
            if let Ok(record) = serde_json::from_slice::<StoredSession>(&bytes)
                && record.expires <= now
            {
                let _ = tokio::fs::remove_file(&path).await;
            }
        }
        Ok(())
    }
}

/// Periodically sweep expired session files from the system temp dir until shutdown.
pub(crate) async fn cleanup_loop(arbiter: Arbiter) -> Result<()> {
    let store = match FsSessionStore::new(std::env::temp_dir()) {
        Ok(store) => store,
        Err(err) => {
            warn!(?err, "session directory not writable; cleanup disabled");
            return Ok(());
        }
    };
    let mut ticker = interval(CLEANUP_INTERVAL);
    loop {
        tokio::select! {
            _ = ticker.tick() => {
                if let Err(err) = store.cleanup().await {
                    warn!(?err, "session cleanup failed");
                }
            }
            () = arbiter.shutdown() => break,
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use std::time::Duration;

    use tempfile::tempdir;

    use super::FsSessionStore;
    use crate::outpost::proxy::{claims::Claims, session::SessionData};

    fn data(sub: &str) -> SessionData {
        SessionData {
            claims: Some(Claims {
                sub: sub.to_owned(),
                sid: "sid".to_owned(),
                ..Claims::default()
            }),
        }
    }

    #[tokio::test]
    async fn save_and_load() {
        let dir = tempdir().expect("tempdir");
        let store = FsSessionStore::new(dir.path().to_path_buf()).expect("store");
        let session = data("user");

        store
            .save("abc", &session, Duration::from_mins(1))
            .await
            .expect("save");
        let loaded = store.load("abc").await.expect("load");

        assert_eq!(loaded, Some(session));
    }

    #[tokio::test]
    async fn load_ignores_unreadable_file() {
        // A session left behind by the old Go proxy isn't our JSON format.
        let dir = tempdir().expect("tempdir");
        let store = FsSessionStore::new(dir.path().to_path_buf()).expect("store");
        let path = dir.path().join("session_legacy");
        std::fs::write(&path, b"securecookie-or-gob-blob, not json").expect("write legacy file");

        // It loads as absent (→ re-login) and is removed so it isn't reprocessed.
        assert_eq!(store.load("legacy").await.expect("load"), None);
        assert!(!path.exists());
    }

    #[tokio::test]
    async fn load_missing_returns_none() {
        let dir = tempdir().expect("tempdir");
        let store = FsSessionStore::new(dir.path().to_path_buf()).expect("store");

        assert_eq!(store.load("nope").await.expect("load"), None);
    }

    #[tokio::test]
    async fn expired_returns_none() {
        let dir = tempdir().expect("tempdir");
        let store = FsSessionStore::new(dir.path().to_path_buf()).expect("store");

        store
            .save("e", &data("user"), Duration::from_secs(0))
            .await
            .expect("save");

        assert_eq!(store.load("e").await.expect("load"), None);
    }

    #[tokio::test]
    async fn cleanup_removes_only_expired() {
        let dir = tempdir().expect("tempdir");
        let store = FsSessionStore::new(dir.path().to_path_buf()).expect("store");

        store
            .save("live", &data("user"), Duration::from_mins(1))
            .await
            .expect("save");
        store
            .save("dead", &data("user"), Duration::from_secs(0))
            .await
            .expect("save");

        store.cleanup().await.expect("cleanup");

        assert!(dir.path().join("session_live").exists());
        assert!(!dir.path().join("session_dead").exists());
    }

    #[tokio::test]
    async fn session_file_is_owner_only() {
        use std::os::unix::fs::PermissionsExt as _;

        let dir = tempdir().expect("tempdir");
        let store = FsSessionStore::new(dir.path().to_path_buf()).expect("store");
        store
            .save("abc", &data("user"), Duration::from_mins(1))
            .await
            .expect("save");

        let mode = std::fs::metadata(dir.path().join("session_abc"))
            .expect("metadata")
            .permissions()
            .mode();
        assert_eq!(mode & 0o777, 0o600);
    }

    #[tokio::test]
    async fn cleanup_skips_while_locked() {
        let dir = tempdir().expect("tempdir");
        let store = FsSessionStore::new(dir.path().to_path_buf()).expect("store");
        store
            .save("dead", &data("user"), Duration::from_secs(0))
            .await
            .expect("save");

        // Hold the cleanup lock as another process would.
        let held =
            std::fs::File::create(dir.path().join(super::CLEANUP_LOCK_FILE)).expect("lock file");
        held.lock().expect("acquire lock");

        // The sweep is skipped, so the expired file survives.
        store.cleanup().await.expect("cleanup");
        assert!(dir.path().join("session_dead").exists());

        // Once released, the next sweep removes it.
        held.unlock().expect("release lock");
        store.cleanup().await.expect("cleanup");
        assert!(!dir.path().join("session_dead").exists());
    }

    #[tokio::test]
    async fn logout_deletes_matching_only() {
        let dir = tempdir().expect("tempdir");
        let store = FsSessionStore::new(dir.path().to_path_buf()).expect("store");

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
