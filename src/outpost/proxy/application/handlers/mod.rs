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

/// The originally-requested URL — path and query — resolved against the
/// configured external host.
fn requested_url(external_host: &str, uri: &Uri) -> String {
    let path_and_query = uri.path_and_query().map_or("/", |target| target.as_str());
    oauth::url_join(external_host, path_and_query)
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

    let params =
        Query::<CallbackParams>::try_from_uri(request.uri()).map_or_default(|query| query.0);

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

#[cfg(test)]
mod tests {
    use std::{net::Ipv4Addr, sync::Arc};

    use ak_axum::extract::{client_ip::ClientIp, host::Host};
    use ak_client::{
        apis::configuration::Configuration,
        models::{OpenIdConnectConfiguration, ProxyMode, ProxyOutpostConfig},
    };
    use arc_swap::ArcSwapOption;
    use axum::{
        Router,
        body::Body,
        extract::{Request, State},
        http::{StatusCode, Uri},
    };
    use moka::future::Cache;

    use super::{
        forward::{handle_envoy, handle_nginx, handle_traefik},
        proxy, requested_url,
    };
    use crate::outpost::proxy::{
        allowlist::compile_skip_regex,
        application::Application,
        backchannel::BackchannelClient,
        cookie::SessionCookie,
        endpoint::OidcEndpoint,
        session::{SessionStore, filesystem::FsSessionStore},
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

    // Allowlist tests send requests through the real handlers, because each one must pass the path
    // as sent to the allowlist check: parsing the URL drops `.` and `..` segments.
    const ALLOWLISTED_PATHS: &[&str] = &[
        "/public",
        "/public/",
        "/public/ok",
        "/public/a%20b",
        "/public/a..b",
        "/public/a%2Fb",
        "/public/a;b",
        "/public//ok",
    ];

    const NOT_ALLOWLISTED_PATHS: &[&str] = &[
        "/public/./ok",
        "/public/../private",
        "/public/./../private",
        "/public/%2e%2e/private",
        "/public/%2E%2E/private",
        "/public/..%2fprivate",
        "/public/%2e%2e%2fprivate",
        "/public/%2f../private",
        "/public/%2F../private",
        "/public/%2F..%2Fprivate",
        "/public%2F..%2Fprivate",
        "/public//../private",
        "/public/..;/private",
        "/public/..%5cprivate",
        "//private/public/ok",
    ];

    const NOT_EXEMPT_PATHS: &[&str] = &[
        "/x\\..\\outpost.goauthentik.io/ping",
        "/.\\outpost.goauthentik.io/ping",
        "/x\\%2e%2e\\outpost.goauthentik.io/ping",
        "/x/..\\outpost.goauthentik.io/ping",
    ];

    fn application(mode: ProxyMode, skip_path_regex: &str) -> Arc<Application> {
        let oidc = OpenIdConnectConfiguration::new(
            "https://authentik.example.com/application/o/app/".to_owned(),
            "https://authentik.example.com/application/o/authorize/".to_owned(),
            "https://authentik.example.com/application/o/token/".to_owned(),
            "https://authentik.example.com/application/o/userinfo/".to_owned(),
            "https://authentik.example.com/application/o/app/end-session/".to_owned(),
            "https://authentik.example.com/application/o/introspect/".to_owned(),
            "https://authentik.example.com/application/o/app/jwks/".to_owned(),
            Vec::new(),
            Vec::new(),
            Vec::new(),
            Vec::new(),
        );
        let mut provider = ProxyOutpostConfig::new(
            1,
            "app".to_owned(),
            "https://app.example.com".to_owned(),
            oidc,
            None,
            Vec::new(),
            "app".to_owned(),
            "app".to_owned(),
        );
        provider.mode = Some(mode);
        provider.skip_path_regex = Some(skip_path_regex.to_owned());
        provider.client_id = Some("client-id".to_owned());
        provider.cookie_secret = Some("0123456789abcdef0123456789abcdef".to_owned());

        Arc::new(Application {
            host: "app.example.com".to_owned(),
            router: Router::new(),
            cert: None,
            endpoint: OidcEndpoint::new(&provider.oidc_configuration, None, None, false),
            session_store: SessionStore::Filesystem(
                FsSessionStore::new(std::env::temp_dir()).expect("session store"),
            ),
            session_cookie: SessionCookie::new(
                "client-id",
                "0123456789abcdef0123456789abcdef",
                true,
                None,
            )
            .expect("session cookie"),
            api_config: Configuration::default(),
            backchannel_client: BackchannelClient::new(reqwest::ClientBuilder::new())
                .expect("backchannel client"),
            token_host: None,
            auth_cache: Cache::builder().build(),
            outpost_name: "outpost".to_owned(),
            unauthenticated_regex: compile_skip_regex(provider.skip_path_regex.as_deref()),
            upstream_client: upstream::build_client(false).expect("upstream client"),
            jwks_cache: ArcSwapOption::empty(),
            provider,
        })
    }

    async fn nginx_allowlisted(app: &Arc<Application>, path: &str) -> bool {
        let request = Request::builder()
            .uri("/outpost.goauthentik.io/auth/nginx")
            .header("x-original-url", format!("https://app.example.com{path}"))
            .body(Body::empty())
            .expect("request");
        let response = handle_nginx(
            State(Arc::clone(app)),
            ClientIp(Ipv4Addr::LOCALHOST.into()),
            request,
        )
        .await
        .expect("response");
        response.status() == StatusCode::OK
    }

    async fn traefik_allowlisted(app: &Arc<Application>, path: &str) -> bool {
        let request = Request::builder()
            .uri("/outpost.goauthentik.io/auth/traefik")
            .header("x-forwarded-proto", "https")
            .header("x-forwarded-host", "app.example.com")
            .header("x-forwarded-uri", path)
            .body(Body::empty())
            .expect("request");
        let response = handle_traefik(
            State(Arc::clone(app)),
            ClientIp(Ipv4Addr::LOCALHOST.into()),
            request,
        )
        .await
        .expect("response");
        response.status() == StatusCode::OK
    }

    async fn envoy_allowlisted(app: &Arc<Application>, path: &str) -> bool {
        let request = Request::builder()
            .uri(format!("/outpost.goauthentik.io/auth/envoy{path}"))
            .body(Body::empty())
            .expect("request");
        let response = handle_envoy(
            State(Arc::clone(app)),
            Host("app.example.com".to_owned()),
            request,
        )
        .await
        .expect("response");
        response.status() == StatusCode::OK
    }

    async fn proxy_allowlisted(app: &Arc<Application>, path: &str) -> bool {
        let request = Request::builder()
            .uri(path)
            .body(Body::empty())
            .expect("request");
        let response = proxy::handle(
            State(Arc::clone(app)),
            ClientIp(Ipv4Addr::LOCALHOST.into()),
            Host("app.example.com".to_owned()),
            request,
        )
        .await
        .expect("response");
        // Requests that are not allowlisted are redirected to the login flow.
        response.status() != StatusCode::FOUND
    }

    #[tokio::test]
    async fn nginx_single_canonical_paths_are_allowlisted() {
        let app = application(ProxyMode::ForwardSingle, "^/public(/.*)?$");
        let mut denied = Vec::new();
        for path in ALLOWLISTED_PATHS {
            if !nginx_allowlisted(&app, path).await {
                denied.push(*path);
            }
        }

        assert!(denied.is_empty(), "not allowlisted: {denied:#?}");
    }

    #[tokio::test]
    async fn nginx_single_non_canonical_paths_are_not_allowlisted() {
        let app = application(ProxyMode::ForwardSingle, "^/public(/.*)?$");
        let mut allowed = Vec::new();
        for path in NOT_ALLOWLISTED_PATHS {
            if nginx_allowlisted(&app, path).await {
                allowed.push(*path);
            }
        }

        assert!(allowed.is_empty(), "allowlisted: {allowed:#?}");
    }

    #[tokio::test]
    async fn nginx_domain_canonical_paths_are_allowlisted() {
        let app = application(
            ProxyMode::ForwardDomain,
            "^https://app\\.example\\.com/public(/.*)?$",
        );
        let mut denied = Vec::new();
        for path in ALLOWLISTED_PATHS {
            if !nginx_allowlisted(&app, path).await {
                denied.push(*path);
            }
        }

        assert!(denied.is_empty(), "not allowlisted: {denied:#?}");
    }

    #[tokio::test]
    async fn nginx_domain_non_canonical_paths_are_not_allowlisted() {
        let app = application(
            ProxyMode::ForwardDomain,
            "^https://app\\.example\\.com/public(/.*)?$",
        );
        let mut allowed = Vec::new();
        for path in NOT_ALLOWLISTED_PATHS {
            if nginx_allowlisted(&app, path).await {
                allowed.push(*path);
            }
        }

        assert!(allowed.is_empty(), "allowlisted: {allowed:#?}");
    }

    // The outpost's own endpoints stay reachable without a session.
    #[tokio::test]
    async fn nginx_outpost_endpoint_is_exempt() {
        let app = application(ProxyMode::ForwardSingle, "");

        assert!(nginx_allowlisted(&app, "/outpost.goauthentik.io/ping").await);
    }

    // A forwarded path that only resembles an outpost endpoint still needs a session.
    #[tokio::test]
    async fn nginx_non_canonical_paths_are_not_exempt() {
        let app = application(ProxyMode::ForwardSingle, "");
        let mut exempt = Vec::new();
        for path in NOT_EXEMPT_PATHS {
            if nginx_allowlisted(&app, path).await {
                exempt.push(*path);
            }
        }

        assert!(exempt.is_empty(), "exempt: {exempt:#?}");
    }

    #[tokio::test]
    async fn traefik_single_canonical_paths_are_allowlisted() {
        let app = application(ProxyMode::ForwardSingle, "^/public(/.*)?$");
        let mut denied = Vec::new();
        for path in ALLOWLISTED_PATHS {
            if !traefik_allowlisted(&app, path).await {
                denied.push(*path);
            }
        }

        assert!(denied.is_empty(), "not allowlisted: {denied:#?}");
    }

    #[tokio::test]
    async fn traefik_single_non_canonical_paths_are_not_allowlisted() {
        let app = application(ProxyMode::ForwardSingle, "^/public(/.*)?$");
        let mut allowed = Vec::new();
        for path in NOT_ALLOWLISTED_PATHS {
            if traefik_allowlisted(&app, path).await {
                allowed.push(*path);
            }
        }

        assert!(allowed.is_empty(), "allowlisted: {allowed:#?}");
    }

    #[tokio::test]
    async fn traefik_domain_canonical_paths_are_allowlisted() {
        let app = application(
            ProxyMode::ForwardDomain,
            "^https://app\\.example\\.com/public(/.*)?$",
        );
        let mut denied = Vec::new();
        for path in ALLOWLISTED_PATHS {
            if !traefik_allowlisted(&app, path).await {
                denied.push(*path);
            }
        }

        assert!(denied.is_empty(), "not allowlisted: {denied:#?}");
    }

    #[tokio::test]
    async fn traefik_domain_non_canonical_paths_are_not_allowlisted() {
        let app = application(
            ProxyMode::ForwardDomain,
            "^https://app\\.example\\.com/public(/.*)?$",
        );
        let mut allowed = Vec::new();
        for path in NOT_ALLOWLISTED_PATHS {
            if traefik_allowlisted(&app, path).await {
                allowed.push(*path);
            }
        }

        assert!(allowed.is_empty(), "allowlisted: {allowed:#?}");
    }

    #[tokio::test]
    async fn envoy_single_canonical_paths_are_allowlisted() {
        let app = application(ProxyMode::ForwardSingle, "^/public(/.*)?$");
        let mut denied = Vec::new();
        for path in ALLOWLISTED_PATHS {
            if !envoy_allowlisted(&app, path).await {
                denied.push(*path);
            }
        }

        assert!(denied.is_empty(), "not allowlisted: {denied:#?}");
    }

    #[tokio::test]
    async fn envoy_single_non_canonical_paths_are_not_allowlisted() {
        let app = application(ProxyMode::ForwardSingle, "^/public(/.*)?$");
        let mut allowed = Vec::new();
        for path in NOT_ALLOWLISTED_PATHS {
            if envoy_allowlisted(&app, path).await {
                allowed.push(*path);
            }
        }

        assert!(allowed.is_empty(), "allowlisted: {allowed:#?}");
    }

    #[tokio::test]
    async fn envoy_domain_canonical_paths_are_allowlisted() {
        let app = application(
            ProxyMode::ForwardDomain,
            "^//app\\.example\\.com/public(/.*)?$",
        );
        let mut denied = Vec::new();
        for path in ALLOWLISTED_PATHS {
            if !envoy_allowlisted(&app, path).await {
                denied.push(*path);
            }
        }

        assert!(denied.is_empty(), "not allowlisted: {denied:#?}");
    }

    #[tokio::test]
    async fn envoy_domain_non_canonical_paths_are_not_allowlisted() {
        let app = application(
            ProxyMode::ForwardDomain,
            "^//app\\.example\\.com/public(/.*)?$",
        );
        let mut allowed = Vec::new();
        for path in NOT_ALLOWLISTED_PATHS {
            if envoy_allowlisted(&app, path).await {
                allowed.push(*path);
            }
        }

        assert!(allowed.is_empty(), "allowlisted: {allowed:#?}");
    }

    #[tokio::test]
    async fn proxy_canonical_paths_are_allowlisted() {
        let app = application(ProxyMode::Proxy, "^/public(/.*)?$");
        let mut denied = Vec::new();
        for path in ALLOWLISTED_PATHS {
            if !proxy_allowlisted(&app, path).await {
                denied.push(*path);
            }
        }

        assert!(denied.is_empty(), "not allowlisted: {denied:#?}");
    }

    #[tokio::test]
    async fn proxy_non_canonical_paths_are_not_allowlisted() {
        let app = application(ProxyMode::Proxy, "^/public(/.*)?$");
        let mut allowed = Vec::new();
        for path in NOT_ALLOWLISTED_PATHS {
            if proxy_allowlisted(&app, path).await {
                allowed.push(*path);
            }
        }

        assert!(allowed.is_empty(), "allowlisted: {allowed:#?}");
    }
}
