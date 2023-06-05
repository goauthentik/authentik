package search

import (
	"beryju.io/ldap"
)

type Searcher interface {
	Search(req *Request) (ldap.ServerSearchResult, error)
}
