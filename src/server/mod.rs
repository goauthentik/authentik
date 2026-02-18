use std::{
    net::SocketAddr,
    sync::{
        Arc,
        atomic::{AtomicBool, Ordering},
    },
    time::Duration,
};

use argh::FromArgs;
use axum::{
    Extension, Router,
    body::Body,
    extract::{Request, State},
    http::{
        HeaderName, StatusCode, Uri,
        header::{CONTENT_TYPE, RETRY_AFTER},
    },
    response::Response,
    routing::any,
};
use axum_server::{
    Handle,
    accept::DefaultAcceptor,
    tls_rustls::{RustlsAcceptor, RustlsConfig},
};
use eyre::{Result, eyre};
use http_body_util::BodyExt;
use hyper_unix_socket::UnixSocketConnector;
use hyper_util::{client::legacy::Client, rt::TokioExecutor};
use rcgen::{
    Certificate, CertificateParams, DistinguishedName, DnType, ExtendedKeyUsagePurpose, KeyPair,
    KeyUsagePurpose, PKCS_ECDSA_P256_SHA256, SanType, SignatureAlgorithm,
};
use rustls::{
    ServerConfig,
    crypto::aws_lc_rs::sign::any_supported_type,
    pki_types::{CertificateDer, PrivateKeyDer},
    server::{ClientHello, ResolvesServerCert},
    sign::CertifiedKey,
};
use serde_json::json;
use tokio::{
    signal::unix::SignalKind,
    sync::{RwLock, broadcast::error::RecvError},
};
use tower::ServiceExt;
use tower_http::trace::{DefaultMakeSpan, DefaultOnRequest, DefaultOnResponse, TraceLayer};
use tracing::{Level, info};

use crate::{
    arbiter::{Arbiter, Tasks},
    axum::{
        accept::{
            proxy_protocol::ProxyProtocolAcceptor,
            tls::{TlsAcceptor, TlsState},
        },
        extract::{client_ip::ClientIP, host::Host, scheme::Scheme},
    },
    config::get_config,
};

mod gunicorn;
mod r#static;

struct ServerState {
    gunicorn: gunicorn::Gunicorn,
    handles: Vec<Handle<SocketAddr>>,
}

impl ServerState {
    fn new(handles: Vec<Handle<SocketAddr>>) -> Result<Self> {
        Ok(Self {
            gunicorn: gunicorn::Gunicorn::new()?,
            handles,
        })
    }

    async fn graceful_shutdown(&mut self) -> Result<()> {
        for handle in &self.handles {
            // TODO: make configurable
            handle.graceful_shutdown(Some(Duration::from_secs(30)));
        }
        self.gunicorn.graceful_shutdown().await
    }

    async fn fast_shutdown(&mut self) -> Result<()> {
        for handle in &self.handles {
            handle.shutdown();
        }
        self.gunicorn.fast_shutdown().await
    }
}

#[derive(Debug, FromArgs, PartialEq)]
/// Run the authentik server.
#[argh(subcommand, name = "server")]
pub(super) struct Cli {}

async fn gunicorn_socket_ready() -> bool {
    let socket_path = std::env::temp_dir().join("authentik-core.sock");
    tokio::net::UnixStream::connect(socket_path).await.is_ok()
}

