package rac

import (
	"testing"

	"github.com/stretchr/testify/assert"
	"golang.org/x/crypto/ssh"
)

func TestSSHCertificateNoToken(t *testing.T) {
	params := map[string]string{"username": "foo"}
	assert.NoError(t, sshCertificate(params))
	assert.Equal(t, map[string]string{"username": "foo"}, params)
}

func TestSSHCertificate(t *testing.T) {
	params := map[string]string{
		"username":      "foo",
		paramSSHToken:   "a-token",
		paramSSHHostKey: "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIB3sK7tW3qkaMCG1xVX0Nnu7qzK6wvI7zPLp7mDz0MRk",
	}
	hostKey := params[paramSSHHostKey]
	assert.NoError(t, sshCertificate(params))

	// The token must not reach guacd
	assert.NotContains(t, params, paramSSHToken)
	assert.NotContains(t, params, paramSSHHostKey)

	key, _, _, _, err := ssh.ParseAuthorizedKey([]byte(params["public-key"]))
	assert.NoError(t, err)
	cert, ok := key.(*ssh.Certificate)
	assert.True(t, ok)
	assert.Equal(t, ssh.UserCert, int(cert.CertType))
	assert.Equal(t, []string{"foo"}, cert.ValidPrincipals)
	assert.Contains(t, cert.Extensions, "permit-pty")
	assert.Equal(t, "a-token", cert.Extensions[extSSHToken])
	assert.Equal(t, hostKey, cert.Extensions[extSSHHostKey])

	// The certificate is signed by the key guacd authenticates with
	signer, err := ssh.ParsePrivateKey([]byte(params["private-key"]))
	assert.NoError(t, err)
	assert.Equal(t, signer.PublicKey().Marshal(), cert.SignatureKey.Marshal())
	assert.NoError(t, (&ssh.CertChecker{
		IsUserAuthority: func(auth ssh.PublicKey) bool {
			return string(auth.Marshal()) == string(cert.SignatureKey.Marshal())
		},
	}).CheckCert("foo", cert))
}
