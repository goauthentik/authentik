package hs256

import (
	"context"
	"encoding/base64"
	"strings"

	"github.com/golang-jwt/jwt"
)

type KeySet struct {
	m      jwt.SigningMethod
	secret string
}

func NewKeySet(secret string) *KeySet {
	return &KeySet{
		m:      jwt.GetSigningMethod("HS256"),
		secret: secret,
	}
}

func (ks *KeySet) VerifySignature(ctx context.Context, jwt string) ([]byte, error) {
	parts := strings.Split(jwt, ".")
	err := ks.m.Verify(strings.Join(parts[0:2], "."), parts[2], []byte(ks.secret))
	if err != nil {
		return nil, err
	}
	payload, err := base64.RawURLEncoding.DecodeString(parts[1])
	return payload, err
}
