/*
Copyright 2026.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

package resources

import (
	"encoding/json"
	"fmt"
	"maps"
	"slices"
	"strconv"
	"strings"

	corev1 "k8s.io/api/core/v1"
)

// ConfigSecret renders the Secret holding authentik's configuration.
//
// Returns nil when the configuration is disabled or read from a Secret the user
// manages, in which case there is nothing for the operator to create.
func (b *Builder) ConfigSecret() (*corev1.Secret, error) {
	config := b.Authentik.Spec.Authentik
	if config != nil {
		if config.Enabled != nil && !*config.Enabled {
			return nil, nil
		}
		if config.ExistingSecret != nil && config.ExistingSecret.SecretName != "" {
			return nil, nil
		}
	}

	data, err := b.configEnv()
	if err != nil {
		return nil, err
	}

	var annotations map[string]string
	if g := b.Authentik.Spec.Global; g != nil {
		annotations = g.SecretAnnotations
	}

	secret := &corev1.Secret{
		ObjectMeta: b.objectMeta(b.Authentik.ConfigSecretName(), "", nil, annotations),
		Type:       corev1.SecretTypeOpaque,
		Data:       map[string][]byte{},
	}
	for key, value := range data {
		secret.Data[key] = []byte(value)
	}

	if geoip := b.Authentik.Spec.GeoIP; geoip != nil && geoip.Enabled &&
		(geoip.ExistingSecret == nil || geoip.ExistingSecret.SecretName == "") {
		if geoip.AccountID == "" || geoip.LicenseKey == "" {
			return nil, fmt.Errorf("geoip.accountId and geoip.licenseKey are required when geoip is enabled without an existingSecret")
		}
		secret.Data["GEOIPUPDATE_ACCOUNT_ID"] = []byte(geoip.AccountID)
		secret.Data["GEOIPUPDATE_LICENSE_KEY"] = []byte(geoip.LicenseKey)
	}

	return secret, nil
}

// configEnv flattens the authentik configuration into the AUTHENTIK_-prefixed
// environment variables the containers read.
//
// This is a port of the chart's "authentik.env" helper: nested keys are joined
// with a double underscore and upper-cased, so {"email": {"host": "x"}} becomes
// AUTHENTIK_EMAIL__HOST. Empty values are dropped rather than set to the empty
// string, because authentik distinguishes unset from empty for several options.
func (b *Builder) configEnv() (map[string]string, error) {
	config := b.Authentik.Spec.Authentik
	if config == nil {
		return map[string]string{}, nil
	}

	// Going through JSON keeps this in step with the spec's own field tags,
	// which are the chart's values.yaml keys, rather than repeating them here.
	encoded, err := json.Marshal(config)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal the authentik configuration: %w", err)
	}

	var configured map[string]any
	if err := json.Unmarshal(encoded, &configured); err != nil {
		return nil, fmt.Errorf("failed to read back the authentik configuration: %w", err)
	}

	// None of these is an authentik option: extraConfig is the operator's
	// escape hatch, existingSecret selects a Secret rather than being part of
	// one, and enabled is a switch for whether to render at all.
	//
	// The chart leaks `enabled` into the Secret as AUTHENTIK_ENABLED, which
	// authentik does not recognize. That is deliberately not reproduced.
	extra, _ := configured["extraConfig"].(map[string]any)
	delete(configured, "extraConfig")
	delete(configured, "existingSecret")
	delete(configured, "enabled")

	// The chart supplies these through values.yaml, and several differ from
	// authentik's own built-in defaults -- error_reporting.environment is "k8s"
	// here but "customer" in authentik -- so they are reproduced rather than
	// left to the application.
	tree := b.configDefaults()
	mergeTree(tree, configured)
	if extra != nil {
		mergeTree(tree, extra)
	}

	env := map[string]string{}
	if err := flatten("", tree, env); err != nil {
		return nil, err
	}
	return env, nil
}

// configDefaults are the authentik options the chart's values.yaml sets.
func (b *Builder) configDefaults() map[string]any {
	return map[string]any{
		"log_level": "info",
		"events": map[string]any{
			"context_processors": map[string]any{
				// Where the GeoIP sidecar mounts its databases.
				"geoip": geoipMountPath + "/GeoLite2-City.mmdb",
				"asn":   geoipMountPath + "/GeoLite2-ASN.mmdb",
			},
		},
		"web": map[string]any{"path": defaultWebPath},
		"email": map[string]any{
			"port":    float64(587),
			"use_tls": false,
			"use_ssl": false,
			"timeout": float64(30),
		},
		"outposts": map[string]any{
			"container_image_base": "ghcr.io/goauthentik/%(type)s:%(version)s",
		},
		"error_reporting": map[string]any{
			"enabled":     false,
			"environment": "k8s",
			"send_pii":    false,
		},
		"postgresql": map[string]any{
			// The chart points authentik at the bundled database's name whether
			// or not it is enabled, so an external database is named explicitly
			// either way.
			"host": b.PostgreSQLServiceName(),
			"name": defaultPostgresDatabase,
			"user": defaultPostgresUser,
			"port": float64(defaultPostgresPort),
		},
	}
}

// flatten walks the configuration tree, writing AUTHENTIK_-prefixed keys.
func flatten(prefix string, tree map[string]any, out map[string]string) error {
	// Sorted for a stable result, so an unchanged config produces an unchanged
	// Secret and does not churn the pod template hash.
	for _, key := range slices.Sorted(maps.Keys(tree)) {
		name := strings.ToUpper(key)
		if prefix != "" {
			name = prefix + "__" + name
		}

		switch value := tree[key].(type) {
		case map[string]any:
			if err := flatten(name, value, out); err != nil {
				return err
			}
		case nil:
			// An explicit null means "not set", same as the chart skipping it.
		default:
			rendered, err := renderValue(value)
			if err != nil {
				return fmt.Errorf("failed to render %s: %w", name, err)
			}
			if rendered != "" {
				out["AUTHENTIK_"+name] = rendered
			}
		}
	}
	return nil
}

// renderValue stringifies a scalar the way the chart's toString would, and
// encodes anything structured as JSON, which is what authentik expects for
// list-valued options such as footer_links.
func renderValue(value any) (string, error) {
	switch typed := value.(type) {
	case string:
		return typed, nil
	case bool:
		return strconv.FormatBool(typed), nil
	case float64:
		// JSON numbers decode as float64; 'f' with precision -1 renders a whole
		// number without gaining a ".0".
		return strconv.FormatFloat(typed, 'f', -1, 64), nil
	default:
		encoded, err := json.Marshal(typed)
		if err != nil {
			return "", err
		}
		return string(encoded), nil
	}
}

// mergeTree deep-merges src over dst so a nested override keeps its siblings.
func mergeTree(dst, src map[string]any) {
	for key, value := range src {
		srcMap, srcIsMap := value.(map[string]any)
		dstMap, dstIsMap := dst[key].(map[string]any)
		if srcIsMap && dstIsMap {
			mergeTree(dstMap, srcMap)
			continue
		}
		dst[key] = value
	}
}
