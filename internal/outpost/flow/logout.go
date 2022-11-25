package flow

import (
	"fmt"
	"net/http"

	log "github.com/sirupsen/logrus"
	"goauthentik.io/api/v3"
)

type LogoutFunc func(*http.Cookie, *api.Configuration)

func Logout(session *http.Cookie, c *api.Configuration) {
	req, err := http.NewRequest("GET", fmt.Sprintf("%s://%s/api/v3/flows/executor/default-invalidation-flow/", c.Scheme, c.Host), nil)
	req.Header.Set("UserAgent", c.UserAgent)
	if err != nil {
		log.WithField("err", err).Warn("Could not create request to invalidate session")
		return
	}
	req.AddCookie(session)
	res, err := c.HTTPClient.Do(req)
	if err != nil {
		log.WithField("err", err).Error("Could not execute request")
		return
	}
	defer res.Body.Close()
	log.Debug("Logout completed")
}
