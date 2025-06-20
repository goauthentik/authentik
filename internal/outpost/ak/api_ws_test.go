package ak

import (
	"net/url"
	"testing"

	"github.com/stretchr/testify/assert"
)

func URLMustParse(u string) *url.URL {
	ur, err := url.Parse(u)
	if err != nil {
		panic(err)
	}
	return ur
}

func TestWebsocketURL(t *testing.T) {
	u := URLMustParse("http://localhost:9000?foo=bar")
	uuid := "23470845-7263-4fe3-bd79-ec1d7bf77d77"
	ac := &APIController{}
	nu := ac.getWebsocketURL(*u, uuid, url.Values{})
	assert.Equal(t, "ws://localhost:9000/ws/outpost/23470845-7263-4fe3-bd79-ec1d7bf77d77/?foo=bar", nu.String())
}

func TestWebsocketURL_Query(t *testing.T) {
	u := URLMustParse("http://localhost:9000?foo=bar")
	uuid := "23470845-7263-4fe3-bd79-ec1d7bf77d77"
	ac := &APIController{}
	v := url.Values{}
	v.Set("bar", "baz")
	nu := ac.getWebsocketURL(*u, uuid, v)
	assert.Equal(t, "ws://localhost:9000/ws/outpost/23470845-7263-4fe3-bd79-ec1d7bf77d77/?bar=baz&foo=bar", nu.String())
}

func TestWebsocketURL_Subpath(t *testing.T) {
	u := URLMustParse("http://localhost:9000/foo/bar/")
	uuid := "23470845-7263-4fe3-bd79-ec1d7bf77d77"
	ac := &APIController{}
	nu := ac.getWebsocketURL(*u, uuid, url.Values{})
	assert.Equal(t, "ws://localhost:9000/foo/bar/ws/outpost/23470845-7263-4fe3-bd79-ec1d7bf77d77/", nu.String())
}
