from django.shortcuts import render, redirect
from .models import Cliente
from .forms import ClienteForm
from django.shortcuts import render, redirect, get_object_or_404

def listar_clientes(request):
    clientes = Cliente.objects.all()
    return render(request, 'clientes/listar.html', {'clientes': clientes})

def novo_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('listar')

    else:
        form = ClienteForm()

    return render(request, 'clientes/cadastrar.html', {'form': form})

def editar_cliente(request, id):
    cliente = get_object_or_404(Cliente, id=id)

    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)

        if form.is_valid():
            form.save()
            return redirect('listar')

    else:
        form = ClienteForm(instance=cliente)

    return render(
        request,
        'clientes/editar.html',
        {
            'form': form,
            'cliente': cliente
        }
    )


def excluir_cliente(request, id):
    cliente = get_object_or_404(Cliente, id=id)

    if request.method == 'POST':
        cliente.delete()
        return redirect('listar')

    return render(
        request,
        'clientes/excluir.html',
        {
            'cliente': cliente
        }
    )