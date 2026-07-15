from django import forms


class BootstrapFormMixin:
    """
    Aplica classes Bootstrap aos widgets sem sobrescrever
    classes CSS previamente configuradas.
    """

    classes_por_widget = {
        forms.CheckboxInput: 'form-check-input',
        forms.CheckboxSelectMultiple: 'form-check-input',
        forms.RadioSelect: 'form-check-input',
        forms.Select: 'form-select',
        forms.SelectMultiple: 'form-select',
    }

    classe_padrao = 'form-control'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._aplicar_classes_bootstrap()

    def _obter_classe_widget(self, widget):
        for tipo_widget, classe_css in self.classes_por_widget.items():
            if isinstance(widget, tipo_widget):
                return classe_css

        return self.classe_padrao

    def _aplicar_classes_bootstrap(self):
        for campo in self.fields.values():
            widget = campo.widget
            classe_bootstrap = self._obter_classe_widget(widget)

            classes_existentes = widget.attrs.get('class', '').split()

            if classe_bootstrap not in classes_existentes:
                classes_existentes.append(classe_bootstrap)

            widget.attrs['class'] = ' '.join(
                classe
                for classe in classes_existentes
                if classe
            )


class BootstrapForm(BootstrapFormMixin, forms.Form):
    pass


class BootstrapModelForm(BootstrapFormMixin, forms.ModelForm):
    pass
