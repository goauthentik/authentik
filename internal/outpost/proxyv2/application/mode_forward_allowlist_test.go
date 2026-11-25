package application

import (
	"net/http"
	"net/http/httptest"
	"regexp"
	"testing"

	"github.com/stretchr/testify/assert"
	api "goauthentik.io/packages/client-go"
)

var allowlistedPaths = []string{
	"/public",
	"/public/",
	"/public/ok",
	"/public/a%20b",
	"/public/a..b",
	"/public/a%2Fb",
	"/public/a;b",
	"/public//ok",
}

var notAllowlistedPaths = []string{
	"/public/./ok",
	"/public/../private",
	"/public/./../private",
	"/public/%2e%2e/private",
	"/public/%2E%2E/private",
	"/public/..%2fprivate",
	"/public/%2e%2e%2fprivate",
	"/public/%2f../private",
	"/public/%2F../private",
	"/public/%2F..%2Fprivate",
	"/public%2F..%2Fprivate",
	"/public//../private",
	"/public/..;/private",
	"/public/..%5cprivate",
	"//private/public/ok",
}

func TestForwardHandleNginx_Single_SkipPaths(t *testing.T) {
	for _, p := range allowlistedPaths {
		t.Run(p, func(t *testing.T) {
			a := newTestApplication()
			a.UnauthenticatedRegex = []*regexp.Regexp{regexp.MustCompile(`^/public(/.*)?$`)}
			req, _ := http.NewRequest("GET", nginxPrefix, nil)
			req.Header.Set("X-Original-URL", "http://test.goauthentik.io"+p)

			rr := httptest.NewRecorder()
			a.forwardHandleNginx(rr, req)

			assert.Equal(t, http.StatusOK, rr.Code)
		})
	}
}

func TestForwardHandleNginx_Single_NonCanonicalPaths(t *testing.T) {
	for _, p := range notAllowlistedPaths {
		t.Run(p, func(t *testing.T) {
			a := newTestApplication()
			a.UnauthenticatedRegex = []*regexp.Regexp{regexp.MustCompile(`^/public(/.*)?$`)}
			req, _ := http.NewRequest("GET", nginxPrefix, nil)
			req.Header.Set("X-Original-URL", "http://test.goauthentik.io"+p)

			rr := httptest.NewRecorder()
			a.forwardHandleNginx(rr, req)

			assert.Equal(t, http.StatusUnauthorized, rr.Code)
		})
	}
}

func TestForwardHandleNginx_Domain_SkipPaths(t *testing.T) {
	for _, p := range allowlistedPaths {
		t.Run(p, func(t *testing.T) {
			a := newTestApplication()
			a.proxyConfig.Mode = api.PROXYMODE_FORWARD_DOMAIN.Ptr()
			a.UnauthenticatedRegex = []*regexp.Regexp{
				regexp.MustCompile(`^http://test\.goauthentik\.io/public(/.*)?$`),
			}
			req, _ := http.NewRequest("GET", nginxPrefix, nil)
			req.Header.Set("X-Original-URL", "http://test.goauthentik.io"+p)

			rr := httptest.NewRecorder()
			a.forwardHandleNginx(rr, req)

			assert.Equal(t, http.StatusOK, rr.Code)
		})
	}
}

func TestForwardHandleNginx_Domain_NonCanonicalPaths(t *testing.T) {
	for _, p := range notAllowlistedPaths {
		t.Run(p, func(t *testing.T) {
			a := newTestApplication()
			a.proxyConfig.Mode = api.PROXYMODE_FORWARD_DOMAIN.Ptr()
			a.UnauthenticatedRegex = []*regexp.Regexp{
				regexp.MustCompile(`^http://test\.goauthentik\.io/public(/.*)?$`),
			}
			req, _ := http.NewRequest("GET", nginxPrefix, nil)
			req.Header.Set("X-Original-URL", "http://test.goauthentik.io"+p)

			rr := httptest.NewRecorder()
			a.forwardHandleNginx(rr, req)

			assert.Equal(t, http.StatusUnauthorized, rr.Code)
		})
	}
}

