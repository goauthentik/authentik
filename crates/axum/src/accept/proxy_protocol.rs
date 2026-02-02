use std::ops::Deref;
use std::task::{Context, Poll};
use std::{net::SocketAddr, pin::Pin, time::Duration};

use axum::{Extension, middleware::AddExtension};
use axum_server::accept::{Accept, DefaultAcceptor};
use bytes::{Buf, BufMut, BytesMut};
use eyre::Result;
use eyre::eyre;
use futures::future::BoxFuture;
use pin_project_lite::pin_project;
use tokio::io::{AsyncRead, AsyncWrite, ReadBuf};
use tokio::net::TcpStream;
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

pin_project! {
    pub struct ProxyProtocolStream<T> {
        #[pin]
        inner: T,
        buf: BytesMut,
        orig_source: Option<SocketAddr>,
        orig_destination: Option<SocketAddr>,
    }
}

impl<T> ProxyProtocolStream<T> {
    fn get_pin_mut(self: Pin<&mut Self>) -> Pin<&mut T> {
        self.project().inner
    }

    pub fn try_into_inner(self) -> Result<T> {
        if self.buf.is_empty() {
            Ok(self.inner)
        } else {
            Err(eyre!(
                "Cannot return inner stream because buffer is not empty"
            ))
        }
    }
}

impl<T> AsRef<T> for ProxyProtocolStream<T> {
    fn as_ref(&self) -> &T {
        &self.inner
    }
}

impl Deref for ProxyProtocolStream<TcpStream> {
    type Target = TcpStream;

    fn deref(&self) -> &Self::Target {
        &self.inner
    }
}

impl<T: AsyncRead> ProxyProtocolStream<T> {
    pub async fn new(stream: T) -> Result<Self> {
        // TODO: read the proxy protocol here
        Ok(Self {
            inner: stream,
            buf: BytesMut::with_capacity(100),
            orig_source: None,
            orig_destination: None,
        })
    }
}

impl<T: AsyncRead> AsyncRead for ProxyProtocolStream<T> {
    fn poll_read(
        self: Pin<&mut Self>,
        cx: &mut Context<'_>,
        buf: &mut ReadBuf<'_>,
    ) -> Poll<std::io::Result<()>> {
        let this = self.project();
        if this.buf.is_empty() {
            this.inner.poll_read(cx, buf)
        } else {
            // send remaining data from buffer
            let to_copy = this.buf.remaining().min(buf.remaining());
            buf.put_slice(&this.buf[0..to_copy]);
            this.buf.advance(to_copy);

            // there is still space in output buffer
            // let's try if we have some bytes to add there
            if buf.has_remaining_mut()
                && let Poll::Ready(Err(e)) = this.inner.poll_read(cx, buf)
            {
                return Poll::Ready(Err(e));
            }
            Poll::Ready(Ok(()))
        }
    }
}
