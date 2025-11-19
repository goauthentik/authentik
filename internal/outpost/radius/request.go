package radius

import (
	"bytes"
	"crypto/hmac"
	"crypto/md5"
	"errors"

	"github.com/getsentry/sentry-go"
	log "github.com/sirupsen/logrus"

	"goauthentik.io/internal/utils"
	"layeh.com/radius"
	"layeh.com/radius/rfc2869"
)

var (
	ErrInvalidMessageAuthenticator = errors.New("invalid message authenticator")
)

type RadiusRequest struct {
	*radius.Request
	log  *log.Entry
	id   string
	span *sentry.Span
	pi   *ProviderInstance
}

func (r *RadiusRequest) Log() *log.Entry {
	return r.log
}

func (r *RadiusRequest) RemoteAddr() string {
	return utils.GetIP(r.Request.RemoteAddr)
}

func (r *RadiusRequest) ID() string {
	return r.id
}

func (r *RadiusRequest) validateMessageAuthenticator() error {
	mauth := rfc2869.MessageAuthenticator_Get(r.Packet)
	hash := hmac.New(md5.New, r.Secret)
	encode, err := r.MarshalBinary()
	if err != nil {
		return err
	}
	hash.Write(encode)
	if bytes.Equal(mauth, hash.Sum(nil)) {
		return ErrInvalidMessageAuthenticator
	}
	return nil
}

func (r *RadiusRequest) setMessageAuthenticator(rp *radius.Packet) error {
	_ = rfc2869.MessageAuthenticator_Set(rp, make([]byte, 16))
	hash := hmac.New(md5.New, rp.Secret)
	encode, err := rp.MarshalBinary()
	if err != nil {
		return err
	}
	hash.Write(encode)
	_ = rfc2869.MessageAuthenticator_Set(rp, hash.Sum(nil))
	return nil
}

func (r *RadiusRequest) Reject() *radius.Packet {
	res := r.Response(radius.CodeAccessReject)
	err := r.setMessageAuthenticator(res)
	if err != nil {
		r.log.WithError(err).Warning("failed to set message authenticator")
	}
	return res
}
