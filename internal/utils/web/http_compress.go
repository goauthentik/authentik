// https://github.com/gorilla/handlers/issues/259#issuecomment-2671695039
package web

import (
	"bufio"
	"net"
	"net/http"

	"github.com/gorilla/handlers"
)

// compressHandler is an HTTP handler that adds the Content-Encoding header
// back to responses when removed by the http.FileServer.
//
// handlers.CompressHandler(newCompressHandler(http.FileServer(...)))
type compressHandler struct {
	// handler is an HTTP handler, usually an http.FileServer.
	handler http.Handler
}

var _ http.Handler = &compressHandler{}

func NewCompressHandler(handler http.Handler) http.Handler {
	h := &compressHandler{
		handler: handler,
	}
	return handlers.CompressHandler(h)
}

func (h *compressHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	// The wrapped response writer saves the incoming content encoding so
	// it can be restored when writing the response headers.
	cw := &compressedResponseWriter{
		encoding:       w.Header().Get("Content-Encoding"),
		fixed:          false,
		responseWriter: w,
	}
	h.handler.ServeHTTP(cw, r)
}

// compressedResponseWriter is an http.ResponseWriter that ensures that a
// previously-set Content-Encoding header is in place before writing the
// response.
type compressedResponseWriter struct {
	encoding       string
	fixed          bool
	responseWriter http.ResponseWriter
}

var _ http.ResponseWriter = &compressedResponseWriter{}

func (w *compressedResponseWriter) Header() http.Header {
	return w.responseWriter.Header()
}

func (w *compressedResponseWriter) fixContentEncoding() {
	if w.fixed {
		return
	}
	w.fixed = true
	// The Go 1.23 http.FileServer() removes headers like Content-Encoding
	// from error responses. This breaks gzip and deflate encoding.
	// https://github.com/gorilla/handlers/issues/259
	// https://github.com/golang/go/issues/66343
	if w.encoding == "gzip" || w.encoding == "deflate" {
		if w.Header().Get("Content-Encoding") == "" {
			w.Header().Set("Content-Encoding", w.encoding)
		}
	}
}

func (w *compressedResponseWriter) Write(data []byte) (int, error) {
	w.fixContentEncoding()
	return w.responseWriter.Write(data)
}

func (w *compressedResponseWriter) WriteHeader(statusCode int) {
	w.fixContentEncoding()
	w.responseWriter.WriteHeader(statusCode)
}

func (w *compressedResponseWriter) Hijack() (net.Conn, *bufio.ReadWriter, error) {
	if hj, ok := w.responseWriter.(http.Hijacker); ok {
		return hj.Hijack()
	}
	return nil, nil, http.ErrNotSupported
}

// Ensure our compressedResponseWriter implements the necessary interfaces.
var _ http.ResponseWriter = &compressedResponseWriter{}
var _ http.Hijacker = &compressedResponseWriter{}
