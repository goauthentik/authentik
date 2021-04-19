package ldap

import (
	log "github.com/sirupsen/logrus"
)

func (ls *LDAPServer) Refresh() error {
	return nil
}

func (ls *LDAPServer) Start() error {
	listen := "0.0.0.0:3389"
	log.Debugf("Listening on %s", listen)
	err := ls.s.ListenAndServe(listen)
	if err != nil {
		ls.log.Errorf("LDAP Server Failed: %s", err.Error())
		return err
	}
	return nil
}
