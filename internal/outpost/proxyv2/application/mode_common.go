package application

import (
	"encoding/base64"
	"fmt"
	"net/http"
	"strings"
)

func (a *Application) addHeaders(r *http.Request, c *Claims) {
	// https://goauthentik.io/docs/providers/proxy/proxy

	// Legacy headers, remove after 2022.1
	r.Header.Set("X-Auth-Username", c.PreferredUsername)
	r.Header.Set("X-Auth-Groups", strings.Join(c.Groups, "|"))
	r.Header.Set("X-Forwarded-Email", c.Email)
	r.Header.Set("X-Forwarded-Preferred-Username", c.PreferredUsername)
	r.Header.Set("X-Forwarded-User", c.Sub)

	// New headers, unique prefix
	r.Header.Set("X-authentik-username", c.PreferredUsername)
	r.Header.Set("X-authentik-groups", strings.Join(c.Groups, "|"))
	r.Header.Set("X-authentik-email", c.Email)
	r.Header.Set("X-authentik-name", c.Name)
	r.Header.Set("X-authentik-uid", c.Sub)

	userAttributes := c.Proxy.UserAttributes
	// Attempt to set basic auth based on user's attributes
	if *a.proxyConfig.BasicAuthEnabled {
		var ok bool
		var password string
		if password, ok = userAttributes[*a.proxyConfig.BasicAuthPasswordAttribute].(string); !ok {
			password = ""
		}
		// Check if we should use email or a custom attribute as username
		var username string
		if username, ok = userAttributes[*a.proxyConfig.BasicAuthUserAttribute].(string); !ok {
			username = c.Email
		}
		authVal := base64.StdEncoding.EncodeToString([]byte(username + ":" + password))
		a.log.WithField("username", username).Trace("setting http basic auth")
		r.Header["Authorization"] = []string{fmt.Sprintf("Basic %s", authVal)}
	}
	// Check if user has additional headers set that we should sent
	if additionalHeaders, ok := userAttributes["additionalHeaders"].(map[string]interface{}); ok {
		a.log.WithField("headers", additionalHeaders).Trace("setting additional headers")
		if additionalHeaders == nil {
			return
		}
		for key, value := range additionalHeaders {
			r.Header.Set(key, toString(value))
		}
	}
}

func copyHeadersToResponse(rw http.ResponseWriter, r *http.Request) {
	for headerKey, headers := range r.Header {
		for _, value := range headers {
			rw.Header().Set(headerKey, value)
		}
	}
}
