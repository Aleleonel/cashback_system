from django.db import migrations, models
import django.db.models.deletion
from decimal import Decimal
import django.core.validators


class Migration(migrations.Migration):
    dependencies = [('produtos', '0004_produto_imagem_principal'), ('empresas', '0005_remove_loja_empresas_lo_matriz__cad783_idx_and_more')]
    operations = [
        migrations.CreateModel(name='ApresentacaoProduto', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('nome', models.CharField(max_length=100)),
            ('tipo', models.CharField(choices=[('POTE', 'Pote'), ('REFIL', 'Refil flexivel'), ('OUTRA', 'Outra')], max_length=10)),
            ('largura_cm', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
            ('altura_cm', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
            ('profundidade_cm', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
            ('ativo', models.BooleanField(default=True)),
            ('matriz', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='apresentacoes_logisticas', to='empresas.matriz')),
        ], options={'constraints': [models.UniqueConstraint(fields=('matriz', 'nome'), name='uniq_apresentacao_nome_matriz')]}),
        migrations.CreateModel(name='ModeloCaixaExpedicao', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('nome', models.CharField(max_length=100)),
            ('largura_cm', models.DecimalField(decimal_places=2, max_digits=8, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
            ('altura_cm', models.DecimalField(decimal_places=2, max_digits=8, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
            ('comprimento_cm', models.DecimalField(decimal_places=2, max_digits=8, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
            ('peso_maximo_gramas', models.PositiveIntegerField(blank=True, null=True)),
            ('ativo', models.BooleanField(default=True)),
            ('matriz', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='modelos_caixa_expedicao', to='empresas.matriz')),
        ], options={'constraints': [models.UniqueConstraint(fields=('matriz', 'nome'), name='uniq_caixa_nome_matriz')]}),
        migrations.CreateModel(name='CapacidadeReferenciaCaixa', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('quantidade', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
            ('matriz', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='capacidades_logisticas', to='empresas.matriz')),
            ('caixa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='capacidades', to='produtos.modelocaixaexpedicao')),
            ('apresentacao', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='capacidades', to='produtos.apresentacaoproduto')),
        ], options={'constraints': [models.UniqueConstraint(fields=('caixa', 'apresentacao'), name='uniq_capacidade_caixa_apresentacao')]}),
        migrations.AddField(model_name='produto', name='apresentacao_logistica', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='produtos', to='produtos.apresentacaoproduto')),
    ]
