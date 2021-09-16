package templates

import (
	_ "embed"
	"html/template"
	"log"
)

//go:embed error.html
var ErrorTemplate string

func GetTemplates() *template.Template {
	t, err := template.New("foo").Parse(ErrorTemplate)
	if err != nil {
		log.Fatalf("failed parsing template %s", err)
	}
	return t
}
