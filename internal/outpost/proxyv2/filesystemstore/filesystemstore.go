package filesystemstore

import (
	"context"
	"errors"
	"os"
	"path"
	"strings"
	"sync"
	"syscall"
	"time"

	"github.com/gorilla/sessions"
	log "github.com/sirupsen/logrus"

	"goauthentik.io/internal/outpost/proxyv2/sessionstore"
)

const (
	SessionCleanupInterval     = 5 * time.Minute
	SessionCleanupLockFileName = "session-cleanup.lock"
	SessionFilePrefix          = "session_"
	SessionTestFile            = SessionFilePrefix + "write_test"
)

var (
	ErrSessionCleanupAlreadyRunning = errors.New("session cleanup is already running by another instance")
	ErrSessionStoreNoPermission     = errors.New("path is not writable")
	ErrSessionStorePathNotExist     = errors.New("path does not exist")
)

type Store struct {
	*sessions.FilesystemStore
	storePath      string
	log            *log.Entry
	cleanupManager *sessionstore.CleanupManager
}

// NewStore checks if the specified store path exists, is writable and creates a new filesystem session store.
func NewStore(storePath string, keyPairs ...[]byte) (*Store, error) {
	if storePath == "" {
		storePath = os.TempDir()
	}

	// check if path exists
	_, err := os.ReadDir(storePath)
	if err != nil {
		if errors.Is(err, os.ErrNotExist) {
			return nil, ErrSessionStorePathNotExist
		}
		return nil, err
	}

	// check if path is writable
	testPath := path.Join(storePath, SessionTestFile)
	testFile, err := os.OpenFile(testPath, os.O_CREATE, 0600)
	if err != nil {
		if errors.Is(err, os.ErrPermission) {
			return nil, ErrSessionStoreNoPermission
		}
		return nil, err
	}
	if err = testFile.Close(); err != nil {
		return nil, err
	}
	if err = os.Remove(testPath); err != nil {
		return nil, err
	}

	store := &Store{
		FilesystemStore: sessions.NewFilesystemStore(storePath, keyPairs...),
		storePath:       storePath,
		log:             log.WithField("logger", "authentik.outpost.proxyv2.filesystemstore"),
	}

	return store, nil
}

// CleanupExpired implements the CleanupStore interface for use with CleanupManager
func (s *Store) CleanupExpired(ctx context.Context) error {
	return s.SessionCleanup(ctx)
}

// SessionCleanup acquires a file lock to ensure only one instance runs at a time,
// then checks and deletes expired session files from the filesystem session store.
// It supports context-based cancellation to allow graceful shutdowns or timeouts.
func (s *Store) SessionCleanup(ctx context.Context) error {
	s.log.Info("Starting session cleanup")
	lockPath := path.Join(s.storePath, SessionCleanupLockFileName)
	lockFile, err := os.OpenFile(lockPath, os.O_CREATE|os.O_RDWR, 0600)
	if err != nil {
		return err
	}
	defer func() {
		if closeErr := lockFile.Close(); closeErr != nil {
			s.log.WithError(closeErr).Warn("failed to close lock file")
		}
	}()

	err = syscall.Flock(int(lockFile.Fd()), syscall.LOCK_EX|syscall.LOCK_NB)
	if err != nil {
		if errno, ok := err.(syscall.Errno); ok && errno == syscall.EWOULDBLOCK {
			return ErrSessionCleanupAlreadyRunning
		}
		return err
	}
	defer func() {
		if flockErr := syscall.Flock(int(lockFile.Fd()), syscall.LOCK_UN); flockErr != nil {
			s.log.WithError(flockErr).Warn("failed to unlock file")
		}

		if removeErr := os.Remove(lockPath); removeErr != nil {
			s.log.WithError(removeErr).Warn("failed to remove lock file")
		}
	}()

	return s.sessionCleanup(ctx)
}

// sessionCleanup checks the modification time of all session files and removes them
// when they reach the configured maximum age in the session store.
// Since the FilesystemStore from Gorilla does not have a session cleanup function,
// it is only necessary for the filesystem session store.
func (s *Store) sessionCleanup(ctx context.Context) error {
	files, err := os.ReadDir(s.storePath)
	if err != nil {
		return err
	}

	var errs []error
	for _, file := range files {
		select {
		case <-ctx.Done():
			s.log.Warn("session cleanup interrupted during file processing")
			return ctx.Err()
		default:
		}

		if !strings.HasPrefix(file.Name(), SessionFilePrefix) {
			continue
		}

		fullPath := path.Join(s.storePath, file.Name())
		stat, err := os.Lstat(fullPath)
		if err != nil {
			s.log.WithError(err).WithField("path", fullPath).Warning("failed to read stats from file")
			errs = append(errs, err)
			continue
		}

		modTime := stat.ModTime()
		if time.Since(modTime) <= time.Duration(s.Options.MaxAge)*time.Second {
			s.log.WithField("max-age", s.Options.MaxAge).WithField("modified", modTime.String()).Debug("session still valid")
			continue
		}

		s.log.WithField("path", fullPath).WithField("modified", modTime.String()).Info("cleanup expired session")
		if err = os.Remove(fullPath); err != nil {
			s.log.WithError(err).WithField("path", fullPath).Warn("failed to delete session")
			errs = append(errs, err)
			continue
		}
	}
	return errors.Join(errs...)
}

var (
	globalStore *Store
	mu          sync.Mutex
)

// GetPersistentStore creates a new filesystem store if it is the first time the function has been called,
// or if the path string has changed. It then stores this in the globalStore variable.
// If the function is called multiple times, the store from the variable is returned to ensure that only one instance is running.
func GetPersistentStore(path string) (*Store, error) {
	mu.Lock()
	defer mu.Unlock()
	if globalStore == nil || globalStore.storePath != path {
		if globalStore != nil && globalStore.cleanupManager != nil {
			globalStore.cleanupManager.Stop()
		}
		store, err := NewStore(path)
		if err != nil {
			return nil, err
		}
		globalStore = store

		// Initialize cleanup manager
		globalStore.cleanupManager = sessionstore.NewCleanupManager(
			globalStore,
			globalStore.log,
		)
		globalStore.cleanupManager.Start()
	}
	return globalStore, nil
}

// StopPersistentStore stops the cleanup background job and clears the globalStore variable.
func StopPersistentStore() {
	mu.Lock()
	defer mu.Unlock()
	if globalStore != nil && globalStore.cleanupManager != nil {
		globalStore.cleanupManager.Stop()
	}
	globalStore = nil
}
