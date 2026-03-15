from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Produto, Receita, Ingrediente, Compra, ItemCompra, Cliente, Pedido, ItemPedido
import json
from datetime import date, timedelta
from collections import defaultdict
from django.core.paginator import Paginator
from decimal import Decimal
import calendar
import csv

STATUS_CHOICES = ['Pendente', 'Confirmado', 'Em produção', 'Pronto', 'Entregue', 'Cancelado']


def _normalizar_chave(texto):
    return str(texto or '').strip().lower().replace(' ', '_')


def _ler_linhas_planilha(arquivo):
    nome = arquivo.name.lower()

    if nome.endswith('.csv'):
        conteudo = arquivo.read().decode('utf-8-sig')
        leitor = csv.DictReader(conteudo.splitlines())
        return [dict(linha) for linha in leitor]

    if nome.endswith('.xlsx'):
        try:
            from openpyxl import load_workbook
        except Exception:
            raise RuntimeError('Para importar .xlsx, instale o pacote openpyxl no ambiente Python.')

        wb = load_workbook(filename=arquivo, data_only=True)
        ws = wb.active

        cabecalho = []
        linhas = []
        for idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
            if idx == 1:
                cabecalho = [str(c or '').strip() for c in row]
                continue
            if not any(c is not None and str(c).strip() for c in row):
                continue
            registro = {}
            for i, coluna in enumerate(cabecalho):
                if not coluna:
                    continue
                registro[coluna] = row[i] if i < len(row) else None
            linhas.append(registro)
        return linhas

    raise RuntimeError('Formato não suportado. Use arquivos .csv ou .xlsx')


def importar_planilha(request):
    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        arquivo = request.FILES.get('arquivo')

        if not arquivo:
            messages.error(request, 'Selecione um arquivo para importar.')
            return redirect('/importar/')

        try:
            linhas = _ler_linhas_planilha(arquivo)
        except RuntimeError as e:
            messages.error(request, str(e))
            return redirect('/importar/')
        except Exception:
            messages.error(request, 'Não foi possível ler a planilha. Verifique o arquivo.')
            return redirect('/importar/')

        criados = 0
        atualizados = 0
        ignorados = 0

        for linha in linhas:
            normalizada = {_normalizar_chave(k): v for k, v in linha.items()}

            if tipo == 'ingredientes':
                nome = normalizada.get('item') or normalizada.get('nome')
                valor_pacote = normalizada.get('valor_do_pacote') or normalizada.get('valor_pacote') or 0
                gramas = normalizada.get('gramas_por_unidade') or normalizada.get('gramas_unidade') or 0
                estoque_inicial = normalizada.get('estoque_inicial') or normalizada.get('estoque') or 0

                if not nome:
                    ignorados += 1
                    continue

                ingrediente, created = Ingrediente.objects.get_or_create(nome=str(nome).strip())
                ingrediente.valor_pacote = valor_pacote or 0
                ingrediente.gramas_por_unidade = gramas or 0
                if estoque_inicial not in (None, ''):
                    ingrediente.estoque_atual = estoque_inicial
                ingrediente.save()

                if created:
                    criados += 1
                else:
                    atualizados += 1

            elif tipo == 'produtos':
                nome = normalizada.get('produto') or normalizada.get('nome')
                preco = normalizada.get('preco') or normalizada.get('preco_venda') or 0

                if not nome:
                    ignorados += 1
                    continue

                produto, created = Produto.objects.get_or_create(nome=str(nome).strip())
                produto.preco_venda = preco or 0
                produto.save()

                if created:
                    criados += 1
                else:
                    atualizados += 1

            else:
                messages.error(request, 'Tipo de importação inválido.')
                return redirect('/importar/')

        messages.success(
            request,
            f'Importação concluída: {criados} criados, {atualizados} atualizados, {ignorados} ignorados.'
        )
        return redirect('/importar/')

    return render(request, 'importar_planilha.html')


