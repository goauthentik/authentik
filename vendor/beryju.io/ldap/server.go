package ldap

import (
	"crypto/tls"
	"io"
	"log"
	"net"
	"strings"
	"sync"

	ber "github.com/nmcclain/asn1-ber"
)

type Binder interface {
	Bind(bindDN, bindSimplePw string, conn net.Conn) (LDAPResultCode, error)
}
type Searcher interface {
	Search(boundDN string, req SearchRequest, conn net.Conn) (ServerSearchResult, error)
}
type Adder interface {
	Add(boundDN string, req AddRequest, conn net.Conn) (LDAPResultCode, error)
}
type Modifier interface {
	Modify(boundDN string, req ModifyRequest, conn net.Conn) (LDAPResultCode, error)
}
type Deleter interface {
	Delete(boundDN, deleteDN string, conn net.Conn) (LDAPResultCode, error)
}
type ModifyDNr interface {
	ModifyDN(boundDN string, req ModifyDNRequest, conn net.Conn) (LDAPResultCode, error)
}
type Comparer interface {
	Compare(boundDN string, req CompareRequest, conn net.Conn) (LDAPResultCode, error)
}
type Abandoner interface {
	Abandon(boundDN string, conn net.Conn) error
}
type Extender interface {
	Extended(boundDN string, req ExtendedRequest, conn net.Conn) (LDAPResultCode, error)
}
type Unbinder interface {
	Unbind(boundDN string, conn net.Conn) (LDAPResultCode, error)
}
type Closer interface {
	Close(boundDN string, conn net.Conn) error
}

type Server struct {
	BindFns     map[string]Binder
	SearchFns   map[string]Searcher
	AddFns      map[string]Adder
	ModifyFns   map[string]Modifier
	DeleteFns   map[string]Deleter
	ModifyDNFns map[string]ModifyDNr
	CompareFns  map[string]Comparer
	AbandonFns  map[string]Abandoner
	ExtendedFns map[string]Extender
	UnbindFns   map[string]Unbinder
	CloseFns    map[string]Closer
	StartTLS    *tls.Config
	Quit        chan bool
	EnforceLDAP bool
	Stats       *Stats
}

type Stats struct {
	Conns      int
	Binds      int
	Unbinds    int
	Searches   int
	statsMutex sync.Mutex
}

type ServerSearchResult struct {
	Entries    []*Entry
	Referrals  []string
	Controls   []Control
	ResultCode LDAPResultCode
}

func NewServer() *Server {
	s := new(Server)
	s.Quit = make(chan bool)

	d := defaultHandler{}
	s.BindFns = make(map[string]Binder)
	s.SearchFns = make(map[string]Searcher)
	s.AddFns = make(map[string]Adder)
	s.ModifyFns = make(map[string]Modifier)
	s.DeleteFns = make(map[string]Deleter)
	s.ModifyDNFns = make(map[string]ModifyDNr)
	s.CompareFns = make(map[string]Comparer)
	s.AbandonFns = make(map[string]Abandoner)
	s.ExtendedFns = make(map[string]Extender)
	s.UnbindFns = make(map[string]Unbinder)
	s.CloseFns = make(map[string]Closer)
	s.BindFunc("", d)
	s.SearchFunc("", d)
	s.AddFunc("", d)
	s.ModifyFunc("", d)
	s.DeleteFunc("", d)
	s.ModifyDNFunc("", d)
	s.CompareFunc("", d)
	s.AbandonFunc("", d)
	s.ExtendedFunc("", d)
	s.UnbindFunc("", d)
	s.CloseFunc("", d)
	s.Stats = nil
	return s
}

func (server *Server) BindFunc(baseDN string, f Binder) {
	server.BindFns[baseDN] = f
}

func (server *Server) SearchFunc(baseDN string, f Searcher) {
	server.SearchFns[baseDN] = f
}

func (server *Server) AddFunc(baseDN string, f Adder) {
	server.AddFns[baseDN] = f
}

