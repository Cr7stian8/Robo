"""
Automação AVA-EFAPE – Robô para assistir vídeos, responder atividades e concluir cursos.
Corrigido e pronto para uso.
"""

import os
import time
import traceback
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple

from playwright.sync_api import sync_playwright, Page, BrowserContext

# =============================================================================
# CONFIGURAÇÕES
# =============================================================================
@dataclass
class Config:
    # Credenciais (utilize variáveis de ambiente para segurança)
    CPF: str = os.getenv("AVA_CPF", "47821023809")
    SENHA: str = os.getenv("AVA_SENHA", "#Calabria7513")

    # Textos padrão para atividades
    TEXTO_DIAGNOSTICO: str = "Turma participativa, Porém tem apresentado dificuldades no conceito abordado que precisam ser superados em sala de aula."
    TEXTO_PLANO_AULA: str = "Plano de aula elaborado com sucesso, contemplando os objetivos propostos."
    TEXTO_PESQUISA: str = "Conteúdo excelente, formador muito didático e planejamento bem estruturado!"

    # Temporização (em segundos)
    TEMPO_MAXIMO_VIDEO: int = 1500
    TEMPO_MINIMO_VIDEO: int = 30
    TEMPO_ESPERA_MODAL: int = 2
    TEMPO_ESPERA_CARREGAMENTO: int = 5
    INTERVALO_CHECAGEM_VIDEO: int = 1

    # Debug
    DEBUG_DIR: Path = Path("debug")
    SALVAR_SCREENSHOTS: bool = True

    def __post_init__(self):
        self.DEBUG_DIR.mkdir(exist_ok=True)

# Cores para terminal
class C:
    R = '\033[0m'
    V = '\033[92m'  # verde
    E = '\033[91m'  # vermelho
    A = '\033[93m'  # amarelo
    C = '\033[96m'  # ciano
    B = '\033[1m'   # negrito
    M = '\033[95m'  # magenta

# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================
def log(msg: str, cor: str = C.C, emoji: str = "•") -> None:
    """Exibe mensagem formatada com timestamp."""
    print(f"{cor}[{datetime.now():%H:%M:%S}] {emoji} {msg}{C.R}")

def save_debug(page: Page, name: str, config: Config) -> None:
    """Salva screenshot para depuração, se habilitado."""
    if config.SALVAR_SCREENSHOTS:
        try:
            page.screenshot(path=config.DEBUG_DIR / f"{name}.png", full_page=True)
        except Exception:
            pass

