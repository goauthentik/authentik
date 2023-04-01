package redisstore

import (
	"github.com/gorilla/securecookie"
	"github.com/gorilla/sessions"
	"goauthentik.io/internal/outpost/proxyv2/redisstore/serializer"
)

func WithKeyPairs(keyPairs ...[]byte) Option {
	return func(op *Options) {
		op.Codecs = securecookie.CodecsFromPairs(keyPairs...)
	}
}

func WithOptions(opts *sessions.Options) Option {
	return func(op *Options) {
		op.Options = opts
	}
}

func WithMaxLength(maxLen int) Option {
	return func(op *Options) {
		op.MaxLength = maxLen
	}
}

func WithKeyPrefix(keyPrefix string) Option {
	return func(op *Options) {
		op.KeyPrefix = keyPrefix
	}
}

func WithKeyGenFunc(fn KeyGenFunc) Option {
	return func(op *Options) {
		op.KeyGenFunc = fn
	}
}

func WithSerializer(serializer serializer.SessionSerializer) Option {
	return func(op *Options) {
		op.Serializer = serializer
	}
}

func WithCodecs(codecs []securecookie.Codec) Option {
	return func(op *Options) {
		op.Codecs = codecs
	}
}