import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  computePollDelayMs,
  createDocumentPoller,
  PollingSnapshot,
} from '../services/polling';

function lastOf<T>(items: T[]): T | undefined {
  return items[items.length - 1];
}

describe('computePollDelayMs', () => {
  it('increases delay exponentially up to maxDelayMs cap', () => {
    const options = { baseDelayMs: 2000, backoffFactor: 2, maxDelayMs: 30000 };

    expect(computePollDelayMs(0, options)).toBe(2000);
    expect(computePollDelayMs(1, options)).toBe(4000);
    expect(computePollDelayMs(2, options)).toBe(8000);
    expect(computePollDelayMs(3, options)).toBe(16000);
    expect(computePollDelayMs(4, options)).toBe(30000);
    expect(computePollDelayMs(5, options)).toBe(30000);
    expect(computePollDelayMs(10, options)).toBe(30000);
  });
});

describe('createDocumentPoller', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('polls with increasing intervals up to cap and stops after maxAttempts', async () => {
    const snapshots: PollingSnapshot[] = [];
    const poll = vi.fn().mockResolvedValue({ items: [] });

    const poller = createDocumentPoller(
      {
        poll,
        onSuccess: vi.fn(),
        onStateChange: (s) => snapshots.push(s),
        isDocumentHidden: () => false,
      },
      { baseDelayMs: 1000, backoffFactor: 2, maxDelayMs: 3000, maxAttempts: 4 },
    );

    poller.start();
    // Tentativa 1 agendada para 1000ms
    expect(lastOf(snapshots)?.nextDelayMs).toBe(1000);

    await vi.advanceTimersByTimeAsync(1000);
    expect(poll).toHaveBeenCalledTimes(1);
    expect(lastOf(snapshots)?.nextDelayMs).toBe(2000);

    await vi.advanceTimersByTimeAsync(2000);
    expect(poll).toHaveBeenCalledTimes(2);
    expect(lastOf(snapshots)?.nextDelayMs).toBe(3000); // teto atingido

    await vi.advanceTimersByTimeAsync(3000);
    expect(poll).toHaveBeenCalledTimes(3);
    expect(lastOf(snapshots)?.nextDelayMs).toBe(3000); // teto mantido

    await vi.advanceTimersByTimeAsync(3000);
    expect(poll).toHaveBeenCalledTimes(4);
    expect(lastOf(snapshots)?.exhausted).toBe(true);
    expect(lastOf(snapshots)?.nextDelayMs).toBeNull();

    // Avancar o tempo novamente nao deve disparar novas tentativas
    await vi.advanceTimersByTimeAsync(60000);
    expect(poll).toHaveBeenCalledTimes(4);
  });

  it('tracks consecutiveErrors on failure and resets on success', async () => {
    const snapshots: PollingSnapshot[] = [];
    const poll = vi
      .fn()
      .mockRejectedValueOnce(new Error('network'))
      .mockRejectedValueOnce(new Error('network'))
      .mockResolvedValueOnce({ items: [] });

    const poller = createDocumentPoller(
      {
        poll,
        onSuccess: vi.fn(),
        onStateChange: (s) => snapshots.push(s),
        isDocumentHidden: () => false,
      },
      { baseDelayMs: 500, backoffFactor: 2, maxDelayMs: 5000, maxAttempts: 5 },
    );

    poller.start();

    await vi.advanceTimersByTimeAsync(500);
    expect(lastOf(snapshots)?.consecutiveErrors).toBe(1);

    await vi.advanceTimersByTimeAsync(1000);
    expect(lastOf(snapshots)?.consecutiveErrors).toBe(2);

    await vi.advanceTimersByTimeAsync(2000);
    expect(lastOf(snapshots)?.consecutiveErrors).toBe(0);

    poller.stop();
  });

  it('pauses when tab is hidden and resumes when visible again', async () => {
    let hidden = true;
    const snapshots: PollingSnapshot[] = [];
    const poll = vi.fn().mockResolvedValue({ items: [] });

    const poller = createDocumentPoller(
      {
        poll,
        onSuccess: vi.fn(),
        onStateChange: (s) => snapshots.push(s),
        isDocumentHidden: () => hidden,
      },
      { baseDelayMs: 1000, backoffFactor: 2, maxDelayMs: 5000, maxAttempts: 5 },
    );

    poller.start();
    expect(lastOf(snapshots)?.pausedByVisibility).toBe(true);

    await vi.advanceTimersByTimeAsync(10000);
    expect(poll).not.toHaveBeenCalled();

    // Aba volta a ficar visivel
    hidden = false;
    poller.handleVisibilityChange();
    await vi.advanceTimersByTimeAsync(0);
    expect(poll).toHaveBeenCalledTimes(1);
    expect(lastOf(snapshots)?.pausedByVisibility).toBe(false);

    poller.stop();
  });
});
