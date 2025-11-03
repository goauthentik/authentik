package application

import (
	"context"
	"encoding/base64"
	"errors"
	"fmt"
	"net/http"
	"net/url"
	"strings"

	"goauthentik.io/api/v3"
	"goauthentik.io/internal/constants"
	"goauthentik.io/internal/outpost/proxyv2/types"
)

func (a *Application) addHeaders(headers http.Header, c *types.Claims) {
	nh := a.getHeaders(c)
	for key, val := range nh {
		headers.Set(key, val)
	}
	a.removeDuplicateUnderscoreHeader(headers)
}

func (a *Application) removeDuplicateUnderscoreHeader(h http.Header) {
	for key := range h {
		ush := strings.ReplaceAll(key, "_", "-")
		if _, ok := h[ush]; !ok {
			h.Del(key)
		}
	}
}

func (a *Application) getHeaders(c *types.Claims) map[string]string {
	headers := map[string]string{}
	// https://docs.goauthentik.io/add-secure-apps/providers/proxy
	headers["X-authentik-username"] = c.PreferredUsername
	headers["X-authentik-groups"] = strings.Join(c.Groups, "|")
	headers["X-authentik-entitlements"] = strings.Join(c.Entitlements, "|")
	headers["X-authentik-email"] = c.Email
	headers["X-authentik-name"] = c.Name
	headers["X-authentik-uid"] = c.Sub
	headers["X-authentik-jwt"] = c.RawToken

	// System headers
	headers["X-authentik-meta-jwks"] = a.endpoint.JwksUri
	headers["X-authentik-meta-outpost"] = a.outpostName
	headers["X-authentik-meta-provider"] = a.proxyConfig.Name
	headers["X-authentik-meta-app"] = a.proxyConfig.AssignedApplicationSlug
	headers["X-authentik-meta-version"] = constants.UserAgentOutpost()

	if c.Proxy == nil {
		return headers
	}
	if authz := a.setAuthorizationHeader(c); authz != "" {
		headers["Authorization"] = authz
	}
	// Check if user has additional headers set that we should sent
	userAttributes := c.Proxy.UserAttributes
	if additionalHeaders, ok := userAttributes["additionalHeaders"]; ok {
		a.log.WithField("headers", additionalHeaders).Trace("setting additional headers")
		if additionalHeaders == nil {
			return headers
		}
		for key, value := range additionalHeaders.(map[string]interface{}) {
			headers[key] = toString(value)
		}
	}
	return headers
}

// Attempt to set basic auth based on user's attributes
func (a *Application) setAuthorizationHeader(c *types.Claims) string {
	if !*a.proxyConfig.BasicAuthEnabled {
		return ""
	}
	userAttributes := c.Proxy.UserAttributes
	var ok bool
	var username string
	var password string
	if password, ok = userAttributes[*a.proxyConfig.BasicAuthPasswordAttribute].(string); !ok {
		password = ""
	}
	// Check if we should use email or a custom attribute as username
	if username, ok = userAttributes[*a.proxyConfig.BasicAuthUserAttribute].(string); !ok {
		username = c.Email
	}
	if password == "" {
		return ""
	}
	authVal := base64.StdEncoding.EncodeToString([]byte(username + ":" + password))
	a.log.WithField("username", username).Trace("setting http basic auth")
	return fmt.Sprintf("Basic %s", authVal)
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
	a.log.WithField("url", u.String()).Trace("traefik forwarded url")
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
		a.log.WithField("url", u.String()).Info("building forward URL from X-Original-URI")
		return u, nil
	}
	h := r.Header.Get("X-Original-URL")
	if len(h) < 1 {
		return nil, errors.New("no forward URL found")
	}
	u, err := url.Parse(h)
	if err != nil {
		a.log.WithError(err).Warning("failed to parse URL from nginx")
		return nil, err
	}
	a.log.WithField("url", u.String()).Trace("nginx forwarded url")
	return u, nil
}

func (a *Application) ReportMisconfiguration(r *http.Request, msg string, fields map[string]interface{}) {
	fields["message"] = msg
	a.log.WithFields(fields).Error("Reporting configuration error")
	req := api.EventRequest{
		Action:   api.EVENTACTIONS_CONFIGURATION_ERROR,
		App:      "authentik.providers.proxy", // must match python apps.py name
		ClientIp: *api.NewNullableString(api.PtrString(r.RemoteAddr)),
		Context:  fields,
	}
	_, _, err := a.ak.Client.EventsApi.EventsEventsCreate(context.Background()).EventRequest(req).Execute()
	if err != nil {
		a.log.WithError(err).Warning("failed to report configuration error")
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
		a.log.WithField("match", match).WithField("regex", ur.String()).WithField("url", testString).Trace("Matching URL against allow list")
		if match {
			return true
		}
	}
	return false
}
