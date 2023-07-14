package ldap

import (
	"log"
	"net"

	ber "github.com/nmcclain/asn1-ber"
)

func HandleBindRequest(req *ber.Packet, fns map[string]Binder, conn net.Conn) (resultCode LDAPResultCode) {
	defer func() {
		if r := recover(); r != nil {
			resultCode = LDAPResultOperationsError
		}
	}()

	// we only support ldapv3
	ldapVersion, ok := req.Children[0].Value.(uint64)
	if !ok {
		return LDAPResultProtocolError
	}
	if ldapVersion != 3 {
		log.Printf("Unsupported LDAP version: %d", ldapVersion)
		return LDAPResultInappropriateAuthentication
	}

	// auth types
	bindDN, ok := req.Children[1].Value.(string)
	if !ok {
		return LDAPResultProtocolError
	}
	bindAuth := req.Children[2]
	switch bindAuth.Tag {
	default:
		log.Print("Unknown LDAP authentication method")
		return LDAPResultInappropriateAuthentication
	case LDAPBindAuthSimple:
		if len(req.Children) == 3 {
			fnNames := []string{}
			for k := range fns {
				fnNames = append(fnNames, k)
			}
			fn := routeFunc(bindDN, fnNames)
			resultCode, err := fns[fn].Bind(bindDN, bindAuth.Data.String(), conn)
			if err != nil {
				log.Printf("BindFn Error %s", err.Error())
				return LDAPResultOperationsError
			}
			return resultCode
		} else {
			log.Print("Simple bind request has wrong # children.  len(req.Children) != 3")
			return LDAPResultInappropriateAuthentication
		}
	case LDAPBindAuthSASL:
		log.Print("SASL authentication is not supported")
		return LDAPResultInappropriateAuthentication
	}
}

func encodeBindResponse(messageID uint64, ldapResultCode LDAPResultCode) *ber.Packet {
	responsePacket := ber.Encode(ber.ClassUniversal, ber.TypeConstructed, ber.TagSequence, nil, "LDAP Response")
	responsePacket.AppendChild(ber.NewInteger(ber.ClassUniversal, ber.TypePrimitive, ber.TagInteger, messageID, "Message ID"))

	bindReponse := ber.Encode(ber.ClassApplication, ber.TypeConstructed, ApplicationBindResponse, nil, "Bind Response")
	bindReponse.AppendChild(ber.NewInteger(ber.ClassUniversal, ber.TypePrimitive, ber.TagEnumerated, uint64(ldapResultCode), "resultCode: "))
	bindReponse.AppendChild(ber.NewString(ber.ClassUniversal, ber.TypePrimitive, ber.TagOctetString, "", "matchedDN: "))
	bindReponse.AppendChild(ber.NewString(ber.ClassUniversal, ber.TypePrimitive, ber.TagOctetString, "", "errorMessage: "))

	responsePacket.AppendChild(bindReponse)

	// ber.PrintPacket(responsePacket)
	return responsePacket
}
