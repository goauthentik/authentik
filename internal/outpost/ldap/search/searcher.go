package search

import "github.com/nmcclain/ldap"

type Searcher interface {
	Search(req *Request) (ldap.ServerSearchResult, error)
}
