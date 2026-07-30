package config

import (
	"fmt"
	"log"
	"os"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestConfigEnv(t *testing.T) {
	assert.NoError(t, os.Setenv("AUTHENTIK_SECRET_KEY", "bar"))
	cfg = nil
	if err := Get().fromEnv(); err != nil {
		panic(err)
	}
	assert.Equal(t, "bar", Get().SecretKey)
}

func TestConfigEnv_Scheme(t *testing.T) {
	assert.NoError(t, os.Setenv("foo", "bar"))
	assert.NoError(t, os.Setenv("AUTHENTIK_SECRET_KEY", "env://foo"))
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
	defer func() {
		assert.NoError(t, os.Remove(file.Name()))
	}()
	_, err = file.Write([]byte("bar"))
	if err != nil {
		panic(err)
	}

	assert.NoError(t, os.Setenv("AUTHENTIK_SECRET_KEY", fmt.Sprintf("file://%s", file.Name())))
	cfg = nil
	if err := Get().fromEnv(); err != nil {
		panic(err)
	}
	assert.Equal(t, "bar", Get().SecretKey)
}