# =============================================================================
# CLASSE PRINCIPAL
# =============================================================================
class AVAAutomacao:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.page: Optional[Page] = None
        self.browser: Optional[BrowserContext] = None
        self.playwright = None

        # Estado da automação
        self.interacoes_resolvidas = 0
        self.total_videos_assistidos = 0
        self.cursos_concluidos = 0
        self.pesquisa_concluida = False
        self.aulas_tentadas: Dict[str, int] = {}
        self.cursos_processados: set = set()

        # Máquina de estratégias para modais persistentes
        self.strategy_index = 0
        self.attempts_with_current_strategy = 0

    # -------------------------------------------------------------------------
    # CONSOLE E LOGS
    # -------------------------------------------------------------------------
    @staticmethod
    def limpar_console() -> None:
        os.system('cls' if os.name == 'nt' else 'clear')

    def menu(self) -> None:
        print(f"""
{C.C}╔══════════════════════════════════════════════════════════════════╗
║     🎮 AUTOMAÇÃO AVA-EFAPE - PARA VOCÊ PODER TRABALHAR 🎮        ║
╚══════════════════════════════════════════════════════════════════╝{C.R}
        """)

    # -------------------------------------------------------------------------
    # SETUP DO NAVEGADOR
    # -------------------------------------------------------------------------
    def iniciar_navegador(self) -> None:
        log("Iniciando navegador...", C.C, "🌐")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=False,
            args=['--window-size=1280,720']
        ).new_context(viewport={'width': 1280, 'height': 720})
        self.page = self.browser.new_page()
        self.page.set_default_timeout(30000)

    def fechar_navegador(self) -> None:
        if self.playwright:
            try:
                self.browser.close()
            except Exception:
                pass
            self.playwright.stop()
            log("Navegador fechado", C.C, "👋")

    # -------------------------------------------------------------------------
    # AUTENTICAÇÃO
    # -------------------------------------------------------------------------
    def login(self) -> bool:
        log("Fazendo login...", C.C, "🔐")
        try:
            self.page.goto("https://avaefape.educacao.sp.gov.br/")
            self.page.wait_for_load_state("networkidle")
            self.page.locator("input[placeholder*='CPF']").fill(self.config.CPF)
            self.page.locator("input[placeholder*='senha']").fill(self.config.SENHA)
            self.page.locator("button:has-text('Acessar')").click()
            self.page.wait_for_load_state("networkidle")
            time.sleep(2)
            log("Login realizado", C.V, "✅")
            return True
        except Exception as e:
            log(f"Falha no login: {e}", C.E, "❌")
            return False

    # -------------------------------------------------------------------------
    # NAVEGAÇÃO
    # -------------------------------------------------------------------------
    def ir_para_meus_cursos(self) -> None:
        log("Indo para Meus Cursos...", C.C, "📚")
        self.page.goto("https://avaefape.educacao.sp.gov.br/my/courses.php")
        self.page.wait_for_load_state("networkidle")
        time.sleep(2)

    def encontrar_proximo_curso_pendente(self) -> Tuple[Optional[any], Optional[any], Optional[str]]:
        log("Procurando cursos pendentes...", C.C, "🔍")
        cursos = self.page.locator(
            ".course-card, .card.course-card, [data-region='course-content'], a[href*='/course/view.php']"
        ).all()
        for curso in cursos:
            try:
                if curso.locator(".badge-success, .completion_complete, i.fa-check-circle, i.bi-check-circle-fill").count() == 0:
                    link = curso.locator("a[href*='/course/view.php']").first or curso.locator("a").first
                    if link.count() > 0:
                        href = link.get_attribute("href")
                        curso_id = href.split("id=")[-1] if "id=" in href else ""
                        if curso_id in self.cursos_processados:
                            continue
                        nome = (link.inner_text() or "Curso sem nome")[:50]
                        log(f"Curso pendente: {nome} (ID: {curso_id})", C.V, "📌")
                        return link, curso, curso_id
            except Exception:
                continue
        log("Nenhum curso pendente!", C.V, "🎉")
        return None, None, None

    def remover_curso_da_visualizacao(self, curso_id: str) -> bool:
        log(f"Removendo curso {curso_id} da visualização...", C.C, "🗑️")
        self.page.wait_for_load_state("networkidle")
        time.sleep(2)
        card = self.page.locator(f"[data-course-id='{curso_id}']").first
        if card.count() == 0:
            link = self.page.locator(f"a[href*='/course/view.php?id={curso_id}']").first
            if link.count() > 0:
                card = link.locator("xpath=ancestor::div[contains(@class, 'course-card') or contains(@class, 'card')]").first
        if card.count() == 0:
            return False
        menu_btn = card.locator(".coursemenubtn, button[data-toggle='dropdown'], button:has(i.fa-ellipsis-v)").first
        if menu_btn.count() == 0:
            return False
        menu_btn.evaluate("el => el.click()")
        time.sleep(1)
        remover = self.page.locator("a[data-action='hide-course'], a.dropdown-item:has-text('Remover da visualização')").first
        if remover.count() > 0:
            remover.evaluate("el => el.click()")
            time.sleep(2)
            return True
        return False

    def garantir_indice_lateral(self) -> bool:
        """Garante que o índice lateral do curso esteja aberto."""
        try:
            drawer = self.page.locator(".drawer.drawer-left, #theme_ava-drawers-courseindex")
            if drawer.count() == 0:
                btn = self.page.locator("[data-action='toggle-courseindex'], button[aria-label='Índice do curso']")
                if btn.count() > 0:
                    btn.first.evaluate("el => el.click()")
                    time.sleep(1)
            self.page.wait_for_selector(".courseindex-item, .drawer .list-group-item", timeout=5000)
            return True
        except Exception:
            return False

    # -------------------------------------------------------------------------
    # ENCONTRAR PRÓXIMA AULA (MÉTODO QUE FALTAVA)
    # -------------------------------------------------------------------------
    def encontrar_proxima_aula_pendente(self):
        """Localiza a próxima aula não concluída dentro do curso atual."""
        self.garantir_indice_lateral()
        itens = self.page.locator(".courseindex-item, .drawer .list-group-item").all()
        if not itens:
            log("Nenhum item no índice. Recarregando...", C.A, "🔄")
            self.page.reload()
            self.page.wait_for_load_state("networkidle")
            time.sleep(3)
            self.garantir_indice_lateral()
            itens = self.page.locator(".courseindex-item, .drawer .list-group-item").all()

        for item in itens:
            try:
                link = item.locator("a[href*='/mod/']").first
                if link.count() == 0:
                    continue
                href = link.get_attribute("href")
                concluido = item.locator(
                    ".completion_complete, i.fa-circle.text-success, i.bi-check-circle-fill"
                ).count() > 0
                if concluido:
                    continue
                if href in self.aulas_tentadas and self.aulas_tentadas[href] >= 3:
                    continue
                nome = (link.inner_text() or "Aula sem nome")[:50]
                log(f"Aula pendente: {nome}", C.V, "📖")
                return link, href
            except Exception:
                continue

        log("Nenhuma aula pendente neste curso!", C.V, "✅")
        return None, None

    # -------------------------------------------------------------------------
    # INTERAÇÕES COM VÍDEO
    # -------------------------------------------------------------------------
    def dar_play_video(self) -> bool:
        time.sleep(1)
        if self.page.locator(".modal-content:visible").count() > 0:
            return False
        try:
            self.page.evaluate("""
                (function() {
                    document.querySelectorAll('video').forEach(v => v.play().catch(()=>{}));
                    document.querySelectorAll('iframe').forEach(iframe => {
                        try { iframe.contentWindow.postMessage('{"event":"command","func":"playVideo","args":""}', '*'); } catch(e) {}
                    });
                    const btn = document.querySelector('#playpause, #play');
                    if (btn) btn.click();
                })();
            """)
            return True
        except Exception:
            return False

    def verificar_video_acabou(self, tempo_inicio: float) -> bool:
        if time.time() - tempo_inicio < self.config.TEMPO_MINIMO_VIDEO:
            return False
        if self.page.locator(".modal-content:visible").count() > 0:
            return False
        if self.pesquisa_concluida:
            time.sleep(2)
            return True
        try:
            current = self.page.locator("#currenttime").inner_text()
            duration = self.page.locator("#duration").inner_text()
            if current and duration and current != "00:00" and duration != "00:00":
                if current.lstrip("0:") == duration.lstrip("0:"):
                    return True
        except Exception:
            pass
        return False

    # -------------------------------------------------------------------------
    # MODAIS – DETECÇÃO E RESOLUÇÃO
    # -------------------------------------------------------------------------
    def detectar_tipo_modal(self) -> str:
        time.sleep(1)
        btn_verificar = self.page.locator("button:has-text('Verifique a conclusão')").first
        if btn_verificar.count() > 0:
            modal_text = ""
            try:
                modal_text = self.page.locator(".modal-content").inner_text().lower()
            except Exception:
                pass
            if "plano de aula" in modal_text or "sala de edição" in modal_text:
                return "plano"
            if self.page.locator(".modal-content iframe").count() > 0:
                iframe = self.page.frame_locator(".modal-content iframe").first
                if iframe.locator("input[type='radio']").count() > 0:
                    return "pergunta"
            return "diagnostico"

        if self.page.locator("textarea[name='field-1768584459']").count() > 0:
            return "pesquisa"

        if self.page.locator(".modal-content iframe").count() > 0:
            iframe = self.page.frame_locator(".modal-content iframe").first
            if iframe.locator("a:has-text('Adicionar envio'), a:has-text('Responder')").count() > 0:
                return "diagnostico"
        if self.page.locator("a:has-text('Adicionar envio'), a:has-text('Responder')").count() > 0:
            return "diagnostico"

        try:
            modal_text = self.page.locator(".modal-content").inner_text().lower()
        except Exception:
            modal_text = ""
        if "plano de aula" in modal_text or "sala de edição" in modal_text:
            return "plano"

        if self.page.locator(".modal-content input[type='radio']").count() > 0:
            return "pergunta"

        if "reflexão" in modal_text:
            return "reflexao"

        return "popup"

    def fechar_modal(self) -> bool:
        time.sleep(1)
        seletores = [
            "button[id^='close-']",
            ".interaction-dismiss",
            "button[aria-label='Fechar']",
            "button[title='Fechar']",
            "button:has(i.bi-x-lg)"
        ]
        for sel in seletores:
            btn = self.page.locator(sel).first
            if btn.count() > 0 and btn.is_visible():
                try:
                    btn.evaluate("el => el.click()")
                    time.sleep(1)
                    return True
                except Exception:
                    continue
        self.page.keyboard.press("Escape")
        time.sleep(0.5)
        return True

    def resolver_popup(self) -> bool:
        return self.fechar_modal()

    def resolver_reflexao(self) -> bool:
        return self.fechar_modal()

    def resolver_pergunta(self) -> bool:
        log("Tentando resolver pergunta...", C.C)
        time.sleep(1)
        if self.page.locator(".modal-content iframe").count() > 0:
            iframe = self.page.frame_locator(".modal-content iframe").first
            opcao = iframe.locator("input[type='radio'][value='correta']").first
            if opcao.count() == 0:
                opcao = iframe.locator("input[type='radio']").first
            if opcao.count() > 0:
                opcao.check(force=True)
                time.sleep(1)
                btn = iframe.locator("#submit-poll, button:has-text('Votar'), button:has-text('Responder')").first
                if btn.count() > 0:
                    btn.click(force=True)
                time.sleep(3)
                self.fechar_modal()
                return True
            else:
                self.fechar_modal()
                return False

        try:
            opcao = self.page.locator("input[type='radio'][value='correta']").first
            if opcao.count() == 0:
                opcao = self.page.locator("input[type='radio']").first
            if opcao.count() > 0:
                opcao.check(force=True)
                time.sleep(1)
                for sel in ["#submit-poll", "button:has-text('Votar')", "button:has-text('Responder')"]:
                    btn = self.page.locator(sel).first
                    if btn.count() > 0:
                        btn.click(force=True)
                        time.sleep(2)
                        break
                self.fechar_modal()
                return True
        except Exception as e:
            log(f"Erro ao resolver pergunta: {e}", C.E)

        self.fechar_modal()
        return False

    def resolver_diagnostico(self) -> bool:
        log("Resolvendo diagnóstico...", C.M, "📝")
        time.sleep(1)
        btn_verificar = self.page.locator("button:has-text('Verifique a conclusão')").first
        if btn_verificar.count() > 0:
            btn_verificar.evaluate("el => el.click()")
            time.sleep(2)

        if self.page.locator(".modal-content iframe").count() > 0:
            iframe = self.page.frame_locator(".modal-content iframe").first
            btn_responder = iframe.locator("a:has-text('Responder'), button:has-text('Responder'), a:has-text('Adicionar envio')").first
            if btn_responder.count() > 0:
                btn_responder.click()
                time.sleep(2)
                editor = iframe.locator(".editor_atto_content, textarea").first
                if editor.count() > 0:
                    self._preencher_texto(editor, self.config.TEXTO_DIAGNOSTICO)
                    time.sleep(1)
                    salvar = iframe.locator("#id_submitbutton, input[value='Salvar mudanças'], button:has-text('Salvar')").first
                    if salvar.count() > 0 and salvar.is_visible():
                        salvar.click()
                        time.sleep(3)
            self.fechar_modal()
            return True

        btn_responder_direto = self.page.locator("button:has-text('Responder'), a:has-text('Responder'), .singlebutton button").first
        if btn_responder_direto.count() > 0 and btn_responder_direto.is_visible():
            btn_responder_direto.click()
            self.page.wait_for_load_state("networkidle")
            time.sleep(2)

        editor = self.page.locator(".editor_atto_content, textarea[name='text']").first
        if editor.count() > 0:
            self._preencher_texto(editor, self.config.TEXTO_DIAGNOSTICO)
            time.sleep(1)

        salvar = self.page.locator("#id_submitbutton, input[value='Salvar mudanças'], button:has-text('Salvar mudanças')").first
        if salvar.count() > 0:
            salvar.click()
            self.page.wait_for_load_state("networkidle")
            time.sleep(2)
            log("Diagnóstico enviado com sucesso", C.V)
            return True
        else:
            log("Botão Salvar não encontrado", C.A)
            return False

    def resolver_plano_aula(self) -> bool:
        log("Resolvendo plano de aula...", C.C)
        time.sleep(1)
        self._clicar_botao("#refresh, button[title='Atualizar']")
        time.sleep(2)
        self._clicar_botao("button:has-text('Verifique a conclusão')")
        time.sleep(1)

        if self.page.locator(".modal-content iframe").count() > 0:
            iframe = self.page.frame_locator(".modal-content iframe").first
            btn = iframe.locator("a:has-text('Responder'), button:has-text('Responder')").first
            if btn.count() > 0:
                btn.evaluate("el => el.click()")
                time.sleep(2)
                editor = iframe.locator(".editor_atto_content").first
                if editor.count() > 0:
                    self._preencher_texto(editor, self.config.TEXTO_PLANO_AULA)
                else:
                    txt = iframe.locator("textarea").first
                    if txt.count() > 0:
                        txt.fill(self.config.TEXTO_PLANO_AULA)
                time.sleep(1)
                salvar = iframe.locator("#id_submitbutton, input[value*='Salvar'], button:has-text('Salvar')").first
                if salvar.count() > 0:
                    salvar.evaluate("el => el.click()")
                    time.sleep(3)
        time.sleep(2)
        self.fechar_modal()
        return True

    def resolver_pesquisa(self) -> bool:
        log("Resolvendo pesquisa de satisfação...", C.M, "⭐")
        time.sleep(2)
        nomes_conhecidos = {
            'field-1768916198', 'field-1768916273', 'field-1768916309',
            'field-1769799109', 'field-1778253076', 'field-1778253089',
            'field-1778253101', 'field-1778253117',
        }
        todos_radios = self.page.locator(
            "input[type='radio'][name^='field-']:not([name='field-1768584459'])"
        ).all()
        nomes_dinamicos = {radio.get_attribute("name") for radio in todos_radios if radio.get_attribute("name")}
        todos_os_nomes = nomes_conhecidos | nomes_dinamicos

        for nome in todos_os_nomes:
            opcoes = self.page.locator(f"input[name='{nome}']").all()
            if opcoes:
                opcoes[-1].evaluate("el => el.click()")
                time.sleep(0.3)

        txt = self.page.locator("textarea[name='field-1768584459']").first
        if txt.count() > 0:
            txt.fill(self.config.TEXTO_PESQUISA)

        btn = self.page.locator("#submitform-submit, button:has-text('Enviar')").first
        if btn.count() > 0:
            btn.evaluate("el => el.click()")
            time.sleep(3)

        time.sleep(2)
        self.fechar_modal()
        self.pesquisa_concluida = True
        return True

    # -------------------------------------------------------------------------
    # MÁQUINA DE MODAIS
    # -------------------------------------------------------------------------
    def handle_modal(self) -> bool:
        ESTRATEGIAS = ["auto", "pergunta", "diagnostico", "pesquisa", "reflexao", "plano", "popup"]
        strategy = ESTRATEGIAS[self.strategy_index]
        log(f"Estratégia atual: {strategy.upper()}", C.A, "🎯")

        if strategy == "auto":
            tipo_alvo = self.detectar_tipo_modal()
        else:
            tipo_alvo = strategy

        handlers = {
            "popup": self.resolver_popup,
            "pergunta": self.resolver_pergunta,
            "diagnostico": self.resolver_diagnostico,
            "reflexao": self.resolver_reflexao,
            "plano": self.resolver_plano_aula,
            "pesquisa": self.resolver_pesquisa,
        }
        handler = handlers.get(tipo_alvo, self.resolver_popup)
        sucesso = handler()

        time.sleep(2)
        modal_ainda_visivel = self.page.locator(".modal-content:visible").count() > 0

        if not modal_ainda_visivel:
            self.strategy_index = 0
            self.attempts_with_current_strategy = 0
            self.interacoes_resolvidas += 1
            print()
            log(f"Interação #{self.interacoes_resolvidas} resolvida", C.V, "✨")
            return True

        self.attempts_with_current_strategy += 1
        if self.attempts_with_current_strategy >= 1:
            self.strategy_index = (self.strategy_index + 1) % len(ESTRATEGIAS)
            self.attempts_with_current_strategy = 0
            if self.strategy_index == 0:
                log("TODAS AS ESTRATÉGIAS FALHARAM!", C.E, "☢️")
                save_debug(self.page, f"modal_falha_total_{datetime.now():%Y%m%d_%H%M%S}", self.config)
                print("\n🚫 O robô não conseguiu fechar o modal mesmo após tentar todos os métodos.")
                print("👉 Vou reiniciar e tentar novamente.\n")
                time.sleep(2)
                raise Exception("RestartBrowser")
            else:
                log(f"Nova estratégia: {ESTRATEGIAS[self.strategy_index]}", C.A, "🔀")
        return False

    # -------------------------------------------------------------------------
    # ASSISTIR VÍDEO
    # -------------------------------------------------------------------------
    def assistir_video(self) -> None:
        inicio = time.time()
        self.pesquisa_concluida = False

        time.sleep(1)
        self.dar_play_video()

        while time.time() - inicio < self.config.TEMPO_MAXIMO_VIDEO:
            m, s = divmod(int(time.time() - inicio), 60)
            print(f"\r ⏱️ {m:02d}:{s:02d} | Resolvidas: {self.interacoes_resolvidas}", end="", flush=True)

            # Processa TODOS os modais visíveis em sequência
            while self.page.locator(".modal-content:visible").count() > 0:
                print()
                self.handle_modal()
                time.sleep(0.5)

            self.dar_play_video()

            if self.verificar_video_acabou(inicio):
                log("Vídeo concluído. Avançando via índice...", C.V, "🏁")
                self.page.reload()
                time.sleep(2)
                break

            time.sleep(self.config.INTERVALO_CHECAGEM_VIDEO)

        print()

    # -------------------------------------------------------------------------
    # PROCESSAR UM CURSO
    # -------------------------------------------------------------------------
    def processar_curso(self, link_curso, card_curso, curso_id: str) -> int:
        self.limpar_console()
        self.menu()
        log(f"NOVO CURSO (ID: {curso_id})", C.B, "📚")
        link_curso.evaluate("el => el.click()")
        self.page.wait_for_load_state("networkidle")
        time.sleep(3)

        videos_curso = 0
        aula_anterior = None

        while True:
            proxima_aula, href_aula = self.encontrar_proxima_aula_pendente()
            if not proxima_aula:
                log("Curso concluído!", C.V, "🎉")
                break

            if aula_anterior == href_aula:
                self.aulas_tentadas[href_aula] = self.aulas_tentadas.get(href_aula, 0) + 1
                if self.aulas_tentadas[href_aula] >= 3:
                    log("Aula não concluiu após 3 tentativas. Pulando...", C.E)
                    aula_anterior = None
                    continue
            else:
                self.aulas_tentadas[href_aula] = 1
                aula_anterior = href_aula

            print()
            log(f"AULA {videos_curso+1} DO CURSO", C.C, "🎬")
            proxima_aula.evaluate("el => el.click()")
            self.page.wait_for_load_state("networkidle")
            time.sleep(3)

            self.page.reload()
            time.sleep(3)
            self.assistir_video()
            videos_curso += 1
            self.total_videos_assistidos += 1
            self.interacoes_resolvidas = 0

            time.sleep(2)
            self.garantir_indice_lateral()

        self.cursos_processados.add(curso_id)
        self.cursos_concluidos += 1

        self.ir_para_meus_cursos()
        sucesso = self.remover_curso_da_visualizacao(curso_id)
        if not sucesso:
            log(f"Não foi possível remover o curso {curso_id}. Recarregando página...", C.A)
            self.page.reload()
            self.page.wait_for_load_state("networkidle")
            time.sleep(2)

        return videos_curso

    # -------------------------------------------------------------------------
    # REINÍCIO COMPLETO
    # -------------------------------------------------------------------------
    def reiniciar_tudo(self) -> None:
        log("Reinicializando completamente o navegador e sessão...", C.A, "🔄")
        self.fechar_navegador()
        self.strategy_index = 0
        self.attempts_with_current_strategy = 0

        time.sleep(2)
        self.iniciar_navegador()
        if not self.login():
            raise Exception("FatalLoginError")
        log("Sessão restabelecida com sucesso!", C.V, "✨")

    # -------------------------------------------------------------------------
    # LOOP INFINITO PRINCIPAL
    # -------------------------------------------------------------------------
    def executar_loop_infinito(self) -> None:
        self.limpar_console()
        self.menu()
        log("Iniciando loop principal para assistir todos os vídeos...", C.C, "🚀")
        while True:
            try:
                self.ir_para_meus_cursos()
                while True:
                    proximo_curso, card_curso, curso_id = self.encontrar_proximo_curso_pendente()
                    if not proximo_curso:
                        log("\n🌟 TODOS OS CURSOS CONCLUÍDOS! 🌟", C.V, "🎉")
                        return
                    self.processar_curso(proximo_curso, card_curso, curso_id)
                    time.sleep(2)
            except Exception as e:
                if "RestartBrowser" in str(e):
                    self.reiniciar_tudo()
                    continue
                elif "FatalLoginError" in str(e):
                    log("Erro crítico de login. Encerrando automação.", C.E, "☢️")
                    break
                else:
                    log(f"Erro inesperado: {e}", C.E, "☢️")
                    traceback.print_exc()
                    self.fechar_navegador()
                    break

    # -------------------------------------------------------------------------
    # EXECUÇÃO PRINCIPAL
    # -------------------------------------------------------------------------
    def run(self) -> None:
        try:
            self.menu()
            self.iniciar_navegador()
            if not self.login():
                return
            self.executar_loop_infinito()
        except KeyboardInterrupt:
            log("\nInterrompido pelo usuário", C.A)
        except Exception as e:
            log(f"Erro: {e}", C.E)
            traceback.print_exc()
        finally:
            log(f"Cursos concluídos: {self.cursos_concluidos}", C.V)
            log(f"Vídeos assistidos: {self.total_videos_assistidos}", C.V)
            input("\nPressione Enter para sair...")
            self.fechar_navegador()

    # -------------------------------------------------------------------------
    # MÉTODOS PRIVADOS AUXILIARES
    # -------------------------------------------------------------------------
    def _preencher_texto(self, editor, texto: str) -> None:
        try:
            editor.click()
            time.sleep(0.5)
            editor.evaluate("el => el.innerHTML = ''")
            editor.evaluate(f"el => el.innerHTML = '<p>{texto}</p>'")
            editor.evaluate("""
                el => {
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                }
            """)
        except Exception:
            editor.fill(texto)

    def _clicar_botao(self, seletor: str) -> bool:
        btn = self.page.locator(seletor).first
        if btn.count() > 0 and btn.is_visible():
            btn.evaluate("el => el.click()")
            return True
        return False

# =============================================================================
# PONTO DE ENTRADA
# =============================================================================
if __name__ == "__main__":
    AVAAutomacao().run()