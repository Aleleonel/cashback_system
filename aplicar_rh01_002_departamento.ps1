param(
    [string]$ProjectRoot = "C:\Users\User\Alexandre\Projetos\cashback_system"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Sprint = "RH-01.002"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogName = "aplicacao_rh01_002_departamento_$Timestamp.txt"
$BackupFolderName = ".backup_rh01_002_departamento_$Timestamp"

function Write-Utf8NoBom {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [Parameter(Mandatory = $true)]
        [string]$Content
    )

    $Directory = Split-Path -Parent $Path

    if ($Directory -and -not (Test-Path -LiteralPath $Directory)) {
        New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    }

    $Encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content, $Encoding)
}

function Backup-ProjectFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RelativePath
    )

    $Source = Join-Path $ProjectRoot $RelativePath

    if (-not (Test-Path -LiteralPath $Source)) {
        return
    }

    $Destination = Join-Path $BackupRoot $RelativePath
    $DestinationDirectory = Split-Path -Parent $Destination

    if (-not (Test-Path -LiteralPath $DestinationDirectory)) {
        New-Item -ItemType Directory -Path $DestinationDirectory -Force | Out-Null
    }

    Copy-Item -LiteralPath $Source -Destination $Destination -Force
}

function Restore-Backups {
    Write-Host ""
    Write-Host "Restaurando arquivos alterados..." -ForegroundColor Yellow

    foreach ($RelativePath in $FilesToBackup) {
        $BackupPath = Join-Path $BackupRoot $RelativePath
        $ProjectPath = Join-Path $ProjectRoot $RelativePath

        if (Test-Path -LiteralPath $BackupPath) {
            $ProjectDirectory = Split-Path -Parent $ProjectPath

            if (-not (Test-Path -LiteralPath $ProjectDirectory)) {
                New-Item -ItemType Directory -Path $ProjectDirectory -Force | Out-Null
            }

            Copy-Item -LiteralPath $BackupPath -Destination $ProjectPath -Force
            Write-Host "RESTAURADO - $RelativePath"
        }
        elseif ($CreatedFiles -contains $RelativePath) {
            if (Test-Path -LiteralPath $ProjectPath) {
                Remove-Item -LiteralPath $ProjectPath -Force
                Write-Host "REMOVIDO - $RelativePath"
            }
        }
    }

    if ($GeneratedMigrationPath -and (Test-Path -LiteralPath $GeneratedMigrationPath)) {
        Remove-Item -LiteralPath $GeneratedMigrationPath -Force
        Write-Host "REMOVIDA - migration gerada nesta execucao"
    }
}

if (-not (Test-Path -LiteralPath $ProjectRoot)) {
    throw "Diretorio do projeto nao encontrado: $ProjectRoot"
}

Set-Location -LiteralPath $ProjectRoot

$LogPath = Join-Path $ProjectRoot $LogName
$BackupRoot = Join-Path $ProjectRoot $BackupFolderName
$GeneratedMigrationPath = $null

$CreatedFiles = @(
    "rh\models\departamento.py",
    "rh\forms\departamento_form.py",
    "rh\selectors\departamento_selector.py",
    "rh\services\departamento_service.py",
    "rh\views\departamento_views.py",
    "rh\templates\rh\departamento\list.html",
    "rh\templates\rh\departamento\form.html",
    "rh\templates\rh\departamento\delete.html",
    "rh\tests\test_departamento_urls.py"
)

$FilesToBackup = @(
    "rh\models\departamento.py",
    "rh\forms\departamento_form.py",
    "rh\selectors\departamento_selector.py",
    "rh\services\departamento_service.py",
    "rh\views\departamento_views.py",
    "rh\templates\rh\departamento\list.html",
    "rh\templates\rh\departamento\form.html",
    "rh\templates\rh\departamento\delete.html",
    "rh\tests\test_departamento_urls.py",
    "rh\models\__init__.py",
    "rh\urls.py",
    "rh\admin.py"
)

