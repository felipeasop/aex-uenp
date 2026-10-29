from .models import Carrinho


def carrinho_context(request):
    """
    Context processor que injeta a contagem de itens do carrinho e o objeto carrinho
    em todas as renderizações de templates.
    """
    carrinho = None
    total_itens = 0

    if request.user.is_authenticated:
        carrinho = Carrinho.objects.filter(usuario=request.user).first()
    else:
        session_key = request.session.session_key
        if session_key:
            carrinho = Carrinho.objects.filter(session_key=session_key).first()

    if carrinho:
        total_itens = carrinho.total_itens()

    return {
        'carrinho_atual': carrinho,
        'carrinho_total_itens': total_itens,
    }
