use std::{
    path::PathBuf,
    sync::{LazyLock, atomic::Ordering},
    time::Duration,
};

use axum::{
    Extension, Router,
    body::Body,
    extract::{Request, State},
    http::{
        HeaderName, HeaderValue, StatusCode, Uri,
        header::{ACCEPT, CONTENT_TYPE, HOST, RETRY_AFTER},
    },
    middleware::{Next, from_fn},
    response::Response,
};
use http_body_util::BodyExt;
use hyper_unix_socket::UnixSocketConnector;
use hyper_util::{client::legacy::Client, rt::TokioExecutor};
use serde_json::json;
use tower_http::trace::{DefaultMakeSpan, DefaultOnRequest, DefaultOnResponse, TraceLayer};
use tracing::Level;

use crate::{
    axum::{
        accept::tls::TlsState,
        error::Result,
        extract::{client_ip::ClientIP, host::Host, scheme::Scheme, trusted_proxy::TrustedProxy},
    },
    config,
    server::{
        core::websockets::{handle_websocket_upgrade, is_websocket_upgrade},
        gunicorn::GUNICORN_READY,
    },
};

pub(crate) type CoreClient = Client<UnixSocketConnector<PathBuf>, Body>;

static STARTUP_RESPONSE_JSON: LazyLock<Response<String>> = LazyLock::new(|| {
    Response::builder()
        .status(StatusCode::SERVICE_UNAVAILABLE)
        .header(RETRY_AFTER, "5")
        .header(CONTENT_TYPE, "application/json")
        .body(
            json!({
                "error": "authentik starting",
            })
            .to_string(),
        )
        .expect("infallible")
});

static STARTUP_RESPONSE_HTML: LazyLock<Response<String>> = LazyLock::new(|| {
    Response::builder()
        .status(StatusCode::SERVICE_UNAVAILABLE)
        .header(CONTENT_TYPE, "text/html")
        .body(include_str!("../../web/dist/standalone/loading/startup.html").to_owned())
        .expect("infallible")
});

static STARTUP_RESPONSE_PLAIN: LazyLock<Response<String>> = LazyLock::new(|| {
    Response::builder()
        .status(StatusCode::SERVICE_UNAVAILABLE)
        .header(CONTENT_TYPE, "text/plain")
        .body("authentik starting".to_owned())
        .expect("infallible")
});

const SERVER: HeaderName = HeaderName::from_static("server");
const X_FORWARDED_CLIENT_CERT: HeaderName = HeaderName::from_static("x-forwarded-client-cert");
const X_FORWARDED_FOR: HeaderName = HeaderName::from_static("x-forwarded-for");
const X_FORWARDED_PROTO: HeaderName = HeaderName::from_static("x-forwarded-proto");
const X_POWERED_BY: HeaderName = HeaderName::from_static("x-powered-by");

const FORWARD_ALWAYS_REMOVED_HEADERS: [HeaderName; 7] = [
    HeaderName::from_static("forwarded"),
    HeaderName::from_static("host"),
    X_FORWARDED_FOR,
    HeaderName::from_static("x-forwarded-host"),
    X_FORWARDED_PROTO,
    HeaderName::from_static("x-forwarded-scheme"),
    HeaderName::from_static("x-real-ip"),
];
const FORWARD_REMOVED_HEADERS_IF_UNTRUSTED: [HeaderName; 3] = [
    HeaderName::from_static("ssl-client-cert"), // nginx-ingress
    HeaderName::from_static("x-forwarded-tls-client-cert"), // traefik
    X_FORWARDED_CLIENT_CERT,                    // envoy
];

fn startup_response(accept_header: &str) -> Response {
    let response = if accept_header.contains("application/json") {
        STARTUP_RESPONSE_JSON.clone()
    } else if accept_header.contains("text/html") {
        STARTUP_RESPONSE_HTML.clone()
    } else {
        STARTUP_RESPONSE_PLAIN.clone()
    };

    let (parts, body) = response.into_parts();
    Response::from_parts(parts, body.into())
}