Start-Transcript -LiteralPath $LogPath -Force | Out-Null

try {
    Write-Host "============================================================"
    Write-Host "$Sprint - Aplicacao do cadastro de Departamentos"
    Write-Host "============================================================"
    Write-Host "Projeto: $ProjectRoot"
    Write-Host "Log: $LogPath"
    Write-Host "Backup: $BackupRoot"

    Write-Host "`n[1/12] Validando estado inicial..."

    $RequiredFiles = @(
        "manage.py",
        "rh\models\cargo.py",
        "rh\models\__init__.py",
        "rh\urls.py",
        "rh\admin.py",
        "rh\migrations\0001_initial.py"
    )

    foreach ($RelativePath in $RequiredFiles) {
        $FullPath = Join-Path $ProjectRoot $RelativePath

        if (-not (Test-Path -LiteralPath $FullPath)) {
            throw "Arquivo obrigatorio nao encontrado: $RelativePath"
        }

        Write-Host "OK - $RelativePath"
    }

    $CurrentBranch = (git branch --show-current).Trim()

    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao identificar a branch atual."
    }

    Write-Host "Branch atual: $CurrentBranch"

    if ($CurrentBranch -ne "feature/rh-01-fundacao") {
        throw "Branch incorreta. Esperado: feature/rh-01-fundacao"
    }

    $StatusBefore = git status --short

    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao consultar o estado do Git."
    }

    $UnexpectedChanges = @(
        $StatusBefore | Where-Object {
            $_ -and
            $_ -notmatch 'diagnostico_rh01_002_departamento\.ps1$' -and
            $_ -notmatch 'saida_diagnostico_rh01_002.*\.txt$' -and
            $_ -notmatch 'aplicar_rh01_002_departamento\.ps1$' -and
            $_ -notmatch 'aplicacao_rh01_002_departamento_.*\.txt$'
        }
    )

    if ($UnexpectedChanges.Count -gt 0) {
        Write-Host "Alteracoes inesperadas encontradas:" -ForegroundColor Yellow
        $UnexpectedChanges | ForEach-Object { Write-Host $_ }
        throw "O repositorio precisa estar limpo antes da aplicacao."
    }

    python manage.py check
    if ($LASTEXITCODE -ne 0) {
        throw "O django check falhou antes da aplicacao."
    }

    python manage.py makemigrations --check --dry-run
    if ($LASTEXITCODE -ne 0) {
        throw "Existem alteracoes de model sem migration antes da aplicacao."
    }

    Write-Host "`n[2/12] Criando backups..."

    New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null

    foreach ($RelativePath in $FilesToBackup) {
        Backup-ProjectFile -RelativePath $RelativePath
    }

    Write-Host "Backups concluidos."

    Write-Host "`n[3/12] Criando model Departamento..."

    $DepartamentoModel = @'
from django.core.validators import MinLengthValidator
from django.db import models

from empresas.models import Matriz


class Departamento(models.Model):
    """
    Departamentos da empresa.

    Exemplos:
        - Administrativo
        - Comercial
        - Financeiro
        - Recursos Humanos
        - Tecnologia
    """

    matriz = models.ForeignKey(
        Matriz,
        on_delete=models.CASCADE,
        related_name="departamentos",
        verbose_name="Matriz",
    )

    nome = models.CharField(
        "Nome",
        max_length=100,
        validators=[MinLengthValidator(2)],
    )

    descricao = models.TextField(
        "Descrição",
        blank=True,
        default="",
    )

    ativo = models.BooleanField(
        "Ativo",
        default=True,
    )

    criado_em = models.DateTimeField(
        "Criado em",
        auto_now_add=True,
    )

    atualizado_em = models.DateTimeField(
        "Atualizado em",
        auto_now=True,
    )

    class Meta:
        db_table = "rh_departamento"
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"
        ordering = ["nome"]

        constraints = [
            models.UniqueConstraint(
                fields=["matriz", "nome"],
                name="uk_rh_departamento_matriz_nome",
            ),
        ]

        indexes = [
            models.Index(
                fields=["matriz", "ativo"],
                name="idx_rh_depart_matriz_ativo",
            ),
            models.Index(
                fields=["nome"],
                name="idx_rh_depart_nome",
            ),
        ]

    def __str__(self):
        return self.nome
