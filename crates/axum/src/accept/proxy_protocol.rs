use std::{net::SocketAddr, time::Duration};

use axum::{Extension, middleware::AddExtension};
use axum_server::accept::{Accept, DefaultAcceptor};
use futures::future::BoxFuture;
use tokio::io::{AsyncRead, AsyncWrite};
use tokio_rustls::{rustls::pki_types::CertificateDer, server::TlsStream};
use tower::Layer;

#[derive(Clone, Debug)]
pub struct ProxyProtocolState {
    pub client_address: Option<SocketAddr>,
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
    A: Accept<I, S> + Clone,
    A::Stream: AsyncRead + AsyncWrite + Unpin,
    I: AsyncRead + AsyncWrite + Unpin + Send + 'static,
{
    type Stream = A::Stream;
    type Service = AddExtension<A::Service, ProxyProtocolState>;
    type Future = BoxFuture<'static, std::io::Result<(Self::Stream, Self::Service)>>;

    fn accept(&self, stream: I, service: S) -> Self::Future {
        let acceptor = self.inner.clone();

        todo!()
        // Box::pin(async move {
        //     let (stream, service) = acceptor.accept(stream, service).await?;
        //
        //     let proxy_protocol_state = ProxyProtocolState {
        //         client_address: None,
        //     };
        //
        //     let service = Extension(proxy_protocol_state).layer(service);
        //
        //     Ok((stream, service))
        // })
    }
}

// impl<I, S> Accept<I, S> for TlsAcceptor
// where
//     I: AsyncRead + AsyncWrite + Unpin + Send + 'static,
//     S: Send + 'static,
// {
//     type Stream = TlsStream<I>;
//     type Service = AddExtension<S, TlsState>;
//     type Future = BoxFuture<'static, std::io::Result<(Self::Stream, Self::Service)>>;
//
//     fn accept(&self, stream: I, service: S) -> Self::Future {
//         let acceptor = self.inner.clone();
//
//         Box::pin(async move {
//             let (stream, service) = acceptor.accept(stream, service).await?;
//             let server_conn = stream.get_ref().1;
//             let tls_state = TlsState {
//                 peer_certificates: server_conn.peer_certificates().map(|c| c.to_owned()),
//             };
//
//             let service = Extension(tls_state).layer(service);
//
//             Ok((stream, service))
//         })
//     }
// }
