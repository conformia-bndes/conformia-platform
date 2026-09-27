/**
 * Conform.IA BNDES - Scripts Customizados de Interatividade
 * Padrao: Vanilla JS, sem dependencias externas, alta performance
 */

document.addEventListener("DOMContentLoaded", () => {
  // Atalho de teclado para busca rapida pressionando '/'
  document.addEventListener("keydown", (e) => {
    if (e.key === "/" && !["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)) {
      const searchInput = document.querySelector(".md-search__input");
      if (searchInput) {
        e.preventDefault();
        searchInput.focus();
      }
    }
  });

  // Marcacao automatica de tabelas longas para rolagem horizontal suave
  document.querySelectorAll(".md-typeset table").forEach((table) => {
    if (!table.parentElement.classList.contains("md-typeset__scrollwrap")) {
      const wrapper = document.createElement("div");
      wrapper.className = "md-typeset__scrollwrap";
      table.parentNode.insertBefore(wrapper, table);
      wrapper.appendChild(table);
    }
  });
});
