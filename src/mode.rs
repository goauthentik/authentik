use std::{
    env,
    path::PathBuf,
    sync::atomic::{AtomicU8, Ordering},
};

use eyre::Result;

static MODE: AtomicU8 = AtomicU8::new(0);

fn mode_path() -> PathBuf {
    env::temp_dir().join("authentik-mode")
}

#[derive(PartialEq, Eq)]
#[repr(u8)]
pub enum Mode {
    #[cfg(feature = "core")]
    AllInOne = 0,
    #[cfg(feature = "core")]
    Server = 1,
    #[cfg(feature = "core")]
    Worker = 2,
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
    pub fn get() -> Self {
        match MODE.load(Ordering::Relaxed) {
            #[cfg(feature = "core")]
            0 => Self::AllInOne,
            #[cfg(feature = "core")]
            1 => Self::Server,
            #[cfg(feature = "core")]
            2 => Self::Worker,
            _ => unreachable!(),
        }
    }

    pub fn set(mode: Self) -> Result<()> {
        std::fs::write(mode_path(), mode.to_string())?;
        MODE.store(mode.into(), Ordering::SeqCst);
        Ok(())
    }

    #[must_use]
    pub fn is_core() -> bool {
        match Self::get() {
            #[cfg(feature = "core")]
            Self::AllInOne | Self::Server | Self::Worker => true,
            #[expect(
                unreachable_patterns,
                reason = "Other features will be added like the proxy outpost"
            )]
            _ => false,
        }
    }
}
