// Copyright 2011 The Go Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package ldap

import (
	"errors"
	"fmt"
	"strings"
	"unicode/utf8"

	ber "github.com/nmcclain/asn1-ber"
)

const (
	FilterAnd             = 0
	FilterOr              = 1
	FilterNot             = 2
	FilterEqualityMatch   = 3
	FilterSubstrings      = 4
	FilterGreaterOrEqual  = 5
	FilterLessOrEqual     = 6
	FilterPresent         = 7
	FilterApproxMatch     = 8
	FilterExtensibleMatch = 9
)

var FilterMap = map[uint8]string{
	FilterAnd:             "And",
	FilterOr:              "Or",
	FilterNot:             "Not",
	FilterEqualityMatch:   "Equality Match",
	FilterSubstrings:      "Substrings",
	FilterGreaterOrEqual:  "Greater Or Equal",
	FilterLessOrEqual:     "Less Or Equal",
	FilterPresent:         "Present",
	FilterApproxMatch:     "Approx Match",
	FilterExtensibleMatch: "Extensible Match",
}

const (
	FilterSubstringsInitial = 0
	FilterSubstringsAny     = 1
	FilterSubstringsFinal   = 2
)

func CompileFilter(filter string) (*ber.Packet, error) {
	if len(filter) == 0 || filter[0] != '(' {
		return nil, NewError(ErrorFilterCompile, errors.New("ldap: filter does not start with an '('"))
	}
	packet, pos, err := compileFilter(filter, 1)
	if err != nil {
		return nil, err
	}
	if pos != len(filter) {
		return nil, NewError(ErrorFilterCompile, errors.New("ldap: finished compiling filter with extra at end: "+fmt.Sprint(filter[pos:])))
	}
	return packet, nil
}

func DecompileFilter(packet *ber.Packet) (ret string, err error) {
	defer func() {
		if r := recover(); r != nil {
			err = NewError(ErrorFilterDecompile, errors.New("ldap: error decompiling filter"))
		}
	}()
	ret = "("
	err = nil
	childStr := ""

	switch packet.Tag {
	case FilterAnd:
		ret += "&"
		for _, child := range packet.Children {
			childStr, err = DecompileFilter(child)
			if err != nil {
				return
			}
			ret += childStr
		}
	case FilterOr:
		ret += "|"
		for _, child := range packet.Children {
			childStr, err = DecompileFilter(child)
			if err != nil {
				return
			}
			ret += childStr
		}
	case FilterNot:
		ret += "!"
		childStr, err = DecompileFilter(packet.Children[0])
		if err != nil {
			return
		}
		ret += childStr

	case FilterSubstrings:
		ret += ber.DecodeString(packet.Children[0].Data.Bytes())
		ret += "="
		switch packet.Children[1].Children[0].Tag {
		case FilterSubstringsInitial:
			ret += ber.DecodeString(packet.Children[1].Children[0].Data.Bytes()) + "*"
		case FilterSubstringsAny:
			ret += "*" + ber.DecodeString(packet.Children[1].Children[0].Data.Bytes()) + "*"
		case FilterSubstringsFinal:
			ret += "*" + ber.DecodeString(packet.Children[1].Children[0].Data.Bytes())
		}
	case FilterEqualityMatch:
		ret += ber.DecodeString(packet.Children[0].Data.Bytes())
		ret += "="
		ret += ber.DecodeString(packet.Children[1].Data.Bytes())
	case FilterGreaterOrEqual:
		ret += ber.DecodeString(packet.Children[0].Data.Bytes())
		ret += ">="
		ret += ber.DecodeString(packet.Children[1].Data.Bytes())
	case FilterLessOrEqual:
		ret += ber.DecodeString(packet.Children[0].Data.Bytes())
		ret += "<="
		ret += ber.DecodeString(packet.Children[1].Data.Bytes())
	case FilterPresent:
		ret += ber.DecodeString(packet.Data.Bytes())
		ret += "=*"
	case FilterApproxMatch:
		ret += ber.DecodeString(packet.Children[0].Data.Bytes())
		ret += "~="
		ret += ber.DecodeString(packet.Children[1].Data.Bytes())
	}

	ret += ")"
	return
}

func compileFilterSet(filter string, pos int, parent *ber.Packet) (int, error) {
	for pos < len(filter) && filter[pos] == '(' {
		child, newPos, err := compileFilter(filter, pos+1)
		if err != nil {
			return pos, err
		}
		pos = newPos
		parent.AppendChild(child)
	}
	if pos == len(filter) {
		return pos, NewError(ErrorFilterCompile, errors.New("ldap: unexpected end of filter"))
	}

	return pos + 1, nil
}

