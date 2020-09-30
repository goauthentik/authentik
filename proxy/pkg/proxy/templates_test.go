package proxy

import (
	"bytes"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestLoadTemplates(t *testing.T) {
	data := struct {
		TestString string
	}{
		TestString: "Testing",
	}

	templates := getTemplates()
	assert.NotEqual(t, templates, nil)

	var defaultSignin bytes.Buffer
	templates.ExecuteTemplate(&defaultSignin, "sign_in.html", data)
	assert.Equal(t, "\n<!DOCTYPE html>", defaultSignin.String()[0:16])

	var defaultError bytes.Buffer
	templates.ExecuteTemplate(&defaultError, "error.html", data)
	assert.Equal(t, "\n<!DOCTYPE html>", defaultError.String()[0:16])
}

func TestTemplatesCompile(t *testing.T) {
	templates := getTemplates()
	assert.NotEqual(t, templates, nil)
}
