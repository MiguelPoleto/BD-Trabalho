(() => {
  const normalize = (value) =>
    value
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLocaleLowerCase("pt-BR")
      .trim();

  document.querySelectorAll("[data-table-filter]").forEach((toolbar) => {
    const table = document.querySelector(toolbar.dataset.table);
    if (!table) return;

    const rows = [...table.querySelectorAll("[data-filter-row]")];
    const query = toolbar.querySelector("[data-search-input]");
    const count = toolbar.querySelector("[data-filter-count]");
    const emptyState = toolbar.parentElement.querySelector("[data-filter-empty]");
    const controls = [
      ...toolbar.querySelectorAll("[data-filter-key], [data-date-from], [data-date-to]"),
    ];

    const applyFilters = () => {
      const term = normalize(query?.value ?? "");
      let visible = 0;

      rows.forEach((row) => {
        let matches = !term || normalize(row.dataset.search ?? "").includes(term);

        controls.forEach((control) => {
          if (!matches || !control.value) return;

          if (control.dataset.filterKey) {
            matches =
              normalize(row.dataset[control.dataset.filterKey] ?? "") ===
              normalize(control.value);
          } else if (control.hasAttribute("data-date-from")) {
            matches = row.dataset.date >= control.value;
          } else if (control.hasAttribute("data-date-to")) {
            matches = row.dataset.date <= control.value;
          }
        });

        row.hidden = !matches;
        if (matches) visible += 1;
      });

      if (count) {
        const label = toolbar.dataset.itemLabel ?? "resultados";
        count.textContent =
          visible === rows.length
            ? `${visible} ${label}`
            : `${visible} de ${rows.length} ${label}`;
      }

      if (emptyState) emptyState.hidden = visible !== 0;
    };

    query?.addEventListener("input", applyFilters);
    controls.forEach((control) => control.addEventListener("change", applyFilters));
    toolbar.querySelector("[data-filter-reset]")?.addEventListener("click", () => {
      if (query) query.value = "";
      controls.forEach((control) => {
        control.value = "";
      });
      applyFilters();
      query?.focus();
    });

    applyFilters();
  });
})();
