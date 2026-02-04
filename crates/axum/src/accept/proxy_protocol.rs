use std::{io, time::Duration};

use authentik_tokio::proxy_protocol::{ProxyProtocolStream, header::Header};
use axum::{Extension, middleware::AddExtension};
use axum_server::accept::{Accept, DefaultAcceptor};
use futures::future::BoxFuture;
use tokio::io::{AsyncRead, AsyncWrite};
use tower::Layer;

#[derive(Clone, Debug)]
pub struct ProxyProtocolState {
    pub header: Option<Header<'static>>,
}

#[derive(Clone)]
pub struct ProxyProtocolAcceptor<A = DefaultAcceptor> {
    inner: A,
    parsing_timeout: Duration,
}

impl ProxyProtocolAcceptor {
    pub fn new() -> Self {
        let inner = DefaultAcceptor::new();

        #[cfg(not(test))]
        let parsing_timeout = Duration::from_secs(10);

        // Don't force tests to wait too long
        #[cfg(test)]
        let parsing_timeout = Duration::from_secs(1);

        Self {
            inner,
            parsing_timeout,
        }
    }
}

impl Default for ProxyProtocolAcceptor {
    fn default() -> Self {
        Self::new()
    }
}

impl<A> ProxyProtocolAcceptor<A> {
    pub fn acceptor<Acceptor>(self, acceptor: Acceptor) -> ProxyProtocolAcceptor<Acceptor> {
        ProxyProtocolAcceptor {
            inner: acceptor,
            parsing_timeout: self.parsing_timeout,
        }
    }
}

impl<A, I, S> Accept<I, S> for ProxyProtocolAcceptor<A>
where
    A: Accept<I, S> + Clone + Send + 'static,
    A::Stream: AsyncRead + AsyncWrite + Unpin + Send,
    A::Service: Send,
    A::Future: Send,
    I: AsyncRead + AsyncWrite + Unpin + Send + 'static,
    S: Send + 'static,
{
    type Future = BoxFuture<'static, io::Result<(Self::Stream, Self::Service)>>;
    type Service = AddExtension<A::Service, ProxyProtocolState>;
    type Stream = ProxyProtocolStream<A::Stream>;

    fn accept(&self, stream: I, service: S) -> Self::Future {
        let acceptor = self.inner.clone();

        Box::pin(async move {
            let (stream, service) = acceptor.accept(stream, service).await?;
            let stream = ProxyProtocolStream::new(stream).await?;

            let proxy_protocol_state = ProxyProtocolState {
                header: stream.header().cloned(),
            };

            let service = Extension(proxy_protocol_state).layer(service);

            Ok((stream, service))
        })
    }
}
