// SPDX-FileCopyrightText: 2020 BoxGo
// SPDX-License-Identifier: MIT

package redisstore

import (
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/go-redis/redismock/v9"
	"github.com/gorilla/sessions"
	"goauthentik.io/internal/outpost/proxyv2/redisstore/serializer"
)

func TestNew(t *testing.T) {
	db, _ := redismock.NewClientMock()

	store, err := NewStoreWithUniversalClient(db,
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
	db, mock := redismock.NewClientMock()

	store, err := NewStoreWithUniversalClient(db,
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

	mock.Regexp().ExpectSet(`amazing\.gao_[A-Z0-9]{52}`, `\[[0-9 ]+\]`, time.Duration(session.Options.MaxAge) * time.Second).SetVal("OK")

	session.Values["key"] = "value"
	err = session.Save(req, w)
	if err != nil {
		t.Fatal("failed to save: ", err)
	}

	if err := mock.ExpectationsWereMet(); err != nil {
		t.Error(err)
	}
}

func TestDelete(t *testing.T) {
	db, mock := redismock.NewClientMock()

	store, err := NewStoreWithUniversalClient(db,
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

	mock.Regexp().ExpectSet(`amazing\.gao_[A-Z0-9]{52}`, `\[[0-9 ]+\]`, time.Duration(session.Options.MaxAge) * time.Second).SetVal("OK")

	session.Values["key"] = "value"
	err = session.Save(req, w)
	if err != nil {
		t.Fatal("failed to save session: ", err)
	}

	mock.Regexp().ExpectDel(session.ID).SetVal(1)

	session.Options.MaxAge = -1
	err = session.Save(req, w)
	if err != nil {
		t.Fatal("failed to delete session: ", err)
	}
}

func TestOptions(t *testing.T) {
	db, _ := redismock.NewClientMock()

	opts := sessions.Options{
		Path:   "/path",
		MaxAge: 99999,
	}

	store, err := NewStoreWithUniversalClient(db,
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
