use smallvec::SmallVec;
use std::ops::Deref;
use std::task::{Context, Poll};
use std::{net::SocketAddr, pin::Pin};
use tokio::io::AsyncReadExt;

use bytes::{Buf, BufMut, BytesMut};
use eyre::Result;
use eyre::eyre;
use pin_project_lite::pin_project;
use tokio::io::{AsyncRead, AsyncWrite, ReadBuf};
use tokio::net::TcpStream;

// Length of v1 header
const V1_PREFIX_LEN: usize = 5;
// Maximum length of a v1 header
const V1_MAX_LENGTH: usize = 107;
// Terminator bytes of a v1 header
const V1_TERMINATOR: &[u8] = b"\r\n";

// Minimum length of a v2 header
const V2_MINIMUM_LEN: usize = 16;
// Index of the start of the big-endian u16 length in the v2 header
const V2_LENGTH_INDEX: usize = 14;

// Length of the read buffer
const READ_BUFFER_LEN: usize = 536;

pin_project! {
    pub struct ProxyProtocolStream<T> {
        #[pin]
        inner: T,
        buf: SmallVec<[u8; READ_BUFFER_LEN]>,
        buf_offset: usize,
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

impl<T: AsyncRead + Unpin> ProxyProtocolStream<T> {
    async fn accept(
        stream: &mut T,
    ) -> Result<(SmallVec<[u8; READ_BUFFER_LEN]>, usize, Option<SocketAddr>), std::io::Error> {
        let mut buf = SmallVec::new();
        let mut buf_offset = 0;

        // Read prefix to check for v1, v2 or none
        stream.read_exact(&mut buf[..V1_PREFIX_LEN]).await?;

        // if &buf[..V1_PREFIX_LEN] == ppp::v1::PROTOCOL_PREFIX.as_bytes() {
        //     read_v1_header()
        // }

        Ok((buf, buf_offset, None))
    }

    pub async fn new(mut stream: T) -> Result<Self> {
        let (buf, buf_offset, orig_destination) = Self::accept(&mut stream).await?;
        // TODO: read the proxy protocol here
        Ok(Self {
            inner: stream,
            buf,
            buf_offset,
            orig_destination,
        })
    }
}

impl<T: AsyncRead> AsyncRead for ProxyProtocolStream<T> {
    fn poll_read(
        self: Pin<&mut Self>,
        cx: &mut Context<'_>,
        buf: &mut ReadBuf<'_>,
    ) -> Poll<std::io::Result<()>> {
        let buf_offset = self.buf_offset;
        let this = self.project();
        if this.buf.is_empty() {
            this.inner.poll_read(cx, buf)
        } else {
            // send remaining data from buffer
            let remaining_buf = &this.buf[buf_offset..];
            let to_copy = remaining_buf.len().min(buf.remaining());
            buf.put_slice(&remaining_buf[..to_copy]);
            *this.buf_offset += to_copy;

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

impl<R: AsyncRead + AsyncWrite> AsyncWrite for ProxyProtocolStream<R> {
    fn poll_write(
        self: Pin<&mut Self>,
        cx: &mut Context<'_>,
        buf: &[u8],
    ) -> Poll<std::io::Result<usize>> {
        self.get_pin_mut().poll_write(cx, buf)
    }

    fn poll_flush(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<std::io::Result<()>> {
        self.get_pin_mut().poll_flush(cx)
    }

    fn poll_shutdown(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<std::io::Result<()>> {
        self.get_pin_mut().poll_shutdown(cx)
    }
}

async fn read_v1_header<T>(
    mut stream: T,
    buf: &mut SmallVec<[u8; READ_BUFFER_LEN]>,
    buf_offset: &mut usize,
) -> Result<bool, std::io::Error>
where
    T: AsyncRead + Unpin,
{
    // read some bytes until terminator is found
    let mut end_found = false;

    for i in V1_PREFIX_LEN..V1_MAX_LENGTH {
        buf[i] = stream.read_u8().await?;

        if [buf[i - 1], buf[i]] == V1_TERMINATOR {
            *buf_offset = i;
            end_found = true;
            break;
        }
    }

    Ok(end_found)
}
