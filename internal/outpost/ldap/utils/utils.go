package utils

import (
	"reflect"

	"github.com/nmcclain/ldap"
	log "github.com/sirupsen/logrus"
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
	if attrs == nil {
		return attrList
	}
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

func EnsureAttributes(attrs []*ldap.EntryAttribute, shouldHave map[string][]string) []*ldap.EntryAttribute {
	for name, values := range shouldHave {
		attrs = MustHaveAttribute(attrs, name, values)
	}
	return attrs
}

func MustHaveAttribute(attrs []*ldap.EntryAttribute, name string, value []string) []*ldap.EntryAttribute {
	shouldSet := true
	for _, attr := range attrs {
		if attr.Name == name {
			shouldSet = false
		}
	}
	if shouldSet {
		return append(attrs, &ldap.EntryAttribute{
			Name:   name,
			Values: value,
		})
	}
	return attrs
}
