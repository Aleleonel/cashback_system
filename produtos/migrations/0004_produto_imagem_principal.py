from django.db import migrations, models
import produtos.models.produtos

class Migration(migrations.Migration):
    dependencies = [('produtos', '0003_produto_atacado_elegivel_produto_promocional')]
    operations = [migrations.AddField(model_name='produto', name='imagem_principal', field=models.ImageField(blank=True, null=True, upload_to=produtos.models.produtos.caminho_imagem_produto, verbose_name='Imagem principal'))]