func (server *Server) ModifyFunc(baseDN string, f Modifier) {
	server.ModifyFns[baseDN] = f
}

func (server *Server) DeleteFunc(baseDN string, f Deleter) {
	server.DeleteFns[baseDN] = f
}

func (server *Server) ModifyDNFunc(baseDN string, f ModifyDNr) {
	server.ModifyDNFns[baseDN] = f
}

func (server *Server) CompareFunc(baseDN string, f Comparer) {
	server.CompareFns[baseDN] = f
}

func (server *Server) AbandonFunc(baseDN string, f Abandoner) {
	server.AbandonFns[baseDN] = f
}

func (server *Server) ExtendedFunc(baseDN string, f Extender) {
	server.ExtendedFns[baseDN] = f
}

func (server *Server) UnbindFunc(baseDN string, f Unbinder) {
	server.UnbindFns[baseDN] = f
}

func (server *Server) CloseFunc(baseDN string, f Closer) {
	server.CloseFns[baseDN] = f
}

func (server *Server) QuitChannel(quit chan bool) {
	server.Quit = quit
}

func (server *Server) ListenAndServeTLS(listenString string, certFile string, keyFile string) error {
	cert, err := tls.LoadX509KeyPair(certFile, keyFile)
	if err != nil {
		return err
	}
	tlsConfig := &tls.Config{Certificates: []tls.Certificate{cert}}
	tlsConfig.ServerName = "localhost"
	ln, err := tls.Listen("tcp", listenString, tlsConfig)
	if err != nil {
		return err
	}
	err = server.Serve(ln)
	if err != nil {
		return err
	}
	return nil
}

func (server *Server) SetStats(enable bool) {
	if enable {
		server.Stats = &Stats{}
	} else {
		server.Stats = nil
	}
}

func (server *Server) GetStats() Stats {
	defer func() {
		server.Stats.statsMutex.Unlock()
	}()
	server.Stats.statsMutex.Lock()
	return *server.Stats
}

func (server *Server) ListenAndServe(listenString string) error {
	ln, err := net.Listen("tcp", listenString)
	if err != nil {
		return err
	}
	err = server.Serve(ln)
	if err != nil {
		return err
	}
	return nil
}

func (server *Server) Serve(ln net.Listener) error {
	newConn := make(chan net.Conn)
	go func() {
		for {
			conn, err := ln.Accept()
			if err != nil {
				if !strings.HasSuffix(err.Error(), "use of closed network connection") {
					log.Printf("Error accepting network connection: %s", err.Error())
				}
				break
			}
			newConn <- conn
		}
	}()

listener:
	for {
		select {
		case c := <-newConn:
			server.Stats.countConns(1)
			go server.handleConnection(c)
		case <-server.Quit:
			ln.Close()
			break listener
		}
	}
	return nil
}

