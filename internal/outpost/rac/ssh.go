package rac

import (
	"crypto/ed25519"
	"crypto/rand"
	"encoding/pem"
	"sync"
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

type sshKey struct {
	signer     ssh.Signer
	privateKey string
}

var outpostSSHKey = sync.OnceValues(newSSHKey)

func newSSHKey() (*sshKey, error) {
	_, private, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		return nil, err
	}
	signer, err := ssh.NewSignerFromKey(private)
	if err != nil {
		return nil, err
	}
	block, err := ssh.MarshalPrivateKey(private, "")
	if err != nil {
		return nil, err
	}
	return &sshKey{signer: signer, privateKey: string(pem.EncodeToMemory(block))}, nil
}

// sshCertificate replaces the token authentik sent with a certificate carrying it,
// which the device accepts once its agent validated the token with authentik.
func sshCertificate(params map[string]string) error {
	token, ok := params[paramSSHToken]
	if !ok {
		return nil
	}
	hostKey := params[paramSSHHostKey]
	delete(params, paramSSHToken)
	delete(params, paramSSHHostKey)

	key, err := outpostSSHKey()
	if err != nil {
		return err
	}
	username := params["username"]
	cert := &ssh.Certificate{
		Key:             key.signer.PublicKey(),
		CertType:        ssh.UserCert,
		KeyId:           username,
		ValidPrincipals: []string{username},
		ValidAfter:      uint64(time.Now().Add(-certValidity).Unix()),
		ValidBefore:     uint64(time.Now().Add(certValidity).Unix()),
		Permissions: ssh.Permissions{
			Extensions: map[string]string{
				"permit-pty":  "",
				extSSHToken:   token,
				extSSHHostKey: hostKey,
			},
		},
	}
	if err := cert.SignCert(rand.Reader, key.signer); err != nil {
		return err
	}
	params["private-key"] = key.privateKey
	params["public-key"] = string(ssh.MarshalAuthorizedKey(cert))
	return nil
}
