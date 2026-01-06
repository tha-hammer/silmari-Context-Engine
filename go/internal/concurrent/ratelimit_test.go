package concurrent

import (
	"context"
	"sync/atomic"
	"testing"
	"time"
)

func TestRateLimiterAllow(t *testing.T) {
	limiter := NewRateLimiter(10, 5) // 10/sec, burst of 5

	// Should allow first 5 immediately (burst)
	for i := 0; i < 5; i++ {
		if !limiter.Allow() {
			t.Errorf("Allow() %d = false, want true", i)
		}
	}

	// 6th should be denied immediately (no tokens left)
	if limiter.Allow() {
		t.Error("Allow() after burst = true, want false")
	}
}

func TestRateLimiterAllowN(t *testing.T) {
	limiter := NewRateLimiter(10, 5)

	// Should allow 3 tokens
	if !limiter.AllowN(3) {
		t.Error("AllowN(3) = false, want true")
	}

	// Should allow 2 more
	if !limiter.AllowN(2) {
		t.Error("AllowN(2) = false, want true")
	}

	// Should deny 1 (no tokens left)
	if limiter.AllowN(1) {
		t.Error("AllowN(1) after exhaustion = true, want false")
	}
}

func TestRateLimiterWait(t *testing.T) {
	limiter := NewRateLimiter(100, 1) // 100/sec, burst of 1

	ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
	defer cancel()

	// First call should succeed immediately
	if err := limiter.Wait(ctx); err != nil {
		t.Errorf("Wait() error = %v, want nil", err)
	}

	// Second call should wait for rate limit
	start := time.Now()
	if err := limiter.Wait(ctx); err != nil {
		t.Errorf("Wait() error = %v, want nil", err)
	}
	elapsed := time.Since(start)

	// Should have waited about 10ms (1/100 sec)
	if elapsed < 5*time.Millisecond || elapsed > 50*time.Millisecond {
		t.Errorf("Wait() took %v, expected ~10ms", elapsed)
	}
}

func TestRateLimiterWaitContext(t *testing.T) {
	limiter := NewRateLimiter(1, 1) // 1/sec

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Millisecond)
	defer cancel()

	// Exhaust token
	limiter.Allow()

	// Wait should timeout
	err := limiter.Wait(ctx)
	if err == nil {
		t.Error("Wait() with cancelled context should return error")
	}
}

func TestRateLimiterReserve(t *testing.T) {
	limiter := NewRateLimiter(10, 2)

	// First reserve should return 0 (immediate)
	wait := limiter.Reserve()
	if wait != 0 {
		t.Errorf("Reserve() = %v, want 0", wait)
	}

	// Second reserve should return 0 (still have tokens)
	wait = limiter.Reserve()
	if wait != 0 {
		t.Errorf("Reserve() = %v, want 0", wait)
	}

	// Third reserve should return positive wait time
	wait = limiter.Reserve()
	if wait <= 0 {
		t.Errorf("Reserve() = %v, want positive duration", wait)
	}
}

func TestRateLimiterTokens(t *testing.T) {
	limiter := NewRateLimiter(10, 5)

	initial := limiter.Tokens()
	if initial < 4.9 || initial > 5.1 {
		t.Errorf("Tokens() = %v, want ~5", initial)
	}

	limiter.Allow()
	after := limiter.Tokens()
	// Allow for some refill between calls
	if after < 3.9 || after > 4.1 {
		t.Errorf("Tokens() after Allow = %v, want ~4", after)
	}
}

func TestRateLimiterRefill(t *testing.T) {
	limiter := NewRateLimiter(100, 5) // 100/sec

	// Exhaust all tokens
	for i := 0; i < 5; i++ {
		limiter.Allow()
	}

	// Should have ~0 tokens (allow small refill between iterations)
	if tokens := limiter.Tokens(); tokens > 0.5 {
		t.Errorf("Tokens() = %v, want ~0", tokens)
	}

	// Wait 50ms (should refill ~5 tokens at 100/sec)
	time.Sleep(50 * time.Millisecond)

	// Should have some tokens now (allowing for timing variance)
	tokens := limiter.Tokens()
	if tokens < 3 || tokens > 6 {
		t.Errorf("Tokens() after 50ms = %v, want ~5", tokens)
	}
}

func TestTicker(t *testing.T) {
	ticker := NewTicker(100) // 100 ticks per second
	defer ticker.Stop()

	count := 0
	timeout := time.After(50 * time.Millisecond)

	for {
		select {
		case <-ticker.C:
			count++
		case <-timeout:
			// Should have ~5 ticks in 50ms at 100/sec
			if count < 3 || count > 7 {
				t.Errorf("Got %d ticks in 50ms, expected ~5", count)
			}
			return
		}
	}
}

func TestThrottle(t *testing.T) {
	var count int32
	fn := func() int {
		return int(atomic.AddInt32(&count, 1))
	}

	throttled := Throttle(100.0, fn) // 100/sec

	// Call rapidly
	for i := 0; i < 5; i++ {
		throttled()
	}

	if count != 5 {
		t.Errorf("count = %d, want 5", count)
	}
}

func TestDebounce(t *testing.T) {
	var count int32
	fn := func() {
		atomic.AddInt32(&count, 1)
	}

	debounced := Debounce(20*time.Millisecond, fn)

	// Call rapidly - only last should execute
	for i := 0; i < 5; i++ {
		debounced()
		time.Sleep(5 * time.Millisecond)
	}

	// Wait for debounce to trigger
	time.Sleep(50 * time.Millisecond)

	if count != 1 {
		t.Errorf("count = %d, want 1 (debounced)", count)
	}
}

func TestNewRateLimiterDefaults(t *testing.T) {
	// Test with invalid inputs
	limiter := NewRateLimiter(0, 0)
	if limiter.rate <= 0 {
		t.Error("rate should be positive")
	}
	if limiter.burst < 1 {
		t.Error("burst should be at least 1")
	}
}