func (server *Server) handleConnection(conn net.Conn) {
	boundDN := "" // "" == anonymous
	// If we're listening on SSL and get a new connection it'll already be tls.Conn
	// otherwise if we're doing StartTLS then the connection might have already
	// been upgraded
	_, connectionTLSActive := conn.(*tls.Conn)
handler:
	for {
		// read incoming LDAP packet
		packet, err := ber.ReadPacket(conn)
		if err == io.EOF { // Client closed connection
			break
		} else if err != nil {
			log.Printf("handleConnection ber.ReadPacket ERROR: %s", err.Error())
			break
		}

		// sanity check this packet
		if len(packet.Children) < 2 {
			log.Print("len(packet.Children) < 2")
			break
		}
		// check the message ID and ClassType
		messageID, ok := packet.Children[0].Value.(uint64)
		if !ok {
			log.Print("malformed messageID")
			break
		}
		req := packet.Children[1]
		if req.ClassType != ber.ClassApplication {
			log.Print("req.ClassType != ber.ClassApplication")
			break
		}
		// handle controls if present
		controls := []Control{}
		if len(packet.Children) > 2 {
			for _, child := range packet.Children[2].Children {
				controls = append(controls, DecodeControl(child))
			}
		}

		// log.Printf("DEBUG: handling operation: %s [%d]", ApplicationMap[req.Tag], req.Tag)
		// ber.PrintPacket(packet) // DEBUG

		// dispatch the LDAP operation
		switch req.Tag { // ldap op code
		default:
			responsePacket := encodeLDAPResponse(messageID, ApplicationAddResponse, LDAPResultOperationsError, "Unsupported operation: add")
			if err = sendPacket(conn, responsePacket); err != nil {
				log.Printf("sendPacket error %s", err.Error())
			}
			log.Printf("Unhandled operation: %s [%d]", ApplicationMap[req.Tag], req.Tag)
			break handler

		case ApplicationBindRequest:
			server.Stats.countBinds(1)
			ldapResultCode := HandleBindRequest(req, server.BindFns, conn)
			if ldapResultCode == LDAPResultSuccess {
				boundDN, ok = req.Children[1].Value.(string)
				if !ok {
					log.Printf("Malformed Bind DN")
					break handler
				}
			}
			responsePacket := encodeBindResponse(messageID, ldapResultCode)
			if err = sendPacket(conn, responsePacket); err != nil {
				log.Printf("sendPacket error %s", err.Error())
				break handler
			}
		case ApplicationSearchRequest:
			server.Stats.countSearches(1)
			if err := HandleSearchRequest(req, &controls, messageID, boundDN, server, conn); err != nil {
				log.Printf("handleSearchRequest error %s", err.Error()) // TODO: make this more testable/better err handling - stop using log, stop using breaks?
				e := err.(*Error)
				if err = sendPacket(conn, encodeSearchDone(messageID, e.ResultCode)); err != nil {
					log.Printf("sendPacket error %s", err.Error())
					break handler
				}
				break handler
			} else {
				if err = sendPacket(conn, encodeSearchDone(messageID, LDAPResultSuccess)); err != nil {
					log.Printf("sendPacket error %s", err.Error())
					break handler
				}
			}
		case ApplicationUnbindRequest:
			server.Stats.countUnbinds(1)
			break handler // simply disconnect
		case ApplicationExtendedRequest:
			if len(req.Children) == 1 {
				name := ber.DecodeString(req.Children[0].Data.Bytes())
				if name == "1.3.6.1.4.1.1466.20037" && server.StartTLS != nil && !connectionTLSActive {
					responseType := uint8(ApplicationExtendedResponse)
					// start tls
					// log.Println("START_TLS")
					// ber.PrintPacket(req)
					ldapResultCode := LDAPResultCode(LDAPResultSuccess)
					responsePacket := ber.Encode(ber.ClassUniversal, ber.TypeConstructed, ber.TagSequence, nil, "LDAP Response")
					responsePacket.AppendChild(ber.NewInteger(ber.ClassUniversal, ber.TypePrimitive, ber.TagInteger, messageID, "Message ID"))
					response := ber.Encode(ber.ClassApplication, ber.TypeConstructed, responseType, nil, ApplicationMap[responseType])
					response.AppendChild(ber.NewInteger(ber.ClassUniversal, ber.TypePrimitive, ber.TagEnumerated, uint64(ldapResultCode), "resultCode: "))
					response.AppendChild(ber.NewString(ber.ClassUniversal, ber.TypePrimitive, ber.TagOctetString, "", "matchedDN: "))
					response.AppendChild(ber.NewString(ber.ClassUniversal, ber.TypePrimitive, ber.TagOctetString, "", "errorMessage: "))
					// No clue what 0x8a is, seems to be correct from testing
					// value taken from looking at Samba's StartTLS via wireshark
					response.AppendChild(ber.NewString(ber.ClassUniversal, ber.TypePrimitive, 0x8a, name, "responseName: "))
					responsePacket.AppendChild(response)
					// log.Println("START_TLS response")
					// ber.PrintPacket(responsePacket)
					if err = sendPacket(conn, responsePacket); err != nil {
						log.Printf("sendPacket error %s", err.Error())
						break handler
					}
					connectionTLSActive = true
					conn = tls.Server(conn, server.StartTLS)
					break
				}
			}
			ldapResultCode := HandleExtendedRequest(req, boundDN, server.ExtendedFns, conn)
			responsePacket := encodeLDAPResponse(messageID, ApplicationExtendedResponse, ldapResultCode, LDAPResultCodeMap[ldapResultCode])
			if err = sendPacket(conn, responsePacket); err != nil {
				log.Printf("sendPacket error %s", err.Error())
				break handler
			}
		case ApplicationAbandonRequest:
			HandleAbandonRequest(req, boundDN, server.AbandonFns, conn)
			break handler

		case ApplicationAddRequest:
			ldapResultCode := HandleAddRequest(req, boundDN, server.AddFns, conn)
			responsePacket := encodeLDAPResponse(messageID, ApplicationAddResponse, ldapResultCode, LDAPResultCodeMap[ldapResultCode])
			if err = sendPacket(conn, responsePacket); err != nil {
				log.Printf("sendPacket error %s", err.Error())
				break handler
			}
		case ApplicationModifyRequest:
			ldapResultCode := HandleModifyRequest(req, boundDN, server.ModifyFns, conn)
			responsePacket := encodeLDAPResponse(messageID, ApplicationModifyResponse, ldapResultCode, LDAPResultCodeMap[ldapResultCode])
			if err = sendPacket(conn, responsePacket); err != nil {
				log.Printf("sendPacket error %s", err.Error())
				break handler
			}
		case ApplicationDelRequest:
			ldapResultCode := HandleDeleteRequest(req, boundDN, server.DeleteFns, conn)
			responsePacket := encodeLDAPResponse(messageID, ApplicationDelResponse, ldapResultCode, LDAPResultCodeMap[ldapResultCode])
			if err = sendPacket(conn, responsePacket); err != nil {
				log.Printf("sendPacket error %s", err.Error())
				break handler
			}
		case ApplicationModifyDNRequest:
			ldapResultCode := HandleModifyDNRequest(req, boundDN, server.ModifyDNFns, conn)
			responsePacket := encodeLDAPResponse(messageID, ApplicationModifyDNResponse, ldapResultCode, LDAPResultCodeMap[ldapResultCode])
			if err = sendPacket(conn, responsePacket); err != nil {
				log.Printf("sendPacket error %s", err.Error())
				break handler
			}
		case ApplicationCompareRequest:
			ldapResultCode := HandleCompareRequest(req, boundDN, server.CompareFns, conn)
			responsePacket := encodeLDAPResponse(messageID, ApplicationCompareResponse, ldapResultCode, LDAPResultCodeMap[ldapResultCode])
			if err = sendPacket(conn, responsePacket); err != nil {
				log.Printf("sendPacket error %s", err.Error())
				break handler
			}
		}
	}

	for _, c := range server.CloseFns {
		c.Close(boundDN, conn)
	}

	conn.Close()
}

