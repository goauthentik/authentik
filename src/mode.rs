use eyre::Result;
use std::{
    env,
    fmt::Display,
    path::PathBuf,
    sync::atomic::{AtomicU8, Ordering},
};

static MODE: AtomicU8 = AtomicU8::new(0);

fn mode_path() -> PathBuf {
    env::temp_dir().join("authentik-mode")
}

#[derive(PartialEq)]
#[repr(u8)]
pub(crate) enum Mode {
    #[cfg(feature = "core")]
    AllInOne = 0,
    #[cfg(feature = "core")]
    Server = 1,
    #[cfg(feature = "core")]
    Worker = 2,
    #[cfg(feature = "proxy")]
    Proxy = 3,
}

impl Display for Mode {
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

impl Mode {
    pub(crate) fn get() -> Self {
        match MODE.load(Ordering::Relaxed) {
            #[cfg(feature = "core")]
            0 => Self::AllInOne,
            #[cfg(feature = "core")]
            1 => Self::Server,
            #[cfg(feature = "core")]
            2 => Self::Worker,
            #[cfg(feature = "proxy")]
            3 => Self::Proxy,
            _ => unreachable!(),
        }
    }

    pub(crate) fn set(mode: Self) -> Result<()> {
        std::fs::write(mode_path(), mode.to_string())?;
        MODE.store(mode as u8, Ordering::SeqCst);
        Ok(())
    }

    pub(crate) fn is_core() -> bool {
        match Self::get() {
            #[cfg(feature = "core")]
            Self::AllInOne | Self::Server | Self::Worker => true,
            _ => false,
        }
    }
}
