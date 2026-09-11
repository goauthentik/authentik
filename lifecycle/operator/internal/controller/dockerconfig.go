package controller

import (
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"strings"

	corev1 "k8s.io/api/core/v1"

	"goauthentik.io/lifecycle/operator/internal/version"
)

// dockerConfig is the part of a dockerconfigjson Secret the operator reads.
type dockerConfig struct {
	Auths map[string]dockerAuth `json:"auths"`
}

type dockerAuth struct {
	Username string `json:"username"`
	Password string `json:"password"`
	// Auth is base64("username:password"), which is what `docker login`
	// actually writes; the split fields are often absent.
	Auth string `json:"auth"`
}

// credentialFromDockerConfig pulls the credentials for one registry out of a
// dockerconfigjson or dockercfg Secret.
func credentialFromDockerConfig(secret *corev1.Secret, registry string) (version.Credential, error) {
	raw, key := dockerConfigData(secret)
	if raw == nil {
		return version.Credential{}, fmt.Errorf("the Secret has neither a %s nor a %s key",
			corev1.DockerConfigJsonKey, corev1.DockerConfigKey)
	}

	auths := map[string]dockerAuth{}
	if key == corev1.DockerConfigJsonKey {
		config := dockerConfig{}
		if err := json.Unmarshal(raw, &config); err != nil {
			return version.Credential{}, fmt.Errorf("failed to parse %s: %w", key, err)
		}
		auths = config.Auths
	} else {
		// The legacy .dockercfg format is the auths map without the wrapper.
		if err := json.Unmarshal(raw, &auths); err != nil {
			return version.Credential{}, fmt.Errorf("failed to parse %s: %w", key, err)
		}
	}

	auth, ok := matchRegistry(auths, registry)
	if !ok {
		return version.Credential{}, fmt.Errorf("no entry for registry %q", registry)
	}

	return decodeAuth(auth)
}

func dockerConfigData(secret *corev1.Secret) ([]byte, string) {
	if raw, ok := secret.Data[corev1.DockerConfigJsonKey]; ok {
		return raw, corev1.DockerConfigJsonKey
	}
	if raw, ok := secret.Data[corev1.DockerConfigKey]; ok {
		return raw, corev1.DockerConfigKey
	}
	return nil, ""
}

// matchRegistry finds the auth entry for a registry. Docker config keys are
// written in a handful of shapes -- bare hosts, hosts with a scheme, hosts with
// a path -- so an exact lookup is not enough.
func matchRegistry(auths map[string]dockerAuth, registry string) (dockerAuth, bool) {
	if auth, ok := auths[registry]; ok {
		return auth, true
	}

	for host, auth := range auths {
		if normalizeRegistryHost(host) == registry {
			return auth, true
		}
	}

	return dockerAuth{}, false
}

// normalizeRegistryHost strips the scheme and any trailing path from a docker
// config key, leaving the host.
func normalizeRegistryHost(host string) string {
	host = strings.TrimPrefix(host, "https://")
	host = strings.TrimPrefix(host, "http://")
	if index := strings.Index(host, "/"); index >= 0 {
		host = host[:index]
	}
	return host
}

func decodeAuth(auth dockerAuth) (version.Credential, error) {
	if auth.Username != "" || auth.Password != "" {
		return version.Credential{Username: auth.Username, Password: auth.Password}, nil
	}

	if auth.Auth == "" {
		return version.Credential{}, errors.New("the entry has no credentials")
	}

	decoded, err := base64.StdEncoding.DecodeString(auth.Auth)
	if err != nil {
		return version.Credential{}, fmt.Errorf("failed to decode the auth field: %w", err)
	}

	username, password, found := strings.Cut(string(decoded), ":")
	if !found {
		return version.Credential{}, errors.New("the auth field is not in username:password form")
	}

	return version.Credential{Username: username, Password: password}, nil
}
