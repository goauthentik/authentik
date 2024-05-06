package hs256

import (
	"context"
	"encoding/base64"
	"fmt"
	"strings"

	"github.com/golang-jwt/jwt/v5"
)

type KeySet struct {
	m      jwt.SigningMethod
	secret string
}

func NewKeySet(secret string) *KeySet {
	return &KeySet{
		m:      jwt.SigningMethodHS256,
		secret: secret,
	}
}

func (ks *KeySet) VerifySignature(ctx context.Context, rawJWT string) ([]byte, error) {
	_, err := jwt.Parse(rawJWT, func(token *jwt.Token) (interface{}, error) {
		// Don't forget to validate the alg is what you expect:
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
		}
		return []byte(ks.secret), nil
	})
	if err != nil {
		return nil, err
	}
	parts := strings.Split(rawJWT, ".")
	payload, err := base64.RawURLEncoding.DecodeString(parts[1])
	return payload, err
}
