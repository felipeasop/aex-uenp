/* Interação de interface: envia os filtros ao Django quando forem alterados. */
document.querySelectorAll('[data-auto-submit]').forEach((form) => {
  form.addEventListener('change', (event) => {
    const campo = event.target;
    if (campo.name === 'status' && campo.checked) {
      form.querySelectorAll('input[name="status"]').forEach((opcao) => {
        if (opcao !== campo) opcao.checked = false;
      });
    }
    form.requestSubmit();
  });
});
