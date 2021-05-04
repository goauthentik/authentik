package ldap

import (
	"fmt"

	"github.com/nmcclain/ldap"
	"goauthentik.io/outpost/pkg/models"
)

func AKAttrsToLDAP(attrs interface{}) []*ldap.EntryAttribute {
	attrList := []*ldap.EntryAttribute{}
	for attrKey, attrValue := range attrs.(map[string]interface{}) {
		entry := &ldap.EntryAttribute{Name: attrKey}
		switch t := attrValue.(type) {
		case []string:
			entry.Values = t
		case string:
			entry.Values = []string{t}
		}
		attrList = append(attrList, entry)
	}
	return attrList
}

func (pi *ProviderInstance) GroupsForUser(user *models.User) []string {
	groups := make([]string, len(user.Groups))
	for i, group := range user.Groups {
		groups[i] = pi.GetGroupDN(group)
	}
	return groups
}

func (pi *ProviderInstance) GetGroupDN(group *models.Group) string {
	return fmt.Sprintf("cn=%s,%s", *group.Name, pi.GroupDN)
}
