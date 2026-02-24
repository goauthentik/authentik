use std::sync::atomic::{AtomicU8, Ordering};

static MODE: AtomicU8 = AtomicU8::new(0);

#[derive(PartialEq)]
pub(crate) enum Mode {
    #[cfg(feature = "core")]
    Server = 0,
    #[cfg(feature = "proxy")]
    Proxy = 2,
}

impl From<u8> for Mode {
    fn from(value: u8) -> Self {
        match value {
            #[cfg(feature = "core")]
            0 => Self::Server,
            #[cfg(feature = "proxy")]
            2 => Self::Proxy,
            _ => unreachable!(),
        }
    }
}

pub(crate) fn get() -> Mode {
    MODE.load(Ordering::Relaxed).into()
}

pub(crate) fn set(mode: Mode) {
    MODE.store(mode as u8, Ordering::SeqCst);
}