func sendPacket(conn net.Conn, packet *ber.Packet) error {
	_, err := conn.Write(packet.Bytes())
	if err != nil {
		log.Printf("Error Sending Message: %s", err.Error())
		return err
	}
	return nil
}

func routeFunc(dn string, funcNames []string) string {
	bestPick := ""
	bestPickWeight := 0
	dnMatch := "," + strings.ToLower(dn)
	var weight int
	for _, fn := range funcNames {
		if strings.HasSuffix(dnMatch, ","+fn) {
			//  empty string as 0, no-comma string 1 , etc
			if fn == "" {
				weight = 0
			} else {
				weight = strings.Count(fn, ",") + 1
			}
			if weight > bestPickWeight {
				bestPick = fn
				bestPickWeight = weight
			}
		}
	}
	return bestPick
}

func encodeLDAPResponse(messageID uint64, responseType uint8, ldapResultCode LDAPResultCode, message string) *ber.Packet {
	responsePacket := ber.Encode(ber.ClassUniversal, ber.TypeConstructed, ber.TagSequence, nil, "LDAP Response")
	responsePacket.AppendChild(ber.NewInteger(ber.ClassUniversal, ber.TypePrimitive, ber.TagInteger, messageID, "Message ID"))
	reponse := ber.Encode(ber.ClassApplication, ber.TypeConstructed, responseType, nil, ApplicationMap[responseType])
	reponse.AppendChild(ber.NewInteger(ber.ClassUniversal, ber.TypePrimitive, ber.TagEnumerated, uint64(ldapResultCode), "resultCode: "))
	reponse.AppendChild(ber.NewString(ber.ClassUniversal, ber.TypePrimitive, ber.TagOctetString, "", "matchedDN: "))
	reponse.AppendChild(ber.NewString(ber.ClassUniversal, ber.TypePrimitive, ber.TagOctetString, message, "errorMessage: "))
	responsePacket.AppendChild(reponse)
	return responsePacket
}

