use std::sync::atomic::{AtomicU8, Ordering};

static MODE: AtomicU8 = AtomicU8::new(0);

#[derive(PartialEq)]
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

    pub(crate) fn set(mode: Self) {
        MODE.store(mode as u8, Ordering::SeqCst);
    }

    pub(crate) fn is_core() -> bool {
        match Self::get() {
            #[cfg(feature = "core")]
            Self::AllInOne | Self::Server | Self::Worker => true,
            _ => false,
        }
    }
}