async fn watch_server_and_gunicorn(
    state_lock: Arc<RwLock<ServerState>>,
    arbiter: Arbiter,
    gunicorn_ready: Arc<AtomicBool>,
) -> Result<()> {
    let mut signals_rx = arbiter.signals_subscribe();
    loop {
        tokio::select! {
            signal = signals_rx.recv() => {
                match signal {
                    Ok(signal) => {
                        if signal == SignalKind::user_defined1() {
                            info!("gunicorn is marked ready for operation");
                            gunicorn_ready.store(true, Ordering::Relaxed);
                        }
                    },
                    Err(RecvError::Lagged(_)) => continue,
                    Err(RecvError::Closed) => {
                        return Err(RecvError::Closed.into());
                    }
                }
            },
            _ = tokio::time::sleep(Duration::from_secs(1)), if !gunicorn_ready.load(Ordering::Relaxed) => {
                // On some platforms the SIGUSR1 can be missed.
                // Fall back to probing the gunicorn unix socket and mark ready once it accepts connections.
                if gunicorn_socket_ready().await {
                    info!("gunicorn socket is accepting connections, marking ready");
                    gunicorn_ready.store(true, Ordering::Relaxed);
                }
            },
            _ = tokio::time::sleep(Duration::from_secs(15)) => {
                let mut state = state_lock.write().await;
                if !state.gunicorn.is_alive().await {
                    return Err(eyre!("gunicorn has exited unexpectedly"));
                }
            },
            _ = arbiter.fast_shutdown() => {
                let mut state = state_lock.write().await;
                state.fast_shutdown().await?;
                return Ok(());
            },
            _ = arbiter.graceful_shutdown() => {
                let mut state = state_lock.write().await;
                state.graceful_shutdown().await?;
                return Ok(());
            },
        }
    }
}

#[derive(Clone, Debug)]
struct CoreRouterState {
    client: Client<UnixSocketConnector<std::path::PathBuf>, Body>,
    gunicorn_ready: Arc<AtomicBool>,
}

fn startup_response(accept: &str) -> Response {
    let mut response = Response::builder();
    response = response.status(StatusCode::SERVICE_UNAVAILABLE);

    if accept.contains("application/json") {
        response = response.header(RETRY_AFTER, "5");
        response = response.header(CONTENT_TYPE, "application/json");
        response
            .body(
                json!({
                    "error": "authentik starting",
                })
                .to_string()
                .into(),
            )
            .unwrap()
    } else if accept.contains("text/html") {
        response = response.header(CONTENT_TYPE, "text/html");
        response
            .body(include_str!("../../web/dist/standalone/loading/startup.html").into())
            .unwrap()
    } else {
        response = response.header(CONTENT_TYPE, "text/plain");
        response.body("authentik starting".into()).unwrap()
    }
}

async fn forward_request(
    ClientIP(client_ip): ClientIP,
    Host(host): Host,
    Scheme(scheme): Scheme,
    State(state): State<CoreRouterState>,
    _tls_state: Option<Extension<TlsState>>,
    req: Request,
) -> Response {
    // TODO: tls state
    let accept = req
        .headers()
        .get("accept")
        .map(|v| v.to_str().unwrap_or(""))
        .unwrap_or("")
        .to_string();

    if !state.gunicorn_ready.load(Ordering::Relaxed) {
        return startup_response(&accept);
    }

    let path_q = req.uri().path_and_query().map(|x| x.as_str()).unwrap_or("");

    let uri = Uri::builder()
        .scheme("http")
        .authority("localhost:8000")
        .path_and_query(path_q)
        .build()
        .unwrap();

    let forward_req = {
        let mut builder = Request::builder().method(req.method().clone()).uri(uri);

        let ignore_headers = &[
            HeaderName::from_static("forwarded"),
            HeaderName::from_static("host"),
            HeaderName::from_static("x-forwarded-for"),
            HeaderName::from_static("x-forwarded-host"),
            HeaderName::from_static("x-forwarded-proto"),
            HeaderName::from_static("x-forwarded-scheme"),
            HeaderName::from_static("x-real-ip"),
        ];

        for (key, value) in req.headers() {
            if !ignore_headers.contains(key) {
                builder = builder.header(key, value);
            }
        }
        builder = builder.header("X-Forwarded-For", client_ip.to_string());
        builder = builder.header("Host", host);
        builder = builder.header("X-Forwarded-Proto", scheme.to_string());

        let (_, body) = req.into_parts();
        builder.body(body).unwrap()
    };

    match state.client.request(forward_req).await {
        Ok(res) => {
            let (parts, body) = res.into_parts();
            let body = Body::from_stream(body.into_data_stream());

            let mut response = Response::new(body);
            *response.status_mut() = parts.status;
            *response.version_mut() = parts.version;
            *response.headers_mut() = parts.headers;
            response
        }
        Err(e) => {
            let backend_transport_error = e.is_connect()
                || matches!(
                    e.to_string().as_str(),
                    "client error (SendRequest)" | "client error (ChannelClosed)"
                );

            if backend_transport_error {
                // Treat transport errors as "starting" only if gunicorn is actually unreachable.
                if !gunicorn_socket_ready().await {
                    return startup_response(&accept);
                }
            }
            let error_msg = e.to_string();
            Response::builder()
                .status(StatusCode::BAD_GATEWAY)
                .body(Body::from(error_msg))
                .unwrap()
        }
    }
}

