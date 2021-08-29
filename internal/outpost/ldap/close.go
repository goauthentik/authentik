package ldap

import (
	"net"
	"time"
)

func (ls *LDAPServer) Close(boundDN string, conn net.Conn) error {
	for _, p := range ls.providers {
		p.delayDeleteUserInfo(boundDN)
	}
	return nil
}

func (pi *ProviderInstance) delayDeleteUserInfo(dn string) {
	ticker := time.NewTicker(30 * time.Second)
	quit := make(chan struct{})
	go func() {
		for {
			select {
			case <-ticker.C:
				pi.boundUsersMutex.Lock()
				delete(pi.boundUsers, dn)
				pi.boundUsersMutex.Unlock()
				close(quit)
			case <-quit:
				ticker.Stop()
				return
			}
		}
	}()
}