'@

    Write-Utf8NoBom `
        -Path (Join-Path $ProjectRoot "rh\models\departamento.py") `
        -Content $DepartamentoModel

    Write-Host "`n[4/12] Atualizando exportacao dos models..."

    $ModelsInit = @'
from .cargo import Cargo
from .departamento import Departamento

__all__ = [
    "Cargo",
    "Departamento",
]
'@

    Write-Utf8NoBom `
        -Path (Join-Path $ProjectRoot "rh\models\__init__.py") `
        -Content $ModelsInit

    Write-Host "`n[5/12] Criando form, selector e service..."

    $DepartamentoForm = @'
from django import forms

from rh.models import Departamento


class DepartamentoForm(forms.ModelForm):
    class Meta:
        model = Departamento

        fields = [
            "matriz",
            "nome",
            "descricao",
            "ativo",
        ]

        widgets = {
            "descricao": forms.Textarea(
                attrs={
                    "rows": 4,
                    "class": "form-control",
                }
            ),
            "nome": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "maxlength": 100,
                    "autocomplete": "off",
                }
            ),
            "matriz": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "ativo": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }

    def clean_nome(self):
        nome = self.cleaned_data["nome"].strip()

        if not nome:
            raise forms.ValidationError(
                "Informe o nome do departamento."
            )

        return nome

    def save(self, commit=True):
        self.instance.nome = self.cleaned_data["nome"].strip()
        self.instance.descricao = self.cleaned_data.get(
            "descricao",
            "",
        ).strip()

        return super().save(commit=commit)
'@

    $DepartamentoSelector = @'
from django.db.models import QuerySet

from rh.models import Departamento


def listar_departamentos(
    matriz=None,
    ativo=True,
) -> QuerySet:
    """
    Retorna os departamentos da matriz.
    """

    queryset = Departamento.objects.select_related("matriz")

    if matriz is not None:
        queryset = queryset.filter(matriz=matriz)

    if ativo is not None:
        queryset = queryset.filter(ativo=ativo)

    return queryset.order_by("nome")


def obter_departamento_por_id(
    departamento_id: int,
    matriz=None,
) -> Departamento:
    """
    Retorna um departamento pelo ID.
    """

    queryset = Departamento.objects.select_related("matriz")

    if matriz is not None:
        queryset = queryset.filter(matriz=matriz)

    return queryset.get(pk=departamento_id)


def buscar_departamentos(
    termo: str,
    matriz=None,
    ativo=True,
) -> QuerySet:
    """
    Pesquisa departamentos pelo nome.
    """

    queryset = listar_departamentos(
        matriz=matriz,
        ativo=ativo,
    )

    if termo:
        queryset = queryset.filter(
            nome__icontains=termo.strip()
        )

    return queryset
'@

    $DepartamentoService = @'
from django.core.exceptions import ValidationError
from django.db import transaction

from rh.models import Departamento


@transaction.atomic
def criar_departamento(
    *,
    matriz,
    nome,
    descricao="",
    ativo=True,
):
    """
    Cria um novo departamento.
    """

    nome = nome.strip()
    descricao = descricao.strip()

    if not nome:
        raise ValidationError(
            "Informe o nome do departamento."
        )

    if Departamento.objects.filter(
        matriz=matriz,
        nome__iexact=nome,
    ).exists():
        raise ValidationError(
            "Já existe um departamento com esse nome nesta matriz."
        )

    departamento = Departamento(
        matriz=matriz,
        nome=nome,
        descricao=descricao,
        ativo=ativo,
    )

    departamento.full_clean()
    departamento.save()

    return departamento


