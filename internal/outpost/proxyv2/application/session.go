package application

import (
	"fmt"
	"math"
	"net/url"
	"os"
	"path"
	"strconv"
	"strings"

	"github.com/garyburd/redigo/redis"
	"github.com/gorilla/securecookie"
	"github.com/gorilla/sessions"
	"goauthentik.io/api/v3"
	"goauthentik.io/internal/config"
	"goauthentik.io/internal/outpost/proxyv2/constants"
	"gopkg.in/boj/redistore.v1"
)

const RedisKeyPrefix = "authentik_proxy_session_"

func (a *Application) getStore(p api.ProxyOutpostConfig, externalHost *url.URL) sessions.Store {
	var store sessions.Store
	if config.Get().Redis.Host != "" {
		rs, err := redistore.NewRediStoreWithDB(10, "tcp", fmt.Sprintf("%s:%d", config.Get().Redis.Host, config.Get().Redis.Port), config.Get().Redis.Password, strconv.Itoa(config.Get().Redis.DB), []byte(*p.CookieSecret))
		if err != nil {
			panic(err)
		}
		rs.SetMaxLength(math.MaxInt)
		rs.SetKeyPrefix(RedisKeyPrefix)
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

func (a *Application) Logout(sub string) error {
	if fs, ok := a.sessions.(*sessions.FilesystemStore); ok {
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
				constants.SessionName, string(data),
				&s.Values, fs.Codecs...,
			)
			if err != nil {
				a.log.WithError(err).Trace("failed to decode session")
				continue
			}
			claims := s.Values[constants.SessionClaims].(Claims)
			if claims.Sub == sub {
				a.log.WithField("path", fullPath).Trace("deleting session")
				err := os.Remove(fullPath)
				if err != nil {
					a.log.WithError(err).Warning("failed to delete session")
					continue
				}
			}
		}
	}
	if rs, ok := a.sessions.(*redistore.RediStore); ok {
		pool := rs.Pool.Get()
		defer pool.Close()
		rep, err := pool.Do("KEYS", fmt.Sprintf("%s*", RedisKeyPrefix))
		if err != nil {
			return err
		}
		keys, err := redis.Strings(rep, err)
		if err != nil {
			return err
		}
		ser := redistore.GobSerializer{}
		for _, key := range keys {
			v, err := pool.Do("GET", key)
			if err != nil {
				a.log.WithError(err).Warning("failed to get value")
				continue
			}
			b, err := redis.Bytes(v, err)
			if err != nil {
				a.log.WithError(err).Warning("failed to load value")
				continue
			}
			s := sessions.Session{}
			err = ser.Deserialize(b, &s)
			if err != nil {
				a.log.WithError(err).Warning("failed to deserialize")
				continue
			}
			c := s.Values[constants.SessionClaims]
			if c == nil {
				continue
			}
			claims := c.(Claims)
			if claims.Sub == sub {
				a.log.WithField("key", key).Trace("deleting session")
				_, err := pool.Do("DEL", key)
				if err != nil {
					a.log.WithError(err).Warning("failed to delete key")
					continue
				}
			}
		}
	}
	return nil
}
