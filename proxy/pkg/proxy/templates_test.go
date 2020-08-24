package proxy

import (
	"bytes"
	"io/ioutil"
	"log"
	"os"
	"path/filepath"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestLoadTemplates(t *testing.T) {
	data := struct {
		TestString string
	}{
		TestString: "Testing",
	}

	templates := loadTemplates("")
	assert.NotEqual(t, templates, nil)

	var defaultSignin bytes.Buffer
	templates.ExecuteTemplate(&defaultSignin, "sign_in.html", data)
	assert.Equal(t, "\n<!DOCTYPE html>", defaultSignin.String()[0:16])

	var defaultError bytes.Buffer
	templates.ExecuteTemplate(&defaultError, "error.html", data)
	assert.Equal(t, "\n<!DOCTYPE html>", defaultError.String()[0:16])

	dir, err := ioutil.TempDir("", "templatetest")
	if err != nil {
		log.Fatal(err)
	}
	defer os.RemoveAll(dir)

	templateHTML := `{{.TestString}} {{.TestString | ToLower}} {{.TestString | ToUpper}}`
	signInFile := filepath.Join(dir, "sign_in.html")
	if err := ioutil.WriteFile(signInFile, []byte(templateHTML), 0666); err != nil {
		log.Fatal(err)
	}
	errorFile := filepath.Join(dir, "error.html")
	if err := ioutil.WriteFile(errorFile, []byte(templateHTML), 0666); err != nil {
		log.Fatal(err)
	}
	templates = loadTemplates(dir)
	assert.NotEqual(t, templates, nil)

	var sitpl bytes.Buffer
	templates.ExecuteTemplate(&sitpl, "sign_in.html", data)
	assert.Equal(t, "Testing testing TESTING", sitpl.String())

	var errtpl bytes.Buffer
	templates.ExecuteTemplate(&errtpl, "error.html", data)
	assert.Equal(t, "Testing testing TESTING", errtpl.String())
}

func TestTemplatesCompile(t *testing.T) {
	templates := getTemplates()
	assert.NotEqual(t, templates, nil)
}
