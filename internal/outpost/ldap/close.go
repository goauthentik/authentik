package ldap

import "net"

func (ls *LDAPServer) Close(dn string, conn net.Conn) error {
	ls.connectionsSync.Lock()
	defer ls.connectionsSync.Unlock()
	key := ""
	for k, c := range ls.connections {
		if c == conn {
			key = k
			break
		}
	}
	if key == "" {
		return nil
	}
	delete(ls.connections, key)
	return nil
}
