from django.db import models

from .validators import validar_cpf


class Cliente(models.Model):
    nome = models.CharField(max_length=100)
    cpf = models.CharField('CPF', max_length=14, unique=True, validators=[validar_cpf])
    email = models.EmailField('E-mail')
    telefone = models.CharField(max_length=20)
    endereco = models.CharField('Endereço', max_length=200)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=2)

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return self.nome
