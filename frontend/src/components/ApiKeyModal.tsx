import React, { useState } from 'react';
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
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="api-key-modal-title"
    >
      <div className="bg-white rounded-xl shadow-xl border border-slate-200 max-w-md w-full overflow-hidden text-slate-800">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
          <div className="flex items-center space-x-2">
            <KeyRound className="w-5 h-5 text-emerald-600" />
            <h2 id="api-key-modal-title" className="text-base font-bold text-slate-900">
              Identificação do Analista (X-API-Key)
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 transition-colors"
            title="Fechar"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <p className="text-xs text-slate-600 leading-relaxed">
            Informe sua chave pessoal no formato{' '}
            <code className="px-1.5 py-0.5 rounded bg-slate-100 font-mono text-slate-800">
              user_id:segredo
            </code>
            . Ela será enviada no cabeçalho <code className="font-mono">X-API-Key</code> apenas
            enquanto esta aba permanecer aberta (armazenamento exclusivo em memória).
          </p>

          <div>
            <label htmlFor="analyst-api-key" className="block text-xs font-semibold text-slate-700 mb-1.5">
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
                autoFocus
                className="w-full pr-10 pl-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 font-mono"
              />
              <button
                type="button"
                onClick={() => setShowKey((prev) => !prev)}
                className="absolute inset-y-0 right-0 px-3 flex items-center text-slate-400 hover:text-slate-600"
                title={showKey ? 'Ocultar chave' : 'Mostrar chave'}
              >
                {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <div className="flex items-center justify-between pt-2">
            {currentKey ? (
              <button
                type="button"
                onClick={handleClear}
                className="inline-flex items-center space-x-1.5 px-3 py-2 rounded-lg text-xs font-semibold text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200 transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Remover Chave</span>
              </button>
            ) : (
              <span />
            )}

            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-100 transition-colors"
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="px-4 py-2 rounded-lg text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 shadow-sm transition-colors"
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
