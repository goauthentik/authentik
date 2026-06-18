use std::str::FromStr;
use std::{fmt, sync::Arc};

use ak_axum::error::Result;
use ak_client::models::ProxyMode;
use axum::{
    extract::{Query, Request, State},
    http::{HeaderMap, StatusCode, Uri, header},
    response::{IntoResponse as _, Response},
};
use eyre::eyre;
use serde::{Deserialize, Deserializer};
use tower::util::ServiceExt as _;
use tracing::{debug, instrument};

use crate::outpost::proxy::{
    application::Application,
    oauth,
    oauth_state::{self, OAuthState},
};

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
pub(super) async fn handle_auth_start(
    State(app): State<Arc<Application>>,
    request: Request,
) -> Result<Response> {
    let client_id = app
        .provider
        .client_id
        .as_deref()
        .ok_or_else(|| eyre!("provider has no client id"))?;
    let cookie_secret = app
        .provider
        .cookie_secret
        .as_deref()
        .ok_or_else(|| eyre!("provider has no cookie secret"))?;

    let jar = app.session_cookie.jar(request.headers());
    let sid = app
        .session_cookie
        .read(&jar)
        .unwrap_or_else(oauth::new_session_id);

    let redirect = oauth::redirect_param(request.uri())
        .zip(app.provider.mode)
        .and_then(|(rd, mode)| {
            oauth::check_redirect_param(
                &rd,
                mode,
                &app.provider.external_host,
                app.provider.cookie_domain.as_deref(),
            )
        })
        .unwrap_or_default();

    let state = OAuthState {
        iss: oauth_state::issuer(client_id),
        sid: sid.clone(),
        state: oauth::new_session_id(),
        redirect,
    };
    let token = state.encode(cookie_secret)?;

    let redirect_uri = oauth::callback_redirect_uri(&app.provider.external_host)?;
    let authorize = oauth::authorize_url(
        &app.endpoint.auth_url,
        client_id,
        &redirect_uri,
        &app.provider.scopes_to_request,
        &token,
    )?;

    let cookie = app.session_cookie.build(&sid, app.session_max_age());
    Ok((
        jar.add(cookie),
        (StatusCode::FOUND, [(header::LOCATION, authorize)]),
    )
        .into_response())
}

/// Redirect an unauthenticated request to the auth-start endpoint, carrying the
/// originally-requested URL in the `rd` parameter.
#[instrument(skip_all)]
pub(super) fn redirect_to_start(app: &Application, headers: &HeaderMap, uri: &Uri) -> Result<Response> {
    // With "Receive header authentication" enabled, don't redirect a request
    // that carries an Authorization header; report 401 instead.
    if headers.contains_key(header::AUTHORIZATION) && app.provider.intercept_header_auth == Some(true)
    {
        return Ok((
            StatusCode::UNAUTHORIZED,
            "Unauthenticated: header authentication is enabled, no redirect is performed.",
        )
            .into_response());
    }

    let mut redirect = oauth::url_join(&app.provider.external_host, uri.path());
    if app.provider.mode == Some(ProxyMode::ForwardDomain) {
        let valid = app
            .provider
            .cookie_domain
            .as_deref()
            .map(|domain| domain.trim_start_matches('.'))
            .zip(uri.host())
            .is_some_and(|(domain, host)| host.ends_with(domain));
        if !valid {
            redirect.clone_from(&app.provider.external_host);
        }
    }

    let start = oauth::start_url(&app.provider.external_host, &redirect)?;
    Ok((StatusCode::FOUND, [(header::LOCATION, start)]).into_response())
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
