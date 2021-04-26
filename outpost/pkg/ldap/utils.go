package ldap

import (
	"github.com/nmcclain/ldap"
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
