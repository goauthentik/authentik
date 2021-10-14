package application

import (
	"fmt"
	"strconv"

	"github.com/gorilla/sessions"
	"goauthentik.io/api"
	"goauthentik.io/internal/config"
	"gopkg.in/boj/redistore.v1"
)

func (a *Application) getStore(p api.ProxyOutpostConfig) sessions.Store {
	var store sessions.Store
	if config.G.Redis.Host != "" {
		rs, err := redistore.NewRediStoreWithDB(10, "tcp", fmt.Sprintf("%s:%d", config.G.Redis.Host, config.G.Redis.Port), config.G.Redis.Password, strconv.Itoa(config.G.Redis.OutpostSessionDB), []byte(*p.CookieSecret))
		if err != nil {
			panic(err)
		}
		if p.TokenValidity.IsSet() {
			t := p.TokenValidity.Get()
			// Add one to the validity to ensure we don't have a session with indefinite length
			rs.Options.MaxAge = int(*t) + 1
		}
		rs.Options.Domain = *p.CookieDomain
		a.log.Info("using redis session backend")
		store = rs
	} else {
		cs := sessions.NewCookieStore([]byte(*p.CookieSecret))
		cs.Options.Domain = *p.CookieDomain
		if p.TokenValidity.IsSet() {
			t := p.TokenValidity.Get()
			// Add one to the validity to ensure we don't have a session with indefinite length
			cs.Options.MaxAge = int(*t) + 1
		}
		a.log.Info("using cookie session backend")
		store = cs
	}
	return store
}
