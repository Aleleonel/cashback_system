@{
    Projeto = @{
        Nome = "Cashback System"
        Tipo = "Django"
        BranchPrincipal = "develop"
    }

    Diretorios = @{
        Relatorios = ".\relatorios"
        Backups = ".\backups"
        Scripts = ".\scripts"
        Bibliotecas = ".\scripts\lib"
        Templates = ".\scripts\templates"
    }

    Django = @{
        ManagePy = ".\manage.py"
        Python = "python"
        VerbosityPadrao = 1
    }

    Git = @{
        Remote = "origin"
        IgnorarNoCommit = @(
            "backups/"
            "relatorios/"
            "*.txt"
        )
    }
}
