package server

import (
	"bufio"
	"errors"
	"fmt"
	"net"
	"net/http"
	"time"

	log "github.com/sirupsen/logrus"
)

// responseLogger is wrapper of http.ResponseWriter that keeps track of its HTTP status
// code and body size
type responseLogger struct {
	w        http.ResponseWriter
	status   int
	size     int
	upstream string
	authInfo string
}

// Header returns the ResponseWriter's Header
func (l *responseLogger) Header() http.Header {
	return l.w.Header()
}

// Support Websocket
func (l *responseLogger) Hijack() (rwc net.Conn, buf *bufio.ReadWriter, err error) {
	if hj, ok := l.w.(http.Hijacker); ok {
		return hj.Hijack()
	}
	return nil, nil, errors.New("http.Hijacker is not available on writer")
}

// ExtractGAPMetadata extracts and removes GAP headers from the ResponseWriter's
// Header
func (l *responseLogger) ExtractGAPMetadata() {
	upstream := l.w.Header().Get("GAP-Upstream-Address")
	if upstream != "" {
		l.upstream = upstream
		l.w.Header().Del("GAP-Upstream-Address")
	}
	authInfo := l.w.Header().Get("GAP-Auth")
	if authInfo != "" {
		l.authInfo = authInfo
		l.w.Header().Del("GAP-Auth")
	}
}

// Write writes the response using the ResponseWriter
func (l *responseLogger) Write(b []byte) (int, error) {
	if l.status == 0 {
		// The status will be StatusOK if WriteHeader has not been called yet
		l.status = http.StatusOK
	}
	l.ExtractGAPMetadata()
	size, err := l.w.Write(b)
	l.size += size
	return size, err
}

// WriteHeader writes the status code for the Response
func (l *responseLogger) WriteHeader(s int) {
	l.ExtractGAPMetadata()
	l.w.WriteHeader(s)
	l.status = s
}

// Status returns the response status code
func (l *responseLogger) Status() int {
	return l.status
}

// Size returns the response size
func (l *responseLogger) Size() int {
	return l.size
}

// Flush sends any buffered data to the client
func (l *responseLogger) Flush() {
	if flusher, ok := l.w.(http.Flusher); ok {
		flusher.Flush()
	}
}

// loggingHandler is the http.Handler implementation for LoggingHandler
type loggingHandler struct {
	handler http.Handler
	logger  *log.Entry
}

// LoggingHandler provides an http.Handler which logs requests to the HTTP server
func LoggingHandler(h http.Handler) http.Handler {
	return loggingHandler{
		handler: h,
		logger:  log.WithField("component", "http-server"),
	}
}

func (h loggingHandler) ServeHTTP(w http.ResponseWriter, req *http.Request) {
	t := time.Now()
	url := *req.URL
	responseLogger := &responseLogger{w: w}
	h.handler.ServeHTTP(responseLogger, req)
	duration := float64(time.Since(t)) / float64(time.Second)
	h.logger.WithFields(log.Fields{
		"Client":          req.RemoteAddr,
		"Host":            req.Host,
		"Protocol":        req.Proto,
		"RequestDuration": fmt.Sprintf("%0.3f", duration),
		"RequestMethod":   req.Method,
		"ResponseSize":    responseLogger.Size(),
		"StatusCode":      responseLogger.Status(),
		"Timestamp":       t,
		"Upstream":        responseLogger.upstream,
		"UserAgent":       req.UserAgent(),
		"Username":        responseLogger.authInfo,
	}).Info(url.RequestURI())
	// logger.PrintReq(responseLogger.authInfo, responseLogger.upstream, req, url, t, , )
}
