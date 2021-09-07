package proxy

import (
	"html/template"

	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/proxy/templates"
)

func getTemplates() *template.Template {
	t, err := template.New("foo").Parse(templates.ErrorTemplate)
	if err != nil {
		log.Fatalf("failed parsing template %s", err)
	}
	return t
}
