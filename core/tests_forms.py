from django import forms
from django.test import SimpleTestCase

from core.forms import BootstrapForm


class FormularioExemplo(BootstrapForm):
    nome = forms.CharField()
    email = forms.EmailField()
    idade = forms.IntegerField()
    descricao = forms.CharField(
        widget=forms.Textarea
    )
    categoria = forms.ChoiceField(
        choices=[
            ('a', 'Categoria A'),
            ('b', 'Categoria B'),
        ]
    )
    categorias = forms.MultipleChoiceField(
        choices=[
            ('a', 'Categoria A'),
            ('b', 'Categoria B'),
        ]
    )
    ativo = forms.BooleanField(
        required=False
    )
    opcao = forms.ChoiceField(
        choices=[
            ('sim', 'Sim'),
            ('nao', 'Não'),
        ],
        widget=forms.RadioSelect
    )


class FormularioClasseExistente(BootstrapForm):
    nome = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'class': 'campo-personalizado'
            }
        )
    )


class BootstrapFormMixinTestCase(SimpleTestCase):
    def test_aplica_form_control_em_texto(self):
        form = FormularioExemplo()

        self.assertIn(
            'form-control',
            form.fields['nome'].widget.attrs['class']
        )

    def test_aplica_form_control_em_email(self):
        form = FormularioExemplo()

        self.assertIn(
            'form-control',
            form.fields['email'].widget.attrs['class']
        )

    def test_aplica_form_control_em_numero(self):
        form = FormularioExemplo()

        self.assertIn(
            'form-control',
            form.fields['idade'].widget.attrs['class']
        )

    def test_aplica_form_control_em_textarea(self):
        form = FormularioExemplo()

        self.assertIn(
            'form-control',
            form.fields['descricao'].widget.attrs['class']
        )

    def test_aplica_form_select_em_select(self):
        form = FormularioExemplo()

        self.assertIn(
            'form-select',
            form.fields['categoria'].widget.attrs['class']
        )

    def test_aplica_form_select_em_select_multiplo(self):
        form = FormularioExemplo()

        self.assertIn(
            'form-select',
            form.fields['categorias'].widget.attrs['class']
        )

    def test_aplica_form_check_input_em_checkbox(self):
        form = FormularioExemplo()

        self.assertIn(
            'form-check-input',
            form.fields['ativo'].widget.attrs['class']
        )

    def test_aplica_form_check_input_em_radio(self):
        form = FormularioExemplo()

        self.assertIn(
            'form-check-input',
            form.fields['opcao'].widget.attrs['class']
        )

    def test_preserva_classe_existente(self):
        form = FormularioClasseExistente()

        classes = form.fields['nome'].widget.attrs['class']

        self.assertIn(
            'campo-personalizado',
            classes
        )
        self.assertIn(
            'form-control',
            classes
        )

    def test_nao_duplica_classe_bootstrap(self):
        form = FormularioClasseExistente()

        form._aplicar_classes_bootstrap()

        classes = (
            form.fields['nome']
            .widget
            .attrs['class']
            .split()
        )

        self.assertEqual(
            classes.count('form-control'),
            1
        )
