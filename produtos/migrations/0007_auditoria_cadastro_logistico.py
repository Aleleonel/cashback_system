from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('produtos','0006_catalogo_logistico_planilha'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [migrations.CreateModel(name='AuditoriaCadastroLogistico', fields=[
        ('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
        ('tipo',models.CharField(max_length=40)),('objeto_id',models.PositiveIntegerField()),
        ('acao',models.CharField(max_length=20)),('antes',models.JSONField(default=dict)),
        ('depois',models.JSONField(default=dict)),('criado_em',models.DateTimeField(auto_now_add=True)),
        ('matriz',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name='auditorias_logisticas',to='empresas.matriz')),
        ('usuario',models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,to=settings.AUTH_USER_MODEL))
    ], options={'ordering':['-criado_em','-pk']})]
