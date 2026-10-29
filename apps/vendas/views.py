from uuid import uuid4
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST
from apps.catalogo.models import Produto, CicloEncomenda
from .models import Carrinho, ItemCarrinho, Cupom, Pedido, ItemPedido, StatusPedido, FilaProducao


def obter_carrinho(request):
    """Obtém ou inicializa o carrinho do usuário ou da sessão visitante."""
    if request.user.is_authenticated:
        carrinho, _ = Carrinho.objects.get_or_create(usuario=request.user)
        # Mescla itens da sessão anônima caso existam
        session_key = request.session.session_key
        if session_key:
            carrinho_anon = Carrinho.objects.filter(session_key=session_key).exclude(id=carrinho.id).first()
            if carrinho_anon:
                for item in carrinho_anon.itens.all():
                    item_user, created = ItemCarrinho.objects.get_or_create(
                        carrinho=carrinho,
                        produto=item.produto,
                        defaults={'quantidade': item.quantidade}
                    )
                    if not created:
                        item_user.quantidade += item.quantidade
                        item_user.save()
                carrinho_anon.delete()
        return carrinho
    else:
        if not request.session.session_key:
            request.session.create()
        carrinho, _ = Carrinho.objects.get_or_create(session_key=request.session.session_key)
        return carrinho


def carrinho_view(request):
    """Exibe o carrinho de compras com itens, subtotal e resumo."""
    carrinho = obter_carrinho(request)
    itens = carrinho.itens.select_related('produto').prefetch_related('produto__fotos')
    subtotal = carrinho.calcular_subtotal()
    desconto = carrinho.calcular_desconto()
    total = carrinho.calcular_total()

    context = {
        'carrinho': carrinho,
        'itens': itens,
        'subtotal': subtotal,
        'desconto': desconto,
        'total': total,
    }
    return render(request, 'vendas/carrinho.html', context)


@require_POST
def adicionar_ao_carrinho(request, produto_id):
    """Adiciona um produto ao carrinho (Req. F08)."""
    produto = get_object_or_404(Produto, id=produto_id, ativo=True, aprovado=True)
    carrinho = obter_carrinho(request)
    item_existente = carrinho.itens.filter(produto=produto).first()
    quantidade_no_carrinho = item_existente.quantidade if item_existente else 0

    if produto.status_disponibilidade == 'esgotado':
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'sucesso': False, 'mensagem': 'Este produto está esgotado.'}, status=400)
        messages.error(request, 'Este produto está esgotado no momento.')
        return redirect('catalogo:home')

    # Validação do ciclo de encomenda para produtos sob encomenda
    if produto.status_disponibilidade == 'encomenda':
        ciclo = produto.ciclo_encomenda or CicloEncomenda.objects.filter(is_aberto=True).first()
        if ciclo:
            vagas = ciclo.vagas_disponiveis()
            if quantidade_no_carrinho + 1 > vagas:
                msg = (
                    f'Limite de encomendas atingido! '
                    f'O ciclo atual só aceita mais {vagas} encomenda(s). '
                    f'Diminua a quantidade de produtos.'
                )
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'sucesso': False, 'mensagem': msg}, status=400)
                messages.error(request, msg)
                return redirect('catalogo:home')

    if produto.status_disponibilidade == 'disponivel' and quantidade_no_carrinho + 1 > produto.estoque:
        msg = f'Estoque insuficiente, o estoque atual desse produto é de {produto.estoque} unidade(s).'
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'sucesso': False, 'mensagem': msg}, status=400)
        messages.error(request, msg)
        return redirect('catalogo:home')

    item, created = ItemCarrinho.objects.get_or_create(
        carrinho=carrinho,
        produto=produto,
        defaults={'quantidade': 1}
    )
    if not created:
        item.quantidade += 1
        item.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'sucesso': True,
            'total_itens': carrinho.total_itens(),
            'subtotal': float(carrinho.calcular_subtotal()),
            'mensagem': f'"{produto.nome}" adicionado ao carrinho!'
        })

    messages.success(request, f'"{produto.nome}" adicionado ao carrinho!')
    return redirect('vendas:carrinho')


