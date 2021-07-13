package ldap

import (
	"fmt"
	"strings"
	"bytes"
	"encoding/hex"
	"encoding/binary"
	"os"
	"strconv"

	"github.com/nmcclain/ldap"
	"goauthentik.io/outpost/api"
)

func BoolToString(in bool) string {
	if in {
		return "true"
	}
	return "false"
}

func AKAttrsToLDAP(attrs interface{}) []*ldap.EntryAttribute {
	attrList := []*ldap.EntryAttribute{}
	a := attrs.(*map[string]interface{})
	for attrKey, attrValue := range *a {
		entry := &ldap.EntryAttribute{Name: attrKey}
		switch t := attrValue.(type) {
		case []string:
			entry.Values = t
		case string:
			entry.Values = []string{t}
		case bool:
			entry.Values = []string{BoolToString(t)}
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

func (pi *ProviderInstance) GetGroupDN(group api.Group) string {
	return fmt.Sprintf("cn=%s,%s", group.Name, pi.GroupDN)
}

func (pi *ProviderInstance) GetUidNumberStart() int32 {
	if (pi.uidNumberStart == 0) {
		val, found := os.LookupEnv("LDAP_UID_NUMBER_START")

		if (!found) {
			pi.uidNumberStart = 2000
		} else {
			i, _ := strconv.ParseInt(val, 10, 32)
			pi.uidNumberStart = int32(i)
		}
	}

	return pi.uidNumberStart
}

func (pi *ProviderInstance) GetGidNumberStart() int32 {
	if (pi.gidNumberStart == 0) {
		val, found := os.LookupEnv("LDAP_GID_NUMBER_START")

		if (!found) {
			pi.gidNumberStart = 2000
		} else {
			i, _ := strconv.ParseInt(val, 10, 32)
			pi.gidNumberStart = int32(i)
		}
	}

	return pi.gidNumberStart
}

func (pi *ProviderInstance) GetUidNumber(user api.User) string {
	return strconv.FormatInt(int64(pi.GetUidNumberStart() + user.Pk), 10)
}

func (pi *ProviderInstance) GetGidNumber(group api.Group) string {
	return strconv.FormatInt(int64(pi.GetGidNumberStart() + pi.GetRIDForGroup(group.Pk)), 10)
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
