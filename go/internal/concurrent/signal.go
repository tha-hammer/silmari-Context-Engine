package concurrent

import (
	"context"
	"os"
	"os/signal"
	"sync"
	"syscall"
)

// SignalHandler manages OS signal handling for graceful shutdown.
type SignalHandler struct {
	signals    []os.Signal
	callbacks  []func(os.Signal)
	ctx        context.Context
	cancel     context.CancelFunc
	sigCh      chan os.Signal
	mu         sync.Mutex
	started    bool
	shutdownWg sync.WaitGroup
}

// NewSignalHandler creates a new signal handler for the given signals.
// If no signals are specified, it defaults to SIGINT and SIGTERM.
func NewSignalHandler(signals ...os.Signal) *SignalHandler {
	if len(signals) == 0 {
		signals = []os.Signal{syscall.SIGINT, syscall.SIGTERM}
	}

	ctx, cancel := context.WithCancel(context.Background())
	return &SignalHandler{
		signals: signals,
		ctx:     ctx,
		cancel:  cancel,
		sigCh:   make(chan os.Signal, 1),
	}
}

// OnSignal registers a callback to be called when a signal is received.
// Multiple callbacks can be registered.
func (h *SignalHandler) OnSignal(fn func(os.Signal)) {
	h.mu.Lock()
	defer h.mu.Unlock()
	h.callbacks = append(h.callbacks, fn)
}

// Start begins listening for signals.
// It returns a context that is cancelled when a signal is received.
func (h *SignalHandler) Start() context.Context {
	h.mu.Lock()
	if h.started {
		h.mu.Unlock()
		return h.ctx
	}
	h.started = true
	h.mu.Unlock()

	signal.Notify(h.sigCh, h.signals...)

	go h.listen()

	return h.ctx
}

// listen handles incoming signals.
func (h *SignalHandler) listen() {
	for {
		select {
		case sig, ok := <-h.sigCh:
			if !ok {
				return
			}

			// Run callbacks
			h.mu.Lock()
			callbacks := make([]func(os.Signal), len(h.callbacks))
			copy(callbacks, h.callbacks)
			h.mu.Unlock()

			for _, cb := range callbacks {
				cb(sig)
			}

			// Cancel context
			h.cancel()
			return

		case <-h.ctx.Done():
			return
		}
	}
}

// Stop stops the signal handler.
func (h *SignalHandler) Stop() {
	h.mu.Lock()
	defer h.mu.Unlock()

	if !h.started {
		return
	}

	signal.Stop(h.sigCh)
	close(h.sigCh)
	h.cancel()
}

// Context returns the handler's context.
func (h *SignalHandler) Context() context.Context {
	return h.ctx
}

// WaitForShutdown blocks until the context is cancelled.
func (h *SignalHandler) WaitForShutdown() {
	<-h.ctx.Done()
}

// RegisterShutdown registers a shutdown function to be executed when
// the signal is received. All registered functions are called in order.
func (h *SignalHandler) RegisterShutdown(fn func()) {
	h.shutdownWg.Add(1)
	h.OnSignal(func(_ os.Signal) {
		defer h.shutdownWg.Done()
		fn()
	})
}

// WaitShutdownComplete waits for all registered shutdown functions to complete.
func (h *SignalHandler) WaitShutdownComplete() {
	h.shutdownWg.Wait()
}

// WithSignalContext creates a context that is cancelled on SIGINT or SIGTERM.
// This is a convenience function for simple use cases.
func WithSignalContext(parent context.Context, signals ...os.Signal) (context.Context, func()) {
	if len(signals) == 0 {
		signals = []os.Signal{syscall.SIGINT, syscall.SIGTERM}
	}

	ctx, cancel := context.WithCancel(parent)
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, signals...)

	go func() {
		select {
		case <-sigCh:
			cancel()
		case <-ctx.Done():
		}
		signal.Stop(sigCh)
	}()

	return ctx, cancel
}

// GracefulShutdown provides a pattern for graceful shutdown of services.
type GracefulShutdown struct {
	handler    *SignalHandler
	shutdownCh chan struct{}
	doneCh     chan struct{}
	once       sync.Once
}

// NewGracefulShutdown creates a new graceful shutdown handler.
func NewGracefulShutdown(signals ...os.Signal) *GracefulShutdown {
	return &GracefulShutdown{
		handler:    NewSignalHandler(signals...),
		shutdownCh: make(chan struct{}),
		doneCh:     make(chan struct{}),
	}
}

// Start begins listening for signals.
// Returns the shutdown channel which is closed when shutdown begins.
func (g *GracefulShutdown) Start() <-chan struct{} {
	g.handler.Start()
	g.handler.OnSignal(func(_ os.Signal) {
		g.once.Do(func() {
			close(g.shutdownCh)
		})
	})
	return g.shutdownCh
}

// Shutdown returns a channel that is closed when shutdown begins.
func (g *GracefulShutdown) Shutdown() <-chan struct{} {
	return g.shutdownCh
}

// Done should be called when shutdown is complete.
func (g *GracefulShutdown) Done() {
	close(g.doneCh)
}

// Wait blocks until Done is called.
func (g *GracefulShutdown) Wait() {
	<-g.doneCh
}

// TriggerShutdown manually triggers shutdown.
func (g *GracefulShutdown) TriggerShutdown() {
	g.once.Do(func() {
		close(g.shutdownCh)
	})
}

// Context returns a context that is cancelled when shutdown begins.
func (g *GracefulShutdown) Context() context.Context {
	return g.handler.Context()
}

// Stop stops the handler and releases resources.
func (g *GracefulShutdown) Stop() {
	g.handler.Stop()
}
