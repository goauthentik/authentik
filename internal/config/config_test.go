package config

import (
	"fmt"
	"log"
	"os"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestConfigEnv(t *testing.T) {
	os.Setenv("AUTHENTIK_SECRET_KEY", "bar")
	cfg = nil
	if err := Get().fromEnv(); err != nil {
		panic(err)
	}
	assert.Equal(t, "bar", Get().SecretKey)
}

func TestConfigEnv_Scheme(t *testing.T) {
	os.Setenv("foo", "bar")
	os.Setenv("AUTHENTIK_SECRET_KEY", "env://foo")
	cfg = nil
	if err := Get().fromEnv(); err != nil {
		panic(err)
	}
	assert.Equal(t, "bar", Get().SecretKey)
}

func TestConfigEnv_File(t *testing.T) {
	file, err := os.CreateTemp("", "")
	if err != nil {
		log.Fatal(err)
	}
	defer os.Remove(file.Name())
	_, err = file.Write([]byte("bar"))
	if err != nil {
		panic(err)
	}

	os.Setenv("AUTHENTIK_SECRET_KEY", fmt.Sprintf("file://%s", file.Name()))
	cfg = nil
	if err := Get().fromEnv(); err != nil {
		panic(err)
	}
	assert.Equal(t, "bar", Get().SecretKey)
}

func TestConfig_UpdateRedisURL(t *testing.T) {
	os.Setenv("AUTHENTIK_REDIS__HOST", "myredis")
	os.Setenv("AUTHENTIK_REDIS__PORT", "9637")
	os.Setenv("AUTHENTIK_REDIS__DB", "56")
	os.Setenv("AUTHENTIK_REDIS__USERNAME", "default")
	os.Setenv("AUTHENTIK_REDIS__PASSWORD", "\"'% !.;.°")
	os.Setenv("AUTHENTIK_REDIS__TLS", "true")
	os.Setenv("AUTHENTIK_REDIS__TLS_REQS", "none")
	cfg = nil
	if err := Get().fromEnv(); err != nil {
		panic(err)
	}
	fmt.Println(Get().Redis.URL)
	assert.Equal(t, "rediss://myredis:9637/56?insecureskipverify=true&password=%22%27%25+%21.%3B.%C2%B0&username=default", Get().Redis.URL)
}
