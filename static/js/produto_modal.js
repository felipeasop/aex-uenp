/**
 * produto_modal.js
 * Abre os detalhes do produto em um modal com overlay borrado,
 * buscando os dados via API JSON sem recarregar a página.
 */
(function () {
  'use strict';

  // ── Referências do DOM ──
  const overlay    = document.getElementById('produto-overlay');
  const modalBody  = document.getElementById('produto-modal-body');
  const btnFechar  = document.getElementById('modal-fechar');
  const pagina     = document.getElementById('pagina');

  if (!overlay || !modalBody) return;

  // ── Abrir modal ao clicar num card de produto ──
  document.querySelectorAll('.card[data-produto-id]').forEach((card) => {
    card.addEventListener('click', (e) => {
      e.preventDefault();
      const id = card.dataset.produtoId;
      abrirModal(id);
    });
  });

  // ── Fechar modal ──
  btnFechar.addEventListener('click', fecharModal);

  overlay.addEventListener('click', (e) => {
    // Fecha ao clicar no fundo (overlay), mas não dentro do modal
    if (e.target === overlay) fecharModal();
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !overlay.hidden) fecharModal();
  });

  // ── Buscar dados e montar modal ──
  async function abrirModal(produtoId) {
    overlay.hidden = false;
    document.body.classList.add('travado');
    pagina.style.filter = 'blur(7px)';
    pagina.style.pointerEvents = 'none';

    modalBody.innerHTML = '<p style="text-align:center;padding:60px;color:var(--cafe-2)">Carregando…</p>';

    try {
      const resp = await fetch('/api/produto/' + produtoId + '/');
      if (!resp.ok) throw new Error(resp.status);
      const p = await resp.json();
      renderModal(p, produtoId);
    } catch (err) {
      modalBody.innerHTML =
        '<p style="text-align:center;padding:60px;color:#c62828">Erro ao carregar produto.</p>';
    }
  }

  function fecharModal() {
    overlay.hidden = true;
    document.body.classList.remove('travado');
    pagina.style.filter = '';
    pagina.style.pointerEvents = '';
  }

  // ── Renderizar conteúdo do modal ──
  function renderModal(p, produtoId) {
    const fotoPrincipal = p.fotos[0] || '';

    // Miniaturas
    const miniaturas = p.fotos
      .map(
        (url, i) =>
          `<button type="button" class="miniatura-btn" data-idx="${i}"
                  aria-label="Foto ${i + 1}"${i === 0 ? ' aria-current="true"' : ''}>
            <img src="${url}" alt="${p.nome}">
          </button>`
      )
      .join('');

    // Chips de categoria + status
    const chips = p.categorias
      .map((c) => `<li>${c}</li>`)
      .concat(`<li>${p.status_label}</li>`)
      .join('');

    // Botão de compra
    let botaoCompra = '';
    if (p.status === 'esgotado') {
      botaoCompra = '<button type="button" class="btn-comprar" disabled>Esgotado</button>';
    } else {
      const label = p.status === 'disponivel' ? 'Comprar' : 'Encomendar';
      botaoCompra = `
        <form method="post" action="/vendas/adicionar/${produtoId}/">
          <input type="hidden" name="csrfmiddlewaretoken" value="${getCsrf()}">
          <button class="btn-comprar" type="submit">${label}</button>
        </form>`;
    }

    modalBody.innerHTML = `
      <div class="galeria">
        <div class="miniaturas">${miniaturas}</div>
        <div class="foto-grande">
          <img id="foto-principal" src="${fotoPrincipal}" alt="${p.nome}">
        </div>
      </div>
      <div class="info">
        <div class="caixa caixa-nome">
          <h2>${p.nome}</h2>
          <p class="preco">R$ ${p.preco}</p>
        </div>
        <div class="caixa caixa-detalhes">
          <ul class="chips">${chips}</ul>
          <p class="tempo">Tempo de produção: <strong>${p.tempo}</strong></p>
          ${botaoCompra}
        </div>
      </div>
      <div class="descricao">
        <h3>Descrição</h3>
        <p>${p.descricao || 'Sem descrição disponível.'}</p>
      </div>
    `;

    // Trocar foto principal ao clicar nas miniaturas
    modalBody.querySelectorAll('.miniatura-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        const idx = parseInt(btn.dataset.idx, 10);
        document.getElementById('foto-principal').src = p.fotos[idx];
        modalBody.querySelectorAll('.miniatura-btn').forEach((b) =>
          b.removeAttribute('aria-current')
        );
        btn.setAttribute('aria-current', 'true');
      });
    });
  }

  // ── Utilitários ──
  function getCsrf() {
    const cookie = document.cookie
      .split('; ')
      .find((c) => c.startsWith('csrftoken='));
    return cookie ? cookie.split('=')[1] : '';
  }
})();