def calcular_necessidades_pedido(pedido):
    totais = defaultdict(lambda: Decimal('0'))
    itens = ItemPedido.objects.filter(pedido=pedido).select_related('produto')
    for item in itens:
        receitas = Receita.objects.filter(produto=item.produto).select_related('ingrediente')
        for r in receitas:
            totais[r.ingrediente_id] += Decimal(r.quantidade) * Decimal(item.quantidade)

    ingredientes = Ingrediente.objects.filter(id__in=totais.keys())
    por_id = {i.id: i for i in ingredientes}

    preview = []
    for ingrediente_id, necessario in totais.items():
        ingrediente = por_id.get(ingrediente_id)
        if not ingrediente:
            continue
        estoque_atual = Decimal(ingrediente.estoque_atual)
        gramas_unidade = Decimal(ingrediente.gramas_por_unidade or 0)
        if gramas_unidade > 0:
            necessario_pacotes = necessario / gramas_unidade
            saldo_final = estoque_atual - necessario_pacotes
            suficiente = saldo_final >= 0
        else:
            necessario_pacotes = Decimal('0')
            saldo_final = estoque_atual
            suficiente = False

        preview.append({
            'ingrediente': ingrediente,
            'necessario': necessario,
            'necessario_pacotes': necessario_pacotes,
            'estoque_atual': estoque_atual,
            'saldo_final': saldo_final,
            'suficiente': suficiente,
        })
    preview.sort(key=lambda x: x['ingrediente'].nome.lower())
    return preview


def dashboard(request):
    hoje = date.today()
    pedidos_hoje = Pedido.objects.filter(data_entrega=hoje).count()
    pedidos_pendentes = Pedido.objects.filter(status__in=['Pendente', 'Confirmado', 'Em produção']).count()
    estoque_baixo = Ingrediente.objects.filter(estoque_atual__lte=1).order_by('estoque_atual', 'nome')
    return render(request, "dashboard.html", {
        'pedidos_hoje': pedidos_hoje,
        'pedidos_pendentes': pedidos_pendentes,
        'estoque_baixo': estoque_baixo,
        'estoque_baixo_total': estoque_baixo.count(),
    })


def ingredientes(request):
    if request.method == "POST":
        estoque_inicial = request.POST.get("estoque_inicial") or 0
        Ingrediente.objects.create(
            nome=request.POST["nome"],
            valor_pacote=request.POST["valor_pacote"],
            gramas_por_unidade=request.POST["gramas_por_unidade"],
            estoque_atual=estoque_inicial,
        )
    lista = Ingrediente.objects.all()
    return render(request, "ingredientes.html", {"ingredientes": lista})


def ingrediente_excluir(request, ingrediente_id):
    if request.method != "POST":
        return redirect('/ingredientes/')

    ingrediente = Ingrediente.objects.filter(id=ingrediente_id).first()
    if not ingrediente:
        messages.error(request, 'Ingrediente não encontrado.')
        return redirect('/ingredientes/')

    if Receita.objects.filter(ingrediente=ingrediente).exists() or ItemCompra.objects.filter(ingrediente=ingrediente).exists():
        messages.error(request, 'Não é possível excluir: ingrediente já está em receita ou compras.')
        return redirect('/ingredientes/')

    nome = ingrediente.nome
    ingrediente.delete()
    messages.success(request, f'Ingrediente "{nome}" removido com sucesso.')
    return redirect('/ingredientes/')


# 🍫 NOVO PRODUTO + RECEITA INLINE

def produto_novo(request):
    if request.method == "POST":
        produto = Produto.objects.create(
            nome=request.POST["nome"],
            preco_venda=request.POST["preco"],
            imagem=request.FILES.get("imagem")
        )
        for ingr in Ingrediente.objects.all():
            val = request.POST.get(f"qtd_{ingr.id}", "").strip()
            if val:
                try:
                    qtd = float(val)
                    if qtd > 0:
                        Receita.objects.create(produto=produto, ingrediente=ingr, quantidade=qtd)
                except ValueError:
                    pass
        return redirect('/produtos/')
    ingredientes_q = request.GET.get("q", "").strip()
    ingredientes_qs = Ingrediente.objects.all().order_by("nome")
    if ingredientes_q:
        ingredientes_qs = ingredientes_qs.filter(nome__icontains=ingredientes_q)
    paginator = Paginator(ingredientes_qs, 12)
    page_obj_ingredientes = paginator.get_page(request.GET.get("page"))
    return render(request, "produto_novo.html", {
        "ingredientes": page_obj_ingredientes,
        "ingredientes_q": ingredientes_q,
    })


# 👁️ LISTA DE PRODUTOS

