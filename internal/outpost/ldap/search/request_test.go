package search

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestNormalizeAttributes(t *testing.T) {
	tests := []struct {
		name           string
		input          []string
		expectedOutput []string
	}{
		{
			name:           "Empty input",
			input:          []string{},
			expectedOutput: []string{},
		},
		{
			name:           "No commas",
			input:          []string{"uid", "cn", "sn"},
			expectedOutput: []string{"uid", "cn", "sn"},
		},
		{
			name:           "Single comma-separated string",
			input:          []string{"uid,cn,sn"},
			expectedOutput: []string{"uid", "cn", "sn"},
		},
		{
			name:           "Mixed input",
			input:          []string{"uid,cn", "sn"},
			expectedOutput: []string{"uid", "cn", "sn"},
		},
		{
			name:           "With spaces",
			input:          []string{"uid, cn, sn"},
			expectedOutput: []string{"uid", "cn", "sn"},
		},
		{
			name:           "Empty parts",
			input:          []string{"uid,, cn"},
			expectedOutput: []string{"uid", "cn"},
		},
		{
			name:           "Single element",
			input:          []string{"uid"},
			expectedOutput: []string{"uid"},
		},
		{
			name:           "Only commas",
			input:          []string{",,,"},
			expectedOutput: []string{},
		},
		{
			name:           "Multiple comma-separated attributes",
			input:          []string{"uid,cn", "sn,mail", "givenName"},
			expectedOutput: []string{"uid", "cn", "sn", "mail", "givenName"},
		},
		{
			name:           "Case preservation",
			input:          []string{"uid,CN,sAMAccountName"},
			expectedOutput: []string{"uid", "CN", "sAMAccountName"},
		},
		{
			name:           "Leading and trailing spaces",
			input:          []string{" uid , cn , sn "},
			expectedOutput: []string{"uid", "cn", "sn"},
		},
		{
			name:           "Real-world LDAP attribute examples",
			input:          []string{"objectClass,memberOf,mail", "sAMAccountName,userPrincipalName"},
			expectedOutput: []string{"objectClass", "memberOf", "mail", "sAMAccountName", "userPrincipalName"},
		},
		{
			name:           "Jira-style attribute format",
			input:          []string{"uid,cn,sn"},
			expectedOutput: []string{"uid", "cn", "sn"},
		},
		{
			name:           "Single string with single attribute",
			input:          []string{"cn"},
			expectedOutput: []string{"cn"},
		},
		{
			name:           "Mix of standard and operational attributes",
			input:          []string{"uid,+", "createTimestamp"},
			expectedOutput: []string{"uid", "+", "createTimestamp"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := normalizeAttributes(tt.input)
			assert.Equal(t, tt.expectedOutput, result)
		})
	}
}