@require_POST
def atualizar_item_carrinho(request, item_id):
    """Altera a quantidade ou remove item do carrinho."""
    carrinho = obter_carrinho(request)
    item = get_object_or_404(ItemCarrinho, id=item_id, carrinho=carrinho)
    acao = request.POST.get('acao')

    if acao == 'mais':
        # Validação do ciclo para produtos sob encomenda
        if item.produto.status_disponibilidade == 'encomenda':
            ciclo = item.produto.ciclo_encomenda or CicloEncomenda.objects.filter(is_aberto=True).first()
            if ciclo:
                vagas = ciclo.vagas_disponiveis()
                if item.quantidade + 1 > vagas:
                    msg = (
                        f'Limite de encomendas atingido! '
                        f'O ciclo atual só aceita mais {vagas} encomenda(s). '
                        f'Diminua a quantidade de produtos.'
                    )
                    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                        return JsonResponse({'sucesso': False, 'mensagem': msg}, status=400)
                    messages.error(request, msg)
                    return redirect('vendas:carrinho')
        if item.produto.status_disponibilidade == 'disponivel' and item.quantidade + 1 > item.produto.estoque:
            msg = f'Estoque insuficiente, o estoque atual desse produto é de {item.produto.estoque} unidade(s).'
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'sucesso': False, 'mensagem': msg}, status=400)
            messages.error(request, msg)
            return redirect('vendas:carrinho')
        item.quantidade += 1
        item.save()
    elif acao == 'menos':
        if item.quantidade > 1:
            item.quantidade -= 1
            item.save()
        else:
            item.delete()
    elif acao == 'remover':
        item.delete()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'sucesso': True,
            'total_itens': carrinho.total_itens(),
            'subtotal': float(carrinho.calcular_subtotal()),
            'total': float(carrinho.calcular_total()),
        })

    return redirect('vendas:carrinho')


@require_POST
def aplicar_cupom(request):
    """Valida e aplica cupom de desconto no carrinho."""
    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip().upper()
        carrinho = obter_carrinho(request)
        cupom = Cupom.objects.filter(codigo=codigo, is_ativo=True).first()

        if not cupom:
            messages.error(request, 'Cupom não encontrado ou inválido.')
        else:
            valido, msg = cupom.is_valido(carrinho.calcular_subtotal())
            if valido:
                carrinho.cupom = cupom
                carrinho.save()
                messages.success(request, f'Cupom {cupom.codigo} aplicado com sucesso!')
            else:
                messages.error(request, msg)

    return redirect('vendas:carrinho')


@require_POST
def remover_cupom(request):
    """Remove o cupom aplicado."""
    carrinho = obter_carrinho(request)
    carrinho.cupom = None
    carrinho.save()
    messages.info(request, 'Cupom removido.')
    return redirect('vendas:carrinho')


