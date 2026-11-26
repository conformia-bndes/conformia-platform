import React, { useEffect, useRef, useState } from 'react';
import { KeyRound, Eye, EyeOff, X, Trash2 } from 'lucide-react';

interface ApiKeyModalProps {
  isOpen: boolean;
  currentKey: string | null;
  onSave: (key: string | null) => void;
  onClose: () => void;
}

export function ApiKeyModal({ isOpen, currentKey, onSave, onClose }: ApiKeyModalProps) {
  const [draftKey, setDraftKey] = useState<string>(currentKey ?? '');
  const [showKey, setShowKey] = useState<boolean>(false);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    previousFocusRef.current = document.activeElement as HTMLElement | null;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      previousFocusRef.current?.focus();
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = draftKey.trim();
    onSave(trimmed.length > 0 ? trimmed : null);
    onClose();
  };

  const handleClear = () => {
    setDraftKey('');
    onSave(null);
    onClose();
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-bndes-ink/60 backdrop-blur-xs p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="api-key-modal-title"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="bg-white rounded-md shadow-(--shadow-bndes-elevated) border border-bndes-border border-t-[3px] border-t-bndes-blue max-w-md w-full overflow-hidden text-bndes-ink">
        <div className="px-6 py-4 border-b border-bndes-border flex items-center justify-between bg-bndes-surface-muted/70">
          <div className="flex items-center space-x-2">
            <KeyRound className="w-5 h-5 text-bndes-blue" aria-hidden="true" />
            <h2 id="api-key-modal-title" className="text-base font-bold text-bndes-blue">
              Identificação do Analista (X-API-Key)
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-bndes-ink-muted hover:text-bndes-ink transition-colors cursor-pointer rounded p-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-bndes-blue-2"
            title="Fechar"
            aria-label="Fechar janela de identificação"
          >
            <X className="w-4 h-4" aria-hidden="true" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <p className="text-xs text-bndes-ink-secondary leading-relaxed">
            Informe sua chave pessoal no formato{' '}
            <code className="px-1.5 py-0.5 rounded bg-bndes-surface-muted border border-bndes-border font-mono text-bndes-ink">
              user_id:segredo
            </code>
            . Ela será enviada no cabeçalho <code className="font-mono">X-API-Key</code> apenas
            enquanto esta aba permanecer aberta (armazenamento exclusivo em memória).
          </p>

          <div>
            <label htmlFor="analyst-api-key" className="block text-xs font-semibold text-bndes-ink mb-1.5">
              Chave Pessoal
            </label>
            <div className="relative">
              <input
                id="analyst-api-key"
                type={showKey ? 'text' : 'password'}
                value={draftKey}
                onChange={(e) => setDraftKey(e.target.value)}
                placeholder="ex.: analista-1:seu-segredo"
                autoComplete="off"
                autoCapitalize="none"
                spellCheck={false}
                autoFocus
                className="w-full pr-10 pl-3 py-2 text-sm border border-bndes-border-strong rounded focus:outline-none focus:ring-2 focus:ring-bndes-blue-2 focus:border-bndes-blue-2 font-mono text-bndes-ink"
              />
              <button
                type="button"
                onClick={() => setShowKey((prev) => !prev)}
                className="absolute inset-y-0 right-0 px-3 flex items-center text-bndes-ink-muted hover:text-bndes-ink cursor-pointer rounded-r focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-bndes-blue-2"
                title={showKey ? 'Ocultar chave' : 'Mostrar chave'}
                aria-label={showKey ? 'Ocultar chave' : 'Mostrar chave'}
              >
                {showKey ? <EyeOff className="w-4 h-4" aria-hidden="true" /> : <Eye className="w-4 h-4" aria-hidden="true" />}
              </button>
            </div>
          </div>

          <div className="flex items-center justify-between pt-2">
            {currentKey ? (
              <button
                type="button"
                onClick={handleClear}
                className="inline-flex items-center space-x-1.5 px-3 py-2 rounded text-xs font-semibold text-bndes-orange-ink bg-bndes-orange-tint hover:bg-[#F9E3D7] border border-bndes-orange-border transition-colors cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-bndes-blue-2"
              >
                <Trash2 className="w-3.5 h-3.5" aria-hidden="true" />
                <span>Remover Chave</span>
              </button>
            ) : (
              <span />
            )}

            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded text-xs font-semibold text-bndes-ink-secondary hover:bg-bndes-surface-muted transition-colors cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-bndes-blue-2"
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="px-4 py-2 rounded text-xs font-semibold text-white bg-bndes-blue hover:bg-bndes-blue-3 active:bg-bndes-blue-deep shadow-xs transition-colors cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-bndes-blue-2"
              >
                Aplicar na Sessão
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
