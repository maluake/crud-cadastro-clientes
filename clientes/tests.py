from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .forms import ClienteForm
from .models import Cliente
from .validators import cpf_valido, validar_cpf

# CPFs fictícios gerados apenas para os testes (dígitos verificadores válidos).
CPF_A = '529.982.247-25'
CPF_B = '111.444.777-35'


def dados_cliente(**extra):
    dados = {
        'nome': 'Ana Teste',
        'cpf': CPF_A,
        'email': 'ana@exemplo.com',
        'telefone': '(11) 90000-0000',
        'endereco': 'Rua Fictícia, 100',
        'cidade': 'São Paulo',
        'estado': 'sp',
    }
    dados.update(extra)
    return dados


class ValidacaoCpfTests(TestCase):
    def test_aceita_cpf_valido_com_e_sem_pontuacao(self):
        self.assertTrue(cpf_valido(CPF_A))
        self.assertTrue(cpf_valido('52998224725'))

    def test_recusa_digito_verificador_errado(self):
        self.assertFalse(cpf_valido('529.982.247-26'))

    def test_recusa_sequencias_repetidas_e_tamanho_errado(self):
        self.assertFalse(cpf_valido('111.111.111-11'))
        self.assertFalse(cpf_valido('1234567890'))
        self.assertFalse(cpf_valido(''))

    def test_validador_levanta_erro(self):
        with self.assertRaises(ValidationError):
            validar_cpf('123.456.789-00')


class ClienteFormTests(TestCase):
    def test_normaliza_cpf_e_estado(self):
        form = ClienteForm(data=dados_cliente(cpf='52998224725'))
        self.assertTrue(form.is_valid(), form.errors)
        cliente = form.save()
        self.assertEqual(cliente.cpf, CPF_A)
        self.assertEqual(cliente.estado, 'SP')

    def test_cpf_invalido_mostra_erro_no_campo(self):
        form = ClienteForm(data=dados_cliente(cpf='529.982.247-26'))
        self.assertFalse(form.is_valid())
        self.assertIn('cpf', form.errors)
        self.assertIn('is-invalid', form.fields['cpf'].widget.attrs['class'])

    def test_cpf_duplicado_mesmo_sem_pontuacao(self):
        Cliente.objects.create(**dados_cliente(estado='SP'))
        form = ClienteForm(data=dados_cliente(cpf='52998224725', email='outra@exemplo.com'))
        self.assertFalse(form.is_valid())
        self.assertIn('cpf', form.errors)


class LoginObrigatorioTests(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(**dados_cliente(estado='SP'))

    def test_todas_as_telas_redirecionam_para_o_login(self):
        urls = [
            reverse('listar'),
            reverse('novo'),
            reverse('editar', args=[self.cliente.id]),
            reverse('excluir', args=[self.cliente.id]),
        ]
        for url in urls:
            with self.subTest(url=url):
                resposta = self.client.get(url)
                self.assertRedirects(resposta, f"{reverse('login')}?next={url}")

    def test_post_sem_login_nao_exclui(self):
        self.client.post(reverse('excluir', args=[self.cliente.id]))
        self.assertTrue(Cliente.objects.filter(id=self.cliente.id).exists())

    def test_login_e_logout(self):
        get_user_model().objects.create_user('operador', password='SenhaDeTeste!2026')
        resposta = self.client.post(reverse('login'), {'username': 'operador', 'password': 'SenhaDeTeste!2026'})
        self.assertRedirects(resposta, reverse('listar'))
        resposta = self.client.post(reverse('logout'))
        self.assertRedirects(resposta, reverse('login'))
        self.assertEqual(self.client.get(reverse('listar')).status_code, 302)

    def test_senha_errada_mostra_mensagem(self):
        get_user_model().objects.create_user('operador', password='SenhaDeTeste!2026')
        resposta = self.client.post(reverse('login'), {'username': 'operador', 'password': 'errada'})
        self.assertContains(resposta, 'Usuário ou senha incorretos')


class CrudTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user('operador', password='SenhaDeTeste!2026')
        self.client.force_login(self.usuario)
        self.ana = Cliente.objects.create(**dados_cliente(estado='SP'))
        self.bruno = Cliente.objects.create(**dados_cliente(
            nome='Bruno Exemplo', cpf=CPF_B, email='bruno@teste.com', estado='RJ'))

    def test_listar_mostra_clientes_em_ordem_alfabetica(self):
        resposta = self.client.get(reverse('listar'))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(list(resposta.context['clientes']), [self.ana, self.bruno])

    def test_busca_por_nome_cpf_e_email(self):
        casos = {'bruno': [self.bruno], 'ANA': [self.ana], '111.444': [self.bruno], '@exemplo.com': [self.ana]}
        for termo, esperado in casos.items():
            with self.subTest(termo=termo):
                resposta = self.client.get(reverse('listar'), {'busca': termo})
                self.assertEqual(list(resposta.context['clientes']), esperado)
                self.assertContains(resposta, f'value="{termo}"')

    def test_busca_sem_resultado_mostra_aviso(self):
        resposta = self.client.get(reverse('listar'), {'busca': 'inexistente'})
        self.assertContains(resposta, 'Nenhum cliente encontrado')

    def test_cadastrar(self):
        resposta = self.client.post(reverse('novo'), dados_cliente(
            nome='Carla Nova', cpf='935.411.347-80', email='carla@exemplo.com'))
        self.assertRedirects(resposta, reverse('listar'))
        self.assertTrue(Cliente.objects.filter(nome='Carla Nova', cpf='935.411.347-80').exists())

    def test_cadastrar_com_cpf_invalido_nao_salva(self):
        resposta = self.client.post(reverse('novo'), dados_cliente(nome='Inválido', cpf='000.000.000-00'))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'CPF inválido')
        self.assertFalse(Cliente.objects.filter(nome='Inválido').exists())

    def test_editar(self):
        url = reverse('editar', args=[self.ana.id])
        self.assertEqual(self.client.get(url).status_code, 200)
        resposta = self.client.post(url, dados_cliente(cidade='Campinas'))
        self.assertRedirects(resposta, reverse('listar'))
        self.ana.refresh_from_db()
        self.assertEqual(self.ana.cidade, 'Campinas')

    def test_excluir_pede_confirmacao_e_so_exclui_no_post(self):
        url = reverse('excluir', args=[self.ana.id])
        resposta = self.client.get(url)
        self.assertContains(resposta, 'Deseja realmente excluir')
        self.assertTrue(Cliente.objects.filter(id=self.ana.id).exists())
        resposta = self.client.post(url)
        self.assertRedirects(resposta, reverse('listar'))
        self.assertFalse(Cliente.objects.filter(id=self.ana.id).exists())

    def test_id_inexistente_retorna_404(self):
        self.assertEqual(self.client.get(reverse('editar', args=[9999])).status_code, 404)
        self.assertEqual(self.client.get(reverse('excluir', args=[9999])).status_code, 404)

    def test_str(self):
        self.assertEqual(str(self.ana), 'Ana Teste')
