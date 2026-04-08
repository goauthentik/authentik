//! Utilities to manage the current execution mode.

use std::{
    env,
    path::PathBuf,
    sync::atomic::{AtomicU8, Ordering},
};

use eyre::{Result, eyre};
use tracing::trace;

/// Stores the current mode.
static MODE: AtomicU8 = AtomicU8::new(0);

fn mode_path() -> PathBuf {
    env::temp_dir().join("authentik-mode")
}

/// authentik execution mode.
#[derive(Debug, Copy, Clone, PartialEq, Eq)]
#[repr(u8)]
pub enum Mode {
    /// Running both the server and the worker.
    #[cfg(feature = "core")]
    AllInOne = 0,
    /// Running the server.
    #[cfg(feature = "core")]
    Server = 1,
    /// Running the worker.
    #[cfg(feature = "core")]
    Worker = 2,
    /// Running the proxy outpost.
    #[cfg(feature = "proxy")]
    Proxy = 128,
}

impl std::fmt::Display for Mode {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            #[cfg(feature = "core")]
            Self::AllInOne => write!(f, "allinone"),
            #[cfg(feature = "core")]
            Self::Server => write!(f, "server"),
            #[cfg(feature = "core")]
            Self::Worker => write!(f, "worker"),
            #[cfg(feature = "proxy")]
            Self::Proxy => write!(f, "proxy"),
        }
    }
}

impl From<Mode> for u8 {
    #[expect(clippy::as_conversions, reason = "repr of enum is u8")]
    fn from(value: Mode) -> Self {
        value as Self
    }
}

impl Mode {
    /// Get the current mode.
    pub fn get() -> Self {
        match MODE.load(Ordering::Relaxed) {
            #[cfg(feature = "core")]
            0 => Self::AllInOne,
            #[cfg(feature = "core")]
            1 => Self::Server,
            #[cfg(feature = "core")]
            2 => Self::Worker,
            #[cfg(feature = "proxy")]
            128 => Self::Proxy,
            _ => unreachable!(),
        }
    }

    /// Set the current mode.
    pub fn set(mode: Self) -> Result<()> {
        std::fs::write(mode_path(), mode.to_string())?;
        MODE.store(mode.into(), Ordering::SeqCst);
        Ok(())
    }

    /// Load the current mode from the filesystem.
    pub fn load() -> Result<()> {
        let mode = std::fs::read_to_string(mode_path())?;
        let mode = match mode.trim() {
            #[cfg(feature = "core")]
            "allinone" => Self::AllInOne,
            #[cfg(feature = "core")]
            "server" => Self::Server,
            #[cfg(feature = "core")]
            "worker" => Self::Worker,
            #[cfg(feature = "proxy")]
            "proxy" => Self::Proxy,
            _ => return Err(eyre!("Mode {mode} not supported")),
        };
        MODE.store(mode.into(), Ordering::SeqCst);
        Ok(())
    }

    /// Cleanup the mode stored on the filesystem.
    pub fn cleanup() {
        let mode_path = mode_path();
        if let Err(err) = std::fs::remove_file(&mode_path) {
            trace!(?err, "failed to remove mode file, ignoring");
        }
    }

    /// Check if the mode is one of the "core" modes, namely [`Mode::AllInOne`], [`Mode::Server`]
    /// or [`Mode::Worker`].
    #[must_use]
    pub fn is_core() -> bool {
        match Self::get() {
            #[cfg(feature = "core")]
            Self::AllInOne | Self::Server | Self::Worker => true,
            _ => false,
        }
    }
}

#[cfg(test)]
mod tests {
    use tempfile::{TempDir, tempdir};

    use super::Mode;

    fn prepare_temp_dir() -> TempDir {
        let tempdir = tempdir().expect("failed to create tempdir");
        #[expect(unsafe_code, reason = "testing")]
        // SAFETY: testing
        unsafe {
            std::env::set_var("TMPDIR", tempdir.path());
        }
        tempdir
    }

    #[test]
    fn get_and_set() {
        let temp_dir = prepare_temp_dir();
        let mode_path = temp_dir.path().join("authentik-mode");
        for mode in [
            (Mode::AllInOne, "allinone"),
            (Mode::Server, "server"),
            (Mode::Worker, "worker"),
            (Mode::Proxy, "proxy"),
        ] {
            Mode::set(mode.0).expect("failed to set mode");
            assert_eq!(Mode::get(), mode.0);
            assert_eq!(
                std::fs::read_to_string(&mode_path).expect("failed to read mode"),
                mode.1
            );
        }
    }

    #[test]
    fn load() {
        let temp_dir = prepare_temp_dir();
        let mode_path = temp_dir.path().join("authentik-mode");
        for mode in [
            ("allinone", Mode::AllInOne),
            ("server", Mode::Server),
            ("worker", Mode::Worker),
            ("proxy", Mode::Proxy),
        ] {
            std::fs::write(&mode_path, mode.0).expect("failed to write mode");
            Mode::load().expect("failed to load mode");
            assert_eq!(Mode::get(), mode.1);
        }
    }

    #[test]
    fn cleanup() {
        let temp_dir = prepare_temp_dir();
        let mode_path = temp_dir.path().join("authentik-mode");
        Mode::set(Mode::AllInOne).expect("failed to set mode");
        Mode::cleanup();
        mode_path.metadata().expect_err("mode file still exists");
    }

    #[test]
    fn is_core() {
        let _temp_dir = prepare_temp_dir();
        for mode in [
            (Mode::AllInOne, true),
            (Mode::Server, true),
            (Mode::Worker, true),
            (Mode::Proxy, false),
        ] {
            Mode::set(mode.0).expect("failed to set mode");
            assert_eq!(Mode::is_core(), mode.1);
        }
    }
}
