package templates

import (
	_ "embed"
	"html/template"

	log "github.com/sirupsen/logrus"
)

//go:embed error.html
var ErrorTemplate string

func GetTemplates() *template.Template {
	t, err := template.New("authentik.outpost.proxy.errors").Parse(ErrorTemplate)
	if err != nil {
		log.Fatalf("failed parsing template %s", err)
	}
	return t
}
