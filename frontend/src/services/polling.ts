export interface PollingOptions {
  /** Intervalo inicial em milissegundos (padrão: 2000ms). */
  baseDelayMs?: number;
  /** Fator de crescimento exponencial por tentativa (padrão: 2). */
  backoffFactor?: number;
  /** Teto máximo do intervalo entre tentativas em ms (padrão: 30000ms). */
  maxDelayMs?: number;
  /** Número máximo de tentativas automáticas antes de pausar (padrão: 10). */
  maxAttempts?: number;
}

export interface PollingSnapshot {
  attempt: number;
  maxAttempts: number;
  consecutiveErrors: number;
  exhausted: boolean;
  pausedByVisibility: boolean;
  nextDelayMs: number | null;
}

export const DEFAULT_POLLING_OPTIONS: Required<PollingOptions> = {
  baseDelayMs: 2000,
  backoffFactor: 2,
  maxDelayMs: 30000,
  maxAttempts: 10,
};

/**
 * Calcula o intervalo de espera (em ms) para a tentativa `attempt` (0-indexed)
 * usando backoff exponencial limitado por `maxDelayMs`.
 */
export function computePollDelayMs(attempt: number, options: PollingOptions = {}): number {
  const base = options.baseDelayMs ?? DEFAULT_POLLING_OPTIONS.baseDelayMs;
  const factor = options.backoffFactor ?? DEFAULT_POLLING_OPTIONS.backoffFactor;
  const maxDelay = options.maxDelayMs ?? DEFAULT_POLLING_OPTIONS.maxDelayMs;

  if (attempt <= 0) return Math.min(base, maxDelay);
  const raw = base * Math.pow(factor, attempt);
  return Math.min(Math.round(raw), maxDelay);
}

export interface DocumentPollerCallbacks<T> {
  poll: () => Promise<T>;
  onSuccess: (result: T) => void;
  onStateChange: (snapshot: PollingSnapshot) => void;
  isDocumentHidden?: () => boolean;
}

export interface DocumentPoller {
  start: () => void;
  stop: () => void;
  handleVisibilityChange: () => void;
}

/**
 * Orquestra polling resiliente com backoff exponencial com teto, limite de tentativas,
 * contagem de falhas consecutivas e pausa quando a aba está oculta.
 */
export function createDocumentPoller<T>(
  callbacks: DocumentPollerCallbacks<T>,
  options: PollingOptions = {},
): DocumentPoller {
  const resolved = { ...DEFAULT_POLLING_OPTIONS, ...options };
  const isHidden =
    callbacks.isDocumentHidden ??
    (() => typeof document !== 'undefined' && document.visibilityState === 'hidden');

  let timerId: ReturnType<typeof setTimeout> | null = null;
  let stopped = false;
  let inFlight = false;
  let attempt = 0;
  let consecutiveErrors = 0;
  let exhausted = false;
  let pausedByVisibility = false;

  const emitState = (nextDelayMs: number | null) => {
    callbacks.onStateChange({
      attempt,
      maxAttempts: resolved.maxAttempts,
      consecutiveErrors,
      exhausted,
      pausedByVisibility,
      nextDelayMs,
    });
  };

  const clearScheduledTimer = () => {
    if (timerId !== null) {
      clearTimeout(timerId);
      timerId = null;
    }
  };

  const scheduleNext = () => {
    clearScheduledTimer();
    if (stopped || exhausted) return;

    if (attempt >= resolved.maxAttempts) {
      exhausted = true;
      emitState(null);
      return;
    }

    if (isHidden()) {
      pausedByVisibility = true;
      emitState(null);
      return;
    }

    pausedByVisibility = false;
    const delay = computePollDelayMs(attempt, resolved);
    emitState(delay);

    timerId = setTimeout(() => {
      timerId = null;
      void runPoll();
    }, delay);
  };

  const runPoll = async () => {
    if (stopped || exhausted || inFlight) return;
    if (isHidden()) {
      pausedByVisibility = true;
      emitState(null);
      return;
    }

    inFlight = true;
    attempt += 1;

    try {
      const result = await callbacks.poll();
      if (stopped) return;
      consecutiveErrors = 0;
      callbacks.onSuccess(result);
    } catch {
      if (stopped) return;
      consecutiveErrors += 1;
    } finally {
      inFlight = false;
    }

    if (!stopped) {
      scheduleNext();
    }
  };

  return {
    start() {
      stopped = false;
      scheduleNext();
    },
    stop() {
      stopped = true;
      clearScheduledTimer();
    },
    handleVisibilityChange() {
      if (stopped || exhausted) return;
      if (isHidden()) {
        clearScheduledTimer();
        pausedByVisibility = true;
        emitState(null);
      } else if (pausedByVisibility) {
        pausedByVisibility = false;
        void runPoll();
      }
    },
  };
}