def produtos(request):
    lista = Produto.objects.all().order_by('nome')
    produtos_data = []

    for produto in lista:
        receitas = Receita.objects.filter(produto=produto).select_related('ingrediente')
        custo_receita = sum(r.custo() for r in receitas)
        margem_valor = produto.preco_venda - custo_receita
        if custo_receita > 0:
            margem_percentual = (margem_valor / custo_receita) * 100
        else:
            margem_percentual = None

        produtos_data.append({
            'produto': produto,
            'custo_receita': custo_receita,
            'margem_valor': margem_valor,
            'margem_percentual': margem_percentual,
        })

    return render(request, "produtos.html", {"produtos_data": produtos_data})


def produto_editar(request, produto_id):
    produto = Produto.objects.filter(id=produto_id).first()
    if not produto:
        messages.error(request, 'Produto não encontrado.')
        return redirect('/produtos/')

    if request.method == 'POST':
        produto.nome = request.POST.get('nome', produto.nome)
        produto.preco_venda = request.POST.get('preco', produto.preco_venda)

        if request.POST.get('remover_imagem') == 'on' and produto.imagem:
            produto.imagem.delete(save=False)
            produto.imagem = None

        nova_imagem = request.FILES.get('imagem')
        if nova_imagem:
            if produto.imagem:
                produto.imagem.delete(save=False)
            produto.imagem = nova_imagem

        produto.save()
        messages.success(request, 'Produto atualizado com sucesso.')
        return redirect('/produtos/')

    return render(request, 'produto_editar.html', {'produto': produto})


def produto_excluir(request, produto_id):
    if request.method != "POST":
        return redirect('/produtos/')

    produto = Produto.objects.filter(id=produto_id).first()
    if not produto:
        messages.error(request, 'Produto não encontrado.')
        return redirect('/produtos/')

    if ItemPedido.objects.filter(produto=produto).exists():
        messages.error(request, 'Não é possível excluir: produto já possui pedidos vinculados.')
        return redirect('/produtos/')

    nome = produto.nome
    produto.delete()
    messages.success(request, f'Produto "{nome}" removido com sucesso.')
    return redirect('/produtos/')


# 📋 RECEITA DE UM PRODUTO

