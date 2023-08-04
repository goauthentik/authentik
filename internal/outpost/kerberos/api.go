package kerberos

import (
	"bytes"
	"context"
	"encoding/binary"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"syscall"
	"time"

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

type PrincipalName struct {
	NameType   int32    `asn1:"explicit,tag:0"`
	NameString []string `asn1:"generalstring,explicit,tag:1"`
}

func (m *PrincipalName) Unmarshal(b []byte) error {
	_, err := asn1.Unmarshal(b, m)
	return err
}

func (m *PrincipalName) Marshal() ([]byte, error) {
	b, err := asn1.Marshal(*m)
	if err != nil {
		return nil, err
	}
	return b, err
}

// Ignoring optional fields, we can't fill them anyway
type KrbError struct {
	Pvno      int           `asn1:"explicit,tag:0"`
	MsgType   int           `asn1:"explicit,tag:1"`
	Stime     time.Time     `asn1:"generalized,explicit,tag:4"`
	Susec     int           `asn1:"explicit,tag:5"`
	ErrorCode int32         `asn1:"explicit,tag:6"`
	Realm     string        `asn1:"explicit,generalstring,tag:9"`
	Sname     PrincipalName `asn1:"explicit,tag:10"`
}

func (m *KrbError) Unmarshal(b []byte) error {
	_, err := asn1.UnmarshalWithParams(b, m, fmt.Sprintf("application,explicit,tag:%v", 30)) // KRB_ERROR
	return err
}

func (m *KrbError) Marshal() ([]byte, error) {
	b, err := asn1.Marshal(*m)
	if err != nil {
		return nil, err
	}
	r := asn1.RawValue{
		Class:      asn1.ClassApplication,
		IsCompound: true,
		Tag:        30, // KRB_ERROR
		Bytes:      b,
	}
	return asn1.Marshal(r)
}

func (ks *KerberosServer) handle(request []byte, remoteAddr string) ([]byte, error) {
	m := KdcProxyMessage{
		Message: request,
		Realm:   ks.provider.realmName,
	}
	body, err := m.Marshal()
	if err != nil {
		return nil, err
	}
	r := bytes.NewReader(body)
	client := ks.ac.Client.GetConfig().HTTPClient
	req, err := http.NewRequest("POST", ks.provider.urlKdcProxy, r)
	if err != nil {
		return nil, err
	}
	for header, value := range ks.ac.Client.GetConfig().DefaultHeader {
		req.Header.Set(header, value)
	}
	req.Header.Set("Content-Type", "application/kerberos")
	req.Header.Set("X-Outpost-RemoteAddr", remoteAddr)
	resp, err := client.Do(req)
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
	addr, err := net.ResolveUDPAddr("udp", config.Get().Listen.Kerberos)
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
			response, err := ks.handle(buf, remoteAddr.IP.String())
			if err != nil {
				ks.log.WithError(err).Debug("failed to handle request")
				return
			}
			// And remove the message length when responding
			_, err = ks.us.WriteToUDP(response[4:], remoteAddr)
			if err != nil {
				if errors.Is(err, syscall.EMSGSIZE) {
					now := time.Now().UTC()
					krbError := KrbError{
						Pvno:      5,
						MsgType:   30, // KRB_ERROR
						Stime:     now,
						Susec:     now.Nanosecond() / 1000000, // Nano to miliseconds
						ErrorCode: 52,                         // KRB_ERR_RESPONSE_TOO_BIG, Response too big for UDP; retry with TCP
						Realm:     ks.provider.realmName,
						Sname: PrincipalName{
							NameType:   2, // NT_SRV_INST
							NameString: []string{"krbtgt", ks.provider.realmName},
						},
					}
					e, err := krbError.Marshal()
					if err != nil {
						ks.log.WithError(err).Debug("failed to create krberror response")
						return
					}
					_, err = ks.us.WriteToUDP(e, remoteAddr)
					if err != nil {
						ks.log.WithError(err).Info("failed to write response")
						return
					}
				}
				ks.log.WithError(err).Info("failed to write response")
				return
			}
		}(append(byteLength, buf[:n]...), remoteAddr)
	}
}

func (ks *KerberosServer) StartTCPServer() error {
	addr, err := net.ResolveTCPAddr("tcp", config.Get().Listen.Kerberos)
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
			remoteAddr, _, _ := net.SplitHostPort(conn.RemoteAddr().String())
			for {
				n, err := conn.Read(buf[:])
				if err != nil {
					ks.log.WithError(err).Info("failed to read from TCP")
					break
				}
				response, err := ks.handle(buf[:n], remoteAddr)
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