async fn build_core_proxy_router(gunicorn_ready: Arc<AtomicBool>) -> Router {
    let connector = UnixSocketConnector::new(std::env::temp_dir().join("authentik-core.sock"));
    let client = Client::builder(TokioExecutor::new())
        .pool_idle_timeout(Duration::from_secs(60))
        .pool_max_idle_per_host(get_config().await.web.workers * get_config().await.web.threads)
        .set_host(false)
        .build(connector);

    let state = CoreRouterState {
        client,
        gunicorn_ready,
    };

    Router::new().fallback(forward_request).with_state(state)
}

// TODO: subpath
async fn build_core_router(gunicorn_ready: Arc<AtomicBool>) -> Router {
    Router::new()
        .merge(r#static::build_router().await)
        .layer(
            // TODO: refine this, probably extract it to its own thing to be used with the proxy
            // outpost
            TraceLayer::new_for_http()
                .make_span_with(DefaultMakeSpan::new().level(Level::INFO))
                .on_request(DefaultOnRequest::new().level(Level::INFO))
                .on_response(DefaultOnResponse::new().level(Level::INFO)),
        )
        .merge(build_core_proxy_router(gunicorn_ready).await)
}

async fn build_router(gunicorn_ready: Arc<AtomicBool>) -> Router {
    let core_router = build_core_router(gunicorn_ready).await;
    let proxy_router: Option<Router> = None;

    Router::new().fallback(any(|request: Request<Body>| async move {
        if let Some(proxy_router) = proxy_router
            && crate::proxy::can_handle(&request)
        {
            proxy_router.oneshot(request).await
        } else {
            core_router.oneshot(request).await
        }
    }))
}

async fn run_server_plain(
    router: Router,
    addr: SocketAddr,
    handle: Handle<SocketAddr>,
) -> Result<()> {
    axum_server::Server::bind(addr)
        .acceptor(ProxyProtocolAcceptor::new().acceptor(DefaultAcceptor::new()))
        .handle(handle)
        .serve(router.into_make_service_with_connect_info::<SocketAddr>())
        .await?;

    Ok(())
}

async fn run_server_tls(
    router: Router,
    addr: SocketAddr,
    config: RustlsConfig,
    handle: Handle<SocketAddr>,
) -> Result<()> {
    axum_server::Server::bind(addr)
        .acceptor(TlsAcceptor::new(RustlsAcceptor::new(config).acceptor(
            ProxyProtocolAcceptor::new().acceptor(DefaultAcceptor::new()),
        )))
        .handle(handle)
        .serve(router.into_make_service_with_connect_info::<SocketAddr>())
        .await?;

    Ok(())
}

fn generate_self_signed_cert(alg: &'static SignatureAlgorithm) -> Result<(Certificate, KeyPair)> {
    let signing_key = KeyPair::generate_for(alg)?;

    let mut params: CertificateParams = Default::default();
    params.not_before = time::OffsetDateTime::now_utc();
    params.not_after = time::OffsetDateTime::now_utc() + time::Duration::days(365);
    params.distinguished_name = {
        let mut dn = DistinguishedName::new();
        dn.push(DnType::OrganizationName, "authentik");
        dn.push(DnType::CommonName, "authentik default certificate");
        dn
    };
    params.subject_alt_names = vec![SanType::DnsName("*".try_into().unwrap())];
    params.key_usages = vec![
        KeyUsagePurpose::DigitalSignature,
        KeyUsagePurpose::KeyEncipherment,
    ];
    params.extended_key_usages = vec![ExtendedKeyUsagePurpose::ServerAuth];

    let cert = params.self_signed(&signing_key)?;

    Ok((cert, signing_key))
}

#[derive(Debug)]
struct CertResolver {
    fallback: Arc<CertifiedKey>,
}

impl CertResolver {
    fn new() -> Result<Self> {
        let (cert, keypair) = generate_self_signed_cert(&PKCS_ECDSA_P256_SHA256)?;

        let cert_der = cert.der().to_vec();
        let key_der = keypair.serialize_der();

        let private_key =
            PrivateKeyDer::try_from(key_der).map_err(|_| rcgen::Error::CouldNotParseKeyPair)?;
        let signing_key =
            any_supported_type(&private_key).map_err(|_| rcgen::Error::CouldNotParseKeyPair)?;

        Ok(Self {
            fallback: Arc::new(CertifiedKey::new(
                vec![CertificateDer::from(cert_der)],
                signing_key,
            )),
        })
    }
}

impl ResolvesServerCert for CertResolver {
    fn resolve(&self, _client_hello: ClientHello<'_>) -> Option<Arc<CertifiedKey>> {
        Some(Arc::clone(&self.fallback))
    }
}

fn make_tls_config() -> Result<ServerConfig> {
    let resolver = CertResolver::new()?;
    let config = ServerConfig::builder()
        .with_no_client_auth()
        .with_cert_resolver(Arc::new(resolver));
    Ok(config)
}

pub(super) async fn run(_cli: Cli, tasks: &mut Tasks) -> Result<()> {
    let gunicorn_ready = Arc::new(AtomicBool::new(false));
    let config = get_config().await;
    let router = build_router(Arc::clone(&gunicorn_ready)).await;
    let tls_config = RustlsConfig::from_config(Arc::new(make_tls_config()?));

    let metrics_router = crate::metrics::build_router();

    let mut handles = Vec::with_capacity(
        config.listen.http.len() + config.listen.https.len() + config.listen.metrics.len(),
    );

    config.listen.http.iter().copied().try_for_each(|addr| {
        let handle = Handle::new();
        let res = tasks
            .build_task()
            .name(&format!("{}::run_server_plain({})", module_path!(), addr))
            .spawn(run_server_plain(router.clone(), addr, handle.clone()))
            .map(|_| ());
        handles.push(handle);
        res
    })?;

    config.listen.https.iter().copied().try_for_each(|addr| {
        let handle = Handle::new();
        let res = tasks
            .build_task()
            .name(&format!("{}::run_server_tls({})", module_path!(), addr))
            .spawn(run_server_tls(
                router.clone(),
                addr,
                tls_config.clone(),
                handle.clone(),
            ))
            .map(|_| ());
        handles.push(handle);
        res
    })?;

    config.listen.metrics.iter().copied().try_for_each(|addr| {
        let handle = Handle::new();
        let res = tasks
            .build_task()
            .name(&format!("{}::metrics({})", module_path!(), addr))
            .spawn(crate::metrics::start_server(
                metrics_router.clone(),
                addr,
                handle.clone(),
            ))
            .map(|_| ());
        handles.push(handle);
        res
    })?;

    let state_lock = Arc::new(RwLock::new(ServerState::new(handles)?));
    let arbiter = tasks.arbiter();
    tasks
        .build_task()
        .name(&format!("{}::watch_server_and_gunicorn", module_path!()))
        .spawn(watch_server_and_gunicorn(
            Arc::clone(&state_lock),
            arbiter,
            gunicorn_ready,
        ))?;

    Ok(())
}
