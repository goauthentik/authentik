# LDAP for Golang

This library provides basic LDAP v3 functionality for the GO programming language.

The **client** portion is limited, but sufficient to perform LDAP authentication and directory lookups (binds and searches) against any modern LDAP server (tested with OpenLDAP and AD).

The **server** portion implements Bind and Search from [RFC4510](http://tools.ietf.org/html/rfc4510), has good testing coverage, and is compatible with any LDAPv3 client.  It provides the building blocks for a custom LDAP server, but you must implement the backend datastore of your choice.


## LDAP client notes:

### A simple LDAP bind operation:
```go
l, err := ldap.Dial("tcp", fmt.Sprintf("%s:%d", ldapServer, ldapPort))
// be sure to add error checking!
defer l.Close()
err = l.Bind(user, passwd)
if err==nil {
  // authenticated
} else {
  // invalid authentication
}
```

### A simple LDAP search operation:
```go
search := &SearchRequest{
  BaseDN: "dc=example,dc=com",
  Filter: "(objectclass=*)",
}
searchResults, err := l.Search(search)
// be sure to add error checking!
```

### Implemented:
* Connecting, binding to LDAP server
* Searching for entries with filtering and paging controls
* Compiling string filters to LDAP filters
* Modify Requests / Responses

### Not implemented:
* Add, Delete, Modify DN, Compare operations
* Most tests / benchmarks

### LDAP client examples:
* examples/search.go: **Basic client bind and search**
* examples/searchSSL.go: **Client bind and search over SSL**
* examples/searchTLS.go: **Client bind and search over TLS**
* examples/modify.go: **Client modify operation**

*Client library by: [mmitton](https://github.com/mmitton), with contributions from:  [uavila](https://github.com/uavila), [vanackere](https://github.com/vanackere), [juju2013](https://github.com/juju2013), [johnweldon](https://github.com/johnweldon), [marcsauter](https://github.com/marcsauter), and [nmcclain](https://github.com/nmcclain)*

## LDAP server notes:
The server library is modeled after net/http - you designate handlers for the LDAP operations you want to support (Bind/Search/etc.), then start the server with ListenAndServe().  You can specify different handlers for different baseDNs - they must implement the interfaces of the operations you want to support:
```go
type Binder interface {
    Bind(bindDN, bindSimplePw string, conn net.Conn) (LDAPResultCode, error)
}
type Searcher interface {
    Search(boundDN string, searchReq SearchRequest, conn net.Conn) (ServerSearchResult, error)
}
type Closer interface {
    Close(conn net.Conn) error
}
```

### A basic bind-only LDAP server
```go
func main() {
  s := ldap.NewServer()
  handler := ldapHandler{}
  s.BindFunc("", handler)
  if err := s.ListenAndServe("localhost:389"); err != nil {
    log.Fatal("LDAP Server Failed: %s", err.Error())
  }
}
type ldapHandler struct {
}
func (h ldapHandler) Bind(bindDN, bindSimplePw string, conn net.Conn) (ldap.LDAPResultCode, error) {
	if bindDN == "" && bindSimplePw == "" {
		return ldap.LDAPResultSuccess, nil
	}
	return ldap.LDAPResultInvalidCredentials, nil
}
```

* Server.EnforceLDAP: Normally, the LDAP server will return whatever results your handler provides.  Set the **Server.EnforceLDAP** flag to **true** and the server will apply the LDAP **search filter**, **attributes limits**, **size/time limits**, **search scope**, and **base DN matching** to your handler's dataset.  This makes it a lot simpler to write a custom LDAP server without worrying about LDAP internals.

### LDAP server examples:
* examples/server.go: **Basic LDAP authentication (bind and search only)**
* examples/proxy.go: **Simple LDAP proxy server.**
* server_test.go: **The _test.go files have examples of all server functions.**

### Known limitations:

* Golang's TLS implementation does not support SSLv2.  Some old OSs require SSLv2, and are not able to connect to an LDAP server created with this library's ListenAndServeTLS() function.  If you *must* support legacy (read: *insecure*) SSLv2 clients, run your LDAP server behind HAProxy.

### Not implemented:
From the server perspective, all of [RFC4510](http://tools.ietf.org/html/rfc4510) is implemented **except**:
* 4.5.1.3.  SearchRequest.derefAliases
* 4.5.1.5.  SearchRequest.timeLimit
* 4.5.1.6.  SearchRequest.typesOnly
* 4.14. StartTLS Operation

*Server library by: [nmcclain](https://github.com/nmcclain)*
