package tenant_tls

import (
	"crypto/tls"
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
	tenants  []api.Tenant
}

func NewWatcher(client *api.APIClient) *Watcher {
	cs := ak.NewCryptoStore(client.CryptoApi)
	l := log.WithField("logger", "authentik.router.tenant_tls")
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
	w.log.Info("Starting Tenant TLS Checker")
	for ; true; <-ticker.C {
		w.Check()
	}
}

func (w *Watcher) Check() {
	w.log.Info("updating tenant certificates")
	tenants, _, err := w.client.CoreApi.CoreTenantsListExecute(api.ApiCoreTenantsListRequest{})
	if err != nil {
		w.log.WithError(err).Warning("failed to get tenants")
		return
	}
	for _, t := range tenants.Results {
		if kp := t.WebCertificate.Get(); kp != nil {
			err := w.cs.AddKeypair(*kp)
			if err != nil {
				w.log.WithError(err).Warning("failed to add certificate")
			}
		}
	}
	w.tenants = tenants.Results
}

func (w *Watcher) GetCertificate(ch *tls.ClientHelloInfo) (*tls.Certificate, error) {
	var bestSelection *api.Tenant
	for _, t := range w.tenants {
		if t.WebCertificate.Get() == nil {
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
		return w.fallback, nil
	}
	cert := w.cs.Get(*bestSelection.WebCertificate.Get())
	if cert == nil {
		return w.fallback, nil
	}
	return cert, nil
}
