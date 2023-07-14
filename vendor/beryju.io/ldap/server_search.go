package ldap

import (
	"errors"
	"fmt"
	"net"
	"strings"

	ber "github.com/nmcclain/asn1-ber"
)

func HandleSearchRequest(req *ber.Packet, controls *[]Control, messageID uint64, boundDN string, server *Server, conn net.Conn) (resultErr error) {
	defer func() {
		if r := recover(); r != nil {
			resultErr = NewError(LDAPResultOperationsError, fmt.Errorf("Search function panic: %s", r))
		}
	}()

	searchReq, err := parseSearchRequest(boundDN, req, controls)
	if err != nil {
		return NewError(LDAPResultOperationsError, err)
	}

	filterPacket, err := CompileFilter(searchReq.Filter)
	if err != nil {
		return NewError(LDAPResultOperationsError, err)
	}

	fnNames := []string{}
	for k := range server.SearchFns {
		fnNames = append(fnNames, k)
	}
	fn := routeFunc(searchReq.BaseDN, fnNames)
	searchResp, err := server.SearchFns[fn].Search(boundDN, searchReq, conn)
	if err != nil {
		return NewError(searchResp.ResultCode, err)
	}

	if server.EnforceLDAP {
		if searchReq.DerefAliases != NeverDerefAliases { // [-a {never|always|search|find}
			// TODO: Server DerefAliases not supported: RFC4511 4.5.1.3
		}
		if searchReq.TimeLimit > 0 {
			// TODO: Server TimeLimit not implemented
		}
	}

	i := 0
	searchReqBaseDNLower := strings.ToLower(searchReq.BaseDN)
	for _, entry := range searchResp.Entries {
		if server.EnforceLDAP {
			// filter
			keep, resultCode := ServerApplyFilter(filterPacket, entry)
			if resultCode != LDAPResultSuccess {
				return NewError(resultCode, errors.New("ServerApplyFilter error"))
			}
			if !keep {
				continue
			}

			// constrained search scope
			switch searchReq.Scope {
			case ScopeWholeSubtree: // The scope is constrained to the entry named by baseObject and to all its subordinates.
			case ScopeBaseObject: // The scope is constrained to the entry named by baseObject.
				if strings.ToLower(entry.DN) != searchReqBaseDNLower {
					continue
				}
			case ScopeSingleLevel: // The scope is constrained to the immediate subordinates of the entry named by baseObject.
				entryDNLower := strings.ToLower(entry.DN)
				parts := strings.Split(entryDNLower, ",")
				if len(parts) < 2 && entryDNLower != searchReqBaseDNLower {
					continue
				}
				if dnSuffix := strings.Join(parts[1:], ","); dnSuffix != searchReqBaseDNLower {
					continue
				}
			}

			// filter attributes
			entry, err = filterAttributes(entry, searchReq.Attributes)
			if err != nil {
				return NewError(LDAPResultOperationsError, err)
			}

			// size limit
			if searchReq.SizeLimit > 0 && i >= searchReq.SizeLimit {
				break
			}
			i++
		}

		// respond
		responsePacket := encodeSearchResponse(messageID, searchReq, entry)
		if err = sendPacket(conn, responsePacket); err != nil {
			return NewError(LDAPResultOperationsError, err)
		}
	}
	return nil
}

// ///////////////////////
func parseSearchRequest(boundDN string, req *ber.Packet, controls *[]Control) (SearchRequest, error) {
	if len(req.Children) != 8 {
		return SearchRequest{}, NewError(LDAPResultOperationsError, errors.New("Bad search request"))
	}

	// Parse the request
	baseObject, ok := req.Children[0].Value.(string)
	if !ok {
		return SearchRequest{}, NewError(LDAPResultProtocolError, errors.New("Bad search request"))
	}
	s, ok := req.Children[1].Value.(uint64)
	if !ok {
		return SearchRequest{}, NewError(LDAPResultProtocolError, errors.New("Bad search request"))
	}
	scope := int(s)
	d, ok := req.Children[2].Value.(uint64)
	if !ok {
		return SearchRequest{}, NewError(LDAPResultProtocolError, errors.New("Bad search request"))
	}
	derefAliases := int(d)
	s, ok = req.Children[3].Value.(uint64)
	if !ok {
		return SearchRequest{}, NewError(LDAPResultProtocolError, errors.New("Bad search request"))
	}
	sizeLimit := int(s)
	t, ok := req.Children[4].Value.(uint64)
	if !ok {
		return SearchRequest{}, NewError(LDAPResultProtocolError, errors.New("Bad search request"))
	}
	timeLimit := int(t)
	typesOnly := false
	if req.Children[5].Value != nil {
		typesOnly, ok = req.Children[5].Value.(bool)
		if !ok {
			return SearchRequest{}, NewError(LDAPResultProtocolError, errors.New("Bad search request"))
		}
	}
	filter, err := DecompileFilter(req.Children[6])
	if err != nil {
		return SearchRequest{}, err
	}
	attributes := []string{}
	for _, attr := range req.Children[7].Children {
		a, ok := attr.Value.(string)
		if !ok {
			return SearchRequest{}, NewError(LDAPResultProtocolError, errors.New("Bad search request"))
		}
		attributes = append(attributes, a)
	}
	searchReq := SearchRequest{
		baseObject, scope,
		derefAliases, sizeLimit, timeLimit,
		typesOnly, filter, attributes, *controls,
	}

	return searchReq, nil
}

