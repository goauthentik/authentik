package application

import (
	"encoding/base64"
	"fmt"
	"net/http"
	"strings"

	"goauthentik.io/internal/constants"
)

func (a *Application) addHeaders(headers http.Header, c *Claims) {
	// https://goauthentik.io/docs/providers/proxy/proxy

	// Legacy headers, remove after 2022.1
	headers.Set("X-Auth-Username", c.PreferredUsername)
	headers.Set("X-Auth-Groups", strings.Join(c.Groups, "|"))
	headers.Set("X-Forwarded-Email", c.Email)
	headers.Set("X-Forwarded-Preferred-Username", c.PreferredUsername)
	headers.Set("X-Forwarded-User", c.Sub)

	// New headers, unique prefix
	headers.Set("X-authentik-username", c.PreferredUsername)
	headers.Set("X-authentik-groups", strings.Join(c.Groups, "|"))
	headers.Set("X-authentik-email", c.Email)
	headers.Set("X-authentik-name", c.Name)
	headers.Set("X-authentik-uid", c.Sub)

	// System headers
	headers.Set("X-authentik-meta-jwks", a.proxyConfig.OidcConfiguration.JwksUri)
	headers.Set("X-authentik-meta-outpost", a.outpostName)
	headers.Set("X-authentik-meta-provider", a.proxyConfig.Name)
	headers.Set("X-authentik-meta-app", a.proxyConfig.AssignedApplicationSlug)
	headers.Set("X-authentik-meta-version", constants.OutpostUserAgent())

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
		headers.Set("Authorization", fmt.Sprintf("Basic %s", authVal))
	}
	// Check if user has additional headers set that we should sent
	if additionalHeaders, ok := userAttributes["additionalHeaders"].(map[string]interface{}); ok {
		a.log.WithField("headers", additionalHeaders).Trace("setting additional headers")
		if additionalHeaders == nil {
			return
		}
		for key, value := range additionalHeaders {
			headers.Set(key, toString(value))
		}
	}
}
