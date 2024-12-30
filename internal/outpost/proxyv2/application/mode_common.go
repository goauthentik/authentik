package application

import (
	"context"
	"encoding/base64"
	"errors"
	"fmt"
	"net/http"
	"net/url"
	"strings"

	"go.uber.org/zap"
	"goauthentik.io/api/v3"
	"goauthentik.io/internal/config"
	"goauthentik.io/internal/constants"
)

// Attempt to set basic auth based on user's attributes
func (a *Application) setAuthorizationHeader(headers http.Header, c *Claims) {
	if !*a.proxyConfig.BasicAuthEnabled {
		return
	}
	userAttributes := c.Proxy.UserAttributes
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
	if username == "" && password == "" {
		return
	}
	authVal := base64.StdEncoding.EncodeToString([]byte(username + ":" + password))
	a.log.Debug("setting http basic auth", zap.String("username", username), config.Trace())
	headers.Set("Authorization", fmt.Sprintf("Basic %s", authVal))
}

func (a *Application) addHeaders(headers http.Header, c *Claims) {
	// https://goauthentik.io/docs/providers/proxy/proxy
	headers.Set("X-authentik-username", c.PreferredUsername)
	headers.Set("X-authentik-groups", strings.Join(c.Groups, "|"))
	headers.Set("X-authentik-entitlements", strings.Join(c.Entitlements, "|"))
	headers.Set("X-authentik-email", c.Email)
	headers.Set("X-authentik-name", c.Name)
	headers.Set("X-authentik-uid", c.Sub)
	headers.Set("X-authentik-jwt", c.RawToken)

	// System headers
	headers.Set("X-authentik-meta-jwks", a.endpoint.JwksUri)
	headers.Set("X-authentik-meta-outpost", a.outpostName)
	headers.Set("X-authentik-meta-provider", a.proxyConfig.Name)
	headers.Set("X-authentik-meta-app", a.proxyConfig.AssignedApplicationSlug)
	headers.Set("X-authentik-meta-version", constants.OutpostUserAgent())

	if c.Proxy == nil {
		return
	}
	userAttributes := c.Proxy.UserAttributes
	a.setAuthorizationHeader(headers, c)
	// Check if user has additional headers set that we should sent
	if additionalHeaders, ok := userAttributes["additionalHeaders"]; ok {
		a.log.Debug("setting additional headers", config.Trace(), zap.Any("headers", additionalHeaders))
		if additionalHeaders == nil {
			return
		}
		for key, value := range additionalHeaders.(map[string]interface{}) {
			headers.Set(key, toString(value))
		}
	}
}

// getTraefikForwardUrl See https://doc.traefik.io/traefik/middlewares/forwardauth/
func (a *Application) getTraefikForwardUrl(r *http.Request) (*url.URL, error) {
	u, err := url.Parse(fmt.Sprintf(
		"%s://%s%s",
		r.Header.Get("X-Forwarded-Proto"),
		r.Header.Get("X-Forwarded-Host"),
		r.Header.Get("X-Forwarded-Uri"),
	))
	if err != nil {
		return nil, err
	}
	a.log.Debug("traefik forward url", zap.String("url", u.String()))
	return u, nil
}

// getNginxForwardUrl See https://github.com/kubernetes/ingress-nginx/blob/main/rootfs/etc/nginx/template/nginx.tmpl
func (a *Application) getNginxForwardUrl(r *http.Request) (*url.URL, error) {
	ou := r.Header.Get("X-Original-URI")
	if ou != "" {
		// Turn this full URL into a relative URL
		u := &url.URL{
			Host:   "",
			Scheme: "",
			Path:   ou,
		}
		a.log.Debug("building forward URL from X-Original-URI", zap.String("url", u.String()))
		return u, nil
	}
	h := r.Header.Get("X-Original-URL")
	if len(h) < 1 {
		return nil, errors.New("no forward URL found")
	}
	u, err := url.Parse(h)
	if err != nil {
		a.log.Warn("failed to parse URL from nginx", zap.Error(err))
		return nil, err
	}
	a.log.Debug("nginx forwarded url", zap.String("url", u.String()), config.Trace())
	return u, nil
}

func (a *Application) ReportMisconfiguration(r *http.Request, msg string, fields map[string]interface{}) {
	fields["message"] = msg
	a.log.Error("Reporting configuration error", zap.Any("fields", fields))
	req := api.EventRequest{
		Action:   api.EVENTACTIONS_CONFIGURATION_ERROR,
		App:      "authentik.providers.proxy", // must match python apps.py name
		ClientIp: *api.NewNullableString(api.PtrString(r.RemoteAddr)),
		Context:  fields,
	}
	_, _, err := a.ak.Client.EventsApi.EventsEventsCreate(context.Background()).EventRequest(req).Execute()
	if err != nil {
		a.log.Warn("failed to report configuration error", zap.Error(err))
	}
}

func (a *Application) IsAllowlisted(u *url.URL) bool {
	for _, ur := range a.UnauthenticatedRegex {
		var testString string
		if a.Mode() == api.PROXYMODE_PROXY || a.Mode() == api.PROXYMODE_FORWARD_SINGLE {
			testString = u.Path
		} else {
			testString = u.String()
		}
		match := ur.MatchString(testString)
		a.log.Debug("Matching URL against allow list", zap.Bool("match", match), zap.String("regex", ur.String()), zap.String("url", testString), config.Trace())
		if match {
			return true
		}
	}
	return false
}
