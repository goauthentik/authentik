// SPDX-FileCopyrightText: 2020 BoxGo
// SPDX-License-Identifier: MIT

package redisstore

import (
	"net/http"
	"net/http/httptest"
	"reflect"
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

func TestSaveAndGet(t *testing.T) {
	db, mock := redismock.NewClientMock()

	store, err := NewStoreWithUniversalClient(db,
		WithKeyPairs([]byte("test")),
	)
	if err != nil {
		t.Fatal("failed to create redis store", err)
	}

	store.keyGenFunc = nil

	req, err := http.NewRequest("GET", "http://www.example.com", nil)
	if err != nil {
		t.Fatal("failed to create request", err)
	}
	w := httptest.NewRecorder()

	session, err := store.New(req, "hello")
	if err != nil {
		t.Fatal("failed to create session", err)
	}

	mock.Regexp().ExpectSet(`session_[A-Z0-9]{52}`, `\[[0-9 ]+\]`, time.Duration(session.Options.MaxAge) * time.Second).SetVal("OK")

	session.Values["key"] = "value"
	err = session.Save(req, w)
	if err != nil {
		t.Fatal("failed to save: ", err)
	}

	value, err := store.Serialize(session)
	if err != nil {
		t.Fatal("failed to serialize session: ", err)
	}

	mock.ExpectGet(store.keyPrefix + session.ID).SetVal(string(value))

	req.AddCookie(w.Result().Cookies()[0])
	duplicateSession, err := store.New(req, "hello")
	if err != nil {
		t.Fatal("failed to re-create existing session", err)
	} else if !reflect.DeepEqual(duplicateSession.Values, session.Values) {
		t.Fatal("wrong values in re-created session")
	}

	mock.ExpectGet(store.keyPrefix + session.ID).SetVal(string(value))

	duplicateSession, err = store.Get(req, "hello")
	if err != nil {
		t.Fatal("failed to get existing session", err)
	} else if !reflect.DeepEqual(duplicateSession.Values, session.Values) {
		t.Fatal("wrong values in returned session")
	}

	if err := mock.ExpectationsWereMet(); err != nil {
		t.Error(err)
	}
}

func TestDeleteByKey(t *testing.T) {
	db, mock := redismock.NewClientMock()

	store, err := NewStoreWithUniversalClient(db,
		WithKeyPairs([]byte("test")),
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

	mock.Regexp().ExpectSet(`session_[A-Z0-9]{52}`, `\[[0-9 ]+\]`, time.Duration(session.Options.MaxAge) * time.Second).SetVal("OK")

	session.Values["key"] = "value"
	err = session.Save(req, w)
	if err != nil {
		t.Fatal("failed to save session: ", err)
	}

	mock.ExpectDel(store.keyPrefix + session.ID).SetVal(1)

	err = store.DeleteByKey(store.keyPrefix + session.ID)
	if err != nil {
		t.Fatal("failed to delete session: ", err)
	}

	mock.ExpectDel(store.keyPrefix + session.ID).SetVal(1)

	err = store.Delete(req, w, session)
	if err != nil {
		t.Fatal("failed to delete store: ", err)
	}

	if err := mock.ExpectationsWereMet(); err != nil {
		t.Error(err)
	}
}

func TestDeleteByMaxAge(t *testing.T) {
	db, mock := redismock.NewClientMock()

	store, err := NewStoreWithUniversalClient(db,
		WithKeyPairs([]byte("test")),
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

	mock.Regexp().ExpectSet(`session_[A-Z0-9]{52}`, `\[[0-9 ]+\]`, time.Duration(session.Options.MaxAge) * time.Second).SetVal("OK")

	session.Values["key"] = "value"
	err = session.Save(req, w)
	if err != nil {
		t.Fatal("failed to save session: ", err)
	}

	mock.ExpectDel(store.keyPrefix + session.ID).SetVal(1)

	session.Options.MaxAge = -1
	err = session.Save(req, w)
	if err != nil {
		t.Fatal("failed to delete session: ", err)
	}

	mock.ExpectDel(store.keyPrefix + session.ID).SetVal(1)

	err = store.Delete(req, w, session)
	if err != nil {
		t.Fatal("failed to delete store: ", err)
	}

	if err := mock.ExpectationsWereMet(); err != nil {
		t.Error(err)
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
