use std::str::FromStr;
use std::{fmt, sync::Arc};

use ak_axum::error::Result;
use axum::{
    extract::{Query, Request, State},
    response::Response,
};
use serde::{Deserialize, Deserializer};
use tower::util::ServiceExt as _;
use tracing::{debug, instrument};

use crate::outpost::proxy::application::Application;

pub(super) mod forward;
pub(super) mod proxy;

// TODO: move this to ak-common
fn empty_string_as_none<'de, D, T>(de: D) -> Result<Option<T>, D::Error>
where
    D: Deserializer<'de>,
    T: FromStr,
    T::Err: fmt::Display,
{
    let opt = Option::<String>::deserialize(de)?;
    match opt.as_deref() {
        None | Some("") => Ok(None),
        Some(s) => FromStr::from_str(s)
            .map_err(serde::de::Error::custom)
            .map(Some),
    }
}

#[derive(Deserialize)]
struct Parameters {
    // #[serde(rename = "rd", default, deserialize_with = "empty_string_as_none")]
    // redirect: Option<String>,
    #[serde(
        rename = "X-authentik-auth-callback",
        default,
        deserialize_with = "empty_string_as_none"
    )]
    callback_signature: Option<bool>,
    #[serde(
        rename = "X-authentik-logout",
        default,
        deserialize_with = "empty_string_as_none"
    )]
    logout_signature: Option<bool>,
}

#[instrument(skip_all)]
pub(crate) async fn handle(app: Arc<Application>, request: Request) -> Result<Response> {
    if let Ok(query) = Query::<Parameters>::try_from_uri(request.uri()) {
        if query.callback_signature == Some(true) {
            debug!("handling OAuth Callback from querystring signature");
            return handle_auth_callback(State(app), request).await;
        }
        if query.logout_signature == Some(true) {
            debug!("handling OAuth Logout from querystring signature");
            return handle_sign_out(State(app), request).await;
        }
    }

    Ok(app.router.clone().with_state(app).oneshot(request).await?)
}

#[instrument(skip_all)]
pub(super) async fn handle_auth_callback(
    State(_app): State<Arc<Application>>,
    _request: Request,
) -> Result<Response> {
    todo!()
}

#[instrument(skip_all)]
pub(super) async fn handle_sign_out(
    State(_app): State<Arc<Application>>,
    _request: Request,
) -> Result<Response> {
    todo!()
}
