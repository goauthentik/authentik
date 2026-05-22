package radius

import (
	"beryju.io/radius-eap/protocol"
	"github.com/sirupsen/logrus"
)

// Fields loosely represents key value pairs that adds context to log lines. The key has to be type of string, whereas
// value can be an arbitrary object.
type Fields []any

// Iterator returns iterator that allows iterating over pair of elements representing field.
// If number of elements is uneven, last element won't be included will be assumed as key with empty string value.
// If key is not string, At will panic.
func (f Fields) Iterator() *iter {
	// We start from -2 as we iterate over two items per iteration and first iteration will advance iterator to 0.
	return &iter{i: -2, f: f}
}

type iter struct {
	f Fields
	i int
}

func (i *iter) Next() bool {
	if i.i >= len(i.f) {
		return false
	}

	i.i += 2
	return i.i < len(i.f)
}

func (i *iter) At() (k string, v any) {
	if i.i < 0 || i.i >= len(i.f) {
		return "", ""
	}

	if i.i+1 == len(i.f) {
		// Non even number of elements, add empty string.
		return i.f[i.i].(string), ""
	}
	return i.f[i.i].(string), i.f[i.i+1]
}

type logrusAdapter struct {
	entry *logrus.Entry
}

func (l *logrusAdapter) fields(args ...any) map[string]any {
	f := make(map[string]any, len(args)/2)
	i := Fields(args).Iterator()
	for i.Next() {
		k, v := i.At()
		f[k] = v
	}
	return f
}

func (l *logrusAdapter) Debug(msg string, args ...any) {
	l.entry.WithFields(l.fields(args...)).Debug(msg)
}
func (l *logrusAdapter) Info(msg string, args ...any) {
	l.entry.WithFields(l.fields(args...)).Info(msg)
}
func (l *logrusAdapter) Warn(msg string, args ...any) {
	l.entry.WithFields(l.fields(args...)).Warn(msg)
}
func (l *logrusAdapter) Error(msg string, args ...any) {
	l.entry.WithFields(l.fields(args...)).Error(msg)
}
func (l *logrusAdapter) With(args ...any) protocol.Logger {
	return &logrusAdapter{l.entry.WithFields(l.fields(args...))}
}
