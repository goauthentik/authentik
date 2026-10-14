//! Exercise the actual wire protocol, not just reqwest's pre-transport headers.

use std::{
    collections::HashMap,
    net::{SocketAddr, TcpListener},
    path::Path,
    sync::Arc,
    time::Duration,
};

use ak_client::models::OpenIdConnectConfiguration;
use ak_common::api::ServerConfig;
use axum::{
    Json, Router,
    body::to_bytes,
    extract::{Request, State},
    http::{HeaderMap, Method, Uri, Version},
    routing::any,
};
use axum_server::{Handle, tls_rustls::RustlsConfig};
use jsonwebtoken::{EncodingKey, Header, encode};
use rustls::pki_types::PrivatePkcs8KeyDer;
use serde_json::{Value, json};
use tokio::{sync::mpsc, task::JoinHandle, time::timeout};
use url::Url;

use super::{
    BackchannelClient, HOST, TokenHost, X_FORWARDED_PROTO, client_credentials_token, exchange_code,
    fetch_jwks, introspect_token,
};
use crate::outpost::proxy::{endpoint::OidcEndpoint, token::verify_hs256};

const TIMEOUT: Duration = Duration::from_secs(10);
const INTERNAL_HOST: &str = "internal.test.goauthentik.io";
const BROWSER: &str = "https://auth.test.goauthentik.io/";
const CLIENT_ID: &str = "test-client";
const SECRET: &str = "test-client-secret";
const ISSUER_PATH: &str = "application/o/test-app/";

struct ObservedRequest {
    version: Version,
    method: Method,
    uri: Uri,
    headers: HeaderMap,
    form: HashMap<String, String>,
}

#[derive(Clone)]
struct ServerState {
    scheme: &'static str,
    requests: mpsc::Sender<ObservedRequest>,
}

async fn respond(State(state): State<ServerState>, request: Request) -> Json<Value> {
    let (parts, body) = request.into_parts();
    // Model RFC 9113's authority precedence. In particular, do not let an
    // HTTP/2 Host override hide the internal :authority when minting a token.
    let authority = parts.uri.authority().map_or_else(
        || parts.headers[HOST].to_str().expect("valid host"),
        |authority| authority.as_str(),
    );
    let scheme = parts
        .headers
        .get(X_FORWARDED_PROTO)
        .map_or(state.scheme, |value| {
            value.to_str().expect("valid forwarded scheme")
        });
    let claims = json!({
        "iss": format!("{scheme}://{authority}/{ISSUER_PATH}"),
        "aud": CLIENT_ID,
        "exp": time::OffsetDateTime::now_utc().unix_timestamp() + 3600_i64,
        "sub": "test-user",
    });
    let token = encode(
        &Header::default(),
        &claims,
        &EncodingKey::from_secret(SECRET.as_bytes()),
    )
    .expect("sign token");
    let response = match parts.uri.path() {
        "/application/o/token/" => json!({"access_token": token, "id_token": token}),
        "/application/o/introspect/" => json!({"active": true, "sub": "test-user"}),
        "/application/o/test-app/jwks/" => json!({"keys": []}),
        _ => json!({}),
    };
    let body = to_bytes(body, 4096).await.expect("read form body");
    state
        .requests
        .try_send(ObservedRequest {
            version: parts.version,
            method: parts.method,
            uri: parts.uri,
            headers: parts.headers,
            form: url::form_urlencoded::parse(&body).into_owned().collect(),
        })
        .expect("record request");
    Json(response)
}

struct TestServer {
    base: Url,
    builder: Option<reqwest::ClientBuilder>,
    requests: mpsc::Receiver<ObservedRequest>,
    handle: Handle<SocketAddr>,
    task: JoinHandle<std::io::Result<()>>,
}

impl TestServer {
    fn tcp(tls: bool) -> Self {
        let listener = TcpListener::bind("127.0.0.1:0").expect("bind test server");
        listener
            .set_nonblocking(true)
            .expect("nonblocking listener");
        let addr = listener.local_addr().expect("local address");
        let scheme = if tls { "https" } else { "http" };
        let base =
            Url::parse(&format!("{scheme}://{INTERNAL_HOST}:{}/", addr.port())).expect("base URL");
        let mut builder = ServerConfig {
            host: base.clone(),
            token: String::new(),
            insecure: false,
        }
        .client_builder()
        .no_proxy()
        .timeout(TIMEOUT)
        .resolve(INTERNAL_HOST, addr);
        let (sender, requests) = mpsc::channel(16);
        let router = Router::new()
            .fallback(any(respond))
            .with_state(ServerState {
                scheme,
                requests: sender,
            });
        let handle = Handle::new();
        let task = if tls {
            let cert = rcgen::generate_simple_self_signed(vec![INTERNAL_HOST.to_owned()])
                .expect("generate test certificate");
            builder = builder
                .tls_certs_only([reqwest::Certificate::from_der(cert.cert.der())
                    .expect("trust test certificate")]);
            let key = PrivatePkcs8KeyDer::from(cert.signing_key.serialize_der());
            let mut config = rustls::ServerConfig::builder()
                .with_no_client_auth()
                .with_single_cert(vec![cert.cert.der().clone()], key.into())
                .expect("server TLS config");
            // Prefer h2: a missing HTTP/1-only restriction must fail the tests.
            config.alpn_protocols = vec![b"h2".to_vec(), b"http/1.1".to_vec()];
            let server =
                axum_server::from_tcp_rustls(listener, RustlsConfig::from_config(Arc::new(config)))
                    .expect("TLS server")
                    .handle(handle.clone());
            tokio::spawn(server.serve(router.into_make_service()))
        } else {
            let server = axum_server::from_tcp(listener)
                .expect("HTTP server")
                .handle(handle.clone());
            tokio::spawn(server.serve(router.into_make_service()))
        };
        Self {
            base,
            builder: Some(builder),
            requests,
            handle,
            task,
        }
    }

