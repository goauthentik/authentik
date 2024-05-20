package redisstore

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gorilla/sessions"
	"github.com/redis/go-redis/v9"
)

const (
	redisAddr = "localhost:6379"
)

func TestNew(t *testing.T) {
	client := redis.NewClient(&redis.Options{
		Addr: redisAddr,
	})

	store, err := NewRedisStore(context.Background(), client)
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

func TestOptions(t *testing.T) {
	client := redis.NewClient(&redis.Options{
		Addr: redisAddr,
	})

	store, err := NewRedisStore(context.Background(), client)
	if err != nil {
		t.Fatal("failed to create redis store", err)
	}

	opts := sessions.Options{
		Path:   "/path",
		MaxAge: 99999,
	}
	store.Options(opts)

	req, err := http.NewRequest("GET", "http://www.example.com", nil)
	if err != nil {
		t.Fatal("failed to create request", err)
	}

	session, err := store.New(req, "hello")
	if err != nil {
		t.Fatal("failed to create store", err)
	}
	if session.Options.Path != opts.Path || session.Options.MaxAge != opts.MaxAge {
		t.Fatal("failed to set options")
	}
}

func TestSave(t *testing.T) {
	client := redis.NewClient(&redis.Options{
		Addr: redisAddr,
	})

	store, err := NewRedisStore(context.Background(), client)
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
	client := redis.NewClient(&redis.Options{
		Addr: redisAddr,
	})

	store, err := NewRedisStore(context.Background(), client)
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

	session.Options.MaxAge = -1
	err = session.Save(req, w)
	if err != nil {
		t.Fatal("failed to delete session: ", err)
	}
}

func TestClose(t *testing.T) {
	client := redis.NewClient(&redis.Options{
		Addr: redisAddr,
	})

	cmd := client.Ping(context.Background())
	err := cmd.Err()
	if err != nil {
		t.Fatal("connection is not opened")
	}

	store, err := NewRedisStore(context.Background(), client)
	if err != nil {
		t.Fatal("failed to create redis store", err)
	}

	err = store.Close()
	if err != nil {
		t.Fatal("failed to close")
	}

	cmd = client.Ping(context.Background())
	if cmd.Err() == nil {
		t.Fatal("connection is properly closed")
	}
}
