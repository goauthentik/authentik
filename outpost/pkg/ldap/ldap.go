package ldap

import (
	"fmt"
	"strings"

	log "github.com/sirupsen/logrus"
	"goauthentik.io/outpost/pkg/ak"

	"github.com/nmcclain/ldap"
)

const GroupObjectClass = "group"
const UserObjectClass = "user"

type LDAPServer struct {
	BaseDN string

	userDN  string
	groupDN string

	s   *ldap.Server
	log *log.Entry
	ac  *ak.APIController

	// TODO: Make configurable
	flowSlug string
	appSlug  string
}

func NewServer(ac *ak.APIController) *LDAPServer {
	s := ldap.NewServer()
	s.EnforceLDAP = true
	ls := &LDAPServer{
		s:   s,
		log: log.WithField("logger", "ldap-server"),
		ac:  ac,

		BaseDN: "DC=ldap,DC=goauthentik,DC=io",
	}
	ls.userDN = strings.ToLower(fmt.Sprintf("cn=users,%s", ls.BaseDN))
	ls.groupDN = strings.ToLower(fmt.Sprintf("cn=groups,%s", ls.BaseDN))
	s.BindFunc("", ls)
	s.SearchFunc("", ls)
	return ls
}
