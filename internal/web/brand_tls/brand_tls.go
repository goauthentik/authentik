package brand_tls

import (
	"context"
	"crypto/tls"
	"crypto/x509"
	"strings"
	"time"

	log "github.com/sirupsen/logrus"

	"goauthentik.io/api/v3"
	"goauthentik.io/internal/crypto"
	"goauthentik.io/internal/outpost/ak"
)

type Watcher struct {
	client   *api.APIClient
	log      *log.Entry
	cs       *ak.CryptoStore
	fallback *tls.Certificate
	brands   []api.Brand
}

func NewWatcher(client *api.APIClient) *Watcher {
	cs := ak.NewCryptoStore(client.CryptoApi)
	l := log.WithField("logger", "authentik.router.brand_tls")
	cert, err := crypto.GenerateSelfSignedCert()
	if err != nil {
		l.WithError(err).Error("failed to generate default cert")
	}

	return &Watcher{
		client:   client,
		log:      l,
		cs:       cs,
		fallback: &cert,
	}
}

func (w *Watcher) Start() {
	ticker := time.NewTicker(time.Minute * 3)
	w.log.Info("Starting Brand TLS Checker")
	for ; true; <-ticker.C {
		w.Check()
	}
}

func (w *Watcher) Check() {
	w.log.Info("updating brand certificates")
	brands, err := ak.Paginator(w.client.CoreApi.CoreBrandsList(context.Background()), ak.PaginatorOptions{
		PageSize: 100,
		Logger:   w.log,
	})
	if err != nil {
		w.log.WithError(err).Warning("failed to get brands")
		return
	}
	for _, b := range brands {
		kp := b.GetWebCertificate()
		if kp != "" {
			err := w.cs.AddKeypair(kp)
			if err != nil {
				w.log.WithError(err).WithField("kp", kp).Warning("failed to add web certificate")
			}
		}
		for _, crt := range b.GetClientCertificates() {
			if crt != "" {
				err := w.cs.AddKeypair(crt)
				if err != nil {
					w.log.WithError(err).WithField("kp", kp).Warning("failed to add client certificate")
				}
			}
		}
	}
	w.brands = brands
}

type CertificateConfig struct {
	Web    *tls.Certificate
	Client *x509.CertPool
}

func (w *Watcher) GetCertificate(ch *tls.ClientHelloInfo) *CertificateConfig {
	var bestSelection *api.Brand
	config := CertificateConfig{
		Web: w.fallback,
	}
	for _, t := range w.brands {
		if !t.WebCertificate.IsSet() && len(t.GetClientCertificates()) < 1 {
			continue
		}
		if *t.Default {
			bestSelection = &t
		}
		if strings.HasSuffix(ch.ServerName, t.Domain) {
			bestSelection = &t
		}
	}
	if bestSelection == nil {
		return &config
	}
	if bestSelection.GetWebCertificate() != "" {
		if cert := w.cs.Get(bestSelection.GetWebCertificate()); cert != nil {
			config.Web = cert
		}
	}
	if len(bestSelection.GetClientCertificates()) > 0 {
		config.Client = x509.NewCertPool()
		for _, kp := range bestSelection.GetClientCertificates() {
			if cert := w.cs.Get(kp); cert != nil {
				config.Client.AddCert(cert.Leaf)
			}
		}
	}
	return &config
}
