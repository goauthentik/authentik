package application

import (
	"fmt"
	"net/http"

	"go.uber.org/zap"
)

type ErrorPageData struct {
	Title       string
	Message     string
	ProxyPrefix string
}

func (a *Application) ErrorPage(rw http.ResponseWriter, r *http.Request, err string) {
	claims, _ := a.checkAuth(rw, r)
	data := ErrorPageData{
		Title:       "Bad Gateway",
		Message:     "Error proxying to upstream server",
		ProxyPrefix: "/outpost.goauthentik.io",
	}
	if claims != nil && claims.Proxy != nil && claims.Proxy.IsSuperuser {
		data.Message = err
	} else {
		data.Message = "Failed to connect to backend."
	}
	er := a.errorTemplates.Execute(rw, data)
	if er != nil {
		http.Error(rw, "Internal Server Error", http.StatusInternalServerError)
	}
}

// NewProxyErrorHandler creates a ProxyErrorHandler using the template given.
func (a *Application) newProxyErrorHandler() func(http.ResponseWriter, *http.Request, error) {
	return func(rw http.ResponseWriter, req *http.Request, proxyErr error) {
		a.log.Warn("Error proxying to upstream server", zap.Error(proxyErr))
		rw.WriteHeader(http.StatusBadGateway)
		a.ErrorPage(rw, req, fmt.Sprintf("Error proxying to upstream server: %v", proxyErr))
	}
}
