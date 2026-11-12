import os
import django
from decimal import Decimal
from datetime import date, timedelta
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.usuarios.models import Usuario
from apps.catalogo.models import TipoProduto, Tag, Colecao, CicloEncomenda, Produto, FotoProduto
from apps.vendas.models import StatusPedido, Cupom

def popular():
    usuario_admin, _ = Usuario.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@luaeflor.com.br',
            'first_name': 'Administrador',
            'last_name': 'Lua e Flor',
            'tipo': Usuario.Tipo.ADMIN,
            'is_staff': True,
            'is_superuser': True,
        }
    )
    usuario_admin.set_password('admin123')
    usuario_admin.save()

    operador_user, _ = Usuario.objects.get_or_create(
        username='operador',
        defaults={
            'email': 'operador@luaeflor.com.br',
            'first_name': 'Foo',
            'last_name': 'Bar',
            'tipo': Usuario.Tipo.OPERADOR,
            'is_staff': True,
        }
    )
    operador_user.set_password('operador123')
    operador_user.save()

    cliente_user, _ = Usuario.objects.get_or_create(
        username='cliente@exemplo.com',
        defaults={
            'email': 'cliente@exemplo.com',
            'first_name': 'Maria',
            'last_name': 'Silva',
            'telefone': '(43) 99988-7766',
            'data_nascimento': date(1995, 5, 20),
            'tipo': Usuario.Tipo.CLIENTE,
        }
    )
    cliente_user.set_password('cliente123')
    cliente_user.save()

    status_lista = [
        ('Aguardando Pagamento', 1),
        ('Pagamento Confirmado', 2),
        ('Em Produção', 3),
        ('Pronto para Entrega', 4),
        ('Entregue', 5),
        ('Cancelado', 6),
    ]
    for nome_st, ordem in status_lista:
        StatusPedido.objects.get_or_create(nome=nome_st, defaults={'ordem': ordem})

    ciclo, _ = CicloEncomenda.objects.get_or_create(
        nome='Ciclo da Primavera 2026',
        defaults={
            'limite_maximo': 10,
            'quantidade_atual': 3,
            'is_aberto': True,
        }
    )
    print(f"-> {ciclo} configurado.")

    # 4. Tipos e Tags
    tipo_amigurumi, _ = TipoProduto.objects.get_or_create(
        nome='Amigurumi',
        defaults={'descricao': 'Peças modeladas e tecidas em crochê ponto a ponto.'}
    )
    tipo_chocalho, _ = TipoProduto.objects.get_or_create(
        nome='Chocalho',
        defaults={'descricao': 'Brinquedos sensoriais com argola de madeira lisa e crochê.'}
    )
    tipo_mobile, _ = TipoProduto.objects.get_or_create(
        nome='Móbile',
        defaults={'descricao': 'Decoração suspensa para berço e quartos infantis.'}
    )

    tags_dict = {}
    tags_data = [
        ('Animais', 'animais'),
        ('Fantasia', 'fantasia'),
        ('Plantas', 'plantas'),
        ('Brinquedos', 'brinquedos'),
        ('Decoração', 'decoracao'),
    ]
    for nome_tag, slug_tag in tags_data:
        t, _ = Tag.objects.get_or_create(nome=nome_tag, defaults={'slug': slug_tag})
        tags_dict[slug_tag] = t
    print("-> Tags e Tipos de Produto criados.")

    # 5. Coleções
    col_mar, _ = Colecao.objects.get_or_create(
        titulo='Fundo do Mar',
        defaults={'descricao': 'Criaturas marinhas e amigurumis aquáticos.', 'is_ativa': True}
    )
    col_jardim, _ = Colecao.objects.get_or_create(
        titulo='Jardim Encantado',
        defaults={'descricao': 'Flores, abelhinhas e natureza artesanal.', 'is_ativa': True}
    )

    # 6. Cupons de Desconto
    Cupom.objects.get_or_create(
        codigo='FOFURA10',
        defaults={
            'tipo_desconto': Cupom.TipoDesconto.PERCENTUAL,
            'valor_desconto': Decimal('10.00'),
            'validade': date.today() + timedelta(days=365),
            'limite_uso': 100,
            'is_ativo': True,
        }
    )
    Cupom.objects.get_or_create(
        codigo='BEMVINDA',
        defaults={
            'tipo_desconto': Cupom.TipoDesconto.FIXO,
            'valor_desconto': Decimal('15.00'),
            'valor_minimo': Decimal('100.00'),
            'validade': date.today() + timedelta(days=180),
            'limite_uso': 50,
            'is_ativo': True,
        }
    )
    print("-> Cupons de teste criados: FOFURA10 (10%) e BEMVINDA (R$ 15,00)")

    # 7. Produtos reais com imagens do template
    media_dir = Path(__file__).resolve().parent / 'media' / 'produtos'

    produtos_info = [
        {
            'nome': 'Amigurumi Hornet',
            'preco': Decimal('149.90'),
            'tempo_estimado': 15,
            'estoque': 0, # Encomenda
            'tipo': tipo_amigurumi,
            'colecao': None,
            'tags': ['animais', 'fantasia'],
            'foto_nome': 'amigurumi hornet.jpg',
            'descricao': 'Amigurumi inspirado na personagem Hornet, confeccionado à mão sob encomenda com linha 100% algodão e olhos com trava de segurança.',
        },
        {
            'nome': 'Chocalho Abelha',
            'preco': Decimal('69.90'),
            'tempo_estimado': 10,
            'estoque': 3, # Pronta entrega
            'tipo': tipo_chocalho,
            'colecao': col_jardim,
            'tags': ['brinquedos', 'animais'],
            'foto_nome': 'chocalho abelha.jpg',
            'descricao': 'Chocalho artesanal de abelhinha, com argola de madeira natural macia ao toque e som suave agradável para bebês.',
        },
        {
            'nome': 'Chocalho Água-viva',
            'preco': Decimal('69.90'),
            'tempo_estimado': 10,
            'estoque': 0, # Encomenda
            'tipo': tipo_chocalho,
            'colecao': col_mar,
            'tags': ['brinquedos', 'animais'],
            'foto_nome': 'chocalho agua viva.jpg',
            'descricao': 'Chocalho de água-viva feito em crochê delicado, com argola de madeira e tentáculos macios em tons pastéis.',
        },
        {
            'nome': 'Móbile Fundo do Mar',
            'preco': Decimal('249.90'),
            'tempo_estimado': 15,
            'estoque': 0, # Encomenda
            'tipo': tipo_mobile,
            'colecao': col_mar,
            'tags': ['decoracao', 'fantasia'],
            'foto_nome': 'móbile fundo do mar.jpg',
            'descricao': 'Móbile artesanal com criaturas marinhas em crochê e estrutura de madeira, ideal para compor o berço do bebê.',
        },
        {
            'nome': 'Móbile Jardim',
            'preco': Decimal('229.90'),
            'tempo_estimado': 15,
            'estoque': 0, # Encomenda
            'tipo': tipo_mobile,
            'colecao': col_jardim,
            'tags': ['decoracao', 'plantas'],
            'foto_nome': 'móbile jardim.jpg',
            'descricao': 'Móbile de jardim com flores, folhagens e abelhinhas em crochê, feito à mão ponto a ponto com muito carinho.',
        },
    ]

    for pdata in produtos_info:
        prod, created = Produto.objects.get_or_create(
            nome=pdata['nome'],
            defaults={
                'preco': pdata['preco'],
                'tempo_estimado': pdata['tempo_estimado'],
                'estoque': pdata['estoque'],
                'tipo_produto': pdata['tipo'],
                'colecao': pdata['colecao'],
                'ciclo_encomenda': ciclo,
                'aprovado': True,
                'ativo': True,
                'descricao': pdata['descricao'],
            }
        )
        for tslug in pdata['tags']:
            if tslug in tags_dict:
                prod.tags.add(tags_dict[tslug])

        # Associa foto se arquivo existir
        caminho_foto = media_dir / pdata['foto_nome']
        if caminho_foto.exists() and not prod.fotos.exists():
            # Aponta para o arquivo que já está em media/produtos (sem duplicar)
            FotoProduto.objects.create(
                produto=prod,
                is_principal=True,
                imagem=f"produtos/{pdata['foto_nome']}",
            )

if __name__ == '__main__':
    popular()
