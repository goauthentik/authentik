package application

import (
	"net/http"
	"net/url"
	"regexp"
	"testing"

	"github.com/stretchr/testify/assert"
	"goauthentik.io/api/v3"
	"goauthentik.io/internal/constants"
	"goauthentik.io/internal/outpost/proxyv2/types"
)

func urlMustParse(u string) *url.URL {
	ur, err := url.Parse(u)
	if err != nil {
		panic(err)
	}
	return ur
}

func TestIsAllowlisted_Proxy_Single(t *testing.T) {
	a := newTestApplication()
	a.proxyConfig.Mode = api.PROXYMODE_PROXY.Ptr()

	assert.Equal(t, false, a.IsAllowlisted(urlMustParse("")))
	a.UnauthenticatedRegex = []*regexp.Regexp{
		regexp.MustCompile("^/foo"),
	}
	assert.Equal(t, true, a.IsAllowlisted(urlMustParse("http://some-host/foo")))
}

func TestIsAllowlisted_Proxy_Domain(t *testing.T) {
	a := newTestApplication()
	a.proxyConfig.Mode = api.PROXYMODE_FORWARD_DOMAIN.Ptr()

	assert.Equal(t, false, a.IsAllowlisted(urlMustParse("")))
	a.UnauthenticatedRegex = []*regexp.Regexp{
		regexp.MustCompile("^/foo"),
	}
	assert.Equal(t, false, a.IsAllowlisted(urlMustParse("http://some-host/foo")))
	a.UnauthenticatedRegex = []*regexp.Regexp{
		regexp.MustCompile("^http://some-host/foo"),
	}
	assert.Equal(t, true, a.IsAllowlisted(urlMustParse("http://some-host/foo")))
	a.UnauthenticatedRegex = []*regexp.Regexp{
		regexp.MustCompile("https://health.domain.tld/ping/*"),
	}
	assert.Equal(t, false, a.IsAllowlisted(urlMustParse("http://some-host/foo")))
	assert.Equal(t, false, a.IsAllowlisted(urlMustParse("https://health.domain.tld/")))
	assert.Equal(t, true, a.IsAllowlisted(urlMustParse("https://health.domain.tld/ping/qq")))
}

func TestAdHeaders_Standard(t *testing.T) {
	a := newTestApplication()
	h := http.Header{}
	a.addHeaders(h, &types.Claims{
		PreferredUsername: "foo",
		Groups:            []string{"foo", "bar"},
		Entitlements:      []string{"bar", "quox"},
		Email:             "bar@authentik.company",
		Name:              "foo",
		Sub:               "bar",
		RawToken:          "baz",
	})
	assert.Equal(t, http.Header{
		"X-Authentik-Email":         []string{"bar@authentik.company"},
		"X-Authentik-Entitlements":  []string{"bar|quox"},
		"X-Authentik-Groups":        []string{"foo|bar"},
		"X-Authentik-Jwt":           []string{"baz"},
		"X-Authentik-Meta-App":      []string{""},
		"X-Authentik-Meta-Jwks":     []string{""},
		"X-Authentik-Meta-Outpost":  []string{""},
		"X-Authentik-Meta-Provider": []string{a.proxyConfig.Name},
		"X-Authentik-Meta-Version":  []string{constants.UserAgentOutpost()},
		"X-Authentik-Name":          []string{"foo"},
		"X-Authentik-Uid":           []string{"bar"},
		"X-Authentik-Username":      []string{"foo"},
	}, h)
}

