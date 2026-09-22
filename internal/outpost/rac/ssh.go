package rac

import (
	"crypto/ed25519"
	"crypto/rand"
	"encoding/pem"
	"time"

	"golang.org/x/crypto/ssh"
)

const (
	// Settings authentik sends instead of credentials, for devices managed by the
	// authentik agent. Keep in sync with `authentik/providers/rac/models.py`.
	paramSSHToken   = "goauthentik.io/rac/ssh-token"
	paramSSHHostKey = "goauthentik.io/rac/ssh-host-key"
	// Certificate extensions the agent reads the token and the device's host key
	// from. Keep in sync with `ak_platform::shared` in the authentik platform.
	extSSHToken   = "goauthentik.io/platform/ssh/ssh/token"
	extSSHHostKey = "goauthentik.io/platform/ssh/host-key"
	// The certificate is only used to log in, the session outlives it
	certValidity = 5 * time.Minute
)

// sshCertificate replaces the token authentik sent with an ephemeral key and a
// self-signed certificate carrying it. The device accepts the key which signed the
// certificate for this one login, once its agent validated the token with authentik.
func sshCertificate(params map[string]string) error {
	token, ok := params[paramSSHToken]
	if !ok {
		return nil
	}
	hostKey := params[paramSSHHostKey]
	delete(params, paramSSHToken)
	delete(params, paramSSHHostKey)

	public, private, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		return err
	}
	signer, err := ssh.NewSignerFromKey(private)
	if err != nil {
		return err
	}
	publicKey, err := ssh.NewPublicKey(public)
	if err != nil {
		return err
	}
	username := params["username"]
	cert := &ssh.Certificate{
		Key:             publicKey,
		CertType:        ssh.UserCert,
		KeyId:           username,
		ValidPrincipals: []string{username},
		ValidAfter:      uint64(time.Now().Add(-certValidity).Unix()),
		ValidBefore:     uint64(time.Now().Add(certValidity).Unix()),
		Permissions: ssh.Permissions{
			Extensions: map[string]string{
				"permit-pty":  "",
				extSSHToken:   sshExtensionValue(token),
				extSSHHostKey: sshExtensionValue(hostKey),
			},
		},
	}
	if err := cert.SignCert(rand.Reader, signer); err != nil {
		return err
	}
	block, err := ssh.MarshalPrivateKey(private, "")
	if err != nil {
		return err
	}
	params["private-key"] = string(pem.EncodeToMemory(block))
	params["public-key"] = string(ssh.MarshalAuthorizedKey(cert))
	return nil
}

// sshExtensionValue wraps a certificate extension value in an SSH string, which
// OpenSSH does for any extension that carries one but Go does not.
func sshExtensionValue(value string) string {
	return string(ssh.Marshal(struct{ Value string }{value}))
}
