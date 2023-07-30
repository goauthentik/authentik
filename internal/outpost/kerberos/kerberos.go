package kerberos

import (
	"context"
	"net"
	"sync"

	log "github.com/sirupsen/logrus"

	"goauthentik.io/internal/outpost/ak"
	"goauthentik.io/internal/outpost/kerberos/metrics"
)

type ProviderInstance struct {
	realmName   string
	urlKdcProxy string
	s           *KerberosServer
	log         *log.Entry
}

type KerberosServer struct {
	us  *net.UDPConn
	ts  *net.TCPListener
	log *log.Entry
	ac  *ak.APIController

	provider *ProviderInstance
}

func NewServer(ac *ak.APIController) *KerberosServer {
	ks := &KerberosServer{
		us:       nil,
		ts:       nil,
		log:      log.WithField("logger", "authentik.outpost.kerberos"),
		ac:       ac,
		provider: nil,
	}
	ks.Refresh() // Make sure we get a provider
	return ks
}

func (ks *KerberosServer) Start() error {
	wg := sync.WaitGroup{}
	wg.Add(3)
	go func() {
		defer wg.Done()
		metrics.RunServer()
	}()
	go func() {
		defer wg.Done()
		err := ks.StartUDPServer()
		if err != nil {
			panic(err)
		}
	}()
	go func() {
		defer wg.Done()
		err := ks.StartTCPServer()
		if err != nil {
			panic(err)
		}
	}()
	wg.Wait()
	return nil
}

func (ks *KerberosServer) Stop() error {
	_, cancel := context.WithCancel(context.Background())
	err1 := ks.us.Close()
	err2 := ks.ts.Close()
	cancel()
	if err1 != nil {
		return err1
	}
	return err2
}

func (ks *KerberosServer) TimerFlowCacheExpiry(context.Context) {}

func (ks *KerberosServer) Type() string {
	return "kerberos"
}
