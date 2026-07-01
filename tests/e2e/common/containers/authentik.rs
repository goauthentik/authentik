use std::borrow::Cow;
use std::collections::HashMap;

use rand::{
    distr::{Alphanumeric, SampleString},
    rng,
};
use testcontainers_modules::testcontainers::{core::Image, core::WaitFor};

#[derive(Debug, Clone)]
pub struct Authentik {
    env_vars: HashMap<String, String>,
}

impl Authentik {
    pub fn env_var(mut self, name: &str, value: &str) -> Self {
        self.env_vars.insert(name.to_string(), value.to_string());
        self
    }
}

impl Default for Authentik {
    fn default() -> Self {
        let mut env_vars = HashMap::new();
        env_vars.insert(
            "AUTHENTIK_SECRET_KEY".to_string(),
            Alphanumeric.sample_string(&mut rng(), 32),
        );
        Self { env_vars }
    }
}

impl Image for Authentik {
    fn name(&self) -> &str {
        "ghcr.io/goauthentik/server"
    }

    fn tag(&self) -> &str {
        "2026.5.3"
    }

    fn ready_conditions(&self) -> Vec<WaitFor> {
        vec![
            WaitFor::message_on_stderr("bite"),
            WaitFor::message_on_stdout("bite"),
        ]
    }

    fn env_vars(
        &self,
    ) -> impl IntoIterator<Item = (impl Into<Cow<'_, str>>, impl Into<Cow<'_, str>>)> {
        &self.env_vars
    }

    fn cmd(&self) -> impl IntoIterator<Item = impl Into<Cow<'_, str>>> {
        vec!["allinone"]
    }
}
