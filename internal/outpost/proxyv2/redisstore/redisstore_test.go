// SPDX-FileCopyrightText: 2020 BoxGo
// SPDX-License-Identifier: MIT

package redisstore

import (
	"errors"
	"fmt"
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

	store, err := NewStore(db,
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

	store, err := NewStore(db,
		WithKeyPairs([]byte("test")),
	)
	if err != nil {
		t.Fatal("failed to create redis store", err)
	}

	store.keyGen = nil

	req, err := http.NewRequest("GET", "http://www.example.com", nil)
	if err != nil {
		t.Fatal("failed to create request", err)
	}
	w := httptest.NewRecorder()

	session, err := store.New(req, "hello")
	if err != nil {
		t.Fatal("failed to create session", err)
	}

	mock.Regexp().ExpectSet(`session_[A-Z0-9]{52}`, `\[[0-9 ]+\]`, time.Duration(session.Options.MaxAge)*time.Second).SetVal("OK")

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

	store, err := NewStore(db,
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

	mock.Regexp().ExpectSet(`session_[A-Z0-9]{52}`, `\[[0-9 ]+\]`, time.Duration(session.Options.MaxAge)*time.Second).SetVal("OK")

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

	store, err := NewStore(db,
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

	mock.Regexp().ExpectSet(`session_[A-Z0-9]{52}`, `\[[0-9 ]+\]`, time.Duration(session.Options.MaxAge)*time.Second).SetVal("OK")

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

	store, err := NewStore(db,
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

func TestKeys(t *testing.T) {
	db, mock := redismock.NewClientMock()

	store, err := NewStore(db, WithKeyPairs([]byte("test")))
	if err != nil {
		t.Fatal("failed to create redis store", err)
	}

	// Mock the KEYS command
	mock.ExpectDo("keys", "session_*").SetVal([]string{"session_123", "session_456"})

	keys, err := store.Keys()
	if err != nil {
		t.Fatal("failed to get keys", err)
	}

	if len(keys) != 2 || keys[0] != "session_123" || keys[1] != "session_456" {
		t.Fatalf("wrong keys returned: %v", keys)
	}

	if err := mock.ExpectationsWereMet(); err != nil {
		t.Error(err)
	}
}

func TestGetBytesByKey(t *testing.T) {
	db, mock := redismock.NewClientMock()

	store, err := NewStore(db, WithKeyPairs([]byte("test")))
	if err != nil {
		t.Fatal("failed to create redis store", err)
	}

	testKey := "session_test123"
	testData := []byte("serialized session data")

	mock.ExpectGet(testKey).SetVal(string(testData))

	data, err := store.GetBytesByKey(testKey)
	if err != nil {
		t.Fatal("failed to get bytes by key", err)
	}

	if !reflect.DeepEqual(data, testData) {
		t.Fatal("retrieved data doesn't match expected data")
	}

	if err := mock.ExpectationsWereMet(); err != nil {
		t.Error(err)
	}
}

func TestPingAndClose(t *testing.T) {
	db, mock := redismock.NewClientMock()

	store, err := NewStore(db, WithKeyPairs([]byte("test")))
	if err != nil {
		t.Fatal("failed to create redis store", err)
	}

	// Test Ping
	mock.ExpectPing().SetVal("PONG")

	err = store.Ping()
	if err != nil {
		t.Fatal("ping failed", err)
	}

	// Test Close
	mock.ExpectQuit().SetVal("OK")

	err = store.Close()
	if err != nil {
		t.Fatal("close failed", err)
	}

	if err := mock.ExpectationsWereMet(); err != nil {
		t.Error(err)
	}
}

func TestCustomKeyGen(t *testing.T) {
	db, mock := redismock.NewClientMock()

	customKeyGen := func(r *http.Request) (string, error) {
		return "custom-key", nil
	}

	store, err := NewStore(db,
		WithKeyPairs([]byte("test")),
		WithKeyGenFunc(customKeyGen),
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

	// Should use our custom key
	mock.ExpectSet("session_custom-key", `\[[0-9 ]+\]`, time.Duration(session.Options.MaxAge)*time.Second).SetVal("OK")

	session.Values["key"] = "value"
	err = session.Save(req, w)
	if err != nil {
		t.Fatal("failed to save session", err)
	}

	if session.ID != "custom-key" {
		t.Fatalf("expected session ID to be 'custom-key', got '%s'", session.ID)
	}

	if err := mock.ExpectationsWereMet(); err != nil {
		t.Error(err)
	}
}

func TestMaxLengthExceeded(t *testing.T) {
	db, _ := redismock.NewClientMock()

	store, err := NewStore(db,
		WithKeyPairs([]byte("test")),
		WithMaxLength(10), // Very small max length to force error
	)
	if err != nil {
		t.Fatal("failed to create redis store", err)
	}

	session := sessions.NewSession(store, "test")
	session.ID = "test-id"
	session.Values["key"] = "value with more than 10 bytes"

	err = store.save(session)
	if err == nil {
		t.Fatal("expected error for max length exceeded, but got nil")
	}

	if err.Error() != "SessionStore: the value to store is too big, length: 28" {
		t.Fatalf("unexpected error: %v", err)
	}
}

func TestLoadError(t *testing.T) {
	db, mock := redismock.NewClientMock()

	store, err := NewStore(db, WithKeyPairs([]byte("test")))
	if err != nil {
		t.Fatal("failed to create redis store", err)
	}
	session := sessions.NewSession(store, "test")
	session.ID = "test-id"
	mock.ExpectGet(store.keyPrefix + session.ID).SetErr(errors.New("connection error"))

	_, err = store.load(session)
	if err == nil {
		t.Fatal("expected error from load, but got nil")
	}
}

// Broken serializer for testing error paths
type brokenTestSerializer struct{}

func (s *brokenTestSerializer) Serialize(session *sessions.Session) ([]byte, error) {
	return nil, fmt.Errorf("serialize error")
}

func (s *brokenTestSerializer) Deserialize(data []byte, session *sessions.Session) error {
	return fmt.Errorf("deserialize error")
}

func TestSerializeDeserializeError(t *testing.T) {
	db, _ := redismock.NewClientMock()

	// Create a broken serializer for testing errors
	brokenSerializer := &brokenTestSerializer{}

	store, err := NewStore(db,
		WithKeyPairs([]byte("test")),
		WithSerializer(brokenSerializer),
	)
	if err != nil {
		t.Fatal("failed to create redis store", err)
	}

	session := sessions.NewSession(store, "test")

	// Test serialization error
	_, err = store.Serialize(session)
	if err == nil || err.Error() != "serialize error" {
		t.Fatalf("expected 'serialize error', got: %v", err)
	}

	// Test deserialization error
	err = store.Deserialize([]byte("test"), session)
	if err == nil || err.Error() != "deserialize error" {
		t.Fatalf("expected 'deserialize error', got: %v", err)
	}
}
