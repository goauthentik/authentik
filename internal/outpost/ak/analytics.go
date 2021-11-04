package ak

import (
	"bytes"
	"crypto/sha512"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io/ioutil"
	"net/http"
	"net/url"
	"os"

	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/constants"
)

func exists(name string) bool {
	_, err := os.Stat(name)
	if err == nil {
		return true
	}
	if errors.Is(err, os.ErrNotExist) {
		return false
	}
	return false
}

func getEnv() string {
	if _, o := os.LookupEnv("KUBERNETES_SERVICE_HOST"); o {
		return "kubernetes"
	}
	if _, o := os.LookupEnv("CI"); o {
		return "ci"
	}
	if exists("/tmp/authentik-mode") {
		return "embedded"
	}
	return "custom"
}

func analytics(akURL url.URL, on string) {
	if _, s := os.LookupEnv("AUTHENTIK_DISABLE_ANALYTICS"); s {
		return
	}
	body := struct {
		Domain   string `json:"domain"`
		Name     string `json:"name"`
		URL      string `json:"url"`
		Referrer string `json:"referrer"`
	}{
		Domain:   "authentik",
		Name:     "pageview",
		URL:      fmt.Sprintf("http://localhost/outpost/%s", getEnv()),
		Referrer: fmt.Sprintf("%s (%s)", constants.VERSION, constants.BUILD()),
	}
	b, err := json.Marshal(body)
	if err != nil {
		log.WithError(err).Debug("test")
	}
	ua := fmt.Sprintf("%s-%s", akURL.Host, on)
	h := sha512.New()
	h.Write([]byte(ua))

	req, err := http.NewRequest("POST", "https://goauthentik.io/api/event", bytes.NewReader(b))
	if err != nil {
		log.WithError(err).Debug("test")
	}
	req.Header.Set("Content-Type", "text/plain")
	req.Header.Set("User-Agent", hex.EncodeToString(h.Sum(nil)))
	r, err := http.DefaultClient.Do(req)
	if err != nil {
		log.WithError(err).Debug("test")
	}
	if r.StatusCode >= 400 {
		b, _ := ioutil.ReadAll(r.Body)
		log.WithField("status", r.StatusCode).WithField("body", string(b)).Debug("failed")
	}
}
