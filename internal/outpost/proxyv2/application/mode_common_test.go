package application

import (
	"net/url"
	"regexp"
	"testing"

	"github.com/stretchr/testify/assert"
	"goauthentik.io/api/v3"
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
	a.proxyConfig.Mode = *api.NewNullableProxyMode(api.PROXYMODE_PROXY.Ptr())

	assert.Equal(t, false, a.IsAllowlisted(urlMustParse("")))
	a.UnauthenticatedRegex = []*regexp.Regexp{
		regexp.MustCompile("^/foo"),
	}
	assert.Equal(t, true, a.IsAllowlisted(urlMustParse("http://some-host/foo")))
}

func TestIsAllowlisted_Proxy_Domain(t *testing.T) {
	a := newTestApplication()
	a.proxyConfig.Mode = *api.NewNullableProxyMode(api.PROXYMODE_FORWARD_DOMAIN.Ptr())

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
