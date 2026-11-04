package memory

import (
	"strings"
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
	// The direct binder reads the bind flow, the unbind flow, MFA support
	// and the base DN from the instance it was built with, so it is always
	// rebuilt from the new instance. Carrying the old binder over kept the
	// previous provider settings in use until the outpost was restarted.
	sb.DirectBinder = *direct.NewDirectBinder(si)
	if oldBinder != nil {
		if oldSb, ok := oldBinder.(*SessionBinder); ok {
			if oldSb.bindSettingsMatch(si) {
				sb.sessions = oldSb.sessions
				sb.log.Debug("re-initialized session binder")
				return sb
			}
			// Every cached result, refusals included, was produced by the
			// old settings; a changed bind flow has to see each bind again.
			oldSb.sessions.Stop()
			sb.log.Info("bind settings changed, discarding cached sessions")
		}
	}
	sb.sessions = ttlcache.New(ttlcache.WithDisableTouchOnHit[Credentials, ldap.LDAPResultCode]())
	go sb.sessions.Start()
	sb.log.Debug("initialized session binder")
	return sb
}

// bindSettingsMatch reports whether the provider settings that decide the
// outcome of a bind are the same on this binder's instance and on si.
func (sb *SessionBinder) bindSettingsMatch(si server.LDAPServerInstance) bool {
	if sb.si.GetAuthenticationFlowSlug() != si.GetAuthenticationFlowSlug() {
		return false
	}
	if sb.si.GetMFASupport() != si.GetMFASupport() {
		return false
	}
	if !strings.EqualFold(sb.si.GetBaseDN(), si.GetBaseDN()) {
		return false
	}
	oldUnbind, newUnbind := sb.si.GetInvalidationFlowSlug(), si.GetInvalidationFlowSlug()
	if oldUnbind == nil || newUnbind == nil {
		return oldUnbind == newUnbind
	}
	return *oldUnbind == *newUnbind
}

func (sb *SessionBinder) Bind(username string, req *bind.Request) (ldap.LDAPResultCode, error) {
	item := sb.sessions.Get(Credentials{
		DN:       req.BindDN,
		Password: req.Password,
	})
	if item != nil {
		sb.log.WithField("bindDN", req.BindDN).Info("authenticated from session")
		return item.Value(), nil
	}
	sb.log.Debug("No session found for user, executing flow")
	result, err := sb.DirectBinder.Bind(username, req)
	// Cache the result, refusals included, whenever the bind itself went
	// through; a transport error is not an outcome and is never cached.
	if err == nil {
		flags := sb.si.GetFlags(req.BindDN)
		if flags == nil {
			sb.log.Error("user flags not set after bind")
			return result, err
		}
		sb.sessions.Set(Credentials{
			DN:       req.BindDN,
			Password: req.Password,
		}, result, time.Until(flags.Session.Expires))
	}
	return result, err
}
