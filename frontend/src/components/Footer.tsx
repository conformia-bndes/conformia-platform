import logoBndesConformiaNegativa from '../assets/logo-bndes-conformia-negativa.svg';

export function Footer() {
  return (
    <footer className="bg-bndes-blue border-t-[3px] border-bndes-green py-6 text-xs text-white/90">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row justify-between items-center gap-4">
        <div className="flex flex-col sm:flex-row items-center gap-4">
          {/* Aplicação da versão monocromática negativa sobre fundo escuro (>50% preto - Seções 1.5 e 1.6) */}
          <div className="py-1.5 px-2 shrink-0">
            <img
              src={logoBndesConformiaNegativa}
              alt="BNDES Conform.IA"
              className="h-8 w-auto object-contain select-none"
            />
          </div>
          <span className="hidden sm:inline-block h-6 w-px bg-white/25" aria-hidden="true" />
          <p className="text-center sm:text-left text-white/90">
            © 2026 Conform.IA BNDES Platform • Consulta Pública BNDES nº 01/2025
          </p>
        </div>
        <div className="flex items-center space-x-4 text-white/85 font-medium">
          <span className="hover:text-white transition-colors">Harness Engineering Standard</span>
          <span>•</span>
          <span className="hover:text-white transition-colors">Maker-Checker Protocol</span>
        </div>
      </div>
    </footer>
  );
}