@transaction.atomic
def atualizar_departamento(
    *,
    departamento,
    nome,
    descricao,
    ativo,
):
    """
    Atualiza um departamento existente.
    """

    nome = nome.strip()
    descricao = descricao.strip()

    if not nome:
        raise ValidationError(
            "Informe o nome do departamento."
        )

    if Departamento.objects.filter(
        matriz=departamento.matriz,
        nome__iexact=nome,
    ).exclude(pk=departamento.pk).exists():
        raise ValidationError(
            "Já existe um departamento com esse nome nesta matriz."
        )

    departamento.nome = nome
    departamento.descricao = descricao
    departamento.ativo = ativo

    departamento.full_clean()
    departamento.save()

    return departamento


@transaction.atomic
def excluir_departamento(departamento):
    """
    Inativa um departamento sem realizar exclusao fisica.
    """

    departamento.ativo = False
    departamento.full_clean()
    departamento.save(update_fields=["ativo", "atualizado_em"])

    return departamento
'@

    Write-Utf8NoBom `
        -Path (Join-Path $ProjectRoot "rh\forms\departamento_form.py") `
        -Content $DepartamentoForm

    Write-Utf8NoBom `
        -Path (Join-Path $ProjectRoot "rh\selectors\departamento_selector.py") `
        -Content $DepartamentoSelector

    Write-Utf8NoBom `
        -Path (Join-Path $ProjectRoot "rh\services\departamento_service.py") `
        -Content $DepartamentoService

    Write-Host "`n[6/12] Criando views..."

    $DepartamentoViews = @'
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from rh.forms.departamento_form import DepartamentoForm
from rh.models import Departamento
from rh.selectors.departamento_selector import listar_departamentos
from rh.services.departamento_service import (
    atualizar_departamento,
    criar_departamento,
    excluir_departamento,
)


def _matriz_do_usuario(request):
    return getattr(request.user, "matriz", None)


@login_required
def departamento_list(request):
    matriz = _matriz_do_usuario(request)

    departamentos = listar_departamentos(
        matriz=matriz,
        ativo=None,
    )

    context = {
        "departamentos": departamentos,
    }

    return render(
        request,
        "rh/departamento/list.html",
        context,
    )


@login_required
def departamento_create(request):
    matriz = _matriz_do_usuario(request)

    if request.method == "POST":
        form = DepartamentoForm(request.POST)

        if form.is_valid():
            try:
                criar_departamento(
                    matriz=matriz or form.cleaned_data["matriz"],
                    nome=form.cleaned_data["nome"],
                    descricao=form.cleaned_data["descricao"],
                    ativo=form.cleaned_data["ativo"],
                )
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                messages.success(
                    request,
                    "Departamento cadastrado com sucesso.",
                )

                return redirect("rh:departamento_list")
    else:
        form = DepartamentoForm(
            initial={
                "matriz": matriz,
            }
        )

    if matriz is not None:
        form.fields["matriz"].queryset = (
            form.fields["matriz"].queryset.filter(pk=matriz.pk)
        )
        form.fields["matriz"].initial = matriz

    return render(
        request,
        "rh/departamento/form.html",
        {
            "form": form,
            "titulo": "Novo Departamento",
        },
    )


@login_required
def departamento_update(request, pk):
    matriz = _matriz_do_usuario(request)

    filtros = {
        "pk": pk,
    }

    if matriz is not None:
        filtros["matriz"] = matriz

    departamento = get_object_or_404(
        Departamento,
        **filtros,
    )

    if request.method == "POST":
        form = DepartamentoForm(
            request.POST,
            instance=departamento,
        )

        if form.is_valid():
            try:
                atualizar_departamento(
                    departamento=departamento,
                    nome=form.cleaned_data["nome"],
                    descricao=form.cleaned_data["descricao"],
                    ativo=form.cleaned_data["ativo"],
                )
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                messages.success(
                    request,
                    "Departamento atualizado com sucesso.",
                )

                return redirect("rh:departamento_list")
    else:
        form = DepartamentoForm(instance=departamento)

    form.fields["matriz"].queryset = (
        form.fields["matriz"].queryset.filter(
            pk=departamento.matriz_id
        )
    )

    return render(
        request,
        "rh/departamento/form.html",
        {
            "form": form,
            "titulo": "Editar Departamento",
        },
    )