func TestForwardHandleTraefik_Single_SkipPaths(t *testing.T) {
	for _, p := range allowlistedPaths {
		t.Run(p, func(t *testing.T) {
			a := newTestApplication()
			a.UnauthenticatedRegex = []*regexp.Regexp{regexp.MustCompile(`^/public(/.*)?$`)}
			req, _ := http.NewRequest("GET", traefikPrefix, nil)
			req.Header.Set("X-Forwarded-Proto", "http")
			req.Header.Set("X-Forwarded-Host", "test.goauthentik.io")
			req.Header.Set("X-Forwarded-Uri", p)

			rr := httptest.NewRecorder()
			a.forwardHandleTraefik(rr, req)

			assert.Equal(t, http.StatusOK, rr.Code)
		})
	}
}

func TestForwardHandleTraefik_Single_NonCanonicalPaths(t *testing.T) {
	for _, p := range notAllowlistedPaths {
		t.Run(p, func(t *testing.T) {
			a := newTestApplication()
			a.UnauthenticatedRegex = []*regexp.Regexp{regexp.MustCompile(`^/public(/.*)?$`)}
			req, _ := http.NewRequest("GET", traefikPrefix, nil)
			req.Header.Set("X-Forwarded-Proto", "http")
			req.Header.Set("X-Forwarded-Host", "test.goauthentik.io")
			req.Header.Set("X-Forwarded-Uri", p)

			rr := httptest.NewRecorder()
			a.forwardHandleTraefik(rr, req)

			assert.Equal(t, http.StatusFound, rr.Code)
		})
	}
}

func TestForwardHandleTraefik_Domain_SkipPaths(t *testing.T) {
	for _, p := range allowlistedPaths {
		t.Run(p, func(t *testing.T) {
			a := newTestApplication()
			a.proxyConfig.Mode = api.PROXYMODE_FORWARD_DOMAIN.Ptr()
			a.UnauthenticatedRegex = []*regexp.Regexp{
				regexp.MustCompile(`^http://test\.goauthentik\.io/public(/.*)?$`),
			}
			req, _ := http.NewRequest("GET", traefikPrefix, nil)
			req.Header.Set("X-Forwarded-Proto", "http")
			req.Header.Set("X-Forwarded-Host", "test.goauthentik.io")
			req.Header.Set("X-Forwarded-Uri", p)

			rr := httptest.NewRecorder()
			a.forwardHandleTraefik(rr, req)

			assert.Equal(t, http.StatusOK, rr.Code)
		})
	}
}

func TestForwardHandleTraefik_Domain_NonCanonicalPaths(t *testing.T) {
	for _, p := range notAllowlistedPaths {
		t.Run(p, func(t *testing.T) {
			a := newTestApplication()
			a.proxyConfig.Mode = api.PROXYMODE_FORWARD_DOMAIN.Ptr()
			a.UnauthenticatedRegex = []*regexp.Regexp{
				regexp.MustCompile(`^http://test\.goauthentik\.io/public(/.*)?$`),
			}
			req, _ := http.NewRequest("GET", traefikPrefix, nil)
			req.Header.Set("X-Forwarded-Proto", "http")
			req.Header.Set("X-Forwarded-Host", "test.goauthentik.io")
			req.Header.Set("X-Forwarded-Uri", p)

			rr := httptest.NewRecorder()
			a.forwardHandleTraefik(rr, req)

			assert.Equal(t, http.StatusFound, rr.Code)
		})
	}
}

func TestForwardHandleCaddy_Single_SkipPaths(t *testing.T) {
	for _, p := range allowlistedPaths {
		t.Run(p, func(t *testing.T) {
			a := newTestApplication()
			a.UnauthenticatedRegex = []*regexp.Regexp{regexp.MustCompile(`^/public(/.*)?$`)}
			req, _ := http.NewRequest("GET", caddyPrefix, nil)
			req.Header.Set("X-Forwarded-Proto", "http")
			req.Header.Set("X-Forwarded-Host", "test.goauthentik.io")
			req.Header.Set("X-Forwarded-Uri", p)

			rr := httptest.NewRecorder()
			a.forwardHandleCaddy(rr, req)

			assert.Equal(t, http.StatusOK, rr.Code)
		})
	}
}