func TestAdHeaders_BasicAuth(t *testing.T) {
	a := newTestApplication()
	a.proxyConfig.BasicAuthEnabled = api.PtrBool(true)
	a.proxyConfig.BasicAuthUserAttribute = api.PtrString("user")
	a.proxyConfig.BasicAuthPasswordAttribute = api.PtrString("pass")
	h := http.Header{}
	a.addHeaders(h, &types.Claims{
		PreferredUsername: "foo",
		Groups:            []string{"foo", "bar"},
		Entitlements:      []string{"bar", "quox"},
		Email:             "bar@authentik.company",
		Name:              "foo",
		Sub:               "bar",
		RawToken:          "baz",
		Proxy: &types.ProxyClaims{
			UserAttributes: map[string]any{
				"user": "foo",
				"pass": "baz",
			},
		},
	})
	assert.Equal(t, http.Header{
		"Authorization":             []string{"Basic Zm9vOmJheg=="},
		"X-Authentik-Email":         []string{"bar@authentik.company"},
		"X-Authentik-Entitlements":  []string{"bar|quox"},
		"X-Authentik-Groups":        []string{"foo|bar"},
		"X-Authentik-Jwt":           []string{"baz"},
		"X-Authentik-Meta-App":      []string{""},
		"X-Authentik-Meta-Jwks":     []string{""},
		"X-Authentik-Meta-Outpost":  []string{""},
		"X-Authentik-Meta-Provider": []string{a.proxyConfig.Name},
		"X-Authentik-Meta-Version":  []string{constants.UserAgentOutpost()},
		"X-Authentik-Name":          []string{"foo"},
		"X-Authentik-Uid":           []string{"bar"},
		"X-Authentik-Username":      []string{"foo"},
	}, h)
}

func TestAdHeaders_Extra(t *testing.T) {
	a := newTestApplication()
	h := http.Header{}
	a.addHeaders(h, &types.Claims{
		PreferredUsername: "foo",
		Groups:            []string{"foo", "bar"},
		Entitlements:      []string{"bar", "quox"},
		Email:             "bar@authentik.company",
		Name:              "foo",
		Sub:               "bar",
		RawToken:          "baz",
		Proxy: &types.ProxyClaims{
			UserAttributes: map[string]any{
				"additionalHeaders": map[string]any{
					"foo": "bar",
				},
			},
		},
	})
	assert.Equal(t, http.Header{
		"Foo":                       []string{"bar"},
		"X-Authentik-Email":         []string{"bar@authentik.company"},
		"X-Authentik-Entitlements":  []string{"bar|quox"},
		"X-Authentik-Groups":        []string{"foo|bar"},
		"X-Authentik-Jwt":           []string{"baz"},
		"X-Authentik-Meta-App":      []string{""},
		"X-Authentik-Meta-Jwks":     []string{""},
		"X-Authentik-Meta-Outpost":  []string{""},
		"X-Authentik-Meta-Provider": []string{a.proxyConfig.Name},
		"X-Authentik-Meta-Version":  []string{constants.UserAgentOutpost()},
		"X-Authentik-Name":          []string{"foo"},
		"X-Authentik-Uid":           []string{"bar"},
		"X-Authentik-Username":      []string{"foo"},
	}, h)
}

func TestAdHeaders_UnderscoreInitial(t *testing.T) {
	a := newTestApplication()
	h := http.Header{}
	h.Set("X_AUTHENTIK_USERNAME", "another user")
	h.Set("X-Authentik_username", "another user")
	a.addHeaders(h, &types.Claims{
		PreferredUsername: "foo",
		Groups:            []string{"foo", "bar"},
		Entitlements:      []string{"bar", "quox"},
		Email:             "bar@authentik.company",
		Name:              "foo",
		Sub:               "bar",
		RawToken:          "baz",
	})
	assert.Equal(t, http.Header{
		"X-Authentik-Email":         []string{"bar@authentik.company"},
		"X-Authentik-Entitlements":  []string{"bar|quox"},
		"X-Authentik-Groups":        []string{"foo|bar"},
		"X-Authentik-Jwt":           []string{"baz"},
		"X-Authentik-Meta-App":      []string{""},
		"X-Authentik-Meta-Jwks":     []string{""},
		"X-Authentik-Meta-Outpost":  []string{""},
		"X-Authentik-Meta-Provider": []string{a.proxyConfig.Name},
		"X-Authentik-Meta-Version":  []string{constants.UserAgentOutpost()},
		"X-Authentik-Name":          []string{"foo"},
		"X-Authentik-Uid":           []string{"bar"},
		"X-Authentik-Username":      []string{"foo"},
	}, h)
}
