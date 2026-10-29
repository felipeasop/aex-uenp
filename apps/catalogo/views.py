from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.templatetags.static import static
from django.views.decorators.http import require_POST
from .models import Produto, Tag, Colecao, AvisoEstoque, Favorito


def home_view(request):
    """
    Página inicial da loja Lua e Flor: exibe catálogo, filtros e prepara
    os dados dos produtos reais para interação dinâmica.
    """
    produtos = Produto.objects.filter(ativo=True, aprovado=True).prefetch_related('tags', 'fotos')
    tags = Tag.objects.all()
    colecoes = Colecao.objects.filter(is_ativa=True)
    categorias_selecionadas = request.GET.getlist('categoria')
    status_selecionado = request.GET.get('status', '')
    if categorias_selecionadas:
        # Cada categoria marcada precisa pertencer ao produto (lógica E).
        for categoria in categorias_selecionadas:
            produtos = produtos.filter(tags__slug=categoria)
    if status_selecionado:
        # Disponibilidade é uma regra calculada pelo modelo, então este filtro
        # permanece no servidor após carregar os produtos elegíveis.
        produtos = [p for p in produtos if p.status_disponibilidade == status_selecionado]

    context = {
        'produtos': produtos,
        'quantidade_produtos': len(produtos) if isinstance(produtos, list) else produtos.count(),
        'tags': tags,
        'colecoes': colecoes,
        'categorias_selecionadas': categorias_selecionadas,
        'status_selecionado': status_selecionado,
    }
    return render(request, 'catalogo/home.html', context)


def produto_detalhe_api(request, produto_id):
    """Retorna dados de um produto em formato JSON."""
    produto = get_object_or_404(Produto, id=produto_id, ativo=True, aprovado=True)
    fotos = [f.imagem.url for f in produto.fotos.all()]
    if not fotos:
        fotos = [static('img/Logo.png')]

    return JsonResponse({
        'id': produto.id,
        'nome': produto.nome,
        'preco': produto.preco_formatado,
        'status': produto.status_disponibilidade,
        'status_label': produto.status_label,
        'categorias': [t.nome for t in produto.tags.all()],
        'fotos': fotos,
        'tempo': produto.tempo_formatado,
        'descricao': produto.descricao,
    })


@login_required
@require_POST
def solicitar_aviso_estoque(request, produto_id):
    """Permite que um cliente autenticado solicite aviso de retorno ao estoque (Req. F10)."""
    produto = get_object_or_404(Produto, id=produto_id)
    aviso, created = AvisoEstoque.objects.get_or_create(
        cliente=request.user,
        produto=produto
    )
    if created:
        messages.success(request, f'Você será avisada(o) assim que o produto "{produto.nome}" voltar ao estoque!')
    else:
        messages.info(request, f'Você já solicitou aviso para o produto "{produto.nome}".')
    return redirect('catalogo:home')


@login_required
@require_POST
def alternar_favorito(request, produto_id):
    """Adiciona ou remove um produto dos favoritos (Req. F25)."""
    produto = get_object_or_404(Produto, id=produto_id)
    favorito = Favorito.objects.filter(cliente=request.user, produto=produto).first()
    if favorito:
        favorito.delete()
        messages.info(request, f'"{produto.nome}" removido dos seus favoritos.')
    else:
        Favorito.objects.create(cliente=request.user, produto=produto)
        messages.success(request, f'"{produto.nome}" adicionado aos seus favoritos!')
    return redirect('catalogo:home')


def produto_detalhe_view(request, produto_id):
    """Exibe a página individual de detalhes de um produto."""
    produto = get_object_or_404(Produto, id=produto_id, ativo=True, aprovado=True)
    return render(request, 'catalogo/produto_modal.html', {'produto': produto})
