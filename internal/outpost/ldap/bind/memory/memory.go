package memory

import (
	"context"
	"sync"
	"time"

	ttlcache "github.com/jellydator/ttlcache/v3"
	"github.com/nmcclain/ldap"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/flow"
	"goauthentik.io/internal/outpost/ldap/bind"
	"goauthentik.io/internal/outpost/ldap/bind/direct"
	"goauthentik.io/internal/outpost/ldap/server"
)

type Credentials struct {
	DN       string
	Password string
}

type LoginResult struct {
	ldap.LDAPResultCode
	Username   string
	ValidUntil time.Time
}

type SessionBinder struct {
	direct.DirectBinder
	si        server.LDAPServerInstance
	log       *log.Entry
	sessions  *ttlcache.Cache[Credentials, LoginResult]
	bindMutex map[string]*sync.Mutex
}

var defaultTTL = time.Hour * time.Duration(24)

func NewSessionBinder(si server.LDAPServerInstance, oldBinder bind.Binder) *SessionBinder {
	sb := &SessionBinder{
		si:        si,
		log:       log.WithField("logger", "authentik.outpost.ldap.binder.session"),
		bindMutex: map[string]*sync.Mutex{},
	}
	if oldSb, ok := oldBinder.(*SessionBinder); ok {
		sb.DirectBinder = oldSb.DirectBinder
		sb.sessions = oldSb.sessions
		sb.bindMutex = oldSb.bindMutex
		sb.log.Info("re-initialised session binder")
	} else {
		sb.sessions = ttlcache.New(
			ttlcache.WithTTL[Credentials, LoginResult](defaultTTL),
			ttlcache.WithDisableTouchOnHit[Credentials, LoginResult](),
		)
		sb.sessions.OnEviction(func(_ context.Context, reason ttlcache.EvictionReason, item *ttlcache.Item[Credentials, LoginResult]) {
			//check if there is something to evict
			dn := item.Key().DN
			username := item.Value().Username
			f := sb.si.GetFlags(dn)
			if f == nil {
				return
			}
			cookie := f.Session
			//get mutex
			sb.lockUser(username, "evict")
			flow.Logout(cookie, sb.si.GetAPIClient().GetConfig())
			//remove flags
			sb.si.DeleteFlags(dn)
			sb.unlockUser(username, "evict")
			sb.log.WithField("username", username).Info("Session closed")
		})
		sb.DirectBinder = *direct.NewDirectBinder(si)
		go sb.sessions.Start()
		sb.log.Info("initialised session binder")
	}
	return sb
}

func (sb *SessionBinder) lockUser(username, id string) {
	if sb.bindMutex[username] == nil {
		sb.bindMutex[username] = new(sync.Mutex)
	}
	sb.bindMutex[username].Lock()
	sb.log.WithField("lock", sb.bindMutex[username]).WithField("username", username).WithField("requestId", id).Debug("Aquired lock!")
}

func (sb *SessionBinder) unlockUser(username, id string) {
	if sb.bindMutex[username] == nil {
		sb.log.WithField("username", username).WithField("requestId", id).Warn("No lock existent to unlock!")
		return
	}
	sb.bindMutex[username].Unlock()
	sb.log.WithField("username", username).WithField("requestId", id).Debug("Released lock!")
}

func (sb *SessionBinder) Bind(username string, req *bind.Request) (ldap.LDAPResultCode, error) {
	//avoid eviction of current session, if
	sb.lockUser(username, req.ID())
	defer func() {
		sb.unlockUser(username, req.ID())
	}()
	creds := Credentials{
		DN:       req.BindDN,
		Password: req.BindPW,
	}
	logger := sb.log.WithFields(log.Fields{
		"username":  username,
		"bindDN":    req.BindDN,
		"requestId": req.ID(),
	})
	item := sb.sessions.Get(creds)
	if item != nil {
		//if Now() < ValidUntil -> still valid
		stillValid := time.Now().Before(item.Value().ValidUntil)
		logger.WithFields(log.Fields{
			"valid": stillValid,
			"now":   time.Now(),
			"until": item.Value().ValidUntil,
		}).Info("authenticated from session")
		if stillValid {
			//we have a hit -> increase ttl
			sb.sessions.Touch(creds)
			return item.Value().LDAPResultCode, nil
		}
		logger.Info("Re-log in user to extend session")
		//The token has expired, but it is still here, because somebody was actively using it
		//so -> logout -> login -> reset!
		fl := sb.si.GetFlags(req.BindDN)
		logger.WithField("flags", fl).Debug("Aquired flags")
		//logout the user -> destroys the session on the server side
		if fl != nil && fl.Session != nil {
			flow.Logout(fl.Session, sb.si.GetAPIClient().GetConfig())
		}
		//always delete the flags, just to be sure here
		sb.si.DeleteFlags(req.BindDN)
		//now continue with normal login flow
		logger.Debug("Continue with login after session delete")
	}
	logger.Debug("No session found for user, executing flow")
	result, err, cookie := sb.DirectBinder.BindNoClean(username, req)
	// Only cache the result if there was no error and we succeeded
	if err == nil && result == ldap.LDAPResultSuccess {
		if cookie == nil {
			//login did succeed, but cookie died?!
			logger.Error("user session not set after bind")
			return result, err
		}
		creds := Credentials{
			DN:       req.BindDN,
			Password: req.BindPW,
		}
		ttl := time.Until(cookie.Expires)
		//check if the cookie actually expires
		if cookie.MaxAge == 0 {
			ttl = defaultTTL
		}
		sb.sessions.Set(creds, LoginResult{result, username, time.Now().Add(ttl)}, ttl)
		logger.WithField("ttl", ttl).Info("Stored in sessions for later use with timeout")
	}
	if err != nil && cookie != nil {
		//force logout
		flow.Logout(cookie, sb.si.GetAPIClient().GetConfig())
	}
	return result, err
}

func (sb *SessionBinder) Cleanup() {
	//terminate the session cleanup process
	sb.log.Info("Delete all sessions")
	sb.sessions.Stop()
	//evict all sessions
	for _, key := range sb.sessions.Keys() {
		fl := sb.si.GetFlags(key.DN)
		if fl == nil || fl.Session == nil {
			continue
		}
		flow.Logout(fl.Session, sb.si.GetAPIClient().GetConfig())
	}
	sb.log.Info("Deleted all sessions")
}
