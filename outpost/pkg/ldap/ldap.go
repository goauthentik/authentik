package ldap

import (
	log "github.com/sirupsen/logrus"
	"goauthentik.io/outpost/pkg/ak"

	"github.com/nmcclain/ldap"
)

const GroupObjectClass = "group"
const UserObjectClass = "user"

type ProviderInstance struct {
	BaseDN string

	UserDN  string
	GroupDN string

	appSlug  string
	flowSlug string
	s        *LDAPServer
	log      *log.Entry
}

type LDAPServer struct {
	s   *ldap.Server
	log *log.Entry
	ac  *ak.APIController

	providers []*ProviderInstance
}

func NewServer(ac *ak.APIController) *LDAPServer {
	s := ldap.NewServer()
	s.EnforceLDAP = true
	ls := &LDAPServer{
		s:         s,
		log:       log.WithField("logger", "authentik.outpost.ldap"),
		ac:        ac,
		providers: []*ProviderInstance{},
	}
	s.BindFunc("", ls)
	s.SearchFunc("", ls)
	return ls
}