func TestForwardHandleCaddy_Single_NonCanonicalPaths(t *testing.T) {
	for _, p := range notAllowlistedPaths {
		t.Run(p, func(t *testing.T) {
			a := newTestApplication()
			a.UnauthenticatedRegex = []*regexp.Regexp{regexp.MustCompile(`^/public(/.*)?$`)}
			req, _ := http.NewRequest("GET", caddyPrefix, nil)
			req.Header.Set("X-Forwarded-Proto", "http")
			req.Header.Set("X-Forwarded-Host", "test.goauthentik.io")
			req.Header.Set("X-Forwarded-Uri", p)

			rr := httptest.NewRecorder()
			a.forwardHandleCaddy(rr, req)

			assert.Equal(t, http.StatusFound, rr.Code)
		})
	}
}

func TestForwardHandleCaddy_Domain_SkipPaths(t *testing.T) {
	for _, p := range allowlistedPaths {
		t.Run(p, func(t *testing.T) {
			a := newTestApplication()
			a.proxyConfig.Mode = api.PROXYMODE_FORWARD_DOMAIN.Ptr()
			a.UnauthenticatedRegex = []*regexp.Regexp{
				regexp.MustCompile(`^http://test\.goauthentik\.io/public(/.*)?$`),
			}
			req, _ := http.NewRequest("GET", caddyPrefix, nil)
			req.Header.Set("X-Forwarded-Proto", "http")
			req.Header.Set("X-Forwarded-Host", "test.goauthentik.io")
			req.Header.Set("X-Forwarded-Uri", p)

			rr := httptest.NewRecorder()
			a.forwardHandleCaddy(rr, req)

			assert.Equal(t, http.StatusOK, rr.Code)
		})
	}
}

func TestForwardHandleCaddy_Domain_NonCanonicalPaths(t *testing.T) {
	for _, p := range notAllowlistedPaths {
		t.Run(p, func(t *testing.T) {
			a := newTestApplication()
			a.proxyConfig.Mode = api.PROXYMODE_FORWARD_DOMAIN.Ptr()
			a.UnauthenticatedRegex = []*regexp.Regexp{
				regexp.MustCompile(`^http://test\.goauthentik\.io/public(/.*)?$`),
			}
			req, _ := http.NewRequest("GET", caddyPrefix, nil)
			req.Header.Set("X-Forwarded-Proto", "http")
			req.Header.Set("X-Forwarded-Host", "test.goauthentik.io")
			req.Header.Set("X-Forwarded-Uri", p)

			rr := httptest.NewRecorder()
			a.forwardHandleCaddy(rr, req)

			assert.Equal(t, http.StatusFound, rr.Code)
		})
	}
}

func TestForwardHandleEnvoy_Single_SkipPaths(t *testing.T) {
	for _, p := range allowlistedPaths {
		t.Run(p, func(t *testing.T) {
			a := newTestApplication()
			a.UnauthenticatedRegex = []*regexp.Regexp{regexp.MustCompile(`^/public(/.*)?$`)}
			req, _ := http.NewRequest("GET", "http://test.goauthentik.io"+p, nil)

			rr := httptest.NewRecorder()
			a.forwardHandleEnvoy(rr, req)

			assert.Equal(t, http.StatusOK, rr.Code)
		})
	}
}

func TestForwardHandleEnvoy_Single_NonCanonicalPaths(t *testing.T) {
	for _, p := range notAllowlistedPaths {
		t.Run(p, func(t *testing.T) {
			a := newTestApplication()
			a.UnauthenticatedRegex = []*regexp.Regexp{regexp.MustCompile(`^/public(/.*)?$`)}
			req, _ := http.NewRequest("GET", "http://test.goauthentik.io"+p, nil)

			rr := httptest.NewRecorder()
			a.forwardHandleEnvoy(rr, req)

			assert.Equal(t, http.StatusFound, rr.Code)
		})
	}
}

func TestProxy_NonCanonicalPaths(t *testing.T) {
	for _, p := range notAllowlistedPaths {
		t.Run(p, func(t *testing.T) {
			reached := false
			upstream := httptest.NewServer(http.HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
				reached = true
			}))
			defer upstream.Close()
			a := newTestApplication()
			a.proxyConfig.InternalHost = &upstream.URL
			a.UnauthenticatedRegex = []*regexp.Regexp{regexp.MustCompile(`^/public(/.*)?$`)}
			_ = a.configureProxy()
			req := httptest.NewRequest("GET", p, nil)

			rr := httptest.NewRecorder()
			a.mux.ServeHTTP(rr, req)

			assert.False(t, reached)
		})
	}
}
