package memory

import (
	"time"

	"beryju.io/ldap"
	ttlcache "github.com/jellydator/ttlcache/v3"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/ldap/bind"
	"goauthentik.io/internal/outpost/ldap/bind/direct"
	"goauthentik.io/internal/outpost/ldap/server"
)

type Credentials struct {
	DN       string
	Password string
}

type SessionBinder struct {
	direct.DirectBinder
	si       server.LDAPServerInstance
	log      *log.Entry
	sessions *ttlcache.Cache[Credentials, ldap.LDAPResultCode]
}

func NewSessionBinder(si server.LDAPServerInstance, oldBinder bind.Binder) *SessionBinder {
	sb := &SessionBinder{
		si:  si,
		log: log.WithField("logger", "authentik.outpost.ldap.binder.session"),
	}
	if oldSb, ok := oldBinder.(*SessionBinder); ok {
		sb.DirectBinder = oldSb.DirectBinder
		sb.sessions = oldSb.sessions
		sb.log.Debug("re-initialised session binder")
	} else {
		sb.sessions = ttlcache.New(ttlcache.WithDisableTouchOnHit[Credentials, ldap.LDAPResultCode]())
		sb.DirectBinder = *direct.NewDirectBinder(si)
		go sb.sessions.Start()
		sb.log.Debug("initialised session binder")
	}
	return sb
}

func (sb *SessionBinder) Bind(username string, req *bind.Request) (ldap.LDAPResultCode, error) {
	item := sb.sessions.Get(Credentials{
		DN:       req.BindDN,
		Password: req.BindPW,
	})
	if item != nil {
		sb.log.WithField("bindDN", req.BindDN).Info("authenticated from session")
		return item.Value(), nil
	}
	sb.log.Debug("No session found for user, executing flow")
	result, err := sb.DirectBinder.Bind(username, req)
	// Only cache the result if there's been an error
	if err == nil {
		flags := sb.si.GetFlags(req.BindDN)
		if flags == nil {
			sb.log.Error("user flags not set after bind")
			return result, err
		}
		sb.sessions.Set(Credentials{
			DN:       req.BindDN,
			Password: req.BindPW,
		}, result, time.Until(flags.Session.Expires))
	}
	return result, err
}
