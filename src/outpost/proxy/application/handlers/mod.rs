use std::str::FromStr;
use std::time::{Duration, SystemTime, UNIX_EPOCH};
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
use tracing::{debug, instrument, warn};

use crate::outpost::proxy::{
    application::Application,
    backchannel, oauth,
    oauth_state::{self, OAuthState},
    session::SessionData,
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
    auth_start(&app, request.headers(), redirect)
}

/// Begin the OAuth flow: ensure a session id, sign the state, and redirect to
/// the authorize endpoint with `redirect` carried in the state.
pub(super) fn auth_start(app: &Application, headers: &HeaderMap, redirect: String) -> Result<Response> {
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

    let jar = app.session_cookie.jar(headers);
    let sid = app
        .session_cookie
        .read(&jar)
        .unwrap_or_else(oauth::new_session_id);

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

#[derive(Default, Deserialize)]
struct CallbackParams {
    code: Option<String>,
    state: Option<String>,
}

/// Remaining session lifetime derived from a token's `exp` (unix seconds).
fn max_age_until(exp: i64) -> Duration {
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_or(0, |elapsed| elapsed.as_secs());
    let remaining = exp
        .saturating_sub(i64::try_from(now).unwrap_or(i64::MAX))
        .max(0);
    Duration::from_secs(u64::try_from(remaining).unwrap_or(0))
}

#[instrument(skip_all)]
pub(super) async fn handle_auth_callback(
    State(app): State<Arc<Application>>,
    request: Request,
) -> Result<Response> {
    let client_id = app
        .provider
        .client_id
        .as_deref()
        .ok_or_else(|| eyre!("provider has no client id"))?;
    let client_secret = app
        .provider
        .client_secret
        .as_deref()
        .ok_or_else(|| eyre!("provider has no client secret"))?;
    let cookie_secret = app
        .provider
        .cookie_secret
        .as_deref()
        .ok_or_else(|| eyre!("provider has no cookie secret"))?;

    let jar = app.session_cookie.jar(request.headers());
    let Some(sid) = app.session_cookie.read(&jar) else {
        warn!("auth callback without a valid session cookie");
        return Ok(StatusCode::BAD_REQUEST.into_response());
    };

    let params = Query::<CallbackParams>::try_from_uri(request.uri())
        .map(|query| query.0)
        .unwrap_or_default();

    // Validate the state JWT (signature + issuer) and that it belongs to this session.
    let Some(state_token) = params.state else {
        return Ok(StatusCode::BAD_REQUEST.into_response());
    };
    let Ok(state) = OAuthState::decode(&state_token, cookie_secret, &oauth_state::issuer(client_id))
    else {
        warn!("invalid oauth state");
        return Ok(StatusCode::BAD_REQUEST.into_response());
    };
    if state.sid != sid {
        warn!("oauth state does not match the session");
        return Ok(StatusCode::BAD_REQUEST.into_response());
    }

    let Some(code) = params.code.filter(|code| !code.is_empty()) else {
        return Ok(StatusCode::BAD_REQUEST.into_response());
    };

    let redirect_uri = oauth::callback_redirect_uri(&app.provider.external_host)?;
    let access_token = backchannel::exchange_code(
        &app.api_config.client,
        &app.endpoint.token_url,
        app.token_host.as_deref(),
        &code,
        &redirect_uri,
        client_id,
        client_secret,
    )
    .await?;

    let claims = app.verify_token(&access_token).await?;

    let max_age = max_age_until(claims.exp);
    let data = SessionData {
        claims: Some(claims),
        redirect: None,
    };
    app.session_store.save(&sid, &data, max_age).await?;

    let location = if state.redirect.is_empty() {
        app.provider.external_host.clone()
    } else {
        state.redirect
    };
    let cookie = app.session_cookie.build(&sid, max_age);
    Ok((jar.add(cookie), (StatusCode::FOUND, [(header::LOCATION, location)])).into_response())
}

#[instrument(skip_all)]
pub(super) async fn handle_sign_out(
    State(_app): State<Arc<Application>>,
    _request: Request,
) -> Result<Response> {
    todo!()
}
