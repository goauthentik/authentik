package utils

import (
	"errors"
	"fmt"
	"os"
	"syscall"
)

func FindProcess(pid int) (*os.Process, error) {
	if pid <= 0 {
		return nil, fmt.Errorf("invalid pid %v", pid)
	}
	// The error doesn't mean anything on Unix systems, let's just check manually
	// that the new gunicorn master has properly started
	// https://github.com/golang/go/issues/34396
	proc, err := os.FindProcess(pid)
	if err != nil {
		return nil, err
	}
	err = proc.Signal(syscall.Signal(0))
	if err == nil {
		return proc, nil
	}
	if errors.Is(err, os.ErrProcessDone) {
		return nil, nil
	}
	errno, ok := err.(syscall.Errno)
	if !ok {
		return nil, err
	}
	switch errno {
	case syscall.ESRCH:
		return nil, nil
	case syscall.EPERM:
		return proc, nil
	}
	return nil, err
}
