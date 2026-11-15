package ldap

import (
	"crypto/tls"
	"testing"

	log "github.com/sirupsen/logrus"
	"github.com/stretchr/testify/assert"
)

func testServerWithCerts() (*LDAPServer, *tls.Certificate, *tls.Certificate, *tls.Certificate) {
	defaultCert := &tls.Certificate{}
	firstCert := &tls.Certificate{}
	secondCert := &tls.Certificate{}
	ls := &LDAPServer{
		log:         log.WithField("logger", "test"),
		defaultCert: defaultCert,
		providers: []*ProviderInstance{
			{tlsServerName: "first.example.com", cert: firstCert, certUUID: "first"},
			{tlsServerName: "second.example.com", cert: secondCert, certUUID: "second"},
		},
	}
	return ls, defaultCert, firstCert, secondCert
}

func TestGetCertificates_ServerName(t *testing.T) {
	ls, _, firstCert, secondCert := testServerWithCerts()

	cert, err := ls.getCertificates(&tls.ClientHelloInfo{ServerName: "first.example.com"})
	assert.NoError(t, err)
	assert.Same(t, firstCert, cert)

	cert, err = ls.getCertificates(&tls.ClientHelloInfo{ServerName: "second.example.com"})
	assert.NoError(t, err)
	assert.Same(t, secondCert, cert)
}

func TestGetCertificates_UnknownServerName(t *testing.T) {
	ls, defaultCert, _, _ := testServerWithCerts()

	cert, err := ls.getCertificates(&tls.ClientHelloInfo{ServerName: "other.example.com"})
	assert.NoError(t, err)
	assert.Same(t, defaultCert, cert)

	cert, err = ls.getCertificates(&tls.ClientHelloInfo{})
	assert.NoError(t, err)
	assert.Same(t, defaultCert, cert)
}

func TestGetCertificates_ServerNameWithoutCertificate(t *testing.T) {
	ls, defaultCert, _, _ := testServerWithCerts()
	ls.providers[1].cert = nil

	cert, err := ls.getCertificates(&tls.ClientHelloInfo{ServerName: "second.example.com"})
	assert.NoError(t, err)
	assert.Same(t, defaultCert, cert)
}
