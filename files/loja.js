(function () {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const LOGO = document.body.dataset.logo;
  const CATALOGO_PADRAO = [
    { id: 1, nome: 'Coelhinha Lua', preco: '89,90', status: 'disponivel', categorias: ['Animais'], fotos: [LOGO], tempo: 'Pronta entrega', descricao: 'Coelhinha feita à mão com fio macio e acabamento delicado.' },
    { id: 2, nome: 'Raposa do bosque', preco: '119,90', status: 'encomenda', categorias: ['Animais', 'Fantasia'], fotos: [LOGO], tempo: 'Até 10 dias úteis', descricao: 'Raposa artesanal, confeccionada sob encomenda.' },
    { id: 3, nome: 'Cacto florido', preco: '59,90', status: 'disponivel', categorias: ['Plantas'], fotos: [LOGO], tempo: 'Pronta entrega', descricao: 'Um cacto simpático em crochê para alegrar sua estante.' },
    { id: 4, nome: 'Estrelinha', preco: '74,90', status: 'esgotado', categorias: ['Fantasia'], fotos: [LOGO], tempo: 'Sob consulta', descricao: 'Uma estrelinha macia, feita à mão e atualmente indisponível.' }
  ];
  const catalogoEl = $('#dados-produtos');
  const produtos = catalogoEl ? JSON.parse(catalogoEl.textContent) : CATALOGO_PADRAO;
  const lerCarrinho = () => {
    try { return JSON.parse(localStorage.getItem('luaeflor-carrinho') || '{}'); }
    catch { return {}; }
  };
  const gravarCarrinho = carrinho => localStorage.setItem('luaeflor-carrinho', JSON.stringify(carrinho));
  const moeda = valor => 'R$ ' + valor.toFixed(2).replace('.', ',');
  const precoNumero = produto => Number(produto.preco.replace('.', '').replace(',', '.'));
  const atualizarSelos = () => {
    const quantidade = Object.values(lerCarrinho()).reduce((soma, qtd) => soma + qtd, 0);
    $$('[data-carrinho-qtd]').forEach(selo => {
      selo.textContent = quantidade;
      selo.hidden = quantidade === 0;
    });
  };
  const adicionar = id => {
    const produto = produtos.find(item => String(item.id) === String(id));
    if (!produto || produto.status === 'esgotado') return;
    const carrinho = lerCarrinho();
    carrinho[id] = (carrinho[id] || 0) + 1;
    gravarCarrinho(carrinho);
    atualizarSelos();
  };
  atualizarSelos();

  /* ---------- filtros (caixas de seleção) ---------- */
  const lista = $('#produtos');
  if (lista) {
    const cards = $$('.card', lista);
    const filtros = $('#filtros');
    const aplicar = () => {
      const marcados = g => $$(`fieldset[data-grupo="${g}"] input:checked`).map(i => i.value);
      const cats = marcados('categoria'), sts = marcados('status');
      let n = 0;
      cards.forEach(c => {
        const ok = (!cats.length || c.dataset.cats.split('|').some(x => cats.includes(x)))
                && (!sts.length || sts.includes(c.dataset.status));
        c.hidden = !ok; if (ok) n++;
      });
      $('#contagem').textContent = n === 1 ? '1 produto' : n + ' produtos';
      $('#sem-resultado').hidden = n > 0;
    };
    filtros.addEventListener('change', aplicar);
    $('#limpar-filtros').addEventListener('click', () => {
      $$('input', filtros).forEach(i => (i.checked = false)); aplicar();
    });
    const tg = $('.filtros-toggle');
    tg.addEventListener('click', () => {
      const aberto = filtros.classList.toggle('aberto');
      tg.setAttribute('aria-expanded', aberto);
    });

    /* ---------- tela de produto (sobreposição) ---------- */
    const dados = produtos;
    const overlay = $('#overlay');
    const rotulo = { disponivel: 'Comprar', encomenda: 'Encomendar', esgotado: 'Esgotado' };
    let ultimo = null;

    const abrir = id => {
      const p = dados.find(x => String(x.id) === String(id));
      if (!p) return;
      const fotos = p.fotos && p.fotos.length ? p.fotos : [LOGO];
      const foto = $('#m-foto');
      const mostrar = i => {
        foto.src = fotos[i]; foto.alt = p.nome;
        $$('#m-minis button').forEach((b, k) => b.setAttribute('aria-current', k === i));
      };
      $('#m-minis').replaceChildren(...fotos.slice(0, 5).map((src, i) => {
        const b = document.createElement('button');
        b.type = 'button'; b.setAttribute('aria-label', 'Foto ' + (i + 1));
        b.innerHTML = '<img alt="">'; b.firstChild.src = src;
        b.addEventListener('click', () => mostrar(i));
        return b;
      }));
      mostrar(0);

      $('#m-nome').textContent = p.nome;
      $('#m-preco').textContent = 'R$ ' + p.preco;
      $('#m-tempo').textContent = p.tempo || 'sob consulta';
      $('#m-desc').textContent = p.descricao || '';
      $('#m-cats').replaceChildren(...(p.categorias || []).map(c => {
        const li = document.createElement('li'); li.textContent = c; return li;
      }));

      const btn = $('#m-comprar'), nota = $('#m-nota');
      btn.textContent = rotulo[p.status] || 'Comprar';
      btn.dataset.status = p.status;
      btn.disabled = p.status === 'esgotado';
      btn.dataset.id = p.id;
      nota.hidden = p.status === 'disponivel';
      nota.textContent = p.status === 'encomenda'
        ? 'Feito sob encomenda: começamos a produção depois do seu pedido.'
        : 'Este amigurumi esgotou. Em breve podemos fazer outro!';

      ultimo = document.activeElement;
      overlay.hidden = false; document.body.classList.add('travado');
      $('#m-fechar').focus();
    };
    const fechar = () => {
      overlay.hidden = true; document.body.classList.remove('travado');
      if (ultimo) ultimo.focus();
    };
    lista.addEventListener('click', e => {
      const c = e.target.closest('.card'); if (c) abrir(c.dataset.id);
    });
    $('#m-fechar').addEventListener('click', fechar);
    $('#m-comprar').addEventListener('click', () => {
      adicionar($('#m-comprar').dataset.id);
      fechar();
      window.location.href = 'carrinho.html';
    });
    overlay.addEventListener('click', e => { if (e.target === overlay) fechar(); });
    document.addEventListener('keydown', e => { if (e.key === 'Escape' && !overlay.hidden) fechar(); });
  }

  /* ---------- carrinho local ---------- */
  const listaCarrinho = $('#itens-carrinho');
  if (listaCarrinho) {
    const atualizarCarrinho = () => {
      const carrinho = lerCarrinho();
      const entradas = Object.entries(carrinho).filter(([, qtd]) => qtd > 0);
      const conteudo = $('#carrinho-conteudo'), vazio = $('#carrinho-vazio');
      conteudo.hidden = entradas.length === 0;
      vazio.hidden = entradas.length > 0;
      listaCarrinho.replaceChildren();
      let total = 0;
      entradas.forEach(([id, quantidade]) => {
        const produto = produtos.find(item => String(item.id) === String(id));
        if (!produto) return;
        const subtotal = precoNumero(produto) * quantidade;
        total += subtotal;
        const item = document.createElement('li');
        item.className = 'item';
        item.innerHTML = `<img alt=""><div class="item-info"><h2></h2><p class="item-unit"></p></div><div class="qtd"><button type="button" data-acao="menos" aria-label="Diminuir">−</button><output></output><button type="button" data-acao="mais" aria-label="Aumentar">+</button></div><p class="item-total"></p><button type="button" class="link" data-acao="remover">Remover</button>`;
        item.dataset.id = id;
        $('img', item).src = (produto.fotos && produto.fotos[0]) || LOGO;
        $('img', item).alt = produto.nome;
        $('h2', item).textContent = produto.nome;
        $('.item-unit', item).textContent = moeda(precoNumero(produto)) + ' cada';
        $('output', item).textContent = quantidade;
        $('.item-total', item).textContent = moeda(subtotal);
        listaCarrinho.append(item);
      });
      $('#subtotal').textContent = moeda(total);
      $('#total').textContent = moeda(total);
      atualizarSelos();
    };
    listaCarrinho.addEventListener('click', event => {
      const botao = event.target.closest('[data-acao]');
      if (!botao) return;
      const item = botao.closest('.item'), carrinho = lerCarrinho(), id = item.dataset.id;
      if (botao.dataset.acao === 'remover' || (botao.dataset.acao === 'menos' && carrinho[id] <= 1)) delete carrinho[id];
      else if (botao.dataset.acao === 'mais') carrinho[id] += 1;
      else carrinho[id] -= 1;
      gravarCarrinho(carrinho);
      atualizarCarrinho();
    });
    $('#finalizar').addEventListener('click', event => {
      event.preventDefault();
      const carrinho = lerCarrinho();
      const itens = Object.entries(carrinho).map(([id, quantidade]) => {
        const produto = produtos.find(item => String(item.id) === String(id));
        return produto ? { id, quantidade, nome: produto.nome, preco: precoNumero(produto) } : null;
      }).filter(Boolean);
      localStorage.setItem('luaeflor-pedido', JSON.stringify({ numero: 'LF-' + Date.now().toString().slice(-6), itens }));
      gravarCarrinho({});
      window.location.href = 'confirmacao.html';
    });
    atualizarCarrinho();
  }

  /* ---------- confirmação local ---------- */
  const itensConfirmacao = $('#itens-confirmacao');
  if (itensConfirmacao) {
    try {
      const pedido = JSON.parse(localStorage.getItem('luaeflor-pedido') || 'null');
      if (pedido && pedido.itens.length) {
        $('#numero-pedido').textContent = '#' + pedido.numero;
        let total = 0;
        pedido.itens.forEach(item => {
          const subtotal = item.preco * item.quantidade;
          total += subtotal;
          const linha = document.createElement('li');
          const nome = document.createElement('span'), valor = document.createElement('span');
          nome.textContent = item.quantidade + '× ' + item.nome;
          valor.textContent = moeda(subtotal);
          linha.append(nome, valor);
          itensConfirmacao.append(linha);
        });
        $('#total-confirmacao').textContent = moeda(total);
      }
    } catch { /* A página ainda funciona sem um pedido salvo. */ }
  }

  /* ---------- abas entrar / criar conta ---------- */
  $$('.abas [data-aba]').forEach(b => b.addEventListener('click', () => {
    $$('.abas [data-aba]').forEach(x => x.setAttribute('aria-selected', x === b));
    $$('[data-painel]').forEach(p => (p.hidden = p.dataset.painel !== b.dataset.aba));
  }));
  $$('form[data-painel]').forEach(form => form.addEventListener('submit', event => {
    event.preventDefault();
    if (form.dataset.painel === 'criar' && form.elements.password1.value !== form.elements.password2.value) {
      form.elements.password2.setCustomValidity('As senhas precisam ser iguais.');
      form.reportValidity();
      form.elements.password2.setCustomValidity('');
      return;
    }
    window.location.href = 'confirmacao.html';
  }));
})();
