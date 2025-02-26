package config

import (
	"fmt"
	"log"
	"os"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestConfigEnv(t *testing.T) {
	cfg = nil
	os.Setenv("AUTHENTIK_SECRET_KEY", "bar")
	assert.Equal(t, "bar", Get().SecretKey)
}

func TestConfigEnv_Scheme(t *testing.T) {
	cfg = nil
	os.Setenv("foo", "bar")
	os.Setenv("AUTHENTIK_SECRET_KEY", "env://foo")
	assert.Equal(t, "bar", Get().SecretKey)
}

func TestConfigEnv_File(t *testing.T) {
	cfg = nil
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
	assert.Equal(t, "bar", Get().SecretKey)
}

func TestConfigEnv_InvalidPath(t *testing.T) {
	cfg = &Config{}
	err := cfg.LoadConfigFromFile("")
	assert.Nil(t, err)
}

func TestConfigEnv_InvalidConfig(t *testing.T) {
	cfg = &Config{}
	file, err := os.CreateTemp("", "")
	if err != nil {
		log.Fatal(err)
	}
	defer os.Remove(file.Name())
	_, err = file.Write([]byte("bar"))
	if err != nil {
		panic(err)
	}
	err = cfg.LoadConfigFromFile(file.Name())
	assert.Error(t, err)
}

func TestConfig_UpdateRedisURL_SetDefault(t *testing.T) {
	cfg = nil
	os.Setenv("AUTHENTIK_REDIS__HOST", "myredis")
	os.Setenv("AUTHENTIK_REDIS__PORT", "9637")
	os.Setenv("AUTHENTIK_REDIS__DB", "56")
	os.Setenv("AUTHENTIK_REDIS__USERNAME", "default")
	os.Setenv("AUTHENTIK_REDIS__PASSWORD", "\"'% !.;.°")
	os.Setenv("AUTHENTIK_REDIS__TLS", "true")
	os.Setenv("AUTHENTIK_REDIS__TLS_REQS", "none")
	assert.Equal(
		t,
		"rediss://myredis:9637/56?insecureskipverify=true&password=%22%27%25+%21.%3B.%C2%B0&username=default",
		Get().Redis.URL,
	)
}

func TestConfig_UpdateRedisURL_Placeholders(t *testing.T) {
	cfg = nil
	os.Setenv("AUTHENTIK_REDIS__URL", "redis://${AUTHENTIK_REDIS__USERNAME}:${AUTHENTIK_REDIS__PASSWORD}@myredis:2493/2?idletimeout=20s&skipverify=true")
	os.Setenv("AUTHENTIK_REDIS__USERNAME", "default")
	os.Setenv("AUTHENTIK_REDIS__PASSWORD", "\"'% !.;.°")
	assert.Equal(
		t,
		"redis://default:%22%27%25+%21.%3B.%C2%B0@myredis:2493/2?idletimeout=20s&skipverify=true",
		Get().Redis.URL,
	)
}
