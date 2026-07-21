package web

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
)

func serveStatic(t *testing.T, rangeHeader string) *http.Response {
	t.Helper()
	content := strings.Repeat("0123456789abcdef", 4096)
	inner := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		http.ServeContent(w, r, "archive.pmtiles", time.Unix(0, 0), strings.NewReader(content))
	})
	ws := &WebServer{}
	req := httptest.NewRequest(http.MethodGet, "/archive.pmtiles", nil)
	if rangeHeader != "" {
		req.Header.Set("Range", rangeHeader)
	}
	rr := httptest.NewRecorder()
	ws.staticHeaderMiddleware(inner).ServeHTTP(rr, req)
	return rr.Result()
}

// The ETag of a 206 must identify the complete representation. The etag
// middleware hashes the bytes it writes, giving every range chunk its own
// ETag — byte-serving consumers such as PMTiles read that as the file
// changing between requests. Ranged responses are served without one.
func TestStaticHeadersSkipEtagForRangeRequests(t *testing.T) {
	first := serveStatic(t, "bytes=0-16383")
	assert.Equal(t, http.StatusPartialContent, first.StatusCode)
	assert.Equal(t, "16384", first.Header.Get("Content-Length"))
	assert.Empty(t, first.Header.Get("Etag"))

	second := serveStatic(t, "bytes=16384-32767")
	assert.Equal(t, http.StatusPartialContent, second.StatusCode)
	assert.Equal(t, first.Header.Get("Etag"), second.Header.Get("Etag"))
}

func TestStaticHeadersSetEtagForFullResponses(t *testing.T) {
	res := serveStatic(t, "")
	assert.Equal(t, http.StatusOK, res.StatusCode)
	assert.NotEmpty(t, res.Header.Get("Etag"))
	assert.Equal(t, "public, no-transform", res.Header.Get("Cache-Control"))
}
