use std::{env::temp_dir, path::PathBuf};

pub(crate) fn socket_path() -> PathBuf {
    temp_dir().join("authentik.sock")
}
