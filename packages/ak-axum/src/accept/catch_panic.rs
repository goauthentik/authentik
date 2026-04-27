//! axum-server acceptor that catches panics and shuts down the application.

use std::{io, panic::AssertUnwindSafe};

use ak_common::Arbiter;
use axum_server::accept::Accept;
use futures::{FutureExt as _, future::BoxFuture};
use tokio::io::{AsyncRead, AsyncWrite};
use tracing::{error, instrument};

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
    A::Stream: Send,
    A::Service: Send,
    A::Future: Send,
    I: AsyncRead + AsyncWrite + Unpin + Send + 'static,
    S: Send + 'static,
{
    type Future = BoxFuture<'static, io::Result<(Self::Stream, Self::Service)>>;
    type Service = A::Service;
    type Stream = A::Stream;

    #[instrument(skip_all)]
    fn accept(&self, stream: I, service: S) -> Self::Future {
        let acceptor = self.inner.clone();
        let arbiter = self.arbiter.clone();

        Box::pin(async move {
            match AssertUnwindSafe(acceptor.accept(stream, service))
                .catch_unwind()
                .await
            {
                Ok(result) => result,
                Err(panic) => {
                    let panic_msg = panic
                        .downcast_ref::<&str>()
                        .copied()
                        .or_else(|| panic.downcast_ref::<String>().map(String::as_str))
                        .unwrap_or("Unknown panic message");
                    error!(panic_msg, "acceptor panicked, shutting down immediately");
                    arbiter.do_fast_shutdown().await;
                    Err(io::Error::other("acceptor panicked"))
                }
            }
        })
    }
}

#[cfg(test)]
mod tests {
    use std::{io, panic::panic_any};

    use ak_common::{Arbiter, Tasks};
    use axum_server::accept::Accept;
    use futures::future::BoxFuture;
    use tokio::{
        io::{DuplexStream, duplex},
        time::{Duration, timeout},
    };

    use super::CatchPanicAcceptor;

    fn stream() -> DuplexStream {
        let (stream, _peer) = duplex(1);
        stream
    }

    /// Returns true if the arbiter's fast-shutdown has already been triggered.
    async fn fast_shutdown_triggered(arbiter: &Arbiter) -> bool {
        timeout(Duration::from_millis(10), arbiter.fast_shutdown())
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

    /// Panics with a `String` payload (format-string panics always produce `String`).
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

    // --- tests ---

    #[tokio::test]
    async fn passes_through_success() {
        let tasks = Tasks::new().expect("failed to create tasks");
        let arbiter = tasks.arbiter();
        let acceptor = CatchPanicAcceptor::new(OkAcceptor, arbiter.clone());

        let result = acceptor.accept(stream(), ()).await;

        assert!(result.is_ok());
        assert!(!fast_shutdown_triggered(&arbiter).await);
    }

    #[tokio::test]
    async fn passes_through_error() {
        let tasks = Tasks::new().expect("failed to create tasks");
        let arbiter = tasks.arbiter();
        let acceptor = CatchPanicAcceptor::new(ErrorAcceptor, arbiter.clone());

        let result = acceptor.accept(stream(), ()).await;

        assert!(result.is_err());
        assert_eq!(result.unwrap_err().to_string(), "inner error");
        assert!(!fast_shutdown_triggered(&arbiter).await);
    }

    #[tokio::test]
    async fn catches_str_panic_and_shuts_down() {
        let tasks = Tasks::new().expect("failed to create tasks");
        let arbiter = tasks.arbiter();
        let acceptor = CatchPanicAcceptor::new(PanicStrAcceptor, arbiter.clone());

        let result = acceptor.accept(stream(), ()).await;

        assert!(result.is_err());
        assert_eq!(result.unwrap_err().to_string(), "acceptor panicked");
        assert!(fast_shutdown_triggered(&arbiter).await);
    }

    #[tokio::test]
    async fn catches_string_panic_and_shuts_down() {
        let tasks = Tasks::new().expect("failed to create tasks");
        let arbiter = tasks.arbiter();
        let acceptor = CatchPanicAcceptor::new(PanicStringAcceptor, arbiter.clone());

        let result = acceptor.accept(stream(), ()).await;

        assert!(result.is_err());
        assert_eq!(result.unwrap_err().to_string(), "acceptor panicked");
        assert!(fast_shutdown_triggered(&arbiter).await);
    }

    #[tokio::test]
    async fn catches_unknown_panic_and_shuts_down() {
        let tasks = Tasks::new().expect("failed to create tasks");
        let arbiter = tasks.arbiter();
        let acceptor = CatchPanicAcceptor::new(PanicUnknownAcceptor, arbiter.clone());

        let result = acceptor.accept(stream(), ()).await;

        assert!(result.is_err());
        assert_eq!(result.unwrap_err().to_string(), "acceptor panicked");
        assert!(fast_shutdown_triggered(&arbiter).await);
    }
}
