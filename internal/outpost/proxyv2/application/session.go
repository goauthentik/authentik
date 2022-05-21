package application

import (
	"fmt"
	"math"
	"net/url"
	"os"
	"strconv"

	"github.com/gorilla/sessions"
	"goauthentik.io/api/v3"
	"goauthentik.io/internal/config"
	"gopkg.in/boj/redistore.v1"
)

func (a *Application) getStore(p api.ProxyOutpostConfig, externalHost *url.URL) sessions.Store {
	var store sessions.Store
	if config.G.Redis.Host != "" {
		rs, err := redistore.NewRediStoreWithDB(10, "tcp", fmt.Sprintf("%s:%d", config.G.Redis.Host, config.G.Redis.Port), config.G.Redis.Password, strconv.Itoa(config.G.Redis.OutpostSessionDB), []byte(*p.CookieSecret))
		if err != nil {
			panic(err)
		}
		rs.SetMaxLength(math.MaxInt)
		if p.TokenValidity.IsSet() {
			t := p.TokenValidity.Get()
			// Add one to the validity to ensure we don't have a session with indefinite length
			rs.SetMaxAge(int(*t) + 1)
		} else {
			rs.SetMaxAge(0)
		}
		rs.Options.Domain = *p.CookieDomain
		a.log.Trace("using redis session backend")
		store = rs
	} else {
		dir := os.TempDir()
		cs := sessions.NewFilesystemStore(dir, []byte(*p.CookieSecret))
		// https://github.com/markbates/goth/commit/7276be0fdf719ddff753f3574ef0f967e4a5a5f7
		// set the maxLength of the cookies stored on the disk to a larger number to prevent issues with:
		// securecookie: the value is too long
		// when using OpenID Connect , since this can contain a large amount of extra information in the id_token

		// Note, when using the FilesystemStore only the session.ID is written to a browser cookie, so this is explicit for the storage on disk
		cs.MaxLength(math.MaxInt)
		if p.TokenValidity.IsSet() {
			t := p.TokenValidity.Get()
			// Add one to the validity to ensure we don't have a session with indefinite length
			cs.MaxAge(int(*t) + 1)
		} else {
			cs.MaxAge(0)
		}
		cs.Options.Domain = *p.CookieDomain
		a.log.WithField("dir", dir).Trace("using filesystem session backend")
		store = cs
	}
	return store
}
