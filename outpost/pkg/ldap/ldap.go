package ldap

import (
	"crypto/tls"
	"sync"

	"github.com/go-openapi/strfmt"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/outpost/api"
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

	tlsServerName *string
	cert          *tls.Certificate

	searchAllowedGroups []*strfmt.UUID
	boundUsersMutex     sync.RWMutex
	boundUsers          map[string]UserFlags

	uidStartNumber int32
	gidStartNumber int32
}

type UserFlags struct {
	UserInfo  api.User
	CanSearch bool
}

type LDAPServer struct {
	s           *ldap.Server
	log         *log.Entry
	ac          *ak.APIController
	defaultCert *tls.Certificate
	providers   []*ProviderInstance
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
	defaultCert, err := ak.GenerateSelfSignedCert()
	if err != nil {
		log.Warning(err)
	}
	ls.defaultCert = &defaultCert
	s.BindFunc("", ls)
	s.SearchFunc("", ls)
	return ls
}
