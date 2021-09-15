package application

import (
	"html/template"
	"net/http"

	log "github.com/sirupsen/logrus"
)

// NewProxyErrorHandler creates a ProxyErrorHandler using the template given.
func NewProxyErrorHandler(errorTemplate *template.Template) func(http.ResponseWriter, *http.Request, error) {
	return func(rw http.ResponseWriter, req *http.Request, proxyErr error) {
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
		err := errorTemplate.Execute(rw, data)
		if err != nil {
			http.Error(rw, "Internal Server Error", http.StatusInternalServerError)
		}
	}
}
