use std::{fmt::Debug, path::PathBuf};

use config::{AsyncSource, ConfigError, Format, Map};
use tokio::fs::read_to_string;

#[derive(Debug)]
pub(crate) struct AsyncFile<F: Format> {
    pub(crate) name: PathBuf,
    pub(crate) format: F,
}

#[async_trait::async_trait]
impl<F: Format + Send + Sync + Debug> AsyncSource for AsyncFile<F> {
    async fn collect(&self) -> Result<Map<String, config::Value>, ConfigError> {
        read_to_string(&self.name)
            .await
            .map_err(|e| ConfigError::Foreign(Box::new(e)))
            .and_then(|text| {
                let name = self.name.to_str().map(|s| s.to_owned());
                self.format
                    .parse(name.as_ref(), &text)
                    .map_err(ConfigError::Foreign)
            })
    }
}
