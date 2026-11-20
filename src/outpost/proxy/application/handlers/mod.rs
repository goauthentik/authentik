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
    auth_start(&app, request.headers(), redirect).await
}

/// Begin the OAuth flow: ensure a session id, persist a placeholder session,
/// sign the state, and redirect to the authorize endpoint with `redirect`
/// carried in the state.
pub(super) async fn auth_start(
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

    // Persist a placeholder session for this id so a request racing this one
    // (the browser may fetch cached assets in parallel with the redirect) can
    // tell an in-flight login apart from a dead session id: only the latter
    // clears the cookie, and clearing an in-flight id makes the callback
    // answer with a bare 400 (see #26447). Skipping the save when a session
    // already exists keeps a stray /start hit from clobbering a live session.
    if !matches!(app.session_store.load(&sid).await, Ok(Some(_)))
        && let Err(err) = app
            .session_store
            .save(&sid, &SessionData::default(), app.session_max_age())
            .await
    {
        warn!(?err, "failed to persist pre-auth session");
    }

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

/// The originally-requested URL — path and query — resolved against the
/// configured external host.
fn requested_url(external_host: &str, uri: &Uri) -> String {
    let path_and_query = uri.path_and_query().map_or("/", |target| target.as_str());
    oauth::url_join(external_host, path_and_query)
}

/// Redirect an unauthenticated request to the auth-start endpoint, carrying the
/// originally-requested URL in the `rd` parameter.
#[instrument(skip_all)]
pub(super) async fn redirect_to_start(
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

    let mut redirect = requested_url(&app.provider.external_host, uri);
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

    // Clear the session cookie only when its id is unknown to the store. An
    // id with a stored session — including the placeholder persisted by
    // `auth_start` while the login is in flight — must survive, or the
    // subsequent callback dead-ends with a bare 400 (see #26447).
    let jar = app.session_cookie.jar(headers);
    if let Some(sid) = app.session_cookie.read(&jar)
        && !matches!(app.session_store.load(&sid).await, Ok(Some(_)))
    {
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
        // Nothing to complete: restart the flow instead of dead-ending on an
        // empty 400 the browser can't recover from by refreshing.
        warn!("auth callback without a valid session cookie; restarting auth flow");
        return Ok((
            StatusCode::FOUND,
            [(header::LOCATION, app.provider.external_host.clone())],
        )
            .into_response());
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
            &app.backchannel_client,
            &app.endpoint.token_url,
            app.token_host.as_ref(),
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
        return redirect_to_start(&app, request.headers(), request.uri()).await;
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

#[cfg(test)]
mod tests {
    use std::{sync::Arc, time::Duration};

    use ak_client::models::{OpenIdConnectConfiguration, ProxyMode, ProxyOutpostConfig};
    use axum::{
        Json,
        extract::State,
        http::{HeaderMap, StatusCode, Uri, header},
        response::IntoResponse as _,
    };
    use jsonwebtoken::{Algorithm, EncodingKey, Header as JwtHeader, encode};
    use tokio::{net::TcpListener, task::JoinHandle};
    use url::Url;

    use super::{auth_start, handle_auth_callback, redirect_to_start, requested_url};
    use crate::outpost::proxy::{
        application::Application,
        cookie::SessionCookie,
        endpoint::OidcEndpoint,
        session::{SessionData, SessionStore, filesystem::FsSessionStore},
        upstream,
    };

    #[test]
    fn requested_url_keeps_query() {
        let uri: Uri = "/some/path?foo=bar&baz=qux".parse().expect("valid uri");
        assert_eq!(
            requested_url("https://app.example.com", &uri),
            "https://app.example.com/some/path?foo=bar&baz=qux"
        );
    }

    #[test]
    fn requested_url_path_only() {
        let uri: Uri = "/some/path".parse().expect("valid uri");
        assert_eq!(
            requested_url("https://app.example.com", &uri),
            "https://app.example.com/some/path"
        );
    }

    // 32-byte secret (matches authentik's generated cookie secret length).
    const SECRET: &str = "0123456789abcdef0123456789abcdef";
    const CLIENT_ID: &str = "client-123";
    const CLIENT_SECRET: &str = "client-secret";
    const EXTERNAL_HOST: &str = "https://app.example.com";
    const ISSUER: &str = "https://authentik.example.com/application/o/test-app/";
    const REDIRECT: &str = "https://app.example.com/page";

    /// A mock IdP token endpoint: always returns an HS256 access token signed
    /// with the provider client secret, so the callback can verify it without
    /// touching the network.
    async fn mock_idp() -> (std::net::SocketAddr, JoinHandle<()>) {
        let listener = TcpListener::bind("127.0.0.1:0").await.expect("bind");
        let addr = listener.local_addr().expect("addr");
        let handle = tokio::spawn(async move {
            let router = axum::Router::new().route(
                "/token",
                axum::routing::post(|| async {
                    Json(serde_json::json!({
                        "access_token": access_token(),
                        "id_token": "",
                    }))
                }),
            );
            axum::serve(listener, router).await.expect("mock idp");
        });
        (addr, handle)
    }

    fn access_token() -> String {
        let exp = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .expect("clock")
            .as_secs()
            + 3_600;
        encode(
            &JwtHeader::new(Algorithm::HS256),
            &serde_json::json!({
                "iss": ISSUER,
                "aud": CLIENT_ID,
                "exp": exp,
                "sub": "user-uuid",
                "preferred_username": "akadmin",
            }),
            &EncodingKey::from_secret(CLIENT_SECRET.as_bytes()),
        )
        .expect("sign token")
    }

    fn provider() -> ProxyOutpostConfig {
        ProxyOutpostConfig {
            client_id: Some(CLIENT_ID.to_owned()),
            client_secret: Some(CLIENT_SECRET.to_owned()),
            cookie_secret: Some(SECRET.to_owned()),
            external_host: EXTERNAL_HOST.to_owned(),
            mode: Some(ProxyMode::Proxy),
            scopes_to_request: vec!["openid".to_owned()],
            access_token_validity: Some(3_600.0),
            oidc_configuration: OpenIdConnectConfiguration {
                id_token_signing_alg_values_supported: vec!["HS256".to_owned()],
                ..Default::default()
            },
            ..Default::default()
        }
    }

    fn test_app(dir: &tempfile::TempDir, token_url: String) -> Application {
        Application {
            host: "app.example.com".to_owned(),
            provider: provider(),
            router: axum::Router::new(),
            cert: None,
            endpoint: OidcEndpoint {
                auth_url: "https://authentik.example.com/application/o/authorize/".to_owned(),
                token_url,
                token_introspection: "https://authentik.example.com/application/o/introspect/"
                    .to_owned(),
                end_session_endpoint:
                    "https://authentik.example.com/application/o/test-app/end-session/".to_owned(),
                jwks_uri: "https://authentik.example.com/application/o/test-app/jwks/".to_owned(),
                issuer: ISSUER.to_owned(),
            },
            session_store: SessionStore::Filesystem(
                FsSessionStore::new(dir.path().to_path_buf()).expect("store"),
            ),
            session_cookie: SessionCookie::new(CLIENT_ID, SECRET, false, None).expect("cookie"),
            api_config: ak_client::apis::configuration::Configuration::default(),
            token_host: None,
            auth_cache: moka::future::Cache::builder().max_capacity(10).build(),
            outpost_name: "test-outpost".to_owned(),
            unauthenticated_regex: vec![],
            upstream_client: upstream::build_client(false).expect("upstream client"),
            jwks_cache: arc_swap::ArcSwapOption::empty(),
        }
    }

    /// The session cookie header from a `Set-Cookie` response header.
    fn headers_from_set_cookie(response: &axum::response::Response) -> HeaderMap {
        let set_cookie = response
            .headers()
            .get(header::SET_COOKIE)
            .expect("set cookie")
            .to_str()
            .expect("utf-8 header");
        let mut headers = HeaderMap::new();
        headers.insert(
            header::COOKIE,
            set_cookie
                .split(';')
                .next()
                .expect("pair")
                .parse()
                .expect("cookie"),
        );
        headers
    }

    /// A request with a signed session cookie for an arbitrary session id.
    fn headers_with_cookie(app: &Application, sid: &str) -> HeaderMap {
        let jar = app.session_cookie.jar(&HeaderMap::new());
        let response = (
            jar.add(app.session_cookie.build(sid, Duration::from_mins(5))),
            (),
        )
            .into_response();
        headers_from_set_cookie(&response)
    }

    /// The `state` query parameter of the authorize URL from a start response.
    fn state_of(start: &axum::response::Response) -> String {
        let location = start
            .headers()
            .get(header::LOCATION)
            .expect("location")
            .to_str()
            .expect("utf-8 header");
        let url = Url::parse(location).expect("valid url");
        url.query_pairs()
            .find(|(key, _)| key == "state")
            .expect("state param")
            .1
            .into_owned()
    }

    fn callback_request(headers: &HeaderMap, state: &str) -> axum::extract::Request {
        axum::extract::Request::builder()
            .method("GET")
            .uri(format!(
                "/outpost.goauthentik.io/callback?code=mock-code&state={state}"
            ))
            .header(header::COOKIE, headers[header::COOKIE].clone())
            .body(axum::body::Body::empty())
            .expect("request")
    }

    #[tokio::test]
    async fn callback_completes_flow() {
        let dir = tempfile::tempdir().expect("tempdir");
        let (addr, _idp) = mock_idp().await;
        let app = test_app(&dir, format!("http://{addr}/token"));

        let start = auth_start(&app, &HeaderMap::new(), REDIRECT.to_owned())
            .await
            .expect("auth start");
        let headers = headers_from_set_cookie(&start);
        let _sid = app
            .session_cookie
            .read(&app.session_cookie.jar(&headers))
            .expect("sid");

        let response = handle_auth_callback(
            State(Arc::new(app)),
            callback_request(&headers, &state_of(&start)),
        )
        .await
        .expect("callback");

        assert_eq!(response.status(), StatusCode::FOUND);
        assert_eq!(response.headers()[header::LOCATION], REDIRECT);
    }

    #[tokio::test]
    async fn start_persists_placeholder_session() {
        let dir = tempfile::tempdir().expect("tempdir");
        let (addr, _idp) = mock_idp().await;
        let app = test_app(&dir, format!("http://{addr}/token"));

        let start = auth_start(&app, &HeaderMap::new(), REDIRECT.to_owned())
            .await
            .expect("auth start");
        let headers = headers_from_set_cookie(&start);
        let sid = app
            .session_cookie
            .read(&app.session_cookie.jar(&headers))
            .expect("sid");

        // The placeholder makes the id known to the store while the login is
        // in flight; the callback replaces it with real claims afterwards.
        assert_eq!(
            app.session_store.load(&sid).await.expect("load"),
            Some(SessionData::default())
        );
    }

    #[tokio::test]
    async fn parallel_request_does_not_kill_inflight_login() {
        let dir = tempfile::tempdir().expect("tempdir");
        let (addr, _idp) = mock_idp().await;
        let app = test_app(&dir, format!("http://{addr}/token"));

        // 1. `/start` issues the session cookie and persists the placeholder.
        let start = auth_start(&app, &HeaderMap::new(), REDIRECT.to_owned())
            .await
            .expect("auth start");
        let headers = headers_from_set_cookie(&start);
        let _sid = app
            .session_cookie
            .read(&app.session_cookie.jar(&headers))
            .expect("sid");

        // 2. A parallel request carrying that cookie reaches the proxy (the
        // browser fetching cached assets in parallel with the redirect).
        let uri: Uri = "/assets/logo.png".parse().expect("uri");
        let response = redirect_to_start(&app, &headers, &uri)
            .await
            .expect("redirect to start");

        // The cookie must survive: no removal may be attached to the redirect.
        assert!(
            response.headers().get(header::SET_COOKIE).is_none(),
            "parallel request cleared the in-flight session cookie"
        );

        // 3. The OAuth callback completes the login normally.
        let response = handle_auth_callback(
            State(Arc::new(app)),
            callback_request(&headers, &state_of(&start)),
        )
        .await
        .expect("callback");
        assert_eq!(response.status(), StatusCode::FOUND);
        assert_eq!(response.headers()[header::LOCATION], REDIRECT);
    }

    #[tokio::test]
    async fn stale_session_cookie_is_still_cleared() {
        let dir = tempfile::tempdir().expect("tempdir");
        let (addr, _idp) = mock_idp().await;
        let app = test_app(&dir, format!("http://{addr}/token"));

        // A signature-valid cookie whose id has no session record: cleared so
        // the browser stops sending a dead session id.
        let headers = headers_with_cookie(&app, "dead-session-id");
        let uri: Uri = "/assets/logo.png".parse().expect("uri");
        let response = redirect_to_start(&app, &headers, &uri)
            .await
            .expect("redirect to start");

        let set_cookie = response
            .headers()
            .get(header::SET_COOKIE)
            .expect("stale cookie must be cleared")
            .to_str()
            .expect("utf-8 header");
        assert!(set_cookie.starts_with("authentik_proxy_"));
        assert!(set_cookie.to_lowercase().contains("max-age=0"));
    }

    #[tokio::test]
    async fn callback_without_cookie_restarts_flow() {
        let dir = tempfile::tempdir().expect("tempdir");
        let (addr, _idp) = mock_idp().await;
        let app = test_app(&dir, format!("http://{addr}/token"));

        let request = axum::extract::Request::builder()
            .method("GET")
            .uri("/outpost.goauthentik.io/callback?code=mock-code&state=whatever")
            .body(axum::body::Body::empty())
            .expect("request");
        let response = handle_auth_callback(State(Arc::new(app)), request)
            .await
            .expect("callback");

        assert_eq!(response.status(), StatusCode::FOUND);
        assert_eq!(response.headers()[header::LOCATION], EXTERNAL_HOST);
    }
}
