//! axum-server acceptor that catches panics and shuts down the application.

use std::{
    any::Any,
    io::{self, IoSlice},
    panic::{AssertUnwindSafe, catch_unwind, resume_unwind},
    task::{Context, Poll},
};

use ak_common::Arbiter;
use axum_server::accept::Accept;
use futures::{FutureExt as _, future::BoxFuture};
use pin_project_lite::pin_project;
use tokio::io::{AsyncRead, AsyncWrite, ReadBuf};
use tower::Service;
use tracing::{error, instrument};

fn extract_panic_msg<'a>(panic: &'a Box<dyn Any + Send + 'static>) -> &'a str {
    panic
        .downcast_ref::<&str>()
        .copied()
        .or_else(|| panic.downcast_ref::<String>().map(String::as_str))
        .unwrap_or("unknown panic message")
}

/// Acceptor catching panics from the underlying acceptor.
///
/// Also wraps the stream and service to catch panics.
#[derive(Clone)]
pub(crate) struct CatchPanicAcceptor<A> {
    inner: A,
    arbiter: Arbiter,
}

impl<A> CatchPanicAcceptor<A> {
    pub(crate) fn new(inner: A, arbiter: Arbiter) -> Self {
        Self { inner, arbiter }
    }
}

impl<A, I, S> Accept<I, S> for CatchPanicAcceptor<A>
where
    A: Accept<I, S> + Clone + Send + 'static,
    A::Stream: AsyncRead + AsyncWrite + Send,
    A::Service: Send,
    A::Future: Send,
    I: AsyncRead + AsyncWrite + Unpin + Send + 'static,
    S: Send + 'static,
{
    type Future = BoxFuture<'static, io::Result<(Self::Stream, Self::Service)>>;
    type Service = CatchPanicService<A::Service>;
    type Stream = CatchPanicStream<A::Stream>;

    #[instrument(skip_all)]
    fn accept(&self, stream: I, service: S) -> Self::Future {
        let acceptor = self.inner.clone();
        let arbiter = self.arbiter.clone();

        Box::pin(async move {
            match AssertUnwindSafe(acceptor.accept(stream, service))
                .catch_unwind()
                .await
            {
                Ok(result) => {
                    let (stream, service) = result?;
                    Ok((
                        CatchPanicStream::new(stream, arbiter.clone()),
                        CatchPanicService::new(service, arbiter),
                    ))
                }
                Err(panic) => {
                    error!(
                        panic = extract_panic_msg(&panic),
                        "acceptor panicked, shutting down immediately"
                    );
                    arbiter.do_fast_shutdown().await;
                    resume_unwind(panic);
                }
            }
        })
    }
}

pin_project! {
    /// A stream wrapper that catches panics from the underlying stream.
    pub(crate) struct CatchPanicStream<S> {
        #[pin]
        inner: S,
        arbiter: Arbiter,
    }
}

impl<S> CatchPanicStream<S> {
    pub(crate) fn new(inner: S, arbiter: Arbiter) -> Self {
        Self { inner, arbiter }
    }
}

impl<S: AsyncRead> AsyncRead for CatchPanicStream<S> {
    fn poll_read(
        self: std::pin::Pin<&mut Self>,
        cx: &mut Context<'_>,
        buf: &mut ReadBuf<'_>,
    ) -> Poll<io::Result<()>> {
        let this = self.project();

        match catch_unwind(AssertUnwindSafe(|| this.inner.poll_read(cx, buf))) {
            Ok(result) => result,
            Err(panic) => {
                error!(
                    panic = extract_panic_msg(&panic),
                    "stream poll_read panicked, shutting down immediately"
                );
                let arbiter = this.arbiter.clone();
                tokio::spawn(async move { arbiter.do_fast_shutdown().await });
                resume_unwind(panic);
            }
        }
    }
}

