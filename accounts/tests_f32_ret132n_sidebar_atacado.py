from unittest.mock import patch
from django.test import SimpleTestCase
from django.template import Context, Template
from accounts.permissions import PERMISSAO_ATACADO_VISUALIZAR

class SidebarAtacadoACLTests(SimpleTestCase):
    def _render(self, allowed):
        with patch('accounts.templatetags.acl_atacado_sidebar.usuario_tem_permissao', return_value=allowed) as check:
            result = Template('{% load acl_atacado_sidebar %}{% pode_visualizar_atacado usuario as visivel %}{% if visivel %}ATACADO{% else %}OCULTO{% endif %}').render(Context({'usuario': object()}))
            self.assertEqual(check.call_args.args[1], PERMISSAO_ATACADO_VISUALIZAR)
            return result

    def test_operador_sem_concessao_menu_oculto(self):
        self.assertEqual(self._render(False), 'OCULTO')

    def test_operador_com_concessao_menu_visivel(self):
        self.assertEqual(self._render(True), 'ATACADO')

    def test_sidebar_nao_usa_perfil_operador_como_liberacao(self):
        from pathlib import Path
        source = Path('templates/partials/sidebar.html').read_text(encoding='utf-8')
        self.assertIn('{% if mostrar_atacado_sidebar %}', source)
        self.assertNotIn("request.user.perfil == 'operador' %}\n        <a href=\"{% url 'atacado:orcamentos_lista' %}", source)
