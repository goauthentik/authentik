package ldap

import (
	"crypto/tls"
	"sync"

	"github.com/go-openapi/strfmt"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/api"
	"goauthentik.io/internal/crypto"
	"goauthentik.io/internal/outpost/ak"

	"github.com/nmcclain/ldap"
)

const GroupObjectClass = "group"
const UserObjectClass = "user"

type ProviderInstance struct {
	BaseDN string

	UserDN string

	VirtualGroupDN string
	GroupDN        string

	appSlug  string
	flowSlug string
	s        *LDAPServer
	log      *log.Entry

	tlsServerName       *string
	cert                *tls.Certificate
	outpostName         string
	searchAllowedGroups []*strfmt.UUID
	boundUsersMutex     sync.RWMutex
	boundUsers          map[string]UserFlags

	uidStartNumber int32
	gidStartNumber int32
}

type UserFlags struct {
	UserInfo  *api.User
	UserPk    int32
	CanSearch bool
}

type LDAPServer struct {
	s           *ldap.Server
	log         *log.Entry
	ac          *ak.APIController
	cs          *ak.CryptoStore
	defaultCert *tls.Certificate
	providers   []*ProviderInstance
}

type LDAPGroup struct {
	dn             string
	cn             string
	uid            string
	gidNumber      string
	member         []string
	isSuperuser    bool
	isVirtualGroup bool
	akAttributes   interface{}
}

func NewServer(ac *ak.APIController) *LDAPServer {
	s := ldap.NewServer()
	s.EnforceLDAP = true
	ls := &LDAPServer{
		s:         s,
		log:       log.WithField("logger", "authentik.outpost.ldap"),
		ac:        ac,
		cs:        ak.NewCryptoStore(ac.Client.CryptoApi),
		providers: []*ProviderInstance{},
	}
	defaultCert, err := crypto.GenerateSelfSignedCert()
	if err != nil {
		log.Warning(err)
	}
	ls.defaultCert = &defaultCert
	s.BindFunc("", ls)
	s.SearchFunc("", ls)
	s.CloseFunc("", ls)
	return ls
}

func (ls *LDAPServer) Type() string {
	return "ldap"
}
