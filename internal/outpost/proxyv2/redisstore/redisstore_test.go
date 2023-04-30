// SPDX-FileCopyrightText: 2020 BoxGo
// SPDX-License-Identifier: MIT

package redisstore

import (
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/go-redis/redis/v9"
	"github.com/gorilla/sessions"
	"goauthentik.io/internal/outpost/proxyv2/redisstore/serializer"
)

func newClient() redis.UniversalClient {
	return redis.NewUniversalClient(&redis.UniversalOptions{
		Addrs: []string{"localhost:6379"},
		DB:    0,
	})
}

func TestNew(t *testing.T) {
	store, err := NewStoreWithUniversalClient(newClient(),
		WithKeyPairs([]byte("test")),
		WithKeyPrefix("amazing.gao_"),
		WithSerializer(&serializer.JSONSerializer{}),
	)
	if err != nil {
		t.Fatal("failed to create redis store", err)
	}

	req, err := http.NewRequest("GET", "http://www.example.com", nil)
	if err != nil {
		t.Fatal("failed to create request", err)
	}

	session, err := store.New(req, "hello")
	if err != nil {
		t.Fatal("failed to create session", err)
	}
	if session.IsNew == false {
		t.Fatal("session is not new")
	}
}

func TestSave(t *testing.T) {
	store, err := NewStoreWithUniversalClient(newClient(),
		WithKeyPairs([]byte("test")),
		WithKeyPrefix("amazing.gao_"),
		WithSerializer(&serializer.JSONSerializer{}),
	)
	if err != nil {
		t.Fatal("failed to create redis store", err)
	}

	req, err := http.NewRequest("GET", "http://www.example.com", nil)
	if err != nil {
		t.Fatal("failed to create request", err)
	}
	w := httptest.NewRecorder()

	session, err := store.New(req, "hello")
	if err != nil {
		t.Fatal("failed to create session", err)
	}

	session.Values["key"] = "value"
	err = session.Save(req, w)
	if err != nil {
		t.Fatal("failed to save: ", err)
	}
}

func TestDelete(t *testing.T) {
	store, err := NewStoreWithUniversalClient(newClient(),
		WithKeyPairs([]byte("test")),
		WithKeyPrefix("amazing.gao_"),
		WithSerializer(&serializer.JSONSerializer{}),
	)
	if err != nil {
		t.Fatal("failed to create redis store", err)
	}

	req, err := http.NewRequest("GET", "http://www.example.com", nil)
	if err != nil {
		t.Fatal("failed to create request", err)
	}
	w := httptest.NewRecorder()

	session, err := store.New(req, "hello")
	if err != nil {
		t.Fatal("failed to create session", err)
	}

	session.Values["key"] = "value"
	err = session.Save(req, w)
	if err != nil {
		t.Fatal("failed to save session: ", err)
	}

	// session.Options.MaxAge = -1
	err = session.Save(req, w)
	if err != nil {
		t.Fatal("failed to delete session: ", err)
	}
}

func TestOptions(t *testing.T) {
	opts := sessions.Options{
		Path:   "/path",
		MaxAge: 99999,
	}

	store, err := NewStoreWithUniversalClient(newClient(),
		WithKeyPairs([]byte("test")),
		WithKeyPrefix("amazing.gao_"),
		WithSerializer(&serializer.JSONSerializer{}),
		WithOptions(&opts),
	)
	if err != nil {
		t.Fatal("failed to create redis store", err)
	}

	req, err := http.NewRequest("GET", "http://www.example.com", nil)
	if err != nil {
		t.Fatal("failed to create request", err)
	}

	session, err := store.New(req, "hello")
	if err != nil {
		t.Fatal("failed to create redis session", err)
	}
	if session.Options.Path != opts.Path || session.Options.MaxAge != opts.MaxAge {
		t.Fatal("failed to set options")
	}
}
