from django.core.exceptions import ValidationError

from fiscal.forms import BootstrapModelForm
from fiscal.models_configuracao_fiscal import ConfiguracaoFiscalMatriz
from fiscal.models_regra_fiscal import RegraFiscal, UFS_VALIDAS


class ConfiguracaoFiscalMatrizForm(BootstrapModelForm):
    class Meta:
        model = ConfiguracaoFiscalMatriz
        fields = (
            "regime_tributario",
            "uf_origem",
            "contribuinte_icms",
            "consumidor_final_padrao",
            "ativa",
            "observacoes",
        )

    def clean_uf_origem(self):
        uf = RegraFiscal.normalizar_uf(
            self.cleaned_data.get("uf_origem")
        )
        if not uf:
            raise ValidationError("Informe a UF de origem.")
        if uf not in UFS_VALIDAS:
            raise ValidationError("Informe uma UF brasileira valida.")
        return uf
