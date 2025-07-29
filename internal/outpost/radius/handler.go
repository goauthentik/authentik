package radius

import (
	"bytes"
	"crypto/hmac"
	"crypto/md5"
	"crypto/sha512"
	"encoding/hex"
	"errors"
	"time"

	"github.com/getsentry/sentry-go"
	"github.com/google/uuid"
	"github.com/prometheus/client_golang/prometheus"
	log "github.com/sirupsen/logrus"

	"goauthentik.io/internal/outpost/radius/metrics"
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

func (rs *RadiusServer) ServeRADIUS(w radius.ResponseWriter, r *radius.Request) {
	span := sentry.StartSpan(r.Context(), "authentik.providers.radius.connect",
		sentry.WithTransactionName("authentik.providers.radius.connect"))
	rid := uuid.New().String()
	span.SetTag("request_uid", rid)
	rl := rs.log.WithField("code", r.Code.String()).WithField("request", rid)
	selectedApp := ""
	defer func() {
		span.Finish()
		metrics.Requests.With(prometheus.Labels{
			"outpost_name": rs.ac.Outpost.Name,
			"app":          selectedApp,
		}).Observe(float64(span.EndTime.Sub(span.StartTime)) / float64(time.Second))
	}()

	nr := &RadiusRequest{
		Request: r,
		log:     rl,
		id:      rid,
		span:    span,
	}

	rl.Info("Radius Request")

	if err := nr.validateMessageAuthenticator(); err != nil {
		rl.WithError(err).Warning("Invalid message authenticator")
		return
	}

	// Lookup provider by shared secret
	var pi *ProviderInstance
	for _, p := range rs.providers {
		if string(p.SharedSecret) == string(r.Secret) {
			pi = p
			selectedApp = pi.appSlug
			break
		}
	}
	if pi == nil {
		hs := sha512.Sum512([]byte(r.Secret))
		bs := hex.EncodeToString(hs[:])
		nr.Log().WithField("hashed_secret", bs).Warning("No provider found")
		_ = w.Write(nr.Reject())
		return
	}
	nr.pi = pi

	if nr.Code == radius.CodeAccessRequest {
		rs.Handle_AccessRequest(w, nr)
	}
}
