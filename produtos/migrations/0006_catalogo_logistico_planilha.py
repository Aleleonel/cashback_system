from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('produtos', '0005_logistica_apresentacoes_caixas')]
    operations = [
        migrations.AddField('apresentacaoproduto', 'observacoes', models.TextField(blank=True, default='')),
        migrations.AddField('modelocaixaexpedicao', 'fornecedor', models.CharField(max_length=150, blank=True, default='')),
        migrations.AddField('modelocaixaexpedicao', 'classificacao', models.CharField(max_length=60, blank=True, default='')),
        migrations.AddField('modelocaixaexpedicao', 'observacoes', models.TextField(blank=True, default='')),
        migrations.AddField('capacidadereferenciacaixa', 'orientacao', models.CharField(max_length=60, blank=True, default='')),
        migrations.AddField('capacidadereferenciacaixa', 'descricao_original', models.CharField(max_length=250, blank=True, default='')),
        migrations.AddField('capacidadereferenciacaixa', 'observacoes', models.TextField(blank=True, default='')),
        migrations.CreateModel(name='ReferenciaCapacidadeRefil', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('apresentacao_original', models.CharField(max_length=250)),
            ('quantidade', models.PositiveIntegerField(blank=True, null=True)),
            ('quantidade_original', models.CharField(max_length=30, blank=True, default='')),
            ('fornecedor', models.CharField(max_length=150, blank=True, default='')),
            ('observacoes', models.TextField(blank=True, default='')),
            ('matriz', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='referencias_refis', to='empresas.matriz')),
            ('refil', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='referencias_capacidade', to='produtos.apresentacaoproduto')),
        ]),
        migrations.AddConstraint('referenciacapacidaderefil', models.UniqueConstraint(fields=('refil', 'apresentacao_original'), name='uniq_refil_tipo_referencia')),
        migrations.CreateModel(name='RegistroFonteLogistica', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('aba', models.CharField(max_length=100)),
            ('linha', models.PositiveIntegerField()),
            ('celulas', models.JSONField(default=dict)),
            ('observacoes', models.TextField(blank=True, default='')),
            ('matriz', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='fontes_logisticas', to='empresas.matriz')),
        ]),
        migrations.AddConstraint('registrofontelogistica', models.UniqueConstraint(fields=('matriz', 'aba', 'linha'), name='uniq_fonte_logistica_matriz_aba_linha')),
    ]
