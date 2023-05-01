// SPDX-FileCopyrightText: 2020 BoxGo
// SPDX-License-Identifier: MIT

package serializer

import (
	"encoding/json"
	"fmt"

	"github.com/gorilla/sessions"
)

// JSONSerializer encode the session map to JSON.
type JSONSerializer struct{}

// Serialize to JSON. Will err if there are unmarshalable key values
func (s JSONSerializer) Serialize(sess *sessions.Session) ([]byte, error) {
	m := make(map[string]interface{}, len(sess.Values))
	for k, v := range sess.Values {
		ks, ok := k.(string)
		if !ok {
			err := fmt.Errorf("non-string key value, cannot serialize session to JSON: %v", k)
			return nil, err
		}
		m[ks] = v
	}
	return json.Marshal(m)
}

// Deserialize back to map[string]interface{}
func (s JSONSerializer) Deserialize(d []byte, sess *sessions.Session) error {
	m := make(map[string]interface{})
	err := json.Unmarshal(d, &m)
	if err != nil {
		return err
	}
	if sess.Values == nil {
		sess.Values = make(map[interface{}]interface{})
	}
	for k, v := range m {
		sess.Values[k] = v
	}
	return nil
}
