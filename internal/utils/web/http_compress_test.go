package web

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
)

func serveRangeable(t *testing.T, rangeHeader string) *http.Response {
	t.Helper()
	content := strings.Repeat("0123456789abcdef", 4096)
	inner := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		http.ServeContent(w, r, "archive.pmtiles", time.Unix(0, 0), strings.NewReader(content))
	})
	req := httptest.NewRequest(http.MethodGet, "/archive.pmtiles", nil)
	req.Header.Set("Accept-Encoding", "gzip, deflate")
	if rangeHeader != "" {
		req.Header.Set("Range", rangeHeader)
	}
	rr := httptest.NewRecorder()
	NewCompressHandler(inner).ServeHTTP(rr, req)
	return rr.Result()
}

// A ranged response must reach the client byte-exact with a Content-Length:
// on-the-fly gzip re-encodes the selected bytes and drops Content-Length,
// which breaks HTTP byte-serving consumers such as PMTiles.
func TestCompressHandlerSkipsRangeRequests(t *testing.T) {
	res := serveRangeable(t, "bytes=0-16383")
	assert.Equal(t, http.StatusPartialContent, res.StatusCode)
	assert.Empty(t, res.Header.Get("Content-Encoding"))
	assert.Equal(t, "16384", res.Header.Get("Content-Length"))
}

func TestCompressHandlerCompressesFullResponses(t *testing.T) {
	res := serveRangeable(t, "")
	assert.Equal(t, http.StatusOK, res.StatusCode)
	assert.Equal(t, "gzip", res.Header.Get("Content-Encoding"))
}