func compileFilter(filter string, pos int) (*ber.Packet, int, error) {
	var packet *ber.Packet
	var err error

	defer func() {
		if r := recover(); r != nil {
			err = NewError(ErrorFilterCompile, errors.New("ldap: error compiling filter"))
		}
	}()

	newPos := pos
	switch filter[pos] {
	case '(':
		packet, newPos, err = compileFilter(filter, pos+1)
		newPos++
		return packet, newPos, err
	case '&':
		packet = ber.Encode(ber.ClassContext, ber.TypeConstructed, FilterAnd, nil, FilterMap[FilterAnd])
		newPos, err = compileFilterSet(filter, pos+1, packet)
		return packet, newPos, err
	case '|':
		packet = ber.Encode(ber.ClassContext, ber.TypeConstructed, FilterOr, nil, FilterMap[FilterOr])
		newPos, err = compileFilterSet(filter, pos+1, packet)
		return packet, newPos, err
	case '!':
		packet = ber.Encode(ber.ClassContext, ber.TypeConstructed, FilterNot, nil, FilterMap[FilterNot])
		var child *ber.Packet
		child, newPos, err = compileFilter(filter, pos+1)
		packet.AppendChild(child)
		return packet, newPos, err
	default:
		attribute := ""
		condition := ""

		for w := 0; newPos < len(filter) && filter[newPos] != ')'; newPos += w {
			rune, width := utf8.DecodeRuneInString(filter[newPos:])
			w = width
			switch {
			case packet != nil:
				condition += fmt.Sprintf("%c", rune)
			case filter[newPos] == '=':
				packet = ber.Encode(ber.ClassContext, ber.TypeConstructed, FilterEqualityMatch, nil, FilterMap[FilterEqualityMatch])
			case filter[newPos] == '>' && filter[newPos+1] == '=':
				packet = ber.Encode(ber.ClassContext, ber.TypeConstructed, FilterGreaterOrEqual, nil, FilterMap[FilterGreaterOrEqual])
				newPos++
			case filter[newPos] == '<' && filter[newPos+1] == '=':
				packet = ber.Encode(ber.ClassContext, ber.TypeConstructed, FilterLessOrEqual, nil, FilterMap[FilterLessOrEqual])
				newPos++
			case filter[newPos] == '~' && filter[newPos+1] == '=':
				packet = ber.Encode(ber.ClassContext, ber.TypeConstructed, FilterApproxMatch, nil, FilterMap[FilterLessOrEqual])
				newPos++
			case packet == nil:
				attribute += fmt.Sprintf("%c", filter[newPos])
			}
		}
		if newPos == len(filter) {
			err = NewError(ErrorFilterCompile, errors.New("ldap: unexpected end of filter"))
			return packet, newPos, err
		}
		if packet == nil {
			err = NewError(ErrorFilterCompile, errors.New("ldap: error parsing filter"))
			return packet, newPos, err
		}
		// Handle FilterEqualityMatch as a separate case (is primitive, not constructed like the other filters)
		if packet.Tag == FilterEqualityMatch && condition == "*" {
			packet.TagType = ber.TypePrimitive
			packet.Tag = FilterPresent
			packet.Description = FilterMap[packet.Tag]
			packet.Data.WriteString(attribute)
			return packet, newPos + 1, nil
		}
		packet.AppendChild(ber.NewString(ber.ClassUniversal, ber.TypePrimitive, ber.TagOctetString, attribute, "Attribute"))
		switch {
		case packet.Tag == FilterEqualityMatch && condition[0] == '*' && condition[len(condition)-1] == '*':
			// Any
			packet.Tag = FilterSubstrings
			packet.Description = FilterMap[packet.Tag]
			seq := ber.Encode(ber.ClassUniversal, ber.TypeConstructed, ber.TagSequence, nil, "Substrings")
			seq.AppendChild(ber.NewString(ber.ClassContext, ber.TypePrimitive, FilterSubstringsAny, condition[1:len(condition)-1], "Any Substring"))
			packet.AppendChild(seq)
		case packet.Tag == FilterEqualityMatch && condition[0] == '*':
			// Final
			packet.Tag = FilterSubstrings
			packet.Description = FilterMap[packet.Tag]
			seq := ber.Encode(ber.ClassUniversal, ber.TypeConstructed, ber.TagSequence, nil, "Substrings")
			seq.AppendChild(ber.NewString(ber.ClassContext, ber.TypePrimitive, FilterSubstringsFinal, condition[1:], "Final Substring"))
			packet.AppendChild(seq)
		case packet.Tag == FilterEqualityMatch && condition[len(condition)-1] == '*':
			// Initial
			packet.Tag = FilterSubstrings
			packet.Description = FilterMap[packet.Tag]
			seq := ber.Encode(ber.ClassUniversal, ber.TypeConstructed, ber.TagSequence, nil, "Substrings")
			seq.AppendChild(ber.NewString(ber.ClassContext, ber.TypePrimitive, FilterSubstringsInitial, condition[:len(condition)-1], "Initial Substring"))
			packet.AppendChild(seq)
		default:
			packet.AppendChild(ber.NewString(ber.ClassUniversal, ber.TypePrimitive, ber.TagOctetString, condition, "Condition"))
		}
		newPos++
		return packet, newPos, err
	}
}

