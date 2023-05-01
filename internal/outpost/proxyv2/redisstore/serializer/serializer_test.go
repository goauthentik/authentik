package serializer

import (
	"reflect"
	"testing"

	"github.com/gorilla/sessions"
)

var (
	serializer SessionSerializer
	// Types not supported at top level by the Gob Encoder.
	unsupportedValues = map[interface{}]interface{}{
		make(chan int): func(a int) bool { return true },
	}
	// Data not supported for deserialization
	unsupportedData = []byte{0xfb, 0xa5, 0x82, 0x2f, 0xca, 0x1}
)

func newSession() *sessions.Session {
	st := sessions.NewFilesystemStore("")
	session := sessions.NewSession(st, "hello")
	session.Values["test"] = "hello"

	return session
}

func TestSerializeJSON(t *testing.T) {
	serializer = JSONSerializer{}
	_, err := serializer.Serialize(newSession())

	if err != nil {
		t.Fatal("failed to serialize session", err)
	}
}

func TestSerializeJSONFail(t *testing.T) {
	serializer = JSONSerializer{}
	session := newSession()
	session.Values[12] = 5
	_, err := serializer.Serialize(session)

	if err == nil {
		t.Fatal("serialization should have failed", err)
	}
}

func TestDeserializeJSON(t *testing.T) {
	serializer = JSONSerializer{}
	origSession := newSession()
	data, err := serializer.Serialize(origSession)

	if err != nil {
		t.Fatal("failed to serialize session", err)
	}

	deserealizedSession := &sessions.Session{}
	err = serializer.Deserialize(data, deserealizedSession)

	if err != nil {
		t.Fatal("failed to deserialize session", err)
	}

	if !reflect.DeepEqual(origSession.Values, deserealizedSession.Values) {
		t.Fatal("deserialized session does not equal original session", err)
	}
}

func TestDeserializeJSONFail(t *testing.T) {
	serializer = JSONSerializer{}
	b := []byte{0xfb, 0xa5, 0x82, 0x2f, 0xca, 0x1}
	if err := serializer.Deserialize(b, &sessions.Session{}); err == nil {
		t.Error("expected error from invalid data for deserialization")
	} else if err.Error() != "invalid character 'û' looking for beginning of value" {
		t.Error("expected error from invalid character; got", err)
	}
}

func TestSerializeGob(t *testing.T) {
	serializer = GobSerializer{}
	_, err := serializer.Serialize(newSession())

	if err != nil {
		t.Fatal("failed to serialize session", err)
	}
}

func TestSerializeGobFail(t *testing.T) {
	serializer = GobSerializer{}
	session := newSession()
	session.Values = unsupportedValues
	_, err := serializer.Serialize(session)

	if err == nil {
		t.Fatal("serialization should have failed", err)
	}
}

func TestDeserializeGob(t *testing.T) {
	serializer = GobSerializer{}
	origSession := newSession()
	data, err := serializer.Serialize(origSession)

	if err != nil {
		t.Fatal("failed to serialize session", err)
	}

	deserealizedSession := &sessions.Session{}
	err = serializer.Deserialize(data, deserealizedSession)

	if err != nil {
		t.Fatal("failed to deserialize session", err)
	}

	if !reflect.DeepEqual(origSession.Values, deserealizedSession.Values) {
		t.Fatal("deserialized session does not equal original session", err)
	}
}

func TestDeserializeGobFail(t *testing.T) {
	serializer = GobSerializer{}

	if err := serializer.Deserialize(unsupportedData, &sessions.Session{}); err == nil {
		t.Error("expected error from invalid data for deserialization")
	} else if err.Error() != "invalid message length" {
		t.Error("expected error from invalid data length; got", err)
	}
}