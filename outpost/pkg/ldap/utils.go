package ldap

import (
	"fmt"
	"strings"
	"bytes"
	"encoding/hex"
	"encoding/binary"
	"strconv"
	"reflect"

	"github.com/nmcclain/ldap"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/outpost/api"
)

func BoolToString(in bool) string {
	if in {
		return "true"
	}
	return "false"
}

func ldapResolveTypeSingle(in interface{}) *string {
	switch t := in.(type) {
	case string:
		return &t
	case *string:
		return t
	case bool:
		s := BoolToString(t)
		return &s
	case *bool:
		s := BoolToString(*t)
		return &s
	default:
		log.WithField("type", reflect.TypeOf(in).String()).Warning("Type can't be mapped to LDAP yet")
		return nil
	}
}

func AKAttrsToLDAP(attrs interface{}) []*ldap.EntryAttribute {
	attrList := []*ldap.EntryAttribute{}
	a := attrs.(*map[string]interface{})
	for attrKey, attrValue := range *a {
		entry := &ldap.EntryAttribute{Name: attrKey}
		switch t := attrValue.(type) {
		case []string:
			entry.Values = t
		case *[]string:
			entry.Values = *t
		case []interface{}:
			entry.Values = make([]string, len(t))
			for idx, v := range t {
				v := ldapResolveTypeSingle(v)
				entry.Values[idx] = *v
			}
		default:
			v := ldapResolveTypeSingle(t)
			if v != nil {
				entry.Values = []string{*v}
			}
		}
		attrList = append(attrList, entry)
	}
	return attrList
}

func (pi *ProviderInstance) GroupsForUser(user api.User) []string {
	groups := make([]string, len(user.Groups))
	for i, group := range user.Groups {
		groups[i] = pi.GetGroupDN(group)
	}
	return groups
}

func (pi *ProviderInstance) UsersForGroup(group api.Group) []string {
	users := make([]string, len(group.UsersObj))
	for i, user := range group.UsersObj {
		users[i] = pi.GetUserDN(user.Username)
	}
	return users
}

func (pi *ProviderInstance) GetUserDN(user string) string {
	return fmt.Sprintf("cn=%s,%s", user, pi.UserDN)
}

func (pi *ProviderInstance) GetGroupDN(group api.Group) string {
	return fmt.Sprintf("cn=%s,%s", group.Name, pi.GroupDN)
}

func (pi *ProviderInstance) GetUidNumber(user api.User) string {
	return strconv.FormatInt(int64(pi.uidStartNumber + user.Pk), 10)
}

func (pi *ProviderInstance) GetGidNumber(group api.Group) string {
	return strconv.FormatInt(int64(pi.gidStartNumber + pi.GetRIDForGroup(group.Pk)), 10)
}

func (pi *ProviderInstance) GetRIDForGroup(uid string) int32 {
	data, err := hex.DecodeString(strings.Replace(uid, "-", "", -1))

	if err != nil {
		panic(err)
	}

	dataSize := len(data);

	// Don't want to give too big numbers to gidNumber to ensure easo of use in LXC containers, unlikely that the 3rd to last and last bytes are the same on two groups.
	// The actual gidNumber isn't very important, just that the group gets the same one each time and that they don't overlap.
	chunk := []byte{ 0, 0, data[dataSize - 3], data[dataSize - 1] }

	buf := bytes.NewBuffer(chunk)
	var rid int32
	binary.Read(buf, binary.BigEndian, &rid)

	return rid
}