impl<S: AsyncWrite> AsyncWrite for CatchPanicStream<S> {
    fn poll_write(
        self: std::pin::Pin<&mut Self>,
        cx: &mut Context<'_>,
        buf: &[u8],
    ) -> Poll<io::Result<usize>> {
        let this = self.project();

        match catch_unwind(AssertUnwindSafe(|| this.inner.poll_write(cx, buf))) {
            Ok(result) => result,
            Err(panic) => {
                error!(
                    panic = extract_panic_msg(&panic),
                    "stream poll_write panicked, shutting down immediately"
                );
                let arbiter = this.arbiter.clone();
                tokio::spawn(async move { arbiter.do_fast_shutdown().await });
                resume_unwind(panic);
            }
        }
    }

    fn poll_write_vectored(
        self: std::pin::Pin<&mut Self>,
        cx: &mut Context<'_>,
        bufs: &[IoSlice<'_>],
    ) -> Poll<io::Result<usize>> {
        let this = self.project();

        match catch_unwind(AssertUnwindSafe(|| {
            this.inner.poll_write_vectored(cx, bufs)
        })) {
            Ok(result) => result,
            Err(panic) => {
                error!(
                    panic = extract_panic_msg(&panic),
                    "stream poll_write_vectored panicked, shutting down immediately"
                );
                let arbiter = this.arbiter.clone();
                tokio::spawn(async move { arbiter.do_fast_shutdown().await });
                resume_unwind(panic)
            }
        }
    }

    fn is_write_vectored(&self) -> bool {
        match catch_unwind(AssertUnwindSafe(|| self.inner.is_write_vectored())) {
            Ok(result) => result,
            Err(panic) => {
                error!(
                    panic = extract_panic_msg(&panic),
                    "stream is_write_vectored panicked, shutting down immediately"
                );
                let arbiter = self.arbiter.clone();
                tokio::spawn(async move { arbiter.do_fast_shutdown().await });
                resume_unwind(panic);
            }
        }
    }

    fn poll_flush(self: std::pin::Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<io::Result<()>> {
        let this = self.project();

        match catch_unwind(AssertUnwindSafe(|| this.inner.poll_flush(cx))) {
            Ok(result) => result,
            Err(panic) => {
                error!(
                    panic = extract_panic_msg(&panic),
                    "stream poll_flush panicked, shutting down immediately"
                );
                let arbiter = this.arbiter.clone();
                tokio::spawn(async move { arbiter.do_fast_shutdown().await });
                resume_unwind(panic);
            }
        }
    }

    fn poll_shutdown(self: std::pin::Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<io::Result<()>> {
        let this = self.project();

        match catch_unwind(AssertUnwindSafe(|| this.inner.poll_shutdown(cx))) {
            Ok(result) => result,
            Err(panic) => {
                error!(
                    panic = extract_panic_msg(&panic),
                    "stream poll_shutdown panicked, shutting down immediately"
                );
                let arbiter = this.arbiter.clone();
                tokio::spawn(async move { arbiter.do_fast_shutdown().await });
                resume_unwind(panic);
            }
        }
    }
}

/// A panic wrapper that catches panics from the underlying service.
#[derive(Clone)]
pub(crate) struct CatchPanicService<S> {
    inner: S,
    arbiter: Arbiter,
}

impl<S> CatchPanicService<S> {
    pub(crate) fn new(inner: S, arbiter: Arbiter) -> Self {
        Self { inner, arbiter }
    }
}

impl<S, R> Service<R> for CatchPanicService<S>
where
    S: Service<R>,
{
    type Error = S::Error;
    type Future = CatchPanicFuture<S::Future>;
    type Response = S::Response;

    fn poll_ready(&mut self, cx: &mut Context<'_>) -> Poll<Result<(), Self::Error>> {
        let inner = &mut self.inner;

        match catch_unwind(AssertUnwindSafe(|| inner.poll_ready(cx))) {
            Ok(result) => result,
            Err(panic) => {
                error!(
                    panic = extract_panic_msg(&panic),
                    "service poll_ready panicked, shutting down immediately"
                );
                let arbiter = self.arbiter.clone();
                tokio::spawn(async move { arbiter.do_fast_shutdown().await });
                resume_unwind(panic);
            }
        }
    }

    fn call(&mut self, req: R) -> Self::Future {
        let inner = &mut self.inner;

        match catch_unwind(AssertUnwindSafe(|| inner.call(req))) {
            Ok(future) => CatchPanicFuture::new(future, self.arbiter.clone()),
            Err(panic) => {
                error!(
                    panic = extract_panic_msg(&panic),
                    "service call panicked, shutting down immediately"
                );
                let arbiter = self.arbiter.clone();
                tokio::spawn(async move { arbiter.do_fast_shutdown().await });
                resume_unwind(panic);
            }
        }
    }
}

pin_project! {
    /// A Future wrapper that catches panics from the inner future.
    pub(crate) struct CatchPanicFuture<F> {
        #[pin]
        inner: F,
        arbiter: Arbiter,
    }
}

impl<F> CatchPanicFuture<F> {
    fn new(inner: F, arbiter: Arbiter) -> Self {
        Self { inner, arbiter }
    }
}

impl<F: Future> Future for CatchPanicFuture<F> {
    type Output = F::Output;

    fn poll(self: std::pin::Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output> {
        let this = self.project();

        match catch_unwind(AssertUnwindSafe(|| this.inner.poll(cx))) {
            Ok(result) => result,
            Err(panic) => {
                error!(
                    panic = extract_panic_msg(&panic),
                    "service future panicked, shutting down immediately"
                );
                let arbiter = this.arbiter.clone();
                tokio::spawn(async move { arbiter.do_fast_shutdown().await });
                resume_unwind(panic);
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use std::{
        convert::Infallible,
        io,
        panic::{AssertUnwindSafe, panic_any},
        task::{Context, Poll},
    };

    use ak_common::{Arbiter, Tasks};
    use axum_server::accept::Accept;
    use futures::{
        FutureExt as _,
        future::{BoxFuture, poll_fn},
    };
    use tokio::{
        io::{AsyncReadExt as _, AsyncWriteExt as _, DuplexStream, ReadBuf, duplex},
        time::{Duration, timeout},
    };
    use tower::Service;

    use super::{CatchPanicAcceptor, CatchPanicService, CatchPanicStream};

    fn duplex_stream() -> DuplexStream {
        let (stream, _peer) = duplex(1024);
        stream
    }

    /// Returns `true` if the arbiter's fast-shutdown has already been triggered.
    async fn fast_shutdown_triggered(arbiter: &Arbiter) -> bool {
        timeout(Duration::from_millis(50), arbiter.fast_shutdown())
            .await
            .is_ok()
    }

    #[derive(Clone)]
    struct OkAcceptor;

    impl<I: Send + 'static, S: Send + 'static> Accept<I, S> for OkAcceptor {
        type Future = BoxFuture<'static, io::Result<(I, S)>>;
        type Service = S;
        type Stream = I;

        fn accept(&self, stream: I, service: S) -> Self::Future {
            Box::pin(async move { Ok((stream, service)) })
        }
    }

    #[derive(Clone)]
    struct ErrorAcceptor;

    impl<I: Send + 'static, S: Send + 'static> Accept<I, S> for ErrorAcceptor {
        type Future = BoxFuture<'static, io::Result<(I, S)>>;
        type Service = S;
        type Stream = I;

        fn accept(&self, _stream: I, _service: S) -> Self::Future {
            Box::pin(async move { Err(io::Error::other("inner error")) })
        }
    }

    /// Panics with a `&'static str` payload.
    #[derive(Clone)]
    struct PanicStrAcceptor;

    impl<I: Send + 'static, S: Send + 'static> Accept<I, S> for PanicStrAcceptor {
        type Future = BoxFuture<'static, io::Result<(I, S)>>;
        type Service = S;
        type Stream = I;

        fn accept(&self, _stream: I, _service: S) -> Self::Future {
            Box::pin(async move { panic!("str panic message") })
        }
    }

    /// Panics with a `String` payload.
    #[derive(Clone)]
    struct PanicStringAcceptor;

    impl<I: Send + 'static, S: Send + 'static> Accept<I, S> for PanicStringAcceptor {
        type Future = BoxFuture<'static, io::Result<(I, S)>>;
        type Service = S;
        type Stream = I;

        fn accept(&self, _stream: I, _service: S) -> Self::Future {
            Box::pin(async move {
                let msg = "string panic message".to_owned();
                panic_any(msg)
            })
        }
    }

    /// Panics with a payload that is neither `&str` nor `String`.
    #[derive(Clone)]
    struct PanicUnknownAcceptor;

    impl<I: Send + 'static, S: Send + 'static> Accept<I, S> for PanicUnknownAcceptor {
        type Future = BoxFuture<'static, io::Result<(I, S)>>;
        type Service = S;
        type Stream = I;

        fn accept(&self, _stream: I, _service: S) -> Self::Future {
            Box::pin(async move { panic_any(42u32) })
        }
    }

    struct PanicStream;

    impl tokio::io::AsyncRead for PanicStream {
        fn poll_read(
            self: std::pin::Pin<&mut Self>,
            _cx: &mut Context<'_>,
            _buf: &mut ReadBuf<'_>,
        ) -> Poll<io::Result<()>> {
            panic!("poll_read panic")
        }
    }

    impl tokio::io::AsyncWrite for PanicStream {
        fn poll_write(
            self: std::pin::Pin<&mut Self>,
            _cx: &mut Context<'_>,
            _buf: &[u8],
        ) -> Poll<io::Result<usize>> {
            panic!("poll_write panic")
        }

        fn poll_flush(
            self: std::pin::Pin<&mut Self>,
            _cx: &mut Context<'_>,
        ) -> Poll<io::Result<()>> {
            panic!("poll_flush panic")
        }

        fn poll_shutdown(
            self: std::pin::Pin<&mut Self>,
            _cx: &mut Context<'_>,
        ) -> Poll<io::Result<()>> {
            panic!("poll_shutdown panic")
        }
    }

    #[derive(Clone)]
    struct OkService;

    impl Service<()> for OkService {
        type Error = Infallible;
        type Future = futures::future::Ready<Result<(), Infallible>>;
        type Response = ();

        fn poll_ready(&mut self, _cx: &mut Context<'_>) -> Poll<Result<(), Self::Error>> {
            Poll::Ready(Ok(()))
        }

        fn call(&mut self, _req: ()) -> Self::Future {
            futures::future::ready(Ok(()))
        }
    }

    struct PanicPollReadyService;

    impl Service<()> for PanicPollReadyService {
        type Error = Infallible;
        type Future = futures::future::Ready<Result<(), Infallible>>;
        type Response = ();

        fn poll_ready(&mut self, _cx: &mut Context<'_>) -> Poll<Result<(), Self::Error>> {
            panic!("poll_ready panic")
        }

        fn call(&mut self, _req: ()) -> Self::Future {
            unreachable!()
        }
    }

    struct PanicCallBodyService;

    impl Service<()> for PanicCallBodyService {
        type Error = Infallible;
        type Future = futures::future::Ready<Result<(), Infallible>>;
        type Response = ();

        fn poll_ready(&mut self, _cx: &mut Context<'_>) -> Poll<Result<(), Self::Error>> {
            Poll::Ready(Ok(()))
        }

        fn call(&mut self, _req: ()) -> Self::Future {
            panic!("call body panic")
        }
    }

    struct PanicFuture;

    impl Future for PanicFuture {
        type Output = Result<(), Infallible>;

        fn poll(self: std::pin::Pin<&mut Self>, _cx: &mut Context<'_>) -> Poll<Self::Output> {
            panic!("future panic")
        }
    }

    struct PanicCallFutureService;

    impl Service<()> for PanicCallFutureService {
        type Error = Infallible;
        type Future = PanicFuture;
        type Response = ();

        fn poll_ready(&mut self, _cx: &mut Context<'_>) -> Poll<Result<(), Self::Error>> {
            Poll::Ready(Ok(()))
        }

        fn call(&mut self, _req: ()) -> Self::Future {
            PanicFuture
        }
    }

    #[tokio::test]
    async fn acceptor_passes_through_success() {
        let tasks = Tasks::new().expect("failed to create tasks");
        let arbiter = tasks.arbiter();
        let acceptor = CatchPanicAcceptor::new(OkAcceptor, arbiter.clone());

        let result = acceptor.accept(duplex_stream(), OkService).await;

        assert!(result.is_ok());
        assert!(!fast_shutdown_triggered(&arbiter).await);
    }

    #[tokio::test]
    async fn acceptor_passes_through_error() {
        let tasks = Tasks::new().expect("failed to create tasks");
        let arbiter = tasks.arbiter();
        let acceptor = CatchPanicAcceptor::new(ErrorAcceptor, arbiter.clone());

        let result = acceptor.accept(duplex_stream(), OkService).await;

        assert!(result.is_err());
        assert_eq!(result.err().unwrap().to_string(), "inner error");
        assert!(!fast_shutdown_triggered(&arbiter).await);
    }

    #[tokio::test]
    async fn acceptor_catches_str_panic_and_shuts_down() {
        let tasks = Tasks::new().expect("failed to create tasks");
        let arbiter = tasks.arbiter();
        let acceptor = CatchPanicAcceptor::new(PanicStrAcceptor, arbiter.clone());

        let result = AssertUnwindSafe(acceptor.accept(duplex_stream(), OkService))
            .catch_unwind()
            .await;

        assert!(result.is_err());
        assert!(fast_shutdown_triggered(&arbiter).await);
    }

    #[tokio::test]
    async fn acceptor_catches_string_panic_and_shuts_down() {
        let tasks = Tasks::new().expect("failed to create tasks");
        let arbiter = tasks.arbiter();
        let acceptor = CatchPanicAcceptor::new(PanicStringAcceptor, arbiter.clone());

        let result = AssertUnwindSafe(acceptor.accept(duplex_stream(), OkService))
            .catch_unwind()
            .await;

        assert!(result.is_err());
        assert!(fast_shutdown_triggered(&arbiter).await);
    }

    #[tokio::test]
    async fn acceptor_catches_unknown_panic_and_shuts_down() {
        let tasks = Tasks::new().expect("failed to create tasks");
        let arbiter = tasks.arbiter();
        let acceptor = CatchPanicAcceptor::new(PanicUnknownAcceptor, arbiter.clone());

        let result = AssertUnwindSafe(acceptor.accept(duplex_stream(), OkService))
            .catch_unwind()
            .await;

        assert!(result.is_err());
        assert!(fast_shutdown_triggered(&arbiter).await);
    }

    #[tokio::test]
    async fn stream_poll_read_passes_through() {
        let tasks = Tasks::new().expect("failed to create tasks");
        let arbiter = tasks.arbiter();
        let (mut a, mut b) = duplex(1024);
        b.write_all(b"hello").await.unwrap();

        let mut stream = CatchPanicStream::new(&mut a, arbiter.clone());
        let mut buf = [0u8; 5];
        let result = stream.read(&mut buf).await;

        assert!(result.is_ok());
        assert_eq!(&buf, b"hello");
        assert!(!fast_shutdown_triggered(&arbiter).await);
    }

    #[tokio::test]
    async fn stream_poll_read_panic_returns_error_and_shuts_down() {
        let tasks = Tasks::new().expect("failed to create tasks");
        let arbiter = tasks.arbiter();
        let mut stream = CatchPanicStream::new(PanicStream, arbiter.clone());

        let result = AssertUnwindSafe(stream.read(&mut [0u8; 10]))
            .catch_unwind()
            .await;

        assert!(result.is_err());
        assert!(fast_shutdown_triggered(&arbiter).await);
    }

    #[tokio::test]
    async fn stream_poll_write_passes_through() {
        let tasks = Tasks::new().expect("failed to create tasks");
        let arbiter = tasks.arbiter();
        let (mut a, _b) = duplex(1024);

        let mut stream = CatchPanicStream::new(&mut a, arbiter.clone());
        let result = stream.write_all(b"hello").await;

        assert!(result.is_ok());
        assert!(!fast_shutdown_triggered(&arbiter).await);
    }

    #[tokio::test]
    async fn stream_poll_write_panic_returns_error_and_shuts_down() {
        let tasks = Tasks::new().expect("failed to create tasks");
        let arbiter = tasks.arbiter();
        let mut stream = CatchPanicStream::new(PanicStream, arbiter.clone());

        let result = AssertUnwindSafe(stream.write(b"hello"))
            .catch_unwind()
            .await;

        assert!(result.is_err());
        assert!(fast_shutdown_triggered(&arbiter).await);
    }

    #[tokio::test]
    async fn stream_poll_flush_panic_returns_error_and_shuts_down() {
        let tasks = Tasks::new().expect("failed to create tasks");
        let arbiter = tasks.arbiter();
        let mut stream = CatchPanicStream::new(PanicStream, arbiter.clone());

        let result = AssertUnwindSafe(stream.flush()).catch_unwind().await;

        assert!(result.is_err());
        assert!(fast_shutdown_triggered(&arbiter).await);
    }

    #[tokio::test]
    async fn stream_poll_shutdown_panic_returns_error_and_shuts_down() {
        let tasks = Tasks::new().expect("failed to create tasks");
        let arbiter = tasks.arbiter();
        let mut stream = CatchPanicStream::new(PanicStream, arbiter.clone());

        let result = AssertUnwindSafe(stream.shutdown()).catch_unwind().await;

        assert!(result.is_err());
        assert!(fast_shutdown_triggered(&arbiter).await);
    }

    #[tokio::test]
    async fn service_poll_ready_passes_through() {
        let tasks = Tasks::new().expect("failed to create tasks");
        let arbiter = tasks.arbiter();
        let mut service = CatchPanicService::new(OkService, arbiter.clone());

        let result = poll_fn(|cx| service.poll_ready(cx)).await;

        assert!(result.is_ok());
        assert!(!fast_shutdown_triggered(&arbiter).await);
    }

    #[tokio::test]
    async fn service_poll_ready_panic_re_panics_and_shuts_down() {
        let tasks = Tasks::new().expect("failed to create tasks");
        let arbiter = tasks.arbiter();
        let mut service = CatchPanicService::new(PanicPollReadyService, arbiter.clone());

        let result = AssertUnwindSafe(poll_fn(|cx| service.poll_ready(cx)))
            .catch_unwind()
            .await;

        assert!(result.is_err());
        assert!(fast_shutdown_triggered(&arbiter).await);
    }

    #[tokio::test]
    async fn service_call_passes_through() {
        let tasks = Tasks::new().expect("failed to create tasks");
        let arbiter = tasks.arbiter();
        let mut service = CatchPanicService::new(OkService, arbiter.clone());

        let result = service.call(()).await;

        assert!(result.is_ok());
        assert!(!fast_shutdown_triggered(&arbiter).await);
    }

    #[tokio::test]
    async fn service_call_body_panic_re_panics_and_shuts_down() {
        let tasks = Tasks::new().expect("failed to create tasks");
        let arbiter = tasks.arbiter();
        let mut service = CatchPanicService::new(PanicCallBodyService, arbiter.clone());

        let result = AssertUnwindSafe(async { service.call(()).await })
            .catch_unwind()
            .await;

        assert!(result.is_err());
        assert!(fast_shutdown_triggered(&arbiter).await);
    }

    #[tokio::test]
    async fn service_call_future_panic_re_panics_and_shuts_down() {
        let tasks = Tasks::new().expect("failed to create tasks");
        let arbiter = tasks.arbiter();
        let mut service = CatchPanicService::new(PanicCallFutureService, arbiter.clone());

        let result = AssertUnwindSafe(service.call(())).catch_unwind().await;

        assert!(result.is_err());
        assert!(fast_shutdown_triggered(&arbiter).await);
    }
}
