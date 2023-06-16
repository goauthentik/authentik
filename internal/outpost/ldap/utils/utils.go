package utils

import (
	"fmt"
	"strconv"
	"strings"

	"beryju.io/ldap"
	ldapConstants "goauthentik.io/internal/outpost/ldap/constants"
)

func AttributeKeySanitize(key string) string {
	return strings.ReplaceAll(
		strings.ReplaceAll(key, "/", "-"),
		".",
		"",
	)
}

func stringify(in interface{}) *string {
	switch t := in.(type) {
	case string:
		return &t
	case *string:
		return t
	case bool:
		s := strconv.FormatBool(t)
		return &s
	case float32:
		s := strconv.FormatFloat(float64(t), 'f', -1, 64)
		return &s
	case float64:
		s := strconv.FormatFloat(t, 'f', -1, 64)
		return &s
	case int:
		s := strconv.FormatInt(int64(t), 10)
		return &s
	default:
		if in != nil {
			s := fmt.Sprintf("%s", in)
			return &s
		}
		return nil
	}
}

func AttributesToLDAP(
	attrs map[string]interface{},
	keyFormatter func(key string) string,
	valueFormatter func(value []string) []string,
) []*ldap.EntryAttribute {
	attrList := []*ldap.EntryAttribute{}
	if attrs == nil {
		return attrList
	}
	for attrKey, attrValue := range attrs {
		entry := &ldap.EntryAttribute{Name: keyFormatter(attrKey)}
		switch t := attrValue.(type) {
		case []string:
			entry.Values = valueFormatter(t)
		case *[]string:
			entry.Values = valueFormatter(*t)
		case []interface{}:
			vv := make([]string, 0)
			for _, v := range t {
				v := stringify(v)
				if v != nil {
					vv = append(vv, *v)
				}
			}
			entry.Values = valueFormatter(vv)
		default:
			v := stringify(t)
			if v != nil {
				entry.Values = valueFormatter([]string{*v})
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
		if strings.EqualFold(attr.Name, name) {
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

func IncludeObjectClass(searchOC string, ocs map[string]bool) bool {
	if searchOC == "" {
		return true
	}

	for key, value := range ocs {
		if strings.EqualFold(key, searchOC) {
			return value
		}
	}
	return false
}

func GetContainerEntry(filterOC string, dn string, ou string) *ldap.Entry {
	if IncludeObjectClass(filterOC, ldapConstants.GetContainerOCs()) {
		return &ldap.Entry{
			DN: dn,
			Attributes: []*ldap.EntryAttribute{
				{
					Name:   "distinguishedName",
					Values: []string{dn},
				},
				{
					Name:   "objectClass",
					Values: []string{"top", "nsContainer"},
				},
				{
					Name:   "commonName",
					Values: []string{ou},
				},
			},
		}
	}

	return nil
}

func HasSuffixNoCase(s1 string, s2 string) bool {
	return strings.HasSuffix(strings.ToLower(s1), strings.ToLower(s2))
}
