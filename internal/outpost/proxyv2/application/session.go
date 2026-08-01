package application

import (
	"context"
	"math"
	"net/http"
	"net/url"
	"os"
	"path"
	"strings"

	"github.com/gorilla/securecookie"
	"github.com/gorilla/sessions"

	"goauthentik.io/internal/outpost/proxyv2/codecs"
	"goauthentik.io/internal/outpost/proxyv2/constants"
	"goauthentik.io/internal/outpost/proxyv2/filesystemstore"
	"goauthentik.io/internal/outpost/proxyv2/postgresstore"
	"goauthentik.io/internal/outpost/proxyv2/types"
	api "goauthentik.io/packages/client-go"
)

const PostgresKeyPrefix = "authentik_proxy_session_"

func (a *Application) getStore(p api.ProxyOutpostConfig, externalHost *url.URL) (sessions.Store, error) {
	maxAge := 0
	if p.AccessTokenValidity.IsSet() {
		t := p.AccessTokenValidity.Get()
		// Add one to the validity to ensure we don't have a session with indefinite length
		maxAge = int(*t) + 1
	}

	sessionBackend := a.srv.SessionBackend()
	switch sessionBackend {
	case "postgres":
		// New PostgreSQL store
		ps, err := postgresstore.NewPostgresStore(a.log)
		if err != nil {
			return nil, err
		}

		ps.KeyPrefix(PostgresKeyPrefix)
		ps.Options(sessions.Options{
			HttpOnly: true,
			Secure:   strings.ToLower(externalHost.Scheme) == "https",
			Domain:   *p.CookieDomain,
			SameSite: http.SameSiteLaxMode,
			MaxAge:   maxAge,
			Path:     "/",
		})

		return ps, nil
	case "filesystem":
		dir := os.TempDir()
		cs, err := filesystemstore.GetPersistentStore(dir)
		if err != nil {
			return nil, err
		}
		cs.Codecs = codecs.CodecsFromPairs(maxAge, []byte(*p.CookieSecret))
		// https://github.com/markbates/goth/commit/7276be0fdf719ddff753f3574ef0f967e4a5a5f7
		// set the maxLength of the cookies stored on the disk to a larger number to prevent issues with:
		// securecookie: the value is too long
		// when using OpenID Connect, since this can contain a large amount of extra information in the id_token

		// Note, when using the FilesystemStore only the session.ID is written to a browser cookie, so this is explicit for the storage on disk
		cs.MaxLength(math.MaxInt)
		cs.Options.HttpOnly = true
		cs.Options.Secure = strings.ToLower(externalHost.Scheme) == "https"
		cs.Options.Domain = *p.CookieDomain
		cs.Options.SameSite = http.SameSiteLaxMode
		cs.Options.MaxAge = maxAge
		cs.Options.Path = "/"
		return cs, nil
	default:
		a.log.WithField("backend", sessionBackend).Panic("unknown session backend type")
		return nil, nil
	}
}

func (a *Application) SessionName() string {
	return a.sessionName
}

// discardSession erases a session that could not be loaded from the store and
// tells the client to drop its session cookie.
//
// It deliberately works on a copy of the session. gorilla's registry memoises
// the *sessions.Session per request, so every a.sessions.Get() within a single
// request hands back the same object — Options included. Setting
// Options.MaxAge = -1 on the shared object makes every later Save() in that
// request take the store's "MaxAge <= 0" branch and erase the session instead
// of persisting it. That is how signing out and logging back in used to fail:
// checkAuth expired the cookie of the session that sign-out had already
// deleted, and createState then "saved" a new session that was never written,
// leaving the state JWT pointing at a session ID the callback could not find
// ("mismatched session ID ... should=").
func (a *Application) discardSession(rw http.ResponseWriter, r *http.Request, s *sessions.Session) {
	if rw == nil {
		return
	}
	expired := *s
	opts := *s.Options
	opts.MaxAge = -1
	expired.Options = &opts
	if err := a.sessions.Save(r, rw, &expired); err != nil {
		a.log.WithError(err).Warning("failed to delete stale session cookie")
	}
}

func (a *Application) getAllCodecs() []securecookie.Codec {
	apps := a.srv.Apps()
	cs := []securecookie.Codec{}
	for _, app := range apps {
		cs = append(cs, codecs.CodecsFromPairs(0, []byte(*app.proxyConfig.CookieSecret))...)
	}
	return cs
}

func (a *Application) Logout(ctx context.Context, filter func(c types.Claims) bool) error {
	if _, ok := a.sessions.(*filesystemstore.Store); ok {
		files, err := os.ReadDir(os.TempDir())
		if err != nil {
			return err
		}
		for _, file := range files {
			s := sessions.Session{}
			if !strings.HasPrefix(file.Name(), "session_") {
				continue
			}
			fullPath := path.Join(os.TempDir(), file.Name())
			data, err := os.ReadFile(fullPath)
			if err != nil {
				a.log.WithError(err).Warning("failed to read file")
				continue
			}
			err = securecookie.DecodeMulti(
				a.SessionName(), string(data),
				&s.Values, a.getAllCodecs()...,
			)
			if err != nil {
				a.log.WithError(err).Trace("failed to decode session")
				continue
			}
			rc, ok := s.Values[constants.SessionClaims]
			if !ok || rc == nil {
				continue
			}
			claims := s.Values[constants.SessionClaims].(types.Claims)
			if filter(claims) {
				a.log.WithField("path", fullPath).Trace("deleting session")
				err := os.Remove(fullPath)
				if err != nil {
					a.log.WithError(err).Warning("failed to delete session")
					continue
				}
			}
		}
	}
	if ps, ok := a.sessions.(*postgresstore.PostgresStore); ok {
		err := ps.LogoutSessions(ctx, func(c types.Claims) bool {
			return filter(types.Claims(c))
		})
		if err != nil {
			a.log.WithError(err).Warning("failed to logout sessions from PostgreSQL")
			return err
		}
	}
	return nil
}
