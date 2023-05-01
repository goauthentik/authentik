// SPDX-FileCopyrightText: 2020 BoxGo
// SPDX-License-Identifier: MIT

package redisstore

import (
	"context"
	"encoding/base32"
	"errors"
	"fmt"
	"net/http"
	"strings"
	"time"

	"github.com/gorilla/securecookie"
	"github.com/gorilla/sessions"
	"github.com/redis/go-redis/v9"
	"goauthentik.io/internal/outpost/proxyv2/redisstore/serializer"
)

type (
	RedisStore struct {
		client     redis.UniversalClient
		codecs     []securecookie.Codec
		options    *sessions.Options
		maxLength  int
		keyPrefix  string
		keyGenFunc KeyGenFunc
		serializer serializer.SessionSerializer
	}

	Options struct {
		Codecs     []securecookie.Codec
		Options    *sessions.Options
		MaxLength  int
		KeyPrefix  string
		KeyGenFunc KeyGenFunc
		Serializer serializer.SessionSerializer
	}

	Option func(ops *Options)

	KeyGenFunc func(*http.Request) (string, error)
)

const (
	defaultMaxLen    = 4096
	defaultKeyPrefix = "session_"
	defaultMaxAge    = 864000 * 30
	defaultPath      = "/"
)

func NewStoreWithUniversalClient(client redis.UniversalClient, optFns ...Option) (*RedisStore, error) {
	newOpts := &Options{}
	for _, optFn := range optFns {
		optFn(newOpts)
	}

	if newOpts.Options == nil {
		newOpts.Options = &sessions.Options{
			Path:   defaultPath,
			MaxAge: defaultMaxAge,
		}
	}
	if newOpts.MaxLength == 0 {
		newOpts.MaxLength = defaultMaxLen
	}
	if newOpts.KeyPrefix == "" {
		newOpts.KeyPrefix = defaultKeyPrefix
	}
	if newOpts.Serializer == nil {
		newOpts.Serializer = &serializer.GobSerializer{}
	}
	if newOpts.KeyGenFunc == nil {
		newOpts.KeyGenFunc = GenerateRandomKey
	}

	return &RedisStore{
		client:     client,
		codecs:     newOpts.Codecs,
		options:    newOpts.Options,
		maxLength:  newOpts.MaxLength,
		keyPrefix:  newOpts.KeyPrefix,
		keyGenFunc: newOpts.KeyGenFunc,
		serializer: newOpts.Serializer,
	}, nil
}

// Get should return a cached session.
func (st *RedisStore) Get(r *http.Request, name string) (*sessions.Session, error) {
	return sessions.GetRegistry(r).Get(st, name)
}

// New should create and return a new session.
//
// Note that New should never return a nil session, even in the case of
// an error if using the Registry infrastructure to cache the session.
func (st *RedisStore) New(r *http.Request, name string) (*sessions.Session, error) {
	var (
		err error
		ok  bool
	)
	session := sessions.NewSession(st, name)

	// make a copy
	options := *st.options
	session.Options = &options
	session.IsNew = true

	if c, errCookie := r.Cookie(name); errCookie == nil {
		err = securecookie.DecodeMulti(name, c.Value, &session.ID, st.codecs...)
		if err == nil {
			ok, err = st.load(session)
			session.IsNew = !(err == nil && ok) // not new if no error and data available
		}
	}
	return session, err
}

// Save should persist session to the underlying store implementation.
func (st *RedisStore) Save(r *http.Request, w http.ResponseWriter, session *sessions.Session) error {
	// Marked for deletion.
	if session.Options.MaxAge <= 0 {
		if err := st.delete(session); err != nil {
			return err
		}

		http.SetCookie(w, sessions.NewCookie(session.Name(), "", session.Options))
	} else {
		// Build an alphanumeric key for the redis store.
		if session.ID == "" {
			keyGenFunc := st.keyGenFunc
			if keyGenFunc == nil {
				keyGenFunc = GenerateRandomKey
			}

			id, err := keyGenFunc(r)
			if err != nil {
				return errors.New("redistore: failed to generate session id")
			}

			session.ID = id
		}

		if err := st.save(session); err != nil {
			return err
		}

		encoded, err := securecookie.EncodeMulti(session.Name(), session.ID, st.codecs...)
		if err != nil {
			return err
		}

		http.SetCookie(w, sessions.NewCookie(session.Name(), encoded, session.Options))
	}
	return nil
}

func (st *RedisStore) Delete(r *http.Request, w http.ResponseWriter, session *sessions.Session) error {
	if err := st.client.Del(context.Background(), st.keyPrefix+session.ID).Err(); err != nil {
		return err
	}
	// Set cookie to expire.
	options := *session.Options
	options.MaxAge = -1
	http.SetCookie(w, sessions.NewCookie(session.Name(), "", &options))
	return nil
}

func (st *RedisStore) Keys() ([]string, error) {
	cmd := st.client.Do(context.Background(), "keys", fmt.Sprintf("%s*", st.keyPrefix))
	keys, err := cmd.StringSlice()
	return keys, err
}

func (st *RedisStore) GetBytesByKey(key string) ([]byte, error) {
	cmd := st.client.Get(context.Background(), key)
	return cmd.Bytes()
}

func (st *RedisStore) Serialize(session *sessions.Session) ([]byte, error) {
	return st.serializer.Serialize(session)
}

func (st *RedisStore) Deserialize(data []byte, session *sessions.Session) error {
	return st.serializer.Deserialize(data, session)
}

func (st *RedisStore) DeleteByKey(key string) error {
	err := st.client.Del(context.Background(), key).Err()
	return err
}

// Ping tests if the cache is alive.
func (st *RedisStore) Ping() error {
	return st.client.Ping(context.Background()).Err()
}

func (st *RedisStore) SetOptions(opts *sessions.Options) {
	st.options = opts
}

func (st *RedisStore) save(session *sessions.Session) error {
	b, err := st.Serialize(session)
	if err != nil {
		return err
	}

	if st.maxLength != 0 && len(b) > st.maxLength {
		return errors.New("SessionStore: the value to store is too big")
	}

	return st.client.Set(context.Background(), st.key(session), b, time.Duration(session.Options.MaxAge)*time.Second).Err()
}

func (st *RedisStore) load(session *sessions.Session) (bool, error) {
	b, err := st.client.Get(context.Background(), st.key(session)).Bytes()
	if err != nil {
		return false, err
	}

	return true, st.Deserialize(b, session)
}

func (st *RedisStore) delete(session *sessions.Session) error {
	return st.client.Del(context.Background(), st.key(session)).Err()
}

func (st *RedisStore) key(session *sessions.Session) string {
	return st.keyPrefix + session.ID
}

func GenerateRandomKey(r *http.Request) (string, error) {
	return strings.TrimRight(base32.StdEncoding.EncodeToString(securecookie.GenerateRandomKey(32)), "="), nil
}
