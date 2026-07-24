use std::{
    sync::Arc,
    time::{Duration, SystemTime, UNIX_EPOCH},
};

use ak_axum::error::Result;
use ak_client::models::ProxyMode;
use axum::{
    extract::{Query, Request, State},
    http::{HeaderMap, StatusCode, Uri, header},
    response::{IntoResponse as _, Response},
};
use axum_extra::extract::cookie::Cookie;
use eyre::eyre;
use serde::Deserialize;
use tower::util::ServiceExt as _;
use tracing::{debug, instrument, warn};
use url::Url;

use crate::outpost::proxy::{
    application::Application,
    backchannel,
    claims::Claims,
    error_page, oauth,
    oauth_state::{self, OAuthState},
    session::SessionData,
};

pub(super) mod forward;
pub(super) mod proxy;

/// Attach a freshly-created session cookie to `response` (if header auth produced
/// one), signing it with the application's cookie key.
fn with_session_cookie(
    app: &Application,
    set_cookie: Option<Cookie<'static>>,
    response: Response,
) -> Response {
    match set_cookie {
        Some(cookie) => (
            app.session_cookie.jar(&HeaderMap::new()).add(cookie),
            response,
        )
            .into_response(),
        None => response,
    }
}

#[instrument(skip_all)]
pub(crate) async fn handle(app: Arc<Application>, request: Request) -> Result<Response> {
    let query = request.uri().query();
    if oauth::has_signature(query, oauth::CALLBACK_SIGNATURE) {
        debug!("handling OAuth Callback from querystring signature");
        return handle_auth_callback(State(app), request).await;
    }
    if oauth::has_signature(query, oauth::LOGOUT_SIGNATURE) {
        debug!("handling OAuth Logout from querystring signature");
        return handle_sign_out(State(app), request).await;
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
pub(super) fn auth_start(
    app: &Application,
    headers: &HeaderMap,
    redirect: String,
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
pub(super) fn redirect_to_start(
    app: &Application,
    headers: &HeaderMap,
    uri: &Uri,
) -> Result<Response> {
    // With "Receive header authentication" enabled, don't redirect a request
    // that carries an Authorization header; report 401 instead.
    if headers.contains_key(header::AUTHORIZATION)
        && app.provider.intercept_header_auth == Some(true)
    {
        return Ok(error_page::error_response(
            StatusCode::UNAUTHORIZED,
            "Unauthenticated",
            "Due to 'Receive header authentication' being set, no redirect is performed.",
        ));
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

    // Reaching here means the session lookup already failed, so any
    // signature-valid session cookie is stale: clear it so the browser stops
    // sending a dead session id.
    let jar = app.session_cookie.jar(headers);
    if app.session_cookie.read(&jar).is_some() {
        let jar = jar.remove(app.session_cookie.removal());
        return Ok((jar, (StatusCode::FOUND, [(header::LOCATION, start)])).into_response());
    }
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
    let Ok(state) =
        OAuthState::decode(&state_token, cookie_secret, &oauth_state::issuer(client_id))
    else {
        warn!("invalid oauth state");
        return Ok(StatusCode::BAD_REQUEST.into_response());
    };
    if state.sid != sid {
        warn!("oauth state does not match the session");
        return Ok(StatusCode::BAD_REQUEST.into_response());
    }

    let Some(code) = params.code.filter(|code| !code.is_empty()) else {
        warn!("missing oauth code");
        return Ok(StatusCode::BAD_REQUEST.into_response());
    };

    let redirect_uri = oauth::callback_redirect_uri(&app.provider.external_host)?;

    // Where to send the user once the callback resolves — the originally requested
    // URL carried in the state, falling back to the external host. Used both on
    // success and to restart the flow on a redeem failure.
    let location = if state.redirect.is_empty() {
        app.provider.external_host.clone()
    } else {
        state.redirect
    };

    // Redeem the code and verify the resulting token. On failure, send the user
    // back to the app rather than erroring, so the auth flow simply restarts
    // instead of dead-ending on an error page.
    let redeemed = async {
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
        app.verify_token(&access_token).await
    }
    .await;
    let claims = match redeemed {
        Ok(claims) => claims,
        Err(err) => {
            warn!(?err, "failed to redeem callback; restarting auth flow");
            return Ok((StatusCode::FOUND, [(header::LOCATION, location)]).into_response());
        }
    };

    let max_age = max_age_until(claims.exp);
    if max_age.is_zero() {
        // The token is already expired (it only got here within the verification
        // leeway). Don't persist a dead session; clear the cookie and restart the
        // flow.
        warn!("callback token already expired; clearing session and restarting");
        return Ok((
            jar.remove(app.session_cookie.removal()),
            (StatusCode::FOUND, [(header::LOCATION, location)]),
        )
            .into_response());
    }

    let data = SessionData {
        claims: Some(claims),
    };
    app.session_store.save(&sid, &data, max_age).await?;

    let cookie = app.session_cookie.build(&sid, max_age);
    Ok((
        jar.add(cookie),
        (StatusCode::FOUND, [(header::LOCATION, location)]),
    )
        .into_response())
}

#[instrument(skip_all)]
pub(super) async fn handle_sign_out(
    State(app): State<Arc<Application>>,
    request: Request,
) -> Result<Response> {
    let jar = app.session_cookie.jar(request.headers());
    let claims = match app.session_cookie.read(&jar) {
        Some(sid) => app
            .session_store
            .load(&sid)
            .await
            .ok()
            .flatten()
            .and_then(|data| data.claims),
        None => None,
    };
    let Some(claims) = claims else {
        return redirect_to_start(&app, request.headers(), request.uri());
    };

    let mut end_session = Url::parse(&app.endpoint.end_session_endpoint)?;
    end_session
        .query_pairs_mut()
        .append_pair("id_token_hint", &claims.raw_token);

    // Log out every session belonging to this user.
    let sub = claims.sub.clone();
    if let Err(err) = app
        .session_store
        .logout(&move |candidate: &Claims| candidate.sub == sub)
        .await
    {
        warn!(?err, "failed to log out sessions");
    }

    let jar = jar.remove(app.session_cookie.removal());
    Ok((
        jar,
        (
            StatusCode::FOUND,
            [(header::LOCATION, end_session.to_string())],
        ),
    )
        .into_response())
}
