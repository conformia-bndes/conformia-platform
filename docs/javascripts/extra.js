/**
 * Conform.IA BNDES - Scripts Customizados de Interatividade
 * Padrao: Vanilla JS, sem dependencias externas, alta performance
 */

const enhanceDocumentation = () => {
  // Atalho de teclado para busca rapida pressionando '/'
  if (!document.documentElement.dataset.searchShortcutReady) {
    document.addEventListener("keydown", (e) => {
      if (
        e.key === "/" &&
        !["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)
      ) {
        const searchInput = document.querySelector(".md-search__input");
        if (searchInput) {
          e.preventDefault();
          searchInput.focus();
        }
      }
    });
    document.documentElement.dataset.searchShortcutReady = "true";
  }

  if (window.mermaid) {
    window.mermaid.initialize({
      startOnLoad: false,
      securityLevel: "loose",
      theme: "base",
    });
    window.mermaid.run({ nodes: document.querySelectorAll(".mermaid") });
  }

  // Marcacao automatica de tabelas longas para rolagem horizontal suave
  document.querySelectorAll(".md-typeset table").forEach((table) => {
    if (!table.parentElement.classList.contains("md-typeset__scrollwrap")) {
      const wrapper = document.createElement("div");
      wrapper.className = "md-typeset__scrollwrap";
      table.parentNode.insertBefore(wrapper, table);
      wrapper.appendChild(table);
    }
  });
};

if (typeof document$ !== "undefined") {
  document$.subscribe(enhanceDocumentation);
} else {
  document.addEventListener("DOMContentLoaded", enhanceDocumentation);
}