@login_required(login_url='usuarios:login')
@transaction.atomic
def checkout_view(request):
    """
    Finalização de compra. Exige cliente cadastrado e autenticado (Req. F09).
    """
    carrinho = obter_carrinho(request)
    if not carrinho.itens.exists():
        messages.warning(request, 'Seu carrinho está vazio.')
        return redirect('catalogo:home')

    subtotal = carrinho.calcular_subtotal()
    desconto = carrinho.calcular_desconto()
    total = carrinho.calcular_total()

    if request.method == 'POST':
        # ── Validação do ciclo de encomendas antes de finalizar ──
        # Soma todas as quantidades de itens sob encomenda no carrinho
        itens_carrinho = carrinho.itens.select_related('produto', 'produto__ciclo_encomenda')
        total_encomendas_por_ciclo = {}
        for item_cart in itens_carrinho:
            produto = item_cart.produto
            if produto.status_disponibilidade == 'disponivel' and item_cart.quantidade > produto.estoque:
                messages.error(
                    request,
                    f'Estoque insuficiente, o estoque atual desse produto é de {produto.estoque} unidade(s).'
                )
                return redirect('vendas:carrinho')
            if produto.status_disponibilidade == 'encomenda':
                ciclo = produto.ciclo_encomenda or CicloEncomenda.objects.filter(is_aberto=True).first()
                if ciclo:
                    ciclo_id = ciclo.id
                    total_encomendas_por_ciclo.setdefault(ciclo_id, {'ciclo': ciclo, 'qtd': 0})
                    total_encomendas_por_ciclo[ciclo_id]['qtd'] += item_cart.quantidade

        for info in total_encomendas_por_ciclo.values():
            ciclo = info['ciclo']
            qtd_pedida = info['qtd']
            if not ciclo.cabe_encomenda(qtd_pedida):
                vagas = ciclo.vagas_disponiveis()
                messages.error(
                    request,
                    f'Limite de encomendas atingido! '
                    f'O ciclo "{ciclo.nome}" aceita apenas mais {vagas} produto(s), '
                    f'mas seu carrinho possui {qtd_pedida} encomenda(s). '
                    f'Volte ao carrinho e diminua a quantidade.'
                )
                return redirect('vendas:carrinho')

        # Coleta os dados de entrega local (Req. NF01 / Astah LocalEncontro)
        rua = request.POST.get('rua', '').strip()
        numero_end = request.POST.get('numero_end', '').strip()
        bairro = request.POST.get('bairro', '').strip()
        cidade = request.POST.get('cidade', 'Bandeirantes - PR').strip()
        complemento = request.POST.get('complemento', '').strip()
        observacoes = request.POST.get('observacoes', '').strip()
        metodo_pagamento = request.POST.get('metodo_pagamento', Pedido.MetodoPagamento.PIX)

        # Status inicial do pedido
        status_inicial, _ = StatusPedido.objects.get_or_create(nome='Aguardando Pagamento', defaults={'ordem': 1})

        # Criação do Pedido no banco de dados
        pedido = Pedido.objects.create(
            numero=uuid4().hex,
            cliente=request.user,
            status=status_inicial,
            cupom=carrinho.cupom,
            subtotal=subtotal,
            desconto=desconto,
            frete=0.00,
            valor_total=total,
            metodo_pagamento=metodo_pagamento,
            status_pagamento=Pedido.StatusPagamento.PENDENTE,
            rua=rua,
            numero_end=numero_end,
            complemento=complemento,
            bairro=bairro,
            cidade=cidade,
            observacoes_entrega=observacoes
        )
        # Número definitivo do pedido a partir do id (#LF-2026-0001)
        pedido.numero = f'#LF-{timezone.now().year}-{pedido.id:04d}'
        pedido.save(update_fields=['numero'])

        # Criação dos Itens do Pedido e Fila de Produção
        for item_cart in carrinho.itens.select_related('produto'):
            produto = item_cart.produto
            is_encomenda = (produto.status_disponibilidade == 'encomenda')

            item_pedido = ItemPedido.objects.create(
                pedido=pedido,
                produto=produto,
                quantidade=item_cart.quantidade,
                preco_unitario=produto.preco,
                is_encomenda=is_encomenda,
                status_producao=ItemPedido.StatusProducao.EM_ESPERA if is_encomenda else ItemPedido.StatusProducao.NAO_APLICAVEL
            )

            if is_encomenda:
                # Aloca no ciclo de encomenda ativo
                ciclo = produto.ciclo_encomenda or CicloEncomenda.objects.filter(is_aberto=True).first()
                if ciclo:
                    ciclo.adicionar_encomenda(item_cart.quantidade)

                # Insere na fila de produção (Req. F33, F34)
                posicao = FilaProducao.objects.count() + 1
                FilaProducao.objects.create(
                    item_pedido=item_pedido,
                    posicao=posicao,
                    tempo_estimado_dias=produto.tempo_estimado * item_cart.quantidade
                )
            else:
                # Baixa imediata de estoque para itens a pronta entrega
                if produto.estoque >= item_cart.quantidade:
                    produto.estoque -= item_cart.quantidade
                    produto.save()

        # Registra uso do cupom se houver
        if carrinho.cupom:
            carrinho.cupom.registrar_uso()

        # Esvazia o carrinho após finalização
        carrinho.limpar()

        return redirect('vendas:confirmacao', pedido_id=pedido.id)

    context = {
        'carrinho': carrinho,
        'itens': carrinho.itens.select_related('produto'),
        'subtotal': subtotal,
        'desconto': desconto,
        'total': total,
    }
    return render(request, 'vendas/checkout.html', context)


@login_required(login_url='usuarios:login')
def confirmacao_view(request, pedido_id):
    """Exibe a tela de confirmação do pedido recém-criado."""
    pedido = get_object_or_404(Pedido, id=pedido_id, cliente=request.user)
    return render(request, 'vendas/confirmacao.html', {'pedido': pedido})
