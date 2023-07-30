package kerberos

import (
	"bytes"
	"context"
	"encoding/binary"
	"errors"
	"io"
	"net"
	"net/http"

	"github.com/jcmturner/gofork/encoding/asn1"
	log "github.com/sirupsen/logrus"

	"goauthentik.io/internal/config"
)

func (ks *KerberosServer) Refresh() error {
	outposts, _, err := ks.ac.Client.OutpostsApi.OutpostsKerberosList(context.Background()).Execute()
	if err != nil {
		return err
	}
	if len(outposts.Results) < 1 {
		return errors.New("no kerberos provider defined")
	}
	// The API garanties us we will only ever have one provider (or realm in this case) defined.
	provider := outposts.Results[0]
	logger := log.WithField("logger", "authentik.outpost.kerberos").WithField("provider", provider.Name)
	providerInstance := &ProviderInstance{
		realmName:   provider.RealmName,
		urlKdcProxy: provider.UrlKdcProxy,
		s:           ks,
		log:         logger,
	}
	ks.provider = providerInstance
	ks.log.Info("Update providers")
	return nil
}

const MaxReadBytes = 1024 * 1024

type KdcProxyMessage struct {
	Message       []byte `asn1:"explicit,tag:0"`
	Realm         string `asn1:"optional,generalstring,explicit,tag:1"`
	DcLocatorHint int    `asn1:"optional,explicit,tag:2"`
}

func (m *KdcProxyMessage) Unmarshal(b []byte) error {
	_, err := asn1.Unmarshal(b, m)
	return err
}

func (m *KdcProxyMessage) Marshal() ([]byte, error) {
	b, err := asn1.Marshal(*m)
	if err != nil {
		return nil, err
	}
	return b, err
}

func (ks *KerberosServer) handle(request []byte) ([]byte, error) {
	m := KdcProxyMessage{
		Message: request,
		Realm:   ks.provider.realmName,
	}
	body, err := m.Marshal()
	if err != nil {
		return nil, err
	}
	r := bytes.NewReader(body)
	resp, err := http.Post(ks.provider.urlKdcProxy, "application/kerberos", r)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		return nil, errors.New("Proxy request failed")
	}
	body, err = io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}
	m = KdcProxyMessage{}
	err = m.Unmarshal(body)
	if err != nil {
		return nil, err
	}
	return m.Message, nil
}

func (ks *KerberosServer) StartUDPServer() error {
	addr, err := net.ResolveUDPAddr("udp", config.Get().Listen.KerberosUDP)
	if err != nil {
		return err
	}
	us, err := net.ListenUDP("udp", addr)
	if err != nil {
		return err
	}
	ks.us = us
	ks.log.WithField("listen", ks.us.LocalAddr()).Info("Starting kerberos UDP server")

	for {
		buf := make([]byte, MaxReadBytes)
		n, remoteAddr, err := ks.us.ReadFromUDP(buf[:])
		if err != nil {
			ks.log.WithError(err).Debug("failed to read from UDP")
			continue
		}
		// We need to prepend the message length in UDP
		byteLength := make([]byte, 4)
		binary.BigEndian.PutUint32(byteLength, uint32(n))
		go func(buf []byte, remoteAddr *net.UDPAddr) {
			response, err := ks.handle(buf)
			if err != nil {
				ks.log.WithError(err).Debug("failed to handle request")
				return
			}
			// And remove the message length when responding
			_, err = ks.us.WriteToUDP(response[4:], remoteAddr)
			if err != nil {
				ks.log.WithError(err).Info("failed to write response")
				return
			}
		}(append(byteLength, buf[:n]...), remoteAddr)
	}
}

func (ks *KerberosServer) StartTCPServer() error {
	addr, err := net.ResolveTCPAddr("tcp", config.Get().Listen.KerberosTCP)
	if err != nil {
		return err
	}
	ts, err := net.ListenTCP("tcp", addr)
	if err != nil {
		return err
	}
	ks.ts = ts
	ks.log.WithField("listen", ks.ts.Addr()).Info("Starting kerberos TCP server")

	for {
		conn, err := ks.ts.Accept()
		if err != nil {
			ks.log.WithError(err).Warning("failed to accept TCP connection")
		}
		go func() {
			defer conn.Close()
			buf := make([]byte, MaxReadBytes)
			for {
				n, err := conn.Read(buf[:])
				if err != nil {
					ks.log.WithError(err).Info("failed to read from TCP")
					break
				}
				response, err := ks.handle(buf[:n])
				if err != nil {
					ks.log.WithError(err).Warning("failed to handle request")
					break
				}
				_, err = conn.Write(response)
				if err != nil {
					ks.log.WithError(err).Info("failed to write response")
					break
				}
			}
		}()
	}
}
