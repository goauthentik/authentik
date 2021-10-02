package application

import (
	"fmt"
	"html/template"
	"net/http"

	log "github.com/sirupsen/logrus"
)

// NewProxyErrorHandler creates a ProxyErrorHandler using the template given.
func (a *Application) newProxyErrorHandler(errorTemplate *template.Template) func(http.ResponseWriter, *http.Request, error) {
	return func(rw http.ResponseWriter, req *http.Request, proxyErr error) {
		claims, _ := a.getClaims(req)
		log.WithError(proxyErr).Warning("Error proxying to upstream server")
		rw.WriteHeader(http.StatusBadGateway)
		data := struct {
			Title       string
			Message     string
			ProxyPrefix string
		}{
			Title:       "Bad Gateway",
			Message:     "Error proxying to upstream server",
			ProxyPrefix: "/akprox",
		}
		if claims != nil {
			data.Message = fmt.Sprintf("Error proxying to upstream server: %s", proxyErr.Error())
		}
		err := errorTemplate.Execute(rw, data)
		if err != nil {
			http.Error(rw, "Internal Server Error", http.StatusInternalServerError)
		}
	}
}
