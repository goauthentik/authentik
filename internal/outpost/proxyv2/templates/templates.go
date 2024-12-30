package templates

import (
	_ "embed"
	"html/template"

	"go.uber.org/zap"
	"goauthentik.io/internal/config"
)

//go:embed error.html
var ErrorTemplate string

func GetTemplates() *template.Template {
	t, err := template.New("authentik.outpost.proxy.errors").Parse(ErrorTemplate)
	if err != nil {
		config.Get().Logger().Fatal("failed parsing template", zap.Error(err))
	}
	return t
}