@login_required
def departamento_delete(request, pk):
    matriz = _matriz_do_usuario(request)

    filtros = {
        "pk": pk,
    }

    if matriz is not None:
        filtros["matriz"] = matriz

    departamento = get_object_or_404(
        Departamento,
        **filtros,
    )

    if request.method == "POST":
        excluir_departamento(departamento)

        messages.success(
            request,
            "Departamento inativado com sucesso.",
        )

        return redirect("rh:departamento_list")

    return render(
        request,
        "rh/departamento/delete.html",
        {
            "departamento": departamento,
        },
    )
'@

    Write-Utf8NoBom `
        -Path (Join-Path $ProjectRoot "rh\views\departamento_views.py") `
        -Content $DepartamentoViews

    Write-Host "`n[7/12] Criando templates..."

    $DepartamentoListTemplate = @'
{% extends "base.html" %}

{% block title %}Departamentos{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <div>
            <h2 class="mb-0">Departamentos</h2>
            <small class="text-muted">
                Organização dos departamentos da empresa
            </small>
        </div>

        <a href="{% url 'rh:departamento_create' %}" class="btn btn-primary">
            <i class="bi bi-plus-circle"></i>
            Novo Departamento
        </a>
    </div>

    {% if messages %}
        {% for message in messages %}
            <div class="alert alert-{{ message.tags }} alert-dismissible fade show">
                {{ message }}
                <button
                    type="button"
                    class="btn-close"
                    data-bs-dismiss="alert"
                    aria-label="Fechar"
                ></button>
            </div>
        {% endfor %}
    {% endif %}

    <div class="card shadow-sm">
        <div class="card-body p-0">
            <div class="table-responsive">
                <table class="table table-hover align-middle mb-0">
                    <thead class="table-light">
                        <tr>
                            <th>Nome</th>
                            <th>Descrição</th>
                            <th>Status</th>
                            <th width="170">Ações</th>
                        </tr>
                    </thead>

                    <tbody>
                        {% for departamento in departamentos %}
                            <tr>
                                <td>
                                    <strong>{{ departamento.nome }}</strong>
                                </td>

                                <td>
                                    {{ departamento.descricao|default:"-" }}
                                </td>

                                <td>
                                    {% if departamento.ativo %}
                                        <span class="badge bg-success">
                                            Ativo
                                        </span>
                                    {% else %}
                                        <span class="badge bg-secondary">
                                            Inativo
                                        </span>
                                    {% endif %}
                                </td>

                                <td>
                                    <a
                                        href="{% url 'rh:departamento_update' departamento.pk %}"
                                        class="btn btn-sm btn-warning"
                                    >
                                        Editar
                                    </a>

                                    {% if departamento.ativo %}
                                        <a
                                            href="{% url 'rh:departamento_delete' departamento.pk %}"
                                            class="btn btn-sm btn-danger"
                                        >
                                            Inativar
                                        </a>
                                    {% endif %}
                                </td>
                            </tr>
                        {% empty %}
                            <tr>
                                <td colspan="4" class="text-center py-5">
                                    Nenhum departamento cadastrado.
                                </td>
                            </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
{% endblock %}
'@

    $DepartamentoFormTemplate = @'
{% extends "base.html" %}

{% block title %}{{ titulo }}{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="row justify-content-center">
        <div class="col-lg-8">
            <div class="card shadow-sm">
                <div class="card-header">
                    <h4 class="mb-0">{{ titulo }}</h4>
                </div>

                <div class="card-body">
                    <form method="post" novalidate>
                        {% csrf_token %}

                        {% if form.non_field_errors %}
                            <div class="alert alert-danger">
                                {{ form.non_field_errors }}
                            </div>
                        {% endif %}

                        <div class="mb-3">
                            <label
                                for="{{ form.matriz.id_for_label }}"
                                class="form-label"
                            >
                                Matriz
                            </label>

                            {{ form.matriz }}

                            {% for erro in form.matriz.errors %}
                                <div class="text-danger small">
                                    {{ erro }}
                                </div>
                            {% endfor %}
                        </div>

                        <div class="mb-3">
                            <label
                                for="{{ form.nome.id_for_label }}"
                                class="form-label"
                            >
                                Nome
                            </label>

                            {{ form.nome }}

                            {% for erro in form.nome.errors %}
                                <div class="text-danger small">
                                    {{ erro }}
                                </div>
                            {% endfor %}
                        </div>

                        <div class="mb-3">
                            <label
                                for="{{ form.descricao.id_for_label }}"
                                class="form-label"
                            >
                                Descrição
                            </label>

                            {{ form.descricao }}

                            {% for erro in form.descricao.errors %}
                                <div class="text-danger small">
                                    {{ erro }}
                                </div>
                            {% endfor %}
                        </div>

                        <div class="form-check mb-4">
                            {{ form.ativo }}

                            <label
                                class="form-check-label"
                                for="{{ form.ativo.id_for_label }}"
                            >
                                Departamento ativo
                            </label>
                        </div>

                        <div class="d-flex justify-content-between">
                            <a
                                href="{% url 'rh:departamento_list' %}"
                                class="btn btn-secondary"
                            >
                                Cancelar
                            </a>

                            <button type="submit" class="btn btn-primary">
                                Salvar
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
'@

    $DepartamentoDeleteTemplate = @'
{% extends "base.html" %}

{% block title %}Inativar Departamento{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="row justify-content-center">
        <div class="col-lg-6">
            <div class="card border-danger shadow-sm">
                <div class="card-header bg-danger text-white">
                    <h4 class="mb-0">
                        Confirmar inativação
                    </h4>
                </div>

                <div class="card-body">
                    <p class="mb-4">
                        Tem certeza que deseja inativar o departamento?
                    </p>

                    <h5 class="text-primary">
                        {{ departamento.nome }}
                    </h5>

                    {% if departamento.descricao %}
                        <p class="text-muted">
                            {{ departamento.descricao }}
                        </p>
                    {% endif %}

                    <div class="alert alert-warning mb-4">
                        O departamento deixará de aparecer como ativo,
                        mas continuará preservado no histórico.
                    </div>

                    <form method="post">
                        {% csrf_token %}

                        <div class="d-flex justify-content-between">
                            <a
                                href="{% url 'rh:departamento_list' %}"
                                class="btn btn-secondary"
                            >
                                Cancelar
                            </a>

                            <button type="submit" class="btn btn-danger">
                                Confirmar inativação
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
'@

    Write-Utf8NoBom `
        -Path (Join-Path $ProjectRoot "rh\templates\rh\departamento\list.html") `
        -Content $DepartamentoListTemplate

    Write-Utf8NoBom `
        -Path (Join-Path $ProjectRoot "rh\templates\rh\departamento\form.html") `
        -Content $DepartamentoFormTemplate

    Write-Utf8NoBom `
        -Path (Join-Path $ProjectRoot "rh\templates\rh\departamento\delete.html") `
        -Content $DepartamentoDeleteTemplate

    Write-Host "`n[8/12] Atualizando URLs..."

    $RhUrls = @'
from django.urls import path

from rh.views.cargo_views import (
    cargo_create,
    cargo_delete,
    cargo_list,
    cargo_update,
)
from rh.views.departamento_views import (
    departamento_create,
    departamento_delete,
    departamento_list,
    departamento_update,
)
from rh.views.inicio import inicio


app_name = "rh"


urlpatterns = [
    path("", inicio, name="inicio"),

    # Cargo
    path(
        "cargos/",
        cargo_list,
        name="cargo_list",
    ),
    path(
        "cargos/novo/",
        cargo_create,
        name="cargo_create",
    ),
    path(
        "cargos/<int:pk>/editar/",
        cargo_update,
        name="cargo_update",
    ),
    path(
        "cargos/<int:pk>/excluir/",
        cargo_delete,
        name="cargo_delete",
    ),

    # Departamento
    path(
        "departamentos/",
        departamento_list,
        name="departamento_list",
    ),
    path(
        "departamentos/novo/",
        departamento_create,
        name="departamento_create",
    ),
    path(
        "departamentos/<int:pk>/editar/",
        departamento_update,
        name="departamento_update",
    ),
    path(
        "departamentos/<int:pk>/inativar/",
        departamento_delete,
        name="departamento_delete",
    ),
]
'@

    Write-Utf8NoBom `
        -Path (Join-Path $ProjectRoot "rh\urls.py") `
        -Content $RhUrls

    Write-Host "`n[9/12] Atualizando admin..."

    $RhAdmin = @'
from django.contrib import admin

from .models import Cargo, Departamento


@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    list_display = (
        "nome",
        "matriz",
        "ativo",
        "criado_em",
    )

    list_filter = (
        "ativo",
        "matriz",
    )

    search_fields = (
        "nome",
        "descricao",
    )

    ordering = (
        "nome",
    )

    readonly_fields = (
        "criado_em",
        "atualizado_em",
    )

    fieldsets = (
        (
            "Informações Gerais",
            {
                "fields": (
                    "matriz",
                    "nome",
                    "descricao",
                    "ativo",
                )
            },
        ),
        (
            "Auditoria",
            {
                "classes": (
                    "collapse",
                ),
                "fields": (
                    "criado_em",
                    "atualizado_em",
                ),
            },
        ),
    )


@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = (
        "nome",
        "matriz",
        "ativo",
        "criado_em",
    )

    list_filter = (
        "ativo",
        "matriz",
    )

    search_fields = (
        "nome",
        "descricao",
    )

    ordering = (
        "nome",
    )

    readonly_fields = (
        "criado_em",
        "atualizado_em",
    )

    fieldsets = (
        (
            "Informações Gerais",
            {
                "fields": (
                    "matriz",
                    "nome",
                    "descricao",
                    "ativo",
                )
            },
        ),
        (
            "Auditoria",
            {
                "classes": (
                    "collapse",
                ),
                "fields": (
                    "criado_em",
                    "atualizado_em",
                ),
            },
        ),
    )
'@

    Write-Utf8NoBom `
        -Path (Join-Path $ProjectRoot "rh\admin.py") `
        -Content $RhAdmin

    Write-Host "`n[10/12] Criando testes de URLs..."

    $DepartamentoUrlTests = @'
from django.test import SimpleTestCase
from django.urls import resolve, reverse

from rh.views.departamento_views import (
    departamento_create,
    departamento_delete,
    departamento_list,
    departamento_update,
)


class DepartamentoUrlsTests(SimpleTestCase):
    def test_rota_lista_resolve_view_correta(self):
        match = resolve("/rh/departamentos/")

        self.assertEqual(match.func, departamento_list)
        self.assertEqual(match.namespace, "rh")
        self.assertEqual(match.url_name, "departamento_list")

    def test_rota_criacao_resolve_view_correta(self):
        match = resolve("/rh/departamentos/novo/")

        self.assertEqual(match.func, departamento_create)
        self.assertEqual(match.url_name, "departamento_create")

    def test_rota_edicao_resolve_view_correta(self):
        match = resolve("/rh/departamentos/1/editar/")

        self.assertEqual(match.func, departamento_update)
        self.assertEqual(match.url_name, "departamento_update")

    def test_rota_inativacao_resolve_view_correta(self):
        match = resolve("/rh/departamentos/1/inativar/")

        self.assertEqual(match.func, departamento_delete)
        self.assertEqual(match.url_name, "departamento_delete")

    def test_lista_exige_autenticacao(self):
        response = self.client.get(
            reverse("rh:departamento_list")
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_criacao_exige_autenticacao(self):
        response = self.client.get(
            reverse("rh:departamento_create")
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)
'@

    Write-Utf8NoBom `
        -Path (Join-Path $ProjectRoot "rh\tests\test_departamento_urls.py") `
        -Content $DepartamentoUrlTests

    Write-Host "`n[11/12] Validando sintaxe e gerando migration..."

    $PythonFiles = @(
        "rh\models\departamento.py",
        "rh\models\__init__.py",
        "rh\forms\departamento_form.py",
        "rh\selectors\departamento_selector.py",
        "rh\services\departamento_service.py",
        "rh\views\departamento_views.py",
        "rh\urls.py",
        "rh\admin.py",
        "rh\tests\test_departamento_urls.py"
    ) | ForEach-Object {
        Join-Path $ProjectRoot $_
    }

    python -m py_compile $PythonFiles

    if ($LASTEXITCODE -ne 0) {
        throw "Falha na validacao de sintaxe dos arquivos Python."
    }

    $MigrationsBefore = @(
        Get-ChildItem `
            -LiteralPath (Join-Path $ProjectRoot "rh\migrations") `
            -Filter "*.py" |
        Select-Object -ExpandProperty FullName
    )

    python manage.py makemigrations rh

    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao gerar migration do Departamento."
    }

    $MigrationsAfter = @(
        Get-ChildItem `
            -LiteralPath (Join-Path $ProjectRoot "rh\migrations") `
            -Filter "*.py" |
        Select-Object -ExpandProperty FullName
    )

    $NewMigrations = @(
        $MigrationsAfter | Where-Object {
            $_ -notin $MigrationsBefore -and
            (Split-Path -Leaf $_) -ne "__init__.py"
        }
    )

    if ($NewMigrations.Count -ne 1) {
        throw "Era esperada exatamente uma nova migration. Encontradas: $($NewMigrations.Count)"
    }

    $GeneratedMigrationPath = $NewMigrations[0]
    Write-Host "Migration gerada: $GeneratedMigrationPath"

    python manage.py makemigrations --check --dry-run

    if ($LASTEXITCODE -ne 0) {
        throw "Ainda existem alteracoes de model sem migration."
    }

    Write-Host "`n[12/12] Executando validacoes finais da aplicacao..."

    python manage.py check

    if ($LASTEXITCODE -ne 0) {
        throw "O django check falhou depois da aplicacao."
    }

    python manage.py test rh -v 2

    if ($LASTEXITCODE -ne 0) {
        throw "Os testes do modulo RH falharam."
    }

    Write-Host "`nEstado final do Git:"
    git status --short

    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao consultar o estado final do Git."
    }

    Write-Host ""
    Write-Host "============================================================"
    Write-Host "$Sprint aplicado com sucesso." -ForegroundColor Green
    Write-Host "A migration foi criada, mas ainda nao foi aplicada ao banco."
    Write-Host "Backup preservado em:"
    Write-Host $BackupRoot
    Write-Host "Log salvo em:"
    Write-Host $LogPath
    Write-Host "============================================================"
}
catch {
    Write-Host ""
    Write-Host "ERRO NA APLICACAO:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red

    Restore-Backups

    Write-Host ""
    Write-Host "A aplicacao foi revertida." -ForegroundColor Yellow
    Write-Host "Consulte o log:"
    Write-Host $LogPath

    throw
}
finally {
    try {
        Stop-Transcript | Out-Null
    }
    catch {
        # O transcript pode nao ter sido iniciado em falhas muito iniciais.
    }
}
