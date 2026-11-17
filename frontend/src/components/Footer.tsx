export function Footer() {
  return (
    <footer className="bg-white border-t border-slate-200 py-6 text-center text-xs text-slate-500">
      <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row justify-between items-center gap-2">
        <p>© 2026 Conform.IA BNDES Platform • Consulta Pública BNDES nº 01/2025</p>
        <div className="flex space-x-4">
          <span className="hover:text-slate-700">Harness Engineering Standard</span>
          <span>•</span>
          <span className="hover:text-slate-700">Maker-Checker Protocol</span>
        </div>
      </div>
    </footer>
  );
}