    fn unix(path: &Path) -> Self {
        let listener = tokio::net::UnixListener::bind(path).expect("bind Unix socket");
        let (sender, requests) = mpsc::channel(16);
        let router = Router::new()
            .fallback(any(respond))
            .with_state(ServerState {
                scheme: "http",
                requests: sender,
            });
        let task = tokio::spawn(async move { axum::serve(listener, router).await });
        Self {
            base: Url::parse("http://localhost/").expect("base URL"),
            builder: Some(
                reqwest::ClientBuilder::new()
                    .unix_socket(path)
                    .no_proxy()
                    .timeout(TIMEOUT),
            ),
            requests,
            handle: Handle::new(),
            task,
        }
    }

    fn client(&mut self) -> BackchannelClient {
        BackchannelClient::new(self.builder.take().expect("unused builder"))
            .expect("build backchannel client")
    }

    async fn received(&mut self) -> ObservedRequest {
        timeout(TIMEOUT, self.requests.recv())
            .await
            .expect("request timeout")
            .expect("server still running")
    }

    async fn shutdown(mut self) {
        self.handle.shutdown();
        // Also cancels axum::serve for the Unix-socket fixture.
        self.task.abort();
        let result = timeout(TIMEOUT, &mut self.task)
            .await
            .expect("shutdown timeout");
        match result {
            Ok(result) => result.expect("server failed"),
            Err(error) => assert!(error.is_cancelled(), "server task failed: {error}"),
        }
    }
}

#[expect(clippy::missing_trait_methods, reason = "We don't use pin drop")]
impl Drop for TestServer {
    fn drop(&mut self) {
        self.handle.shutdown();
        self.task.abort();
    }
}

fn endpoint(base: &Url, browser: &Url, embedded: bool) -> OidcEndpoint {
    let oidc = OpenIdConnectConfiguration {
        token_endpoint: base.join("application/o/token/").expect("token URL").into(),
        introspection_endpoint: base
            .join("application/o/introspect/")
            .expect("introspection URL")
            .into(),
        jwks_uri: base
            .join("application/o/test-app/jwks/")
            .expect("JWKS URL")
            .into(),
        issuer: base.join(ISSUER_PATH).expect("issuer").into(),
        ..Default::default()
    };
    if embedded {
        OidcEndpoint::new(&oidc, Some(browser), None, true)
    } else {
        OidcEndpoint::new(&oidc, Some(base), Some(browser), false)
    }
}

fn assert_request(
    request: &ObservedRequest,
    browser: &Url,
    path: &str,
    expected_form: &[(&str, &str)],
) {
    assert_eq!(request.version, Version::HTTP_11);
    assert_eq!(request.method, Method::POST);
    assert_eq!(request.uri.path(), path);
    assert_eq!(request.headers.get_all(HOST).iter().count(), 1);
    assert_eq!(request.headers[HOST], browser.authority());
    assert_eq!(
        request.form,
        expected_form
            .iter()
            .map(|(key, value)| ((*key).to_owned(), (*value).to_owned()))
            .collect()
    );
}

async fn code_exchange(
    server: &mut TestServer,
    client: &BackchannelClient,
    browser: &Url,
    embedded: bool,
) {
    let ep = endpoint(&server.base, browser, embedded);
    let host = TokenHost::new(browser).expect("token host");
    let token = exchange_code(
        client,
        &ep.token_url,
        Some(&host),
        "authorization-code",
        "https://app.test.goauthentik.io/callback",
        CLIENT_ID,
        SECRET,
    )
    .await
    .expect("exchange code");
    // Assert the actual failure symptom before checking the protocol, so removal
    // of http1_only demonstrates InvalidIssuer rather than only a version change.
    let claims =
        verify_hs256(&token, SECRET, &ep.issuer, CLIENT_ID).expect("public issuer must verify");
    assert_eq!(claims.sub, "test-user");
    let request = server.received().await;
    assert_request(
        &request,
        browser,
        "/application/o/token/",
        &[
            ("grant_type", "authorization_code"),
            ("code", "authorization-code"),
            ("redirect_uri", "https://app.test.goauthentik.io/callback"),
            ("client_id", CLIENT_ID),
            ("client_secret", SECRET),
        ],
    );
    if server.base.authority() == browser.authority() {
        assert!(request.headers.get(X_FORWARDED_PROTO).is_none());
    } else {
        assert_eq!(request.headers[X_FORWARDED_PROTO], browser.scheme());
    }
}

