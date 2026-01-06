package concurrent

import (
	"context"
	"os"
	"sync"
	"syscall"
	"testing"
	"time"
)

func TestSignalHandler(t *testing.T) {
	handler := NewSignalHandler(syscall.SIGUSR1)

	var received os.Signal
	var mu sync.Mutex
	handler.OnSignal(func(sig os.Signal) {
		mu.Lock()
		received = sig
		mu.Unlock()
	})

	ctx := handler.Start()

	// Send signal
	p, _ := os.FindProcess(os.Getpid())
	p.Signal(syscall.SIGUSR1)

	// Wait for context to be cancelled
	select {
	case <-ctx.Done():
		// Expected
	case <-time.After(time.Second):
		t.Error("Context not cancelled after signal")
	}

	mu.Lock()
	if received != syscall.SIGUSR1 {
		t.Errorf("Received signal %v, want SIGUSR1", received)
	}
	mu.Unlock()

	handler.Stop()
}

func TestSignalHandlerMultipleCallbacks(t *testing.T) {
	handler := NewSignalHandler(syscall.SIGUSR1)

	var count int
	var mu sync.Mutex
	for i := 0; i < 3; i++ {
		handler.OnSignal(func(sig os.Signal) {
			mu.Lock()
			count++
			mu.Unlock()
		})
	}

	handler.Start()

	// Send signal
	p, _ := os.FindProcess(os.Getpid())
	p.Signal(syscall.SIGUSR1)

	// Wait a bit
	time.Sleep(100 * time.Millisecond)

	mu.Lock()
	if count != 3 {
		t.Errorf("Callback count = %d, want 3", count)
	}
	mu.Unlock()

	handler.Stop()
}

func TestSignalHandlerStartOnce(t *testing.T) {
	handler := NewSignalHandler(syscall.SIGUSR1)

	ctx1 := handler.Start()
	ctx2 := handler.Start()

	// Should return same context
	if ctx1 != ctx2 {
		t.Error("Start() should return same context when called twice")
	}

	handler.Stop()
}

func TestWithSignalContext(t *testing.T) {
	ctx, cancel := WithSignalContext(context.Background(), syscall.SIGUSR1)
	defer cancel()

	// Send signal
	p, _ := os.FindProcess(os.Getpid())
	p.Signal(syscall.SIGUSR1)

	// Wait for context to be cancelled
	select {
	case <-ctx.Done():
		// Expected
	case <-time.After(time.Second):
		t.Error("Context not cancelled after signal")
	}
}

func TestWithSignalContextCancel(t *testing.T) {
	ctx, cancel := WithSignalContext(context.Background(), syscall.SIGUSR1)

	// Cancel manually
	cancel()

	select {
	case <-ctx.Done():
		// Expected
	case <-time.After(time.Second):
		t.Error("Context not cancelled")
	}
}

func TestGracefulShutdown(t *testing.T) {
	gs := NewGracefulShutdown(syscall.SIGUSR1)
	shutdownCh := gs.Start()

	// Should not be closed initially
	select {
	case <-shutdownCh:
		t.Error("Shutdown channel closed prematurely")
	default:
		// Expected
	}

	// Trigger shutdown manually
	gs.TriggerShutdown()

	// Should be closed now
	select {
	case <-shutdownCh:
		// Expected
	case <-time.After(time.Second):
		t.Error("Shutdown channel not closed")
	}

	// Mark done
	gs.Done()

	// Should not block
	gs.Wait()

	gs.Stop()
}

func TestGracefulShutdownSignal(t *testing.T) {
	gs := NewGracefulShutdown(syscall.SIGUSR1)
	shutdownCh := gs.Start()

	// Send signal
	p, _ := os.FindProcess(os.Getpid())
	p.Signal(syscall.SIGUSR1)

	// Wait for shutdown channel
	select {
	case <-shutdownCh:
		// Expected
	case <-time.After(time.Second):
		t.Error("Shutdown channel not closed after signal")
	}

	gs.Done()
	gs.Stop()
}

func TestGracefulShutdownContext(t *testing.T) {
	gs := NewGracefulShutdown(syscall.SIGUSR1)
	gs.Start()

	ctx := gs.Context()

	// Context should not be done initially
	select {
	case <-ctx.Done():
		t.Error("Context done prematurely")
	default:
		// Expected
	}

	// Send signal to trigger shutdown (TriggerShutdown only closes channel, not context)
	p, _ := os.FindProcess(os.Getpid())
	p.Signal(syscall.SIGUSR1)

	// Context should be done
	select {
	case <-ctx.Done():
		// Expected
	case <-time.After(time.Second):
		t.Error("Context not done after signal")
	}

	gs.Done()
	gs.Stop()
}

func TestSignalHandlerRegisterShutdown(t *testing.T) {
	handler := NewSignalHandler(syscall.SIGUSR1)

	var executed bool
	var mu sync.Mutex
	handler.RegisterShutdown(func() {
		mu.Lock()
		executed = true
		mu.Unlock()
	})

	handler.Start()

	// Send signal
	p, _ := os.FindProcess(os.Getpid())
	p.Signal(syscall.SIGUSR1)

	// Wait for shutdown functions to complete
	handler.WaitShutdownComplete()

	mu.Lock()
	if !executed {
		t.Error("Shutdown function not executed")
	}
	mu.Unlock()

	handler.Stop()
}
