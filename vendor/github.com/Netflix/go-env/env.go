// Copyright 2018 Netflix, Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// Package env provides an `env` struct field tag to marshal and unmarshal
// environment variables.
package env

import (
	"errors"
	"fmt"
	"os"
	"reflect"
	"strconv"
	"strings"
	"time"
)

var (
	// ErrInvalidValue returned when the value passed to Unmarshal is nil or not a
	// pointer to a struct.
	ErrInvalidValue = errors.New("value must be a non-nil pointer to a struct")

	// ErrUnsupportedType returned when a field with tag "env" is unsupported.
	ErrUnsupportedType = errors.New("field is an unsupported type")

	// ErrUnexportedField returned when a field with tag "env" is not exported.
	ErrUnexportedField = errors.New("field must be exported")

	unmarshalType = reflect.TypeOf((*Unmarshaler)(nil)).Elem()
)

// ErrMissingRequiredValue returned when a field with required=true contains no value or default
type ErrMissingRequiredValue struct {
	Value string
}

func (e ErrMissingRequiredValue) Error() string {
	return fmt.Sprintf("value for this field is required [%s]", e.Value)
}

// Unmarshal parses an EnvSet and stores the result in the value pointed to by
// v. Fields that are matched in v will be deleted from EnvSet, resulting in
// an EnvSet with the remaining environment variables. If v is nil or not a
// pointer to a struct, Unmarshal returns an ErrInvalidValue.
//
// Fields tagged with "env" will have the unmarshalled EnvSet of the matching
// key from EnvSet. If the tagged field is not exported, Unmarshal returns
// ErrUnexportedField.
//
// If the field has a type that is unsupported, Unmarshal returns
// ErrUnsupportedType.
func Unmarshal(es EnvSet, v interface{}) error {
	rv := reflect.ValueOf(v)
	if rv.Kind() != reflect.Ptr || rv.IsNil() {
		return ErrInvalidValue
	}

	rv = rv.Elem()
	if rv.Kind() != reflect.Struct {
		return ErrInvalidValue
	}

	t := rv.Type()
	for i := 0; i < rv.NumField(); i++ {
		valueField := rv.Field(i)
		switch valueField.Kind() {
		case reflect.Struct:
			if !valueField.Addr().CanInterface() {
				continue
			}

			iface := valueField.Addr().Interface()
			err := Unmarshal(es, iface)
			if err != nil {
				return err
			}
		}

		typeField := t.Field(i)
		tag := typeField.Tag.Get("env")
		if tag == "" {
			continue
		}

		if !valueField.CanSet() {
			return ErrUnexportedField
		}

		envTag := parseTag(tag)

		var (
			envValue string
			ok       bool
		)
		for _, envKey := range envTag.Keys {
			envValue, ok = es[envKey]
			if ok {
				break
			}
		}

		if !ok {
			if envTag.Default != "" {
				envValue = envTag.Default
			} else if envTag.Required {
				return &ErrMissingRequiredValue{Value: envTag.Keys[0]}
			} else {
				continue
			}
		}

		err := set(typeField.Type, valueField, envValue)
		if err != nil {
			return err
		}
		delete(es, tag)
	}

	return nil
}

func set(t reflect.Type, f reflect.Value, value string) error {
	// See if the type implements Unmarshaler and use that first,
	// otherwise, fallback to the previous logic
	var isUnmarshaler bool
	isPtr := t.Kind() == reflect.Ptr
	if isPtr {
		isUnmarshaler = t.Implements(unmarshalType) && f.CanInterface()
	} else if f.CanAddr() {
		isUnmarshaler = f.Addr().Type().Implements(unmarshalType) && f.Addr().CanInterface()
	}

	if isUnmarshaler {
		var ptr reflect.Value
		if isPtr {
			// In the pointer case, we need to create a new element to have an
			// address to point to
			ptr = reflect.New(t.Elem())
		} else {
			// And for scalars, we need the pointer to be able to modify the value
			ptr = f.Addr()
		}
		if u, ok := ptr.Interface().(Unmarshaler); ok {
			if err := u.UnmarshalEnvironmentValue(value); err != nil {
				return err
			}
			if isPtr {
				f.Set(ptr)
			}
			return nil
		}
	}

	switch t.Kind() {
	case reflect.Ptr:
		ptr := reflect.New(t.Elem())
		err := set(t.Elem(), ptr.Elem(), value)
		if err != nil {
			return err
		}
		f.Set(ptr)
	case reflect.String:
		f.SetString(value)
	case reflect.Bool:
		v, err := strconv.ParseBool(value)
		if err != nil {
			return err
		}
		f.SetBool(v)
	case reflect.Float32:
		v, err := strconv.ParseFloat(value, 32)
		if err != nil {
			return err
		}
		f.SetFloat(v)
	case reflect.Float64:
		v, err := strconv.ParseFloat(value, 64)
		if err != nil {
			return err
		}
		f.SetFloat(v)
	case reflect.Int, reflect.Int8, reflect.Int16, reflect.Int32, reflect.Int64:
		if t.PkgPath() == "time" && t.Name() == "Duration" {
			duration, err := time.ParseDuration(value)
			if err != nil {
				return err
			}

			f.Set(reflect.ValueOf(duration))
			break
		}

		v, err := strconv.Atoi(value)
		if err != nil {
			return err
		}
		f.SetInt(int64(v))
	default:
		return ErrUnsupportedType
	}

	return nil
}

