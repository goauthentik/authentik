package proxy

import (
	"encoding/base64"
	"encoding/json"
	"strings"
)

type Claims struct {
	Proxy struct {
		UserAttributes map[string]interface{} `json:"user_attributes"`
	} `json:"pb_proxy"`
}

func (c *Claims) FromIDToken(idToken string) error {
	// id_token is a base64 encode ID token payload
	// https://developers.google.com/accounts/docs/OAuth2Login#obtainuserinfo
	jwt := strings.Split(idToken, ".")
	jwtData := strings.TrimSuffix(jwt[1], "=")
	b, err := base64.RawURLEncoding.DecodeString(jwtData)
	if err != nil {
		return err
	}

	err = json.Unmarshal(b, c)
	if err != nil {
		return err
	}
	return nil
}