async fn forward_request(
    ClientIP(client_ip): ClientIP,
    Host(host): Host,
    Scheme(scheme): Scheme,
    State(client): State<CoreClient>,
    TrustedProxy(trusted_proxy): TrustedProxy,
    tls_state: Option<Extension<TlsState>>,
    mut request: Request,
) -> Result<Response> {
    let accept_header = request
        .headers()
        .get(ACCEPT)
        .map(|v| v.to_str().unwrap_or_default().to_owned())
        .unwrap_or_default();

    if !GUNICORN_READY.load(Ordering::Relaxed) {
        return Ok(startup_response(&accept_header));
    }

    let uri = Uri::builder()
        .scheme("http")
        .authority("localhost:8000")
        .path_and_query(
            request
                .uri()
                .path_and_query()
                .map(|x| x.as_str())
                .unwrap_or_default(),
        )
        .build()?;
    *request.uri_mut() = uri;

    for header_name in FORWARD_ALWAYS_REMOVED_HEADERS {
        request.headers_mut().remove(header_name);
    }
    if !trusted_proxy {
        for header_name in FORWARD_REMOVED_HEADERS_IF_UNTRUSTED {
            request.headers_mut().remove(header_name);
        }
    }

    request.headers_mut().insert(
        X_FORWARDED_FOR,
        HeaderValue::from_str(&client_ip.to_string())?,
    );
    request
        .headers_mut()
        .insert(HOST, HeaderValue::from_str(&host)?);
    request
        .headers_mut()
        .insert(X_FORWARDED_PROTO, HeaderValue::from_str(scheme.as_ref())?);

    if is_websocket_upgrade(request.headers()) {
        return handle_websocket_upgrade(request).await;
    }

    if let Some(tls_state) = tls_state
        && let Some(peer_certificates) = &tls_state.peer_certificates
    {
        let xfcc = peer_certificates
            .iter()
            .map(|cert| {
                let pem_encoded = pem::encode(&pem::Pem::new("CERTIFICATE", cert.as_ref()));
                let url_encoded: String =
                    url::form_urlencoded::byte_serialize(pem_encoded.as_bytes()).collect();
                format!("Cert={url_encoded}")
            })
            .collect::<Vec<_>>()
            .join(",");
        request
            .headers_mut()
            .insert("X_FORWARDED_CLIENT_CERT", HeaderValue::from_str(&xfcc)?);
    }

    match client.request(request).await {
        Ok(res) => {
            let (parts, body) = res.into_parts();
            Ok(Response::from_parts(
                parts,
                Body::from_stream(body.into_data_stream()),
            ))
        }
        Err(_) => Ok(startup_response(&accept_header)),
    }
}

pub(crate) fn build_client() -> CoreClient {
    let config = config::get();
    let connector = UnixSocketConnector::new(super::gunicorn::gunicorn_socket_path());
    Client::builder(TokioExecutor::new())
        .pool_idle_timeout(Duration::from_secs(60))
        .pool_max_idle_per_host(config.web.workers * config.web.threads)
        .set_host(false)
        .build(connector)
}

async fn build_proxy_router() -> Router {
    let client = build_client();

    Router::new().fallback(forward_request).with_state(client)
}

async fn powered_by_middleware(request: Request, next: Next) -> Response {
    let mut response = next.run(request).await;
    response.headers_mut().remove(SERVER);
    response
        .headers_mut()
        .insert(X_POWERED_BY, HeaderValue::from_static("authentik"));
    response
}

