from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ClienteForm
from .models import Cliente


@login_required
def listar_clientes(request):
    busca = request.GET.get('busca', '').strip()
    clientes = Cliente.objects.all()
    if busca:
        clientes = clientes.filter(
            Q(nome__icontains=busca) | Q(cpf__icontains=busca) | Q(email__icontains=busca)
        )
    return render(request, 'clientes/listar.html', {'clientes': clientes, 'busca': busca})


@login_required
def novo_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save()
            messages.success(request, f'Cliente {cliente.nome} cadastrado.')
            return redirect('listar')
    else:
        form = ClienteForm()

    return render(request, 'clientes/cadastrar.html', {'form': form})


@login_required
def editar_cliente(request, id):
    cliente = get_object_or_404(Cliente, id=id)

    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, f'Cliente {cliente.nome} atualizado.')
            return redirect('listar')
    else:
        form = ClienteForm(instance=cliente)

    return render(request, 'clientes/editar.html', {'form': form, 'cliente': cliente})


@login_required
def excluir_cliente(request, id):
    cliente = get_object_or_404(Cliente, id=id)

    if request.method == 'POST':
        nome = cliente.nome
        cliente.delete()
        messages.success(request, f'Cliente {nome} excluído.')
        return redirect('listar')

    return render(request, 'clientes/excluir.html', {'cliente': cliente})
