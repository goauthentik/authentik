use std::{
    net::SocketAddr,
    process::Stdio,
    sync::{
        Arc,
        atomic::{AtomicBool, Ordering},
    },
    time::Duration,
};

use argh::FromArgs;
use authentik_axum::{
    accept::{
        proxy_protocol::ProxyProtocolAcceptor,
        tls::{TlsAcceptor, TlsState},
    },
    extract::{ClientIP, Host, Scheme},
};
use authentik_config::get_config;
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
use nix::{
    sys::signal::{Signal, kill},
    unistd::Pid,
};
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
    process::{Child, Command},
    signal::unix::SignalKind,
    sync::{
        RwLock,
        broadcast::{self, error::RecvError},
    },
    task::JoinSet,
};
use tokio_util::sync::CancellationToken;
use tower::ServiceExt;
use tower_http::trace::{DefaultMakeSpan, DefaultOnRequest, DefaultOnResponse, TraceLayer};
use tracing::{Level, info, warn};

mod r#static;

struct ServerState {
    gunicorn: Child,
    handles: Vec<Handle<SocketAddr>>,
}

impl ServerState {
    fn new(handles: Vec<Handle<SocketAddr>>) -> Result<Self> {
        Ok(Self {
            gunicorn: Command::new("gunicorn")
                .args([
                    "-c",
                    "./lifecycle/gunicorn.conf.py",
                    "authentik.root.asgi:application",
                ])
                // TODO: catch those
                .stdout(Stdio::inherit())
                .stderr(Stdio::inherit())
                .spawn()?,
            handles,
        })
    }

    async fn shutdown(&mut self, signal: Signal) -> Result<()> {
        if let Some(id) = self.gunicorn.id() {
            kill(Pid::from_raw(id as i32), signal)?;
        }
        self.gunicorn.wait().await?;
        Ok(())
    }

    async fn graceful_shutdown(&mut self) -> Result<()> {
        for handle in &self.handles {
            // TODO: make configurable
            handle.graceful_shutdown(Some(Duration::from_secs(30)));
        }
        self.shutdown(Signal::SIGTERM).await
    }

    async fn fast_shutdown(&mut self) -> Result<()> {
        for handle in &self.handles {
            handle.shutdown();
        }
        self.shutdown(Signal::SIGINT).await
    }
}

#[derive(Debug, FromArgs, PartialEq)]
/// Run the authentik server.
#[argh(subcommand, name = "server")]
pub struct Cli {}

async fn gunicorn_socket_ready() -> bool {
    let socket_path = std::env::temp_dir().join("authentik-core.sock");
    tokio::net::UnixStream::connect(socket_path).await.is_ok()
}

async fn watch_gunicorn(
    state_lock: Arc<RwLock<ServerState>>,
    stop: CancellationToken,
    signals_tx: broadcast::Sender<SignalKind>,
    gunicorn_ready: Arc<AtomicBool>,
) -> Result<()> {
    let mut signals_rx = signals_tx.subscribe();
    loop {
        tokio::select! {
            signal = signals_rx.recv() => {
                match signal {
                    Ok(signal) => {
                        let mut state = state_lock.write().await;
                        if signal == SignalKind::interrupt() {
                            state.fast_shutdown().await?;
                            return Ok(())
                        } else if signal == SignalKind::terminate() {
                            state.graceful_shutdown().await?;
                            return Ok(())
                        } else if signal == SignalKind::user_defined1()
                        {
                            info!("gunicorn is marked ready for operation");
                            gunicorn_ready.store(true, Ordering::Relaxed);
                        }
                    }
                    Err(RecvError::Lagged(_)) => continue,
                    Err(RecvError::Closed) => {
                        let mut state = state_lock.write().await;
                        state.fast_shutdown().await?;
                        return Ok(());
                    }
                }
            },
            _ = tokio::time::sleep(Duration::from_secs(1)), if !gunicorn_ready.load(Ordering::Relaxed) => {
                // On some platforms the SIGUSR1 readiness signal can be missed.
                // Fall back to probing the gunicorn unix socket and mark ready once it accepts connections.
                if gunicorn_socket_ready().await {
                    info!("gunicorn socket is accepting connections, marking ready");
                    gunicorn_ready.store(true, Ordering::Relaxed);
                }
            },
            _ = tokio::time::sleep(Duration::from_secs(15)) => {
                let mut state = state_lock.write().await;
                let try_wait = state.gunicorn.try_wait();
                match try_wait {
                    // Gunicorn has exited. stop as soon as possible
                    Ok(Some(code)) => {
                        state.fast_shutdown().await?;
                        return Err(eyre!("gunicorn has exited unexpectedly with status {code}"));
                    }
                    // Gunicorn is still running, or we failed to check the status
                    Ok(None) => continue,
                    Err(err) => {
                        warn!("failed to check the status of gunicorn process, ignoring: {err}");
                        continue;
                    },
                }
            },
            _ = stop.cancelled() => {
                let mut state = state_lock.write().await;
                state.fast_shutdown().await?;
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
            .body(include_str!("../../../web/dist/standalone/loading/startup.html").into())
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
    tls_state: Option<Extension<TlsState>>,
    req: Request,
) -> Response {
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
            if e.is_connect()
                || matches!(
                    e.to_string().as_str(),
                    "client error (SendRequest)" | "client error (ChannelClosed)"
                )
            {
                return startup_response(&accept);
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
            && authentik_proxy::can_handle(&request)
        {
            proxy_router.oneshot(request).await
        } else {
            core_router.oneshot(request).await
        }
    }))
}

async fn start_server_plain(
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

async fn start_server_tls(
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

pub async fn run(
    _cli: Cli,
    tasks: &mut JoinSet<Result<()>>,
    stop: CancellationToken,
    signals_tx: broadcast::Sender<SignalKind>,
) -> Result<()> {
    let gunicorn_ready = Arc::new(AtomicBool::new(false));
    let config = get_config().await;
    let router = build_router(Arc::clone(&gunicorn_ready)).await;
    let tls_config = RustlsConfig::from_config(Arc::new(make_tls_config()?));

    let mut handles = Vec::with_capacity(
        config.listen.http.len() + config.listen.https.len() + config.listen.metrics.len(),
    );

    config.listen.http.iter().for_each(|addr| {
        let handle = Handle::new();
        tasks.spawn(start_server_plain(router.clone(), *addr, handle.clone()));
        handles.push(handle);
    });

    config.listen.https.iter().for_each(|addr| {
        let handle = Handle::new();
        tasks.spawn(start_server_tls(
            router.clone(),
            *addr,
            tls_config.clone(),
            handle.clone(),
        ));
        handles.push(handle);
    });

    let state_lock = Arc::new(RwLock::new(ServerState::new(handles)?));
    tasks.spawn(watch_gunicorn(
        Arc::clone(&state_lock),
        stop.clone(),
        signals_tx,
        gunicorn_ready,
    ));

    Ok(())
}