type defaultHandler struct{}

func (h defaultHandler) Bind(bindDN, bindSimplePw string, conn net.Conn) (LDAPResultCode, error) {
	return LDAPResultInvalidCredentials, nil
}

func (h defaultHandler) Search(boundDN string, req SearchRequest, conn net.Conn) (ServerSearchResult, error) {
	return ServerSearchResult{make([]*Entry, 0), []string{}, []Control{}, LDAPResultSuccess}, nil
}

func (h defaultHandler) Add(boundDN string, req AddRequest, conn net.Conn) (LDAPResultCode, error) {
	return LDAPResultInsufficientAccessRights, nil
}

func (h defaultHandler) Modify(boundDN string, req ModifyRequest, conn net.Conn) (LDAPResultCode, error) {
	return LDAPResultInsufficientAccessRights, nil
}

func (h defaultHandler) Delete(boundDN, deleteDN string, conn net.Conn) (LDAPResultCode, error) {
	return LDAPResultInsufficientAccessRights, nil
}

func (h defaultHandler) ModifyDN(boundDN string, req ModifyDNRequest, conn net.Conn) (LDAPResultCode, error) {
	return LDAPResultInsufficientAccessRights, nil
}

func (h defaultHandler) Compare(boundDN string, req CompareRequest, conn net.Conn) (LDAPResultCode, error) {
	return LDAPResultInsufficientAccessRights, nil
}

func (h defaultHandler) Abandon(boundDN string, conn net.Conn) error {
	return nil
}

func (h defaultHandler) Extended(boundDN string, req ExtendedRequest, conn net.Conn) (LDAPResultCode, error) {
	return LDAPResultProtocolError, nil
}

func (h defaultHandler) Unbind(boundDN string, conn net.Conn) (LDAPResultCode, error) {
	return LDAPResultSuccess, nil
}

func (h defaultHandler) Close(boundDN string, conn net.Conn) error {
	conn.Close()
	return nil
}

func (stats *Stats) countConns(delta int) {
	if stats != nil {
		stats.statsMutex.Lock()
		stats.Conns += delta
		stats.statsMutex.Unlock()
	}
}

func (stats *Stats) countBinds(delta int) {
	if stats != nil {
		stats.statsMutex.Lock()
		stats.Binds += delta
		stats.statsMutex.Unlock()
	}
}

func (stats *Stats) countUnbinds(delta int) {
	if stats != nil {
		stats.statsMutex.Lock()
		stats.Unbinds += delta
		stats.statsMutex.Unlock()
	}
}

func (stats *Stats) countSearches(delta int) {
	if stats != nil {
		stats.statsMutex.Lock()
		stats.Searches += delta
		stats.statsMutex.Unlock()
	}
}

//