#[tokio::test]
async fn tls_fixture_negotiates_http2_with_an_unrestricted_client() {
    let mut server = TestServer::tcp(true);
    let client = server
        .builder
        .take()
        .expect("builder")
        .build()
        .expect("client");
    let response = client
        .get(server.base.clone())
        .send()
        .await
        .expect("control request");
    assert_eq!(response.version(), Version::HTTP_2);
    assert_eq!(server.received().await.version, Version::HTTP_2);
    server.shutdown().await;
}

#[tokio::test]
async fn code_exchange_preserves_public_issuer_with_an_http2_capable_peer() {
    let mut server = TestServer::tcp(true);
    let client = server.client();
    for browser in [
        Url::parse(BROWSER).expect("browser URL"),
        Url::parse("https://auth.test.goauthentik.io:9443/").expect("non-default public port"),
        Url::parse(&format!("https://{INTERNAL_HOST}/")).expect("same host, different port"),
        server.base.clone(),
    ] {
        code_exchange(&mut server, &client, &browser, false).await;
    }
    server.shutdown().await;
}

#[tokio::test]
async fn client_credentials_preserve_public_issuer_with_an_http2_capable_peer() {
    let mut server = TestServer::tcp(true);
    let client = server.client();
    let browser = Url::parse(BROWSER).expect("browser URL");
    let ep = endpoint(&server.base, &browser, false);
    let host = TokenHost::new(&browser).expect("token host");
    let token = client_credentials_token(
        &client,
        &ep.token_url,
        Some(&host),
        CLIENT_ID,
        "test-user",
        "test-password",
        "openid profile",
    )
    .await
    .expect("exchange credentials")
    .expect("successful grant");
    verify_hs256(&token, SECRET, &ep.issuer, CLIENT_ID).expect("public issuer must verify");
    let request = server.received().await;
    assert_request(
        &request,
        &browser,
        "/application/o/token/",
        &[
            ("grant_type", "client_credentials"),
            ("client_id", CLIENT_ID),
            ("username", "test-user"),
            ("password", "test-password"),
            ("scope", "openid profile"),
        ],
    );
    assert_eq!(request.headers[X_FORWARDED_PROTO], "https");
    server.shutdown().await;
}

#[tokio::test]
async fn introspection_preserves_public_authority_with_an_http2_capable_peer() {
    let mut server = TestServer::tcp(true);
    let client = server.client();
    let browser = Url::parse(BROWSER).expect("browser URL");
    let ep = endpoint(&server.base, &browser, false);
    let host = TokenHost::new(&browser).expect("token host");
    let claims = introspect_token(
        &client,
        &ep.token_introspection,
        Some(&host),
        CLIENT_ID,
        SECRET,
        "bearer-token",
    )
    .await
    .expect("introspect token")
    .expect("active token");
    assert_eq!(claims.sub, "test-user");
    assert_eq!(claims.raw_token, "bearer-token");
    let request = server.received().await;
    assert_request(
        &request,
        &browser,
        "/application/o/introspect/",
        &[
            ("client_id", CLIENT_ID),
            ("client_secret", SECRET),
            ("token", "bearer-token"),
        ],
    );
    assert_eq!(request.headers[X_FORWARDED_PROTO], "https");
    server.shutdown().await;
}

#[tokio::test]
async fn jwks_fetch_uses_the_internal_authority() {
    let mut server = TestServer::tcp(true);
    let client = server.client();
    let ep = endpoint(
        &server.base,
        &Url::parse(BROWSER).expect("browser URL"),
        false,
    );
    assert!(
        fetch_jwks(&client, &ep.jwks_uri)
            .await
            .expect("fetch JWKS")
            .keys
            .is_empty()
    );
    let request = server.received().await;
    assert_eq!(request.version, Version::HTTP_11);
    assert_eq!(request.method, Method::GET);
    assert_eq!(request.uri.path(), "/application/o/test-app/jwks/");
    assert_eq!(request.headers[HOST], server.base.authority());
    assert!(request.headers.get(X_FORWARDED_PROTO).is_none());
    server.shutdown().await;
}

#[tokio::test]
async fn cleartext_backchannel_preserves_https_issuer() {
    let mut server = TestServer::tcp(false);
    let client = server.client();
    code_exchange(
        &mut server,
        &client,
        &Url::parse(BROWSER).expect("browser URL"),
        false,
    )
    .await;
    server.shutdown().await;
}

#[tokio::test]
async fn embedded_backchannel_preserves_unix_socket_and_https_issuer() {
    let directory = tempfile::tempdir().expect("temporary socket directory");
    let mut server = TestServer::unix(&directory.path().join("core.sock"));
    let client = server.client();
    code_exchange(
        &mut server,
        &client,
        &Url::parse(BROWSER).expect("browser URL"),
        true,
    )
    .await;
    server.shutdown().await;
}
