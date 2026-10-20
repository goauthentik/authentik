package connection

import (
	"encoding/json"
	"errors"
	"io"
	"os"
	"path"
	"sort"
	"strings"
	"unicode"
)

const fileListPrefix = "0.authentik.list."
const maxDirectoryReply = 128 * 1024

type directoryRequest struct {
	Request string `json:"request"`
	Path    string `json:"path"`
	Cursor  string `json:"cursor"`
}

type directoryEntry struct {
	Name string `json:"name"`
	Path string `json:"path"`
	Kind string `json:"kind"`
	Size *int64 `json:"size"`
}

type directoryResponse struct {
	Request string           `json:"request"`
	Status  int              `json:"status"`
	Entries []directoryEntry `json:"entries"`
	Cursor  string           `json:"cursor,omitempty"`
}

// listDirectory reads only the redirected drive and excludes symlinks and
// special files. A cursor names the last entry in the previous page.
func listDirectory(drivePath string, request directoryRequest) directoryResponse {
	response := directoryResponse{Request: request.Request, Status: 400, Entries: []directoryEntry{}}
	if len(request.Request) != 32 || !validVirtualPath(request.Path) ||
		strings.ContainsAny(request.Cursor, "/\\\x00") {
		return response
	}
	if drivePath == "" {
		response.Status = 404
		return response
	}
	root, err := os.OpenRoot(drivePath)
	if err != nil {
		response.Status = 503
		return response
	}
	defer func() { _ = root.Close() }()
	relative := strings.TrimPrefix(request.Path, "/")
	if relative == "" {
		relative = "."
	}
	directory, err := root.Open(relative)
	if err != nil {
		response.Status = 404
		return response
	}
	defer func() { _ = directory.Close() }()
	info, err := directory.Stat()
	if err != nil || !info.IsDir() {
		response.Status = 404
		return response
	}
	// Read directory names in batches. Keep only the first 201 valid entries
	// after the cursor so a large shared drive cannot grow this response or
	// the list's working set without bound.
	candidates := make([]directoryEntry, 0, 201)
	for {
		names, readErr := directory.Readdirnames(256)
		for _, name := range names {
			if name <= request.Cursor || strings.Contains(name, "/") {
				continue
			}
			virtual := path.Join(request.Path, name)
			if !validVirtualPath(virtual) {
				continue
			}
			entryInfo, statErr := root.Lstat(strings.TrimPrefix(virtual, "/"))
			if statErr != nil {
				continue
			}
			entry := directoryEntry{Name: name, Path: virtual}
			switch {
			case entryInfo.Mode().IsRegular():
				entry.Kind = "file"
				size := entryInfo.Size()
				entry.Size = &size
			case entryInfo.IsDir():
				entry.Kind = "directory"
			default:
				continue
			}
			position := sort.Search(len(candidates), func(index int) bool {
				return candidates[index].Name >= name
			})
			if position >= 201 {
				continue
			}
			candidates = append(candidates, directoryEntry{})
			copy(candidates[position+1:], candidates[position:])
			candidates[position] = entry
			if len(candidates) > 201 {
				candidates = candidates[:201]
			}
		}
		if errors.Is(readErr, io.EOF) {
			break
		}
		if readErr != nil {
			response.Status = 503
			return response
		}
	}
	// The Channels message carrying this control reply has a 128 KiB limit.
	// Deep virtual paths can make 200 entries exceed it, so end the page at
	// the last name that fits and let the next request continue from there.
	used := 1024 // Reserve space for request, status and cursor JSON fields.
	for index, entry := range candidates {
		encoded, marshalErr := json.Marshal(entry)
		if marshalErr != nil {
			response.Status = 503
			return response
		}
		if index == 200 || used+len(encoded)+1 > maxDirectoryReply {
			if len(response.Entries) == 0 {
				response.Status = 503
				return response
			}
			response.Cursor = response.Entries[len(response.Entries)-1].Name
			break
		}
		response.Entries = append(response.Entries, entry)
		used += len(encoded) + 1
	}
	response.Status = 200
	return response
}

func validVirtualPath(value string) bool {
	return len(value) <= 4096 && strings.HasPrefix(value, "/") && path.Clean(value) == value &&
		!strings.Contains(value, "\\") && strings.IndexFunc(value, unicode.IsControl) == -1
}

func (c *Connection) sendFileList(data []byte) error {
	var request directoryRequest
	if len(data) > 8192 || json.Unmarshal(data, &request) != nil {
		return nil
	}
	response, err := json.Marshal(listDirectory(c.drivePath, request))
	if err != nil {
		return err
	}
	return c.writeSocket(append([]byte(fileListPrefix), response...))
}
