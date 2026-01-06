package concurrent

import (
	"context"
	"sync"
	"time"
)

// RateLimiter limits the rate of operations using a token bucket algorithm.
type RateLimiter struct {
	rate     float64       // tokens per second
	burst    int           // maximum tokens
	tokens   float64       // current tokens
	lastTime time.Time     // last token refill time
	mu       sync.Mutex
}

// NewRateLimiter creates a new rate limiter.
// rate is the number of operations per second.
// burst is the maximum number of operations that can happen at once.
func NewRateLimiter(rate float64, burst int) *RateLimiter {
	if rate <= 0 {
		rate = 1
	}
	if burst < 1 {
		burst = 1
	}
	return &RateLimiter{
		rate:     rate,
		burst:    burst,
		tokens:   float64(burst),
		lastTime: time.Now(),
	}
}

// refill adds tokens based on elapsed time.
func (r *RateLimiter) refill() {
	now := time.Now()
	elapsed := now.Sub(r.lastTime).Seconds()
	r.tokens += elapsed * r.rate
	if r.tokens > float64(r.burst) {
		r.tokens = float64(r.burst)
	}
	r.lastTime = now
}

// Allow checks if one operation is allowed immediately.
// Returns true if allowed, false if rate limited.
func (r *RateLimiter) Allow() bool {
	r.mu.Lock()
	defer r.mu.Unlock()

	r.refill()
	if r.tokens >= 1 {
		r.tokens--
		return true
	}
	return false
}

// AllowN checks if n operations are allowed immediately.
func (r *RateLimiter) AllowN(n int) bool {
	r.mu.Lock()
	defer r.mu.Unlock()

	r.refill()
	needed := float64(n)
	if r.tokens >= needed {
		r.tokens -= needed
		return true
	}
	return false
}

// Wait blocks until one operation is allowed or context is cancelled.
func (r *RateLimiter) Wait(ctx context.Context) error {
	return r.WaitN(ctx, 1)
}

// WaitN blocks until n operations are allowed or context is cancelled.
func (r *RateLimiter) WaitN(ctx context.Context, n int) error {
	for {
		r.mu.Lock()
		r.refill()
		needed := float64(n)

		if r.tokens >= needed {
			r.tokens -= needed
			r.mu.Unlock()
			return nil
		}

		// Calculate wait time for needed tokens
		tokensNeeded := needed - r.tokens
		waitTime := time.Duration(tokensNeeded/r.rate*float64(time.Second))
		r.mu.Unlock()

		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(waitTime):
			// Loop and try again
		}
	}
}

// Reserve reserves one operation and returns the time to wait.
// The operation is reserved even if Wait must be called.
func (r *RateLimiter) Reserve() time.Duration {
	return r.ReserveN(1)
}

// ReserveN reserves n operations and returns the time to wait.
func (r *RateLimiter) ReserveN(n int) time.Duration {
	r.mu.Lock()
	defer r.mu.Unlock()

	r.refill()
	needed := float64(n)

	if r.tokens >= needed {
		r.tokens -= needed
		return 0
	}

	tokensNeeded := needed - r.tokens
	r.tokens = 0 // Reserve all available tokens

	return time.Duration(tokensNeeded / r.rate * float64(time.Second))
}

// Tokens returns the current number of available tokens.
func (r *RateLimiter) Tokens() float64 {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.refill()
	return r.tokens
}

// Ticker provides a tick at a limited rate.
// It wraps time.Ticker with rate limiting.
type Ticker struct {
	C      <-chan time.Time
	ticker *time.Ticker
	done   chan struct{}
}

// NewTicker creates a ticker that ticks at the specified rate.
// rate is operations per second.
func NewTicker(rate float64) *Ticker {
	if rate <= 0 {
		rate = 1
	}
	interval := time.Duration(float64(time.Second) / rate)
	ticker := time.NewTicker(interval)
	return &Ticker{
		C:      ticker.C,
		ticker: ticker,
		done:   make(chan struct{}),
	}
}

// Stop stops the ticker.
func (t *Ticker) Stop() {
	t.ticker.Stop()
	close(t.done)
}

// Throttle limits function calls to the specified rate.
// Returns a throttled version of the function.
func Throttle[T any](rate float64, fn func() T) func() T {
	limiter := NewRateLimiter(rate, 1)
	return func() T {
		limiter.Wait(context.Background())
		return fn()
	}
}

// ThrottleWithContext limits function calls with context support.
func ThrottleWithContext[T any](rate float64, fn func(context.Context) T) func(context.Context) T {
	limiter := NewRateLimiter(rate, 1)
	return func(ctx context.Context) T {
		limiter.Wait(ctx)
		return fn(ctx)
	}
}

// Debounce delays function execution until the interval has passed
// without new calls. Only the last call within the interval is executed.
func Debounce(interval time.Duration, fn func()) func() {
	var mu sync.Mutex
	var timer *time.Timer

	return func() {
		mu.Lock()
		defer mu.Unlock()

		if timer != nil {
			timer.Stop()
		}
		timer = time.AfterFunc(interval, fn)
	}
}

// DebounceWithContext is like Debounce but with context support.
func DebounceWithContext(interval time.Duration, fn func(context.Context)) func(context.Context) {
	var mu sync.Mutex
	var timer *time.Timer
	var lastCtx context.Context

	return func(ctx context.Context) {
		mu.Lock()
		defer mu.Unlock()

		lastCtx = ctx
		if timer != nil {
			timer.Stop()
		}
		timer = time.AfterFunc(interval, func() {
			fn(lastCtx)
		})
	}
}