def receita_produto(request, produto_id):
    produto = Produto.objects.get(id=produto_id)
    if request.method == "POST":
        Receita.objects.create(
            produto=produto,
            ingrediente_id=request.POST["ingrediente"],
            quantidade=request.POST["quantidade"]
        )

    ingrediente_q = request.GET.get("ingrediente_q", "").strip()
    receitas = Receita.objects.filter(produto=produto).select_related("ingrediente")
    if ingrediente_q:
        receitas = receitas.filter(ingrediente__nome__icontains=ingrediente_q)

    paginator = Paginator(receitas.order_by("ingrediente__nome"), 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    ingredientes = Ingrediente.objects.all()
    custo_total = sum(r.custo() for r in Receita.objects.filter(produto=produto).select_related("ingrediente"))
    return render(request, "receita.html", {
        "produto": produto,
        "receitas": page_obj,
        "ingredientes": ingredientes,
        "custo_total": custo_total,
        "ingrediente_q": ingrediente_q,
    })


# 📋 COMPRAS - ESTOQUE

def compras(request):
    if request.method == "POST":
        data_str = request.POST.get("data") or str(date.today())
        local = request.POST.get("local", "")
        compra = Compra.objects.create(data=data_str, local=local)

        ingrediente_ids = request.POST.getlist("ingrediente_id")
        quantidades_gramas = request.POST.getlist("quantidade_gramas")
        quantidades_pacotes = request.POST.getlist("quantidade_pacotes")
        custos = request.POST.getlist("custo")

        for i, ingr_id in enumerate(ingrediente_ids):
            if not ingr_id:
                continue
            qtd_g = quantidades_gramas[i] if i < len(quantidades_gramas) else "0"
            qtd_p = quantidades_pacotes[i] if i < len(quantidades_pacotes) else "0"
            cst = custos[i] if i < len(custos) else "0"

            try:
                ingrediente = Ingrediente.objects.filter(id=ingr_id).first()
                if not ingrediente:
                    continue

                gramas_unidade = Decimal(ingrediente.gramas_por_unidade or 0)
                qtd_gramas_dec = Decimal(str(qtd_g or 0))
                qtd_pacotes_dec = Decimal(str(qtd_p or 0))

                if qtd_gramas_dec <= 0 and qtd_pacotes_dec > 0 and gramas_unidade > 0:
                    qtd_gramas_dec = qtd_pacotes_dec * gramas_unidade

                if qtd_gramas_dec > 0:
                    item = ItemCompra.objects.create(
                        compra=compra,
                        ingrediente=ingrediente,
                        quantidade=qtd_gramas_dec,
                        custo_total=cst or 0
                    )

                    if gramas_unidade > 0:
                        pacotes_entrada = Decimal(item.quantidade) / gramas_unidade
                        ingrediente.estoque_atual = Decimal(ingrediente.estoque_atual) + pacotes_entrada
                        ingrediente.save()
            except ValueError:
                pass
            except Exception:
                pass

    ingredientes = Ingrediente.objects.all()
    produtos = Produto.objects.all()

    receitas_por_produto = {}
    for produto in produtos:
        receitas = Receita.objects.filter(produto=produto).select_related('ingrediente')
        receitas_por_produto[str(produto.id)] = [
            {'id': r.ingrediente.id, 'nome': r.ingrediente.nome, 'quantidade': float(r.quantidade)}
            for r in receitas
        ]

    compras_list = Compra.objects.prefetch_related('itemcompra_set__ingrediente').order_by("-data")
    return render(request, "compras.html", {
        "ingredientes": ingredientes,
        "produtos": produtos,
        "compras": compras_list,
        "receitas_json": json.dumps(receitas_por_produto),
        "today": date.today(),
    })


# 📦 PEDIDOS

def pedidos(request):
    status_filter = request.GET.get('status', '')
    qs = Pedido.objects.select_related('cliente').prefetch_related('itempedido_set__produto')
    if status_filter:
        qs = qs.filter(status=status_filter)
    lista = qs.order_by('data_entrega')
    return render(request, 'pedidos.html', {
        'pedidos': lista,
        'status_filter': status_filter,
        'status_choices': STATUS_CHOICES,
    })


def pedido_novo(request):
    if request.method == 'POST':
        telefone = request.POST.get('cliente_telefone', '').strip()
        nome = request.POST.get('cliente_nome', '').strip()
        endereco = request.POST.get('cliente_endereco', '').strip()

        cliente, _ = Cliente.objects.get_or_create(
            telefone=telefone,
            defaults={'nome': nome, 'endereco': endereco}
        )
        if nome:
            cliente.nome = nome
        if endereco:
            cliente.endereco = endereco
        cliente.save()

        pedido = Pedido.objects.create(
            cliente=cliente,
            data_entrega=request.POST['data_entrega'],
            taxa_entrega=request.POST.get('taxa_entrega') or 0,
            observacoes=request.POST.get('observacoes', ''),
            status='Pendente'
        )

        produto_ids = request.POST.getlist('produto_id')
        quantidades = request.POST.getlist('quantidade')
        for i, pid in enumerate(produto_ids):
            if not pid:
                continue
            try:
                qtd = int(quantidades[i]) if i < len(quantidades) else 1
                if qtd > 0:
                    produto = Produto.objects.get(id=pid)
                    ItemPedido.objects.create(
                        pedido=pedido,
                        produto=produto,
                        quantidade=qtd,
                        preco_unitario=produto.preco_venda
                    )
            except (ValueError, Produto.DoesNotExist):
                pass

        return redirect(f'/pedidos/{pedido.id}/')

    produtos_list = Produto.objects.all()
    clientes = Cliente.objects.order_by('nome')
    return render(request, 'pedido_novo.html', {
        'produtos': produtos_list,
        'clientes': clientes,
        'today': date.today(),
        'status_choices': STATUS_CHOICES,
    })


def pedido_detalhe(request, pedido_id):
    pedido = Pedido.objects.select_related('cliente').get(id=pedido_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'status':
            pedido.status = request.POST['status']
            pedido.save()
        elif action == 'add_item':
            if pedido.baixa_estoque_aprovada:
                messages.error(request, 'Baixa de estoque já aprovada. Não é possível alterar itens deste pedido.')
                return redirect(f'/pedidos/{pedido_id}/')
            try:
                produto = Produto.objects.get(id=request.POST['produto_id'])
                ItemPedido.objects.create(
                    pedido=pedido,
                    produto=produto,
                    quantidade=int(request.POST['quantidade']),
                    preco_unitario=produto.preco_venda
                )
            except (Produto.DoesNotExist, ValueError):
                pass
        elif action == 'remove_item':
            if pedido.baixa_estoque_aprovada:
                messages.error(request, 'Baixa de estoque já aprovada. Não é possível alterar itens deste pedido.')
                return redirect(f'/pedidos/{pedido_id}/')
            ItemPedido.objects.filter(id=request.POST['item_id'], pedido=pedido).delete()
        elif action == 'aprovar_baixa_estoque':
            if pedido.baixa_estoque_aprovada:
                messages.error(request, 'A baixa deste pedido já foi aprovada anteriormente.')
                return redirect(f'/pedidos/{pedido_id}/')

            preview = calcular_necessidades_pedido(pedido)
            if any(not p['suficiente'] for p in preview):
                messages.error(request, 'Estoque insuficiente para aprovar a baixa. Ajuste o estoque primeiro.')
                return redirect(f'/pedidos/{pedido_id}/')

            for p in preview:
                ingrediente = p['ingrediente']
                ingrediente.estoque_atual = p['saldo_final']
                ingrediente.save()

            pedido.baixa_estoque_aprovada = True
            pedido.save()
            messages.success(request, 'Baixa de estoque aprovada e aplicada com sucesso.')
        return redirect(f'/pedidos/{pedido_id}/')

    itens = ItemPedido.objects.filter(pedido=pedido).select_related('produto')
    produtos_list = Produto.objects.all()
    total = sum(i.subtotal() for i in itens)
    total_com_entrega = total + pedido.taxa_entrega
    estoque_preview = calcular_necessidades_pedido(pedido)
    faltas_estoque = [p for p in estoque_preview if not p['suficiente']]
    return render(request, 'pedido_detalhe.html', {
        'pedido': pedido,
        'itens': itens,
        'produtos': produtos_list,
        'total': total,
        'total_com_entrega': total_com_entrega,
        'status_choices': STATUS_CHOICES,
        'estoque_preview': estoque_preview,
        'tem_falta_estoque': len(faltas_estoque) > 0,
    })


# 📅 AGENDA

def agenda(request):
    hoje = date.today()
    mes_param = request.GET.get('mes', '')
    if mes_param:
        try:
            ano, mes = map(int, mes_param.split('-'))
        except ValueError:
            ano, mes = hoje.year, hoje.month
    else:
        ano, mes = hoje.year, hoje.month

    primeiro_dia = date(ano, mes, 1)
    if mes == 12:
        prox_mes = date(ano + 1, 1, 1)
    else:
        prox_mes = date(ano, mes + 1, 1)

    pedidos_qs = Pedido.objects.filter(
        data_entrega__gte=primeiro_dia,
        data_entrega__lt=prox_mes
    ).select_related('cliente').prefetch_related('itempedido_set__produto').order_by('data_entrega')

    por_data = defaultdict(list)
    for p in pedidos_qs:
        por_data[p.data_entrega].append(p)

    cal = calendar.Calendar(firstweekday=6)
    semanas = []
    for semana in cal.monthdatescalendar(ano, mes):
        semana_items = []
        for d in semana:
            semana_items.append({
                'data': d,
                'no_mes': d.month == mes,
                'hoje': d == hoje,
                'pedidos': por_data.get(d, []),
            })
        semanas.append(semana_items)

    mes_anterior = primeiro_dia - timedelta(days=1)
    mes_seguinte = prox_mes

    return render(request, 'agenda.html', {
        'semanas': semanas,
        'mes_data': primeiro_dia,
        'mes_anterior': f"{mes_anterior.year}-{mes_anterior.month:02d}",
        'mes_seguinte': f"{mes_seguinte.year}-{mes_seguinte.month:02d}",
    })


# 🌐 PÁGINAS PÚBLICAS

def catalogo(request):
    produtos_list = Produto.objects.all()
    return render(request, 'catalogo.html', {'produtos': produtos_list})


def consulta_pedido(request):
    pedido = None
    erro = None
    if request.method == 'POST':
        pedido_id = request.POST.get('pedido_id', '').strip()
        telefone = request.POST.get('telefone', '').strip()
        if pedido_id and telefone:
            try:
                pedido = Pedido.objects.select_related('cliente').prefetch_related(
                    'itempedido_set__produto'
                ).get(id=pedido_id, cliente__telefone=telefone)
            except (Pedido.DoesNotExist, ValueError):
                erro = 'Pedido não encontrado. Verifique o número do pedido e o telefone cadastrado.'
        else:
            erro = 'Preencha o número do pedido e o telefone.'
    return render(request, 'consulta_pedido.html', {'pedido': pedido, 'erro': erro})
