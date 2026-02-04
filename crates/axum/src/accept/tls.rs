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
pub struct TlsAcceptor<A> {
    inner: RustlsAcceptor<A>,
}

impl<A> TlsAcceptor<A> {
    pub fn new(inner: RustlsAcceptor<A>) -> Self {
        Self { inner }
    }
}

impl<A, I, S> Accept<I, S> for TlsAcceptor<A>
where
    A: Accept<I, S> + Clone + Send + 'static,
    A::Stream: AsyncRead + AsyncWrite + Unpin + Send,
    A::Service: Send,
    A::Future: Send,
    I: AsyncRead + AsyncWrite + Unpin + Send + 'static,
    S: Send + 'static,
{
    type Future = BoxFuture<'static, std::io::Result<(Self::Stream, Self::Service)>>;
    type Service = AddExtension<A::Service, TlsState>;
    type Stream = TlsStream<A::Stream>;

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
