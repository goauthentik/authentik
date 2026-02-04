use std::{
    cmp::min,
    io,
    io::IoSlice,
    ops::Deref,
    pin::Pin,
    task::{Context, Poll},
};

use eyre::{Result, eyre};
use pin_project_lite::pin_project;
use tokio::io::{AsyncBufRead, AsyncRead, AsyncReadExt, AsyncWrite, ReadBuf};

use crate::proxy_protocol::header::{Error, Header};

pub mod header;
mod utils;
mod v1;
mod v2;

// Length of the read buffer
const READ_BUFFER_LEN: usize = 536;

pin_project! {
    pub struct ProxyProtocolStream<S> {
        #[pin]
        stream: S,
        remaining: Vec<u8>,
        header: Option<Header<'static>>,
    }
}

impl<S> ProxyProtocolStream<S> {
    pub fn header(&self) -> Option<&Header<'static>> {
        self.header.as_ref()
    }

    fn get_pin_mut(self: Pin<&mut Self>) -> Pin<&mut S> {
        self.project().stream
    }

    pub fn try_into_stream(self) -> Result<S> {
        if self.remaining.is_empty() {
            Ok(self.stream)
        } else {
            Err(eyre!(
                "Cannot return inner stream because buffer is not empty"
            ))
        }
    }
}

impl<S> AsRef<S> for ProxyProtocolStream<S> {
    fn as_ref(&self) -> &S {
        &self.stream
    }
}

impl<S> Deref for ProxyProtocolStream<S> {
    type Target = S;

    fn deref(&self) -> &Self::Target {
        &self.stream
    }
}

impl<S> ProxyProtocolStream<S>
where S: AsyncRead + Unpin
{
    pub async fn new(mut stream: S) -> Result<Self, io::Error> {
        let mut remaining = Vec::with_capacity(READ_BUFFER_LEN);

        loop {
            let bytes_read = stream.read_buf(&mut remaining).await?;
            if bytes_read == 0 {
                return Err(io::Error::new(
                    io::ErrorKind::UnexpectedEof,
                    "end of stream",
                ));
            }

            match Header::parse(&remaining) {
                Ok((header, consumed)) => {
                    let header = header.into_owned();
                    remaining.drain(..consumed);

                    return Ok(Self {
                        stream,
                        remaining,
                        header: Some(header),
                    });
                }
                Err(Error::BufferTooShort) => continue,
                // Something went wrong parsing the PROXY protocol. We assume that we weren't meant
                // to parse it, and that this is just a regular stream without the PROXY protocol.
                Err(_) => {
                    return Ok(Self {
                        stream,
                        remaining,
                        header: None,
                    });
                }
            }
        }
    }
}

impl<S> AsyncRead for ProxyProtocolStream<S>
where S: AsyncRead
{
    fn poll_read(
        self: Pin<&mut Self>,
        cx: &mut Context<'_>,
        buf: &mut ReadBuf<'_>,
    ) -> Poll<io::Result<()>> {
        let this = self.project();

        if !this.remaining.is_empty() {
            let to_copy = min(this.remaining.len(), buf.remaining());

            buf.put_slice(&this.remaining[..to_copy]);
            this.remaining.drain(..to_copy);

            return Poll::Ready(Ok(()));
        }

        this.stream.poll_read(cx, buf)
    }
}

impl<S> AsyncBufRead for ProxyProtocolStream<S>
where S: AsyncBufRead
{
    fn poll_fill_buf(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<io::Result<&[u8]>> {
        let this = self.project();

        if !this.remaining.is_empty() {
            return Poll::Ready(Ok(&this.remaining[..]));
        }

        this.stream.poll_fill_buf(cx)
    }

    fn consume(self: Pin<&mut Self>, amt: usize) {
        let this = self.project();

        if !this.remaining.is_empty() {
            let len = this.remaining.len();
            if amt <= len {
                this.remaining.drain(..amt);
            } else {
                this.remaining.drain(..len);
                this.stream.consume(amt - len);
            }
        } else {
            this.stream.consume(amt);
        }
    }
}

impl<S> AsyncWrite for ProxyProtocolStream<S>
where S: AsyncWrite
{
    fn poll_write(
        self: Pin<&mut Self>,
        cx: &mut Context<'_>,
        buf: &[u8],
    ) -> Poll<io::Result<usize>> {
        self.get_pin_mut().poll_write(cx, buf)
    }

    fn poll_flush(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<io::Result<()>> {
        self.get_pin_mut().poll_flush(cx)
    }

    fn poll_shutdown(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<io::Result<()>> {
        self.get_pin_mut().poll_shutdown(cx)
    }

    fn poll_write_vectored(
        self: Pin<&mut Self>,
        cx: &mut Context<'_>,
        bufs: &[IoSlice<'_>],
    ) -> Poll<io::Result<usize>> {
        self.get_pin_mut().poll_write_vectored(cx, bufs)
    }

    fn is_write_vectored(&self) -> bool {
        self.stream.is_write_vectored()
    }
}

#[cfg(test)]
mod tests {
    use std::{
        io::Cursor,
        net::{IpAddr, Ipv4Addr, SocketAddr},
    };

    use super::*;
    use crate::proxy_protocol::header::{Address, Protocol};

    #[tokio::test]
    async fn test_parse() {
        let mut buf = [0; 1024];
        let header = b"PROXY TCP4 127.0.0.1 192.168.0.1 12345 443\r\n";
        buf[..header.len()].copy_from_slice(header);
        buf[header.len()..].fill(255);

        let mut stream = Cursor::new(&buf);

        let mut proxied = ProxyProtocolStream::new(&mut stream).await.unwrap();
        assert_eq!(
            proxied.header(),
            Some(Header(
                Some(Address {
                    protocol: Protocol::Stream,
                    source: SocketAddr::new(IpAddr::V4(Ipv4Addr::new(127, 0, 0, 1)), 12345),
                    destination: SocketAddr::new(IpAddr::V4(Ipv4Addr::new(192, 168, 0, 1)), 443),
                }),
                vec![0; 0].into(),
            ))
            .as_ref()
        );

        let mut buf = Vec::new();
        AsyncReadExt::read_to_end(&mut proxied, &mut buf)
            .await
            .unwrap();
        assert_eq!(buf.len(), 1024 - header.len());
        assert!(buf.into_iter().all(|b| b == 255));
    }
}