// TODO: subpath
pub(super) async fn build_router() -> Router {
    Router::new()
        .merge(super::r#static::build_router().await)
        .layer(
            // TODO: refine this, probably extract it to its own thing to be used with the proxy
            // outpost
            TraceLayer::new_for_http()
                .make_span_with(DefaultMakeSpan::new().level(Level::INFO))
                .on_request(DefaultOnRequest::new().level(Level::INFO))
                .on_response(DefaultOnResponse::new().level(Level::INFO)),
        )
        .merge(build_proxy_router().await)
        .layer(from_fn(powered_by_middleware))
}

mod websockets {
    use axum::{
        body::Body,
        extract::Request,
        http::{
            HeaderMap, HeaderValue, StatusCode,
            header::{
                CONNECTION, SEC_WEBSOCKET_ACCEPT, SEC_WEBSOCKET_KEY, SEC_WEBSOCKET_VERSION, UPGRADE,
            },
        },
        response::{IntoResponse, Response},
    };
    use futures::{SinkExt, StreamExt};
    use hyper_util::rt::TokioIo;
    use tokio::{net::UnixStream, sync::mpsc};
    use tokio_tungstenite::{
        WebSocketStream, client_async,
        tungstenite::{Message, handshake::derive_accept_key, protocol::Role},
    };
    use tracing::{debug, trace, warn};

    use crate::{
        axum::error::{AppError, Result},
        server::gunicorn::gunicorn_socket_path,
    };

    pub(super) fn is_websocket_upgrade(headers: &HeaderMap<HeaderValue>) -> bool {
        let has_upgrade = headers
            .get(UPGRADE)
            .and_then(|v| v.to_str().ok())
            .map(|v| v.eq_ignore_ascii_case("websocket"))
            .unwrap_or(false);

        let has_connection = headers
            .get(CONNECTION)
            .and_then(|v| v.to_str().ok())
            .map(|v| {
                v.split(',')
                    .any(|part| part.trim().eq_ignore_ascii_case("upgrade"))
            })
            .unwrap_or(false);

        let has_websocket_key = headers.contains_key(SEC_WEBSOCKET_KEY);
        let has_websocket_version = headers.contains_key(SEC_WEBSOCKET_VERSION);

        has_upgrade && has_connection && has_websocket_key && has_websocket_version
    }

    pub(super) async fn handle_websocket_upgrade(request: Request) -> Result<Response> {
        let ws_key = match request
            .headers()
            .get(SEC_WEBSOCKET_KEY)
            .and_then(|key| key.to_str().ok())
        {
            Some(key) => key,
            None => return Ok((StatusCode::BAD_REQUEST, "").into_response()),
        };

        let ws_accept = derive_accept_key(ws_key.as_bytes());

        let path_q = request
            .uri()
            .path_and_query()
            .map(|x| x.as_str())
            .unwrap_or_default();
        let uri = format!("ws://localhost:8000{path_q}");

        let mut ws_request =
            tokio_tungstenite::tungstenite::handshake::client::Request::builder().uri(uri);
        for (k, v) in request.headers() {
            ws_request = ws_request.header(k.as_str(), v);
        }
        let ws_request = ws_request.body(())?;

        let response = Response::builder()
            .status(StatusCode::SWITCHING_PROTOCOLS)
            .header(UPGRADE, "websocket")
            .header(CONNECTION, "upgrade")
            .header(SEC_WEBSOCKET_ACCEPT, ws_accept)
            .body(Body::empty())?;

        tokio::spawn(async move {
            if let Err(err) = handle_websocket_connection(request, ws_request).await {
                warn!("WebSocket connection error: {}", err.0);
            }
        });

        Ok(response)
    }

    async fn handle_websocket_connection(
        request: Request,
        ws_request: tokio_tungstenite::tungstenite::handshake::client::Request,
    ) -> Result<()> {
        let upgraded = hyper::upgrade::on(request).await?;
        let io = TokioIo::new(upgraded);
        let client_ws = WebSocketStream::from_raw_socket(io, Role::Server, None).await;

        let upstream_ws = {
            let stream = UnixStream::connect(gunicorn_socket_path()).await?;
            let (ws_stream, _) = client_async(ws_request, stream).await?;
            ws_stream
        };

        let (mut client_sender, mut client_receiver) = client_ws.split();
        let (mut upstream_sender, mut upstream_receiver) = upstream_ws.split();

        let (close_tx, mut close_rx) = mpsc::channel::<()>(1);
        let close_tx_upstream = close_tx.clone();

        let client_to_upstream = tokio::spawn(async move {
            let mut client_closed = false;
            while let Some(msg) = client_receiver.next().await {
                let msg = msg?;
                match msg {
                    Message::Close(_) => {
                        if !client_closed {
                            upstream_sender.send(Message::Close(None)).await?;
                            close_tx.send(()).await.ok();
                            client_closed = true;
                            break;
                        }
                    }
                    msg @ Message::Binary(_)
                    | msg @ Message::Text(_)
                    | msg @ Message::Ping(_)
                    | msg @ Message::Pong(_) => {
                        if !client_closed {
                            upstream_sender.send(msg).await?;
                        }
                    }
                    Message::Frame(_) => {}
                }
            }
            if !client_closed {
                upstream_sender.send(Message::Close(None)).await?;
                close_tx.send(()).await.ok();
            }
            Ok::<_, AppError>(())
        });

        let upstream_to_client = tokio::spawn(async move {
            let mut upstream_closed = false;
            while let Some(msg) = upstream_receiver.next().await {
                let msg = msg?;
                match msg {
                    Message::Close(_) => {
                        if !upstream_closed {
                            client_sender.send(Message::Close(None)).await?;
                            close_tx_upstream.send(()).await.ok();
                            upstream_closed = true;
                            break;
                        }
                    }
                    msg @ Message::Binary(_)
                    | msg @ Message::Text(_)
                    | msg @ Message::Ping(_)
                    | msg @ Message::Pong(_) => {
                        if !upstream_closed {
                            client_sender.send(msg).await?;
                        }
                    }
                    Message::Frame(_) => {}
                }
            }
            if !upstream_closed {
                client_sender.send(Message::Close(None)).await?;
                close_tx_upstream.send(()).await.ok();
            }
            Ok::<_, AppError>(())
        });

        tokio::select! {
            _ = close_rx.recv() => {
                trace!("WebSocket connection closed gracefully");
            },
            res = client_to_upstream => {
                if let Err(err) = res {
                    debug!("Client to upstream task failed: {:?}", err);
                }
            }
            res = upstream_to_client => {
                if let Err(err) = res {
                    debug!("Upstream to client task failed: {:?}", err);
                }
            }
        }

        Ok(())
    }
}

pub(crate) mod tls {
    use arc_swap::ArcSwap;
    use eyre::{Result, eyre};
    use rustls::{
        RootCertStore,
        crypto::CryptoProvider,
        pki_types::{CertificateDer, PrivateKeyDer},
        server::{ClientHello, WebPkiClientVerifier, danger::ClientCertVerifier},
        sign::CertifiedKey,
    };
    use rustls_pemfile::{certs, private_key};
    use std::ops::Deref;
    use std::{
        collections::{HashMap, hash_map::Entry},
        io::BufReader,
        sync::Arc,
        time::Duration,
    };
    use tracing::{debug, warn};

    use crate::{
        arbiter::{Arbiter, Tasks},
        db,
    };

    #[derive(Debug)]
    struct Certificate {
        certificate_data: String,
        key_data: String,
    }

    #[derive(Debug)]
    struct Brand {
        domain: String,
        default: bool,
        web_certificate: Option<Arc<CertifiedKey>>,
        client_certificates: Vec<Certificate>,
    }

    #[derive(Debug)]
    pub(crate) struct CertificateManager {
        brands: ArcSwap<Vec<Brand>>,
        client_verifier: ArcSwap<Arc<dyn ClientCertVerifier>>,
    }

    async fn fetch_brands() -> Result<Vec<Brand>> {
        #[derive(sqlx::FromRow)]
        struct BrandRow {
            brand_uuid: uuid::Uuid,
            domain: String,
            default: bool,
            web_cert_data: Option<String>,
            web_cert_key: Option<String>,
            client_cert_data: Option<String>,
            client_cert_key: Option<String>,
        }

        let rows = sqlx::query_as::<_, BrandRow>(
            "
            SELECT
                b.brand_uuid,
                b.domain,
                b.default,
                wc.certificate_data AS web_cert_data,
                wc.key_data AS web_cert_key,
                cc.certificate_data AS client_cert_data,
                cc.key_data AS client_cert_key
            FROM authentik_brands_brand b
            LEFT JOIN authentik_crypto_certificatekeypair wc
                ON wc.kp_uuid = b.web_certificate_id
            LEFT JOIN authentik_brands_brand_client_certificates bcc
                ON bcc.brand_id = b.brand_uuid
            LEFT JOIN authentik_crypto_certificatekeypair cc
                ON cc.kp_uuid = bcc.certificatekeypair_id
        ",
        )
        .fetch_all(db::get())
        .await?;

        let mut brands = HashMap::new();

        for row in rows {
            let BrandRow {
                brand_uuid,
                domain,
                default,
                web_cert_data,
                web_cert_key,
                client_cert_data,
                client_cert_key,
            } = row;
            let brand = match brands.entry(brand_uuid) {
                Entry::Occupied(e) => e.into_mut(),
                Entry::Vacant(e) => e.insert(Brand {
                    domain,
                    default,
                    web_certificate: match (web_cert_data, web_cert_key) {
                        (Some(certificate_data), Some(key_data)) => {
                            let cert_chain: Vec<CertificateDer<'static>> =
                                certs(&mut BufReader::new(certificate_data.as_bytes()))
                                    .collect::<Result<Vec<_>, _>>()?;
                            let key_der: PrivateKeyDer<'static> =
                                private_key(&mut BufReader::new(key_data.as_bytes()))?
                                    .ok_or(eyre!("no private key found"))?;
                            let provider = CryptoProvider::get_default()
                                .expect("no rustls provider installed");
                            Some(Arc::new(CertifiedKey::new(
                                cert_chain,
                                provider.key_provider.load_private_key(key_der)?,
                            )))
                        }
                        _ => None,
                    },
                    client_certificates: vec![],
                }),
            };

            if let (Some(certificate_data), Some(key_data)) = (client_cert_data, client_cert_key) {
                brand.client_certificates.push(Certificate {
                    certificate_data,
                    key_data,
                });
            }
        }

        Ok(brands.into_values().collect())
    }

    async fn watch_brands(arbiter: Arbiter, manager: Arc<CertificateManager>) -> Result<()> {
        tokio::select! {
            _ = db::wait_for_required_tables() => {},
            _ = arbiter.shutdown() => return Ok(()),
        };

        loop {
            debug!("refreshing brands certificates");
            tokio::select! {
                res = fetch_brands() => match res {
                    Ok(brands) => manager.brands.store(Arc::new(brands)),
                    Err(err) => warn!("error fetching brands, retrying in 1 minute: {err:?}"),
                },
                _ = arbiter.shutdown() => return Ok(()),
            }

            tokio::select! {
                _ = tokio::time::sleep(Duration::from_secs(60)) => {},
                _ = arbiter.shutdown() => return Ok(()),
            }
        }
    }

    pub(crate) async fn init(tasks: &mut Tasks) -> Result<Arc<CertificateManager>> {
        let arbiter = tasks.arbiter();
        let manager = Arc::new(CertificateManager::new()?);
        tasks
            .build_task()
            .name(&format!("{}::watch_brands", module_path!(),))
            .spawn(watch_brands(arbiter, manager.clone()))?;

        Ok(manager)
    }

    impl CertificateManager {
        fn new() -> Result<Self> {
            Ok(Self {
                brands: ArcSwap::from_pointee(Vec::new()),
                client_verifier: ArcSwap::from_pointee(
                    WebPkiClientVerifier::builder(Arc::new(RootCertStore::empty()))
                        .allow_unauthenticated()
                        .build()?,
                ),
            })
        }

        pub(crate) fn resolve(&self, client_hello: &ClientHello<'_>) -> Option<Arc<CertifiedKey>> {
            let server_name = client_hello.server_name()?;
            let mut best = None;

            for brand in self.brands.load().deref().iter() {
                if let Some(cert) = &brand.web_certificate {
                    if best.is_none() && brand.default {
                        best = Some(Arc::clone(cert));
                    }
                    if server_name == brand.domain
                        || server_name.ends_with(&format!(".{}", brand.domain))
                    {
                        best = Some(Arc::clone(cert));
                    }
                }
            }

            best
        }
    }

    impl ClientCertVerifier for CertificateManager {
        fn root_hint_subjects(&self) -> &[rustls::DistinguishedName] {
            let hints = self
                .client_verifier
                .load_full()
                .root_hint_subjects()
                .to_owned();
            hints
        }

        fn verify_client_cert(
            &self,
            end_entity: &CertificateDer<'_>,
            intermediates: &[CertificateDer<'_>],
            now: rustls::pki_types::UnixTime,
        ) -> std::result::Result<rustls::server::danger::ClientCertVerified, rustls::Error>
        {
            self.client_verifier
                .load()
                .verify_client_cert(end_entity, intermediates, now)
        }

        fn verify_tls12_signature(
            &self,
            message: &[u8],
            cert: &CertificateDer<'_>,
            dss: &rustls::DigitallySignedStruct,
        ) -> std::result::Result<rustls::client::danger::HandshakeSignatureValid, rustls::Error>
        {
            self.client_verifier
                .load()
                .verify_tls12_signature(message, cert, dss)
        }

        fn verify_tls13_signature(
            &self,
            message: &[u8],
            cert: &CertificateDer<'_>,
            dss: &rustls::DigitallySignedStruct,
        ) -> std::result::Result<rustls::client::danger::HandshakeSignatureValid, rustls::Error>
        {
            self.client_verifier
                .load()
                .verify_tls13_signature(message, cert, dss)
        }

        fn supported_verify_schemes(&self) -> Vec<rustls::SignatureScheme> {
            self.client_verifier.load().supported_verify_schemes()
        }

        fn offer_client_auth(&self) -> bool {
            self.client_verifier.load().offer_client_auth()
        }

        fn client_auth_mandatory(&self) -> bool {
            self.client_verifier.load().client_auth_mandatory()
        }

        fn requires_raw_public_keys(&self) -> bool {
            self.client_verifier.load().requires_raw_public_keys()
        }
    }
}
