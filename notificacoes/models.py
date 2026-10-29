from django.conf import settings
from django.db import models
from django.utils import timezone


class AvisoInterno(models.Model):
    PRIORIDADE_INFORMATIVO = "informativo"
    PRIORIDADE_LEMBRETE = "lembrete"
    PRIORIDADE_ATENCAO = "atencao"
    PRIORIDADE_URGENTE = "urgente"
    PRIORIDADES = [
        (PRIORIDADE_INFORMATIVO, "Informativo"),
        (PRIORIDADE_LEMBRETE, "Lembrete"),
        (PRIORIDADE_ATENCAO, "Atenção"),
        (PRIORIDADE_URGENTE, "Urgente"),
    ]

    matriz = models.ForeignKey(
        "empresas.Matriz", on_delete=models.CASCADE, related_name="avisos_internos"
    )
    loja = models.ForeignKey(
        "empresas.Loja", on_delete=models.CASCADE, related_name="avisos_internos",
        null=True, blank=True,
        help_text="Vazio significa todas as lojas da matriz.",
    )
    titulo = models.CharField(max_length=160)
    mensagem = models.TextField()
    prioridade = models.CharField(
        max_length=20, choices=PRIORIDADES, default=PRIORIDADE_INFORMATIVO
    )
    inicio_exibicao = models.DateTimeField(default=timezone.now)
    fim_exibicao = models.DateTimeField(null=True, blank=True)
    ativo = models.BooleanField(default=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="avisos_internos_criados",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-prioridade", "-inicio_exibicao", "-id"]
        verbose_name = "Aviso interno"
        verbose_name_plural = "Avisos internos"

    def __str__(self):
        return self.titulo

    def vigente(self, agora=None):
        agora = agora or timezone.now()
        if not self.ativo or self.inicio_exibicao > agora:
            return False
        return self.fim_exibicao is None or self.fim_exibicao >= agora


class LeituraAviso(models.Model):
    aviso = models.ForeignKey(
        AvisoInterno, on_delete=models.CASCADE, related_name="leituras"
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="leituras_avisos_internos",
    )
    lido_em = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["aviso", "usuario"], name="uq_leitura_aviso_usuario"
            )
        ]
        ordering = ["-lido_em"]
        verbose_name = "Leitura de aviso"
        verbose_name_plural = "Leituras de avisos"