func ServerApplyFilter(f *ber.Packet, entry *Entry) (bool, LDAPResultCode) {
	switch FilterMap[f.Tag] {
	default:
		// log.Fatalf("Unknown LDAP filter code: %d", f.Tag)
		return false, LDAPResultOperationsError
	case "Equality Match":
		if len(f.Children) != 2 {
			return false, LDAPResultOperationsError
		}
		attribute := f.Children[0].Value.(string)
		value := f.Children[1].Value.(string)
		for _, a := range entry.Attributes {
			if strings.EqualFold(a.Name, attribute) {
				for _, v := range a.Values {
					if strings.EqualFold(v, value) {
						return true, LDAPResultSuccess
					}
				}
			}
		}
	case "Present":
		for _, a := range entry.Attributes {
			if strings.EqualFold(a.Name, f.Data.String()) {
				return true, LDAPResultSuccess
			}
		}
	case "And":
		for _, child := range f.Children {
			ok, exitCode := ServerApplyFilter(child, entry)
			if exitCode != LDAPResultSuccess {
				return false, exitCode
			}
			if !ok {
				return false, LDAPResultSuccess
			}
		}
		return true, LDAPResultSuccess
	case "Or":
		anyOk := false
		for _, child := range f.Children {
			ok, exitCode := ServerApplyFilter(child, entry)
			if exitCode != LDAPResultSuccess {
				return false, exitCode
			} else if ok {
				anyOk = true
			}
		}
		if anyOk {
			return true, LDAPResultSuccess
		}
	case "Not":
		if len(f.Children) != 1 {
			return false, LDAPResultOperationsError
		}
		ok, exitCode := ServerApplyFilter(f.Children[0], entry)
		if exitCode != LDAPResultSuccess {
			return false, exitCode
		} else if !ok {
			return true, LDAPResultSuccess
		}
	case "Substrings":
		if len(f.Children) != 2 {
			return false, LDAPResultOperationsError
		}
		attribute := f.Children[0].Value.(string)
		valueBytes := f.Children[1].Children[0].Data.Bytes()
		valueLower := strings.ToLower(string(valueBytes[:]))
		for _, a := range entry.Attributes {
			if strings.ToLower(a.Name) == strings.ToLower(attribute) {
				for _, v := range a.Values {
					vLower := strings.ToLower(v)
					switch f.Children[1].Children[0].Tag {
					case FilterSubstringsInitial:
						if strings.HasPrefix(vLower, valueLower) {
							return true, LDAPResultSuccess
						}
					case FilterSubstringsAny:
						if strings.Contains(vLower, valueLower) {
							return true, LDAPResultSuccess
						}
					case FilterSubstringsFinal:
						if strings.HasSuffix(vLower, valueLower) {
							return true, LDAPResultSuccess
						}
					}
				}
			}
		}
	case "FilterGreaterOrEqual": // TODO
		return false, LDAPResultOperationsError
	case "FilterLessOrEqual": // TODO
		return false, LDAPResultOperationsError
	case "FilterApproxMatch": // TODO
		return false, LDAPResultOperationsError
	case "FilterExtensibleMatch": // TODO
		return false, LDAPResultOperationsError
	}

	return false, LDAPResultSuccess
}

func GetFilterObjectClass(filter string) (string, error) {
	f, err := CompileFilter(filter)
	if err != nil {
		return "", err
	}
	return parseFilterObjectClass(f)
}

func parseFilterObjectClass(f *ber.Packet) (string, error) {
	objectClass := ""
	switch FilterMap[f.Tag] {
	case "Equality Match":
		if len(f.Children) != 2 {
			return "", errors.New("Equality match must have only two children")
		}
		attribute := strings.ToLower(f.Children[0].Value.(string))
		value := f.Children[1].Value.(string)
		if attribute == "objectclass" {
			objectClass = strings.ToLower(value)
		}
	case "And":
		for _, child := range f.Children {
			subType, err := parseFilterObjectClass(child)
			if err != nil {
				return "", err
			}
			if len(subType) > 0 {
				objectClass = subType
			}
		}
	case "Or":
		for _, child := range f.Children {
			subType, err := parseFilterObjectClass(child)
			if err != nil {
				return "", err
			}
			if len(subType) > 0 {
				objectClass = subType
			}
		}
	case "Not":
		if len(f.Children) != 1 {
			return "", errors.New("Not filter must have only one child")
		}
		subType, err := parseFilterObjectClass(f.Children[0])
		if err != nil {
			return "", err
		}
		if len(subType) > 0 {
			objectClass = subType
		}

	}
	return strings.ToLower(objectClass), nil
}
