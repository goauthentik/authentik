use axum::{Extension, middleware::AddExtension};
use axum_server::{accept::Accept, tls_rustls::RustlsAcceptor};
use futures::future::BoxFuture;
use tokio::io::{AsyncRead, AsyncWrite};
use tokio_rustls::{rustls::pki_types::CertificateDer, server::TlsStream};
use tower::Layer;

#[derive(Clone, Debug)]
pub struct TlsState {
    pub peer_certificates: Option<Vec<CertificateDer<'static>>>,
}

#[derive(Clone)]
pub struct TlsAcceptor {
    inner: RustlsAcceptor,
}

impl TlsAcceptor {
    pub fn new(inner: RustlsAcceptor) -> Self {
        Self { inner }
    }
}

impl<I, S> Accept<I, S> for TlsAcceptor
where
    I: AsyncRead + AsyncWrite + Unpin + Send + 'static,
    S: Send + 'static,
{
    type Stream = TlsStream<I>;
    type Service = AddExtension<S, TlsState>;
    type Future = BoxFuture<'static, std::io::Result<(Self::Stream, Self::Service)>>;

    fn accept(&self, stream: I, service: S) -> Self::Future {
        let acceptor = self.inner.clone();

        Box::pin(async move {
            let (stream, service) = acceptor.accept(stream, service).await?;
            let server_conn = stream.get_ref().1;
            let tls_state = TlsState {
                peer_certificates: server_conn.peer_certificates().map(|c| c.to_owned()),
            };

            let service = Extension(tls_state).layer(service);

            Ok((stream, service))
        })
    }
}