// UnmarshalFromEnviron parses an EnvSet from os.Environ and stores the result
// in the value pointed to by v. Fields that weren't matched in v are returned
// in an EnvSet with the remaining environment variables. If v is nil or not a
// pointer to a struct, UnmarshalFromEnviron returns an ErrInvalidValue.
//
// Fields tagged with "env" will have the unmarshalled EnvSet of the matching
// key from EnvSet. If the tagged field is not exported, UnmarshalFromEnviron
// returns ErrUnexportedField.
//
// If the field has a type that is unsupported, UnmarshalFromEnviron returns
// ErrUnsupportedType.
func UnmarshalFromEnviron(v interface{}) (EnvSet, error) {
	es, err := EnvironToEnvSet(os.Environ())
	if err != nil {
		return nil, err
	}

	return es, Unmarshal(es, v)
}

// Marshal returns an EnvSet of v. If v is nil or not a pointer, Marshal returns
// an ErrInvalidValue.
//
// Marshal uses fmt.Sprintf to transform encountered values to its default
// string format. Values without the "env" field tag are ignored.
//
// Nested structs are traversed recursively.
func Marshal(v interface{}) (EnvSet, error) {
	rv := reflect.ValueOf(v)
	if rv.Kind() != reflect.Ptr || rv.IsNil() {
		return nil, ErrInvalidValue
	}

	rv = rv.Elem()
	if rv.Kind() != reflect.Struct {
		return nil, ErrInvalidValue
	}

	es := make(EnvSet)
	t := rv.Type()
	for i := 0; i < rv.NumField(); i++ {
		valueField := rv.Field(i)
		switch valueField.Kind() {
		case reflect.Struct:
			if !valueField.Addr().CanInterface() {
				continue
			}

			iface := valueField.Addr().Interface()
			nes, err := Marshal(iface)
			if err != nil {
				return nil, err
			}

			for k, v := range nes {
				es[k] = v
			}
		}

		typeField := t.Field(i)
		tag := typeField.Tag.Get("env")
		if tag == "" {
			continue
		}

		envKeys := strings.Split(tag, ",")

		var el interface{}
		if typeField.Type.Kind() == reflect.Ptr {
			if valueField.IsNil() {
				continue
			}
			el = valueField.Elem().Interface()
		} else {
			el = valueField.Interface()
		}

		var err error
		var envValue string
		if m, ok := el.(Marshaler); ok {
			envValue, err = m.MarshalEnvironmentValue()
			if err != nil {
				return nil, err
			}
		} else {
			envValue = fmt.Sprintf("%v", el)
		}

		for _, envKey := range envKeys {
			es[envKey] = envValue
		}
	}

	return es, nil
}

type tag struct {
	Keys     []string
	Default  string
	Required bool
}

func parseTag(tagString string) tag {
	var t tag
	envKeys := strings.Split(tagString, ",")
	for _, key := range envKeys {
		if strings.Contains(key, "=") {
			keyData := strings.SplitN(key, "=", 2)
			switch strings.ToLower(keyData[0]) {
			case "default":
				t.Default = keyData[1]
			case "required":
				t.Required = strings.ToLower(keyData[1]) == "true"
			default:
				// just ignoring unsupported keys
				continue
			}
		} else {
			t.Keys = append(t.Keys, key)
		}
	}
	return t
}
