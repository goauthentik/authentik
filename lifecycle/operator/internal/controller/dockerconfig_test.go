package controller

import (
	"encoding/base64"
	"testing"

	corev1 "k8s.io/api/core/v1"
)

const (
	testUser  = "bot"
	testToken = "token"
)

func dockerSecret(key, payload string) *corev1.Secret {
	return &corev1.Secret{Data: map[string][]byte{key: []byte(payload)}}
}

func TestCredentialFromDockerConfigExplicitFields(t *testing.T) {
	secret := dockerSecret(corev1.DockerConfigJsonKey,
		`{"auths":{"ghcr.io":{"username":"bot","password":"token"}}}`)

	credential, err := credentialFromDockerConfig(secret, "ghcr.io")
	if err != nil {
		t.Fatalf("credentialFromDockerConfig: %v", err)
	}
	if credential.Username != testUser || credential.Password != testToken {
		t.Errorf("credential = %+v, want bot/token", credential)
	}
}

func TestCredentialFromDockerConfigBase64Auth(t *testing.T) {
	// `docker login` writes only the base64 auth field, not the split ones, so
	// this is the common case in practice.
	auth := base64.StdEncoding.EncodeToString([]byte("bot:token"))
	secret := dockerSecret(corev1.DockerConfigJsonKey,
		`{"auths":{"ghcr.io":{"auth":"`+auth+`"}}}`)

	credential, err := credentialFromDockerConfig(secret, "ghcr.io")
	if err != nil {
		t.Fatalf("credentialFromDockerConfig: %v", err)
	}
	if credential.Username != testUser || credential.Password != testToken {
		t.Errorf("credential = %+v, want bot/token", credential)
	}
}

func TestCredentialFromDockerConfigPasswordContainingColons(t *testing.T) {
	// Only the first colon separates the username, so a token with colons in it
	// has to survive intact.
	auth := base64.StdEncoding.EncodeToString([]byte("bot:tok:en:with:colons"))
	secret := dockerSecret(corev1.DockerConfigJsonKey,
		`{"auths":{"ghcr.io":{"auth":"`+auth+`"}}}`)

	credential, err := credentialFromDockerConfig(secret, "ghcr.io")
	if err != nil {
		t.Fatalf("credentialFromDockerConfig: %v", err)
	}
	if credential.Password != "tok:en:with:colons" {
		t.Errorf("password = %q, want it kept whole", credential.Password)
	}
}

func TestCredentialFromDockerConfigMatchesRegistryKeyShapes(t *testing.T) {
	// Docker config keys turn up with a scheme, with a trailing path, or bare.
	for _, key := range []string{
		"ghcr.io",
		"https://ghcr.io",
		"http://ghcr.io",
		"https://ghcr.io/v2/",
		"ghcr.io/goauthentik",
	} {
		secret := dockerSecret(corev1.DockerConfigJsonKey,
			`{"auths":{"`+key+`":{"username":"bot","password":"token"}}}`)

		credential, err := credentialFromDockerConfig(secret, "ghcr.io")
		if err != nil {
			t.Errorf("key %q: %v", key, err)
			continue
		}
		if credential.Username != testUser {
			t.Errorf("key %q: credential = %+v", key, credential)
		}
	}
}

func TestCredentialFromDockerConfigLegacyDockercfg(t *testing.T) {
	// The legacy .dockercfg format is the auths map without the wrapper.
	secret := dockerSecret(corev1.DockerConfigKey,
		`{"ghcr.io":{"username":"bot","password":"token"}}`)

	credential, err := credentialFromDockerConfig(secret, "ghcr.io")
	if err != nil {
		t.Fatalf("credentialFromDockerConfig: %v", err)
	}
	if credential.Username != testUser {
		t.Errorf("credential = %+v", credential)
	}
}

func TestCredentialFromDockerConfigErrors(t *testing.T) {
	cases := map[string]*corev1.Secret{
		"no credential key":  {Data: map[string][]byte{"other": []byte("{}")}},
		"malformed json":     dockerSecret(corev1.DockerConfigJsonKey, `{"auths":`),
		"registry not found": dockerSecret(corev1.DockerConfigJsonKey, `{"auths":{"docker.io":{"auth":"x"}}}`),
		"entry with no credentials": dockerSecret(corev1.DockerConfigJsonKey,
			`{"auths":{"ghcr.io":{}}}`),
		"auth is not base64": dockerSecret(corev1.DockerConfigJsonKey,
			`{"auths":{"ghcr.io":{"auth":"!!!not base64!!!"}}}`),
		"auth has no colon": dockerSecret(corev1.DockerConfigJsonKey,
			`{"auths":{"ghcr.io":{"auth":"`+base64.StdEncoding.EncodeToString([]byte("nocolon"))+`"}}}`),
	}

	for name, secret := range cases {
		t.Run(name, func(t *testing.T) {
			if _, err := credentialFromDockerConfig(secret, "ghcr.io"); err == nil {
				t.Error("expected an error")
			}
		})
	}
}
