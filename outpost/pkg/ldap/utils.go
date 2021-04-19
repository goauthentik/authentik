package ldap

import (
	"github.com/nmcclain/ldap"
)

func AKAttrsToLDAP(attrs interface{}) []*ldap.EntryAttribute {
	attrList := []*ldap.EntryAttribute{}
	for attrKey, attrValue := range attrs.(map[string]interface{}) {
		entry := &ldap.EntryAttribute{Name: attrKey}
		switch attrValue.(type) {
		case []string:
			entry.Values = attrValue.([]string)
		case string:
			entry.Values = []string{attrValue.(string)}
		}
		attrList = append(attrList, entry)
	}
	return attrList
}