// ///////////////////////
func filterAttributes(entry *Entry, attributes []string) (*Entry, error) {
	// only return requested attributes
	newAttributes := []*EntryAttribute{}

	if len(attributes) > 1 || (len(attributes) == 1 && len(attributes[0]) > 0) {
		for _, attr := range entry.Attributes {
			attrNameLower := strings.ToLower(attr.Name)
			for _, requested := range attributes {
				requestedLower := strings.ToLower(requested)
				// You can request the directory server to return operational attributes by adding + (the plus sign) in your ldapsearch command.
				// "+supportedControl" is treated as an operational attribute
				if strings.HasPrefix(attrNameLower, "+") {
					if requestedLower == "+" || attrNameLower == "+"+requestedLower {
						newAttributes = append(newAttributes, &EntryAttribute{attr.Name[1:], attr.Values})
						break
					}
				} else {
					if requested == "*" || attrNameLower == requestedLower {
						newAttributes = append(newAttributes, attr)
						break
					}
				}
			}
		}
	} else {
		// remove operational attributes
		for _, attr := range entry.Attributes {
			if !strings.HasPrefix(attr.Name, "+") {
				newAttributes = append(newAttributes, attr)
			}
		}
	}
	entry.Attributes = newAttributes

	return entry, nil
}

// ///////////////////////
func encodeSearchResponse(messageID uint64, req SearchRequest, res *Entry) *ber.Packet {
	responsePacket := ber.Encode(ber.ClassUniversal, ber.TypeConstructed, ber.TagSequence, nil, "LDAP Response")
	responsePacket.AppendChild(ber.NewInteger(ber.ClassUniversal, ber.TypePrimitive, ber.TagInteger, messageID, "Message ID"))

	searchEntry := ber.Encode(ber.ClassApplication, ber.TypeConstructed, ApplicationSearchResultEntry, nil, "Search Result Entry")
	searchEntry.AppendChild(ber.NewString(ber.ClassUniversal, ber.TypePrimitive, ber.TagOctetString, res.DN, "Object Name"))

	attrs := ber.Encode(ber.ClassUniversal, ber.TypeConstructed, ber.TagSequence, nil, "Attributes:")
	for _, attribute := range res.Attributes {
		attrs.AppendChild(encodeSearchAttribute(attribute.Name, attribute.Values))
	}

	searchEntry.AppendChild(attrs)
	responsePacket.AppendChild(searchEntry)

	return responsePacket
}

func encodeSearchAttribute(name string, values []string) *ber.Packet {
	packet := ber.Encode(ber.ClassUniversal, ber.TypeConstructed, ber.TagSequence, nil, "Attribute")
	packet.AppendChild(ber.NewString(ber.ClassUniversal, ber.TypePrimitive, ber.TagOctetString, name, "Attribute Name"))

	valuesPacket := ber.Encode(ber.ClassUniversal, ber.TypeConstructed, ber.TagSet, nil, "Attribute Values")
	for _, value := range values {
		valuesPacket.AppendChild(ber.NewString(ber.ClassUniversal, ber.TypePrimitive, ber.TagOctetString, value, "Attribute Value"))
	}

	packet.AppendChild(valuesPacket)

	return packet
}

func encodeSearchDone(messageID uint64, ldapResultCode LDAPResultCode) *ber.Packet {
	responsePacket := ber.Encode(ber.ClassUniversal, ber.TypeConstructed, ber.TagSequence, nil, "LDAP Response")
	responsePacket.AppendChild(ber.NewInteger(ber.ClassUniversal, ber.TypePrimitive, ber.TagInteger, messageID, "Message ID"))
	donePacket := ber.Encode(ber.ClassApplication, ber.TypeConstructed, ApplicationSearchResultDone, nil, "Search result done")
	donePacket.AppendChild(ber.NewInteger(ber.ClassUniversal, ber.TypePrimitive, ber.TagEnumerated, uint64(ldapResultCode), "resultCode: "))
	donePacket.AppendChild(ber.NewString(ber.ClassUniversal, ber.TypePrimitive, ber.TagOctetString, "", "matchedDN: "))
	donePacket.AppendChild(ber.NewString(ber.ClassUniversal, ber.TypePrimitive, ber.TagOctetString, "", "errorMessage: "))
	responsePacket.AppendChild(donePacket)

	return responsePacket
}
