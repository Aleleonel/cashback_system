from django import forms
from django.utils.html import format_html

class LojaOperacionalFixaWidget(forms.Select):
    def __init__(self, attrs=None, choices=(), *, loja_id=None, loja_nome=None):
        super().__init__(attrs=attrs, choices=choices)
        self.loja_id = loja_id
        self.loja_nome = loja_nome

    def render(self, name, value, attrs=None, renderer=None):
        # Nunca apresentar o valor enviado por POST como loja operacional.
        # A validacao do ModelChoiceField permanece vinculada ao POST original.
        if self.loja_id is None:
            return super().render(name, value, attrs=attrs, renderer=renderer)
        return format_html(
            '<div class="form-control bg-light" role="textbox" aria-readonly="true">{}</div>'
            '<input type="hidden" name="{}" value="{}">',
            self.loja_nome, name, self.loja_id,
        )
