#   Me ajude a implementar o seguinte tratamento pois tenho certeza de que funcionará
#   ajustar o fluxo de tentativa de resolver os modais
#   se aparecer três vezes o mesmo modal em seguida significa que ele travou nesse modal
#   ou identificou o tipo de modal errado
#   Então ele começa um fluxo de tentar resolver como se fosse outro tipo de modal
#   Se continuar repetindo três vezes ele tenta outro e assim em diante até tentar todos os tipos de modais e se voltar ao tipo inicial
#   Tentar três vezes e não conseguir ele exibe uma mensagem pedindo para reiniciar o código
#   Tira um print e salva na pasta debug

from playwright.sync_api import sync_playwright
import time
from pathlib import Path
from datetime import datetime
import os

# CONFIGURAÇÕES
CPF = "47821023809"
SENHA = "#Calabria7513"
TEXTO_DIAGNOSTICO = "Turma participativa, Porém tem apresentado dificuldades no conceito abordado que precisam ser superados em sala de aula."
TEXTO_PLANO_AULA = "Plano de aula elaborado com sucesso, contemplando os objetivos propostos."
TEXTO_PESQUISA = "Conteúdo excelente, formador muito didático e planejamento bem estruturado!"
TEMPO_MAXIMO_VIDEO = 300000
TEMPO_MINIMO_VIDEO = 30
DEBUG_DIR = Path("debug")
DEBUG_DIR.mkdir(exist_ok=True)
SALVAR_SCREENSHOTS = True

class C:
    R, V, E, A, C, B, M = '\033[0m', '\033[92m', '\033[91m', '\033[93m', '\033[96m', '\033[1m', '\033[95m'

def log(msg, cor=C.C, emoji="•"):
    print(f"{cor}[{datetime.now():%H:%M:%S}] {emoji} {msg}{C.R}")

def save_debug(page, name): #Não salvo mais debug pois está funcionando
    if SALVAR_SCREENSHOTS:
        try: page.screenshot(path=DEBUG_DIR / f"{name}.png", full_page=True)
        except: pass

class AVAAutomacao:
    def __init__(self):
        self.page = self.playwright = None
        self.interacoes_resolvidas = self.total_videos_assistidos = self.cursos_concluidos = 0
        self.pesquisa_concluida = False
        self.modal_fechado_recentemente = False
        self.ultimo_modal_fechado = 0
        self.aulas_tentadas = {}
        self.cursos_processados = set()
        self.modal_resolved_success = False

    def limpar_console(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def iniciar(self):
        log("Iniciando navegador...", C.C, "🌐")
        self.playwright = sync_playwright().start()
        self.page = self.playwright.chromium.launch(headless=False, args=['--window-size=1280,720']).new_context(viewport={'width':1280,'height':720}).new_page()
        self.page.set_default_timeout(30000)

    def fechar(self):
        if self.playwright:
            self.playwright.stop()
            log("Navegador fechado", C.C, "👋")

    def login(self):
        log("Fazendo login...", C.C, "🔐")
        try:
            self.page.goto("https://avaefape.educacao.sp.gov.br/")
            time.sleep(3)
            self.page.locator("input[placeholder*='CPF']").fill(CPF)
            self.page.locator("input[placeholder*='senha']").fill(SENHA)
            self.page.locator("button:has-text('Acessar')").click()
            self.page.wait_for_load_state("networkidle")
            time.sleep(5)
            log("Login realizado", C.V, "✅")
            return True
        except Exception as e:
            log(f"Falha no login: {e}", C.E, "❌")
            return False

    def ir_para_meus_cursos(self):
        log("Indo para Meus Cursos...", C.C, "📚")
        self.page.goto("https://avaefape.educacao.sp.gov.br/my/courses.php")
        self.page.wait_for_load_state("networkidle")
        time.sleep(4)

    def encontrar_proximo_curso_pendente(self):
        log("Procurando cursos pendentes...", C.C, "🔍")
        cursos = self.page.locator(".course-card, .card.course-card, [data-region='course-content'], a[href*='/course/view.php']").all()
        for curso in cursos:
            try:
                if curso.locator(".badge-success, .completion_complete, i.fa-check-circle, i.bi-check-circle-fill").count() == 0:
                    link = curso.locator("a[href*='/course/view.php']").first or curso.locator("a").first
                    if link.count() > 0:
                        href = link.get_attribute("href")
                        curso_id = href.split("id=")[-1] if "id=" in href else ""
                        if curso_id in self.cursos_processados: continue
                        nome = (link.inner_text() or "Curso sem nome")[:50]
                        log(f"Curso pendente: {nome} (ID: {curso_id})", C.V, "📌")
                        return link, curso, curso_id
            except: continue
        log("Nenhum curso pendente!", C.V, "🎉")
        return None, None, None

    def remover_curso_da_visualizacao(self, curso_id):
        log(f" Removendo curso {curso_id} da visualização...", C.C, "🗑️")
        time.sleep(3)
        card = self.page.locator(f"[data-course-id='{curso_id}']").first
        if card.count() == 0:
            link = self.page.locator(f"a[href*='/course/view.php?id={curso_id}']").first
            if link.count() > 0:
                card = link.locator("xpath=ancestor::div[contains(@class, 'course-card') or contains(@class, 'card')]").first
        if card.count() == 0: return False
        menu_btn = card.locator(".coursemenubtn, button[data-toggle='dropdown'], button:has(i.fa-ellipsis-v)").first
        if menu_btn.count() == 0: return False
        menu_btn.evaluate("el => el.click()")
        time.sleep(2)
        remover = self.page.locator("a[data-action='hide-course'], a.dropdown-item:has-text('Remover da visualização')").first
        if remover.count() > 0:
            remover.evaluate("el => el.click()")
            time.sleep(3)
            return True
        return False

    def garantir_indice_lateral(self):
        try:
            drawer = self.page.locator(".drawer.drawer-left, #theme_ava-drawers-courseindex")
            if drawer.count() == 0:
                btn = self.page.locator("[data-action='toggle-courseindex'], button[aria-label='Índice do curso']")
                if btn.count() > 0:
                    btn.first.evaluate("el => el.click()")
                    time.sleep(2)
            self.page.wait_for_selector(".courseindex-item, .drawer .list-group-item", timeout=5000)
            time.sleep(1)
            return True
        except:
            time.sleep(2)
            return False

    def encontrar_proxima_aula_pendente(self):
        self.garantir_indice_lateral()
        itens = self.page.locator(".courseindex-item, .drawer .list-group-item").all()
        if not itens:
            log("Nenhum item no índice. Recarregando...", C.A,"🎉")
            self.page.reload()
            time.sleep(2)
            self.page.wait_for_load_state("networkidle")
            time.sleep(5)
            self.garantir_indice_lateral()
            itens = self.page.locator(".courseindex-item, .drawer .list-group-item").all()
        for item in itens:
            try:
                link = item.locator("a[href*='/mod/']").first
                if link.count() == 0: continue
                href = link.get_attribute("href")
                concluido = item.locator(".completion_complete, i.fa-circle.text-success, i.bi-check-circle-fill").count() > 0
                if concluido: continue
                if href in self.aulas_tentadas and self.aulas_tentadas[href] >= 3: continue
                nome = (link.inner_text() or "Aula sem nome")[:50]
                log(f"Aula pendente: {nome}", C.V, "📖")
                return link, href
            except: continue
        log("Nenhuma aula pendente neste curso!", C.V, "✅")
        return None, None

    def dar_play_video(self):
        time.sleep(4)
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
        except:
            return False

    def verificar_video_acabou(self, tempo_inicio):
        if time.time() - tempo_inicio < TEMPO_MINIMO_VIDEO:
            return False
        if self.page.locator(".modal-content:visible").count() > 0:
            return False
        if self.pesquisa_concluida:
            print("Pesquisa concluída. Aguardando 5 segundos...")
            for segundo in range(5, 0, -1):
                print(f"\rAguardando... {segundo} segundos restantes", end="")
                time.sleep(1)
            print("\r" + " " * 50 + "\r", end="")
            print("Tempo de espera concluído. Deu certo!")
            return True
        try:
            current = self.page.locator("#currenttime").inner_text()
            duration = self.page.locator("#duration").inner_text()
            if current and duration and current != "00:00" and duration != "00:00":
                if current.lstrip("0:") == duration.lstrip("0:"):
                    return True
        except:
            pass
        return False

    def fechar_modal(self):
        time.sleep(4)
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
                    time.sleep(2)
                    self.modal_fechado_recentemente = True
                    self.ultimo_modal_fechado = time.time()
                    return True
                except: continue
        self.page.keyboard.press("Escape")
        time.sleep(1)
        self.modal_fechado_recentemente = True
        self.ultimo_modal_fechado = time.time()
        return True

    def clicar_atualizar(self):
        time.sleep(4)
        btn = self.page.locator("#refresh, button[title='Atualizar']").first
        if btn.count() > 0:
            btn.evaluate("el => el.click()")
            time.sleep(4)
            return True
        return False

    def clicar_verificar_conclusao(self):
        time.sleep(4)
        btn = self.page.locator("button:has-text('Verifique a conclusão')").first
        if btn.count() > 0:
            btn.evaluate("el => el.click()")
            time.sleep(4)
            return True
        return False

    def resolver_popup(self):
        log("Tentando resolver popup...", C.C)
        time.sleep(4)
        self.fechar_modal()
        return True

    def resolver_reflexao(self):
        log("Tentando resolver reflexao...", C.C)
        time.sleep(4)
        self.fechar_modal()
        return True

    def resolver_pergunta(self):
        log("Tentando resolver pergunta...", C.C)
        time.sleep(4)

        try:
            opcao = self.page.locator("input[type='radio'][value='correta']").first
            if opcao.count() == 0:
                opcao = self.page.locator("input[type='radio']").first

            if opcao.count() > 0:
                opcao.check(force=True)
                log("Opção selecionada.", C.V)
                time.sleep(1)

                seletores_botao = ["#submit-poll", "button:has-text('Votar')", "button:has-text('Responder')"]

                for sel in seletores_botao:
                    btn = self.page.locator(sel).first
                    if btn.count() > 0:
                        log(f"Botão de envio encontrado: {sel}", C.V)
                        btn.click(force=True)
                        log("Botão clicado com sucesso.", C.V)
                        time.sleep(6)
                        self.fechar_modal()
                        return True
                    else:
                        time.sleep(5)
                        self.fechar_modal()
                        return True

            else:
                log("Nenhuma opção de rádio encontrada.", C.E)

        except Exception as e:
            log(f"Erro ao resolver pergunta: {e}", C.E)
            time.sleep(3)
            self.fechar_modal()

        return False
        log("Tentando resolver pergunta...", C.C)
        time.sleep(3)

        opcao = self.page.locator("input[type='radio'][value='correta']").first
        if opcao.count() == 0:
            opcao = self.page.locator("input[type='radio']").first

        if opcao.count() > 0:
            opcao.evaluate("el => el.click()")
            time.sleep(1)
            respondido = False
            seletores_botao = ["#submit-poll", "button:has-text('Votar')", "button:has-text('Responder')", ".submitbutton"]

            for sel in seletores_botao:
                btn = self.page.locator(sel).first
                if btn.count() > 0 and btn.is_visible():
                    log(f"Botão de envio encontrado: {sel}", C.V)
                    btn.click()
                    respondido = True
                    time.sleep(5)
                    break
            if respondido:
                log("Pergunta respondida, fechando modal.", C.V)
                self.fechar_modal()
                return True
            else:
                log("Opção selecionada, mas botão de 'Responder' não foi encontrado.", C.A)
                return False
        else:
            log("Nenhuma opção de resposta encontrada no modal.", C.E)
            return False

    def resolver_diagnostico(self):
        log("Resolvendo diagnóstico...", C.M, "📝")
        time.sleep(4)

        self.clicar_verificar_conclusao()
        time.sleep(3)

        if self.page.locator(".modal-content iframe").count() > 0:
            log("Diagnóstico via modal com iframe", C.C)
            iframe = self.page.frame_locator(".modal-content iframe").first
            btn_responder = iframe.locator("a:has-text('Responder'), button:has-text('Responder'), a:has-text('Adicionar envio')").first
            if btn_responder.count() > 0:
                btn_responder.click()
                time.sleep(5)

                editor = iframe.locator(".editor_atto_content, textarea").first
                if editor.count() > 0:
                    editor.click()
                    time.sleep(1)
                    try:
                        editor.evaluate("el => el.innerHTML = ''")
                        editor.evaluate(f"el => el.innerHTML = '<p>{TEXTO_DIAGNOSTICO}</p>'")
                        editor.evaluate("""
                            el => {
                                el.dispatchEvent(new Event('input', { bubbles: true }));
                                el.dispatchEvent(new Event('change', { bubbles: true }));
                            }
                        """)
                    except:
                        editor.fill(TEXTO_DIAGNOSTICO)
                    time.sleep(2)

                for sel in ["#id_submitbutton", "input[value='Salvar mudanças']", "button:has-text('Salvar')"]:
                    salvar = iframe.locator(sel).first
                    if salvar.count() > 0 and salvar.is_visible():
                        salvar.click()
                        time.sleep(5)
                        break
            time.sleep(5)
            self.fechar_modal()
            return True

        log("Diagnóstico via página de tarefa padrão", C.C)
        btn_responder_direto = self.page.locator("button:has-text('Responder'), a:has-text('Responder'), .singlebutton button").first
        if btn_responder_direto.count() > 0 and btn_responder_direto.is_visible():
            btn_responder_direto.click()
            self.page.wait_for_load_state("networkidle")
            time.sleep(5)

        editor = self.page.locator(".editor_atto_content, textarea[name='text']").first
        if editor.count() > 0:
            editor.click()
            time.sleep(1)
            try:
                editor.evaluate("el => el.innerHTML = ''")
                editor.evaluate(f"el => el.innerHTML = '<p>{TEXTO_DIAGNOSTICO}</p>'")
                editor.evaluate("""
                    el => {
                        el.dispatchEvent(new Event('input', { bubbles: true }));
                        el.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                """)
            except:
                editor.fill(TEXTO_DIAGNOSTICO)
            time.sleep(2)

        salvar = self.page.locator("#id_submitbutton, input[value='Salvar mudanças'], button:has-text('Salvar mudanças')").first
        if salvar.count() > 0:
            salvar.click()
            time.sleep(5)
            self.page.wait_for_load_state("networkidle")
            log("Diagnóstico enviado com sucesso", C.V)
            return True
        else:
            log("Botão Salvar não encontrado", C.A)
            return False

    def resolver_plano_aula(self):
        time.sleep(3)
        self.clicar_atualizar()
        time.sleep(3)
        self.clicar_verificar_conclusao()
        time.sleep(3)
        iframe = self.page.frame_locator(".modal-content iframe").first
        btn = iframe.locator("a:has-text('Responder'), button:has-text('Responder')").first
        if btn.count() > 0:
            btn.evaluate("el => el.click()")
            time.sleep(4)
            editor = iframe.locator(".editor_atto_content").first
            if editor.count() > 0:
                editor.click()
                time.sleep(1)
                editor.evaluate("el => el.innerHTML = ''")
                editor.evaluate(f"el => el.innerHTML = '<p>{TEXTO_PLANO_AULA}</p>'")
            else:
                editor = iframe.locator("textarea").first
                if editor.count() > 0:
                    editor.fill(TEXTO_PLANO_AULA)
            time.sleep(1)
            for sel in ["#id_submitbutton", "input[value*='Salvar']", "button:has-text('Salvar')"]:
                salvar = iframe.locator(sel).first
                if salvar.count() > 0:
                    salvar.evaluate("el => el.click()")
                    time.sleep(5)
                    break
        time.sleep(5)
        self.fechar_modal()
        return True

    def resolver_pesquisa(self):
        time.sleep(5)
        for name in ['field-1768916198', 'field-1768916273', 'field-1768916309', 'field-1769799109']:
            ops = self.page.locator(f"input[name='{name}']").all()
            if ops:
                ops[-1].evaluate("el => el.click()")
                time.sleep(0.3)
        txt = self.page.locator("textarea[name='field-1768584459']").first
        if txt.count() > 0:
            txt.fill(TEXTO_PESQUISA)
        btn = self.page.locator("#submitform-submit, button:has-text('Enviar')").first
        if btn.count() > 0:
            btn.evaluate("el => el.click()")
            time.sleep(5)
        time.sleep(5)
        self.fechar_modal()
        time.sleep(10)
        self.pesquisa_concluida = True
        return True

    def detectar_tipo_modal(self):
        try:
            time.sleep(3)
            texto = self.page.locator(".modal-content").inner_text().lower()
        except:
            texto = ""
        if "diagnóstico da turma" in texto:
            return "diagnostico"
        if "plano de aula" in texto or "sala de edição" in texto:
            return "plano"
        if "pesquisa" in texto or "satisfação" in texto:
            return "pesquisa"
        if "reflexão" in texto:
            return "reflexao"
        if self.page.locator(".modal-content input[type='radio']").count() > 0:
            return "pergunta"
        return "popup"

    def handle_modal(self):
        ESTRATEGIAS = ["auto", "pergunta", "diagnostico", "pesquisa", "reflexao", "plano",  "popup"]

        # Estado da máquina (inicializa se não existir)
        if not hasattr(self, 'stuck_strategy_idx'):
            self.stuck_strategy_idx = 0
            self.stuck_fail_count = 0

        strategy = ESTRATEGIAS[self.stuck_strategy_idx]
        log(f"Estratégia atual: {strategy.upper()}", C.A, "🎯")

        # Escolhe o tipo alvo: se for 'auto', usa a detecção real
        if strategy == "auto":
            tipo_alvo = self.detectar_tipo_modal()
        else:
            tipo_alvo = strategy

        # Executa o handler correspondente
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

        # Aguarda um instante e verifica se o modal ainda está visível
        time.sleep(3)
        modal_ainda_visivel = self.page.locator(".modal-content:visible").count() > 0

        if not modal_ainda_visivel:
            # Sucesso! Reseta tudo e retorna
            self.stuck_strategy_idx = 0
            self.stuck_fail_count = 0
            self.interacoes_resolvidas += 1
            print("\n")
            log(f"Interação #{self.interacoes_resolvidas} resolvida", C.V, "✨")
            return True

        # Falha: incrementa contador
        self.stuck_fail_count += 1

        if self.stuck_fail_count >= 2:
            # Troca de estratégia
            self.stuck_strategy_idx = (self.stuck_strategy_idx + 1) % len(ESTRATEGIAS)
            self.stuck_fail_count = 0

            # Se voltou ao início (auto) significa que todas falharam
            if self.stuck_strategy_idx == 0:
                log("TODAS AS ESTRATÉGIAS FALHARAM!", C.E, "☢️")
                save_debug(self.page, f"modal_falha_total_{datetime.now():%Y%m%d_%H%M%S}")
                print("\n🚫 O robô não conseguiu fechar o modal mesmo após tentar todos os métodos.")
                print("👉 Vou reiniciar essa badarosca e começar outra vez, relaxa.\n")
                time.sleep(2)
                raise Exception("RestartBrowser")
            else:
                log(f"Nova estratégia: {ESTRATEGIAS[self.stuck_strategy_idx]}", C.A, "🔀")

        return False

    def assistir_video(self):
        inicio = time.time()
        self.pesquisa_concluida = False
        self.modal_fechado_recentemente = False

        time.sleep(2)
        self.dar_play_video()

        while time.time() - inicio < TEMPO_MAXIMO_VIDEO:
            m, s = divmod(int(time.time() - inicio), 60)
            print(f"\r ⏱️ {m:02d}:{s:02d} | Resolvidas: {self.interacoes_resolvidas}", end="", flush=True)

            modal = self.page.locator(".modal-content:visible").first
            if modal.count() > 0:
                agora = time.time()
                # Evita nova tentativa imediatamente após fechar um modal
                if self.modal_fechado_recentemente and (agora - self.ultimo_modal_fechado) < 3:
                    time.sleep(1)
                    continue

                self.modal_fechado_recentemente = False
                print()
                self.handle_modal()
                self.dar_play_video()
            else:
                self.dar_play_video()

            if self.verificar_video_acabou(inicio):
                log("Vídeo concluído. Avançando via índice...", C.V, "🏁")
                self.page.reload()
                time.sleep(2)
                break

            time.sleep(1)

        print()
        return True

    def processar_curso(self, link_curso, card_curso, curso_id):
        time.sleep(5)
        self.limpar_console()
        self.menu()
        log(f"NOVO CURSO (ID: {curso_id})", C.B, "📚")
        link_curso.evaluate("el => el.click()")
        self.page.wait_for_load_state("networkidle")
        time.sleep(5)

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
                    log("Aula não conclui após 3 tentativas. Pulando...", C.E)
                    aula_anterior = None
                    continue
            else:
                self.aulas_tentadas[href_aula] = 1
                aula_anterior = href_aula

            print("\n")
            log(f"AULA {videos_curso+1} DO CURSO", C.C,"🎬")
            proxima_aula.evaluate("el => el.click()")
            self.page.wait_for_load_state("networkidle")
            time.sleep(5)
            print("\n")


            self.page.reload()
            time.sleep(5)
            self.assistir_video()
            videos_curso += 1
            self.total_videos_assistidos += 1
            self.interacoes_resolvidas = 0

            time.sleep(3)
            self.garantir_indice_lateral()

        self.cursos_processados.add(curso_id)   # marca antes de tentar remover
        self.cursos_concluidos += 1

        self.ir_para_meus_cursos()
        sucesso = self.remover_curso_da_visualizacao(curso_id)
        if not sucesso:
            log(f"Não foi possível remover o curso {curso_id}. Recarregando página...", C.A)
            self.page.reload()
            self.page.wait_for_load_state("networkidle")
            time.sleep(3)

        return videos_curso

    def reiniciar_tudo(self):
        log("Iniciando reinicialização completa do sistema...", C.A, "🔄")

        try:
            self.fechar()
        except Exception as e:
            log(f"Aviso ao fechar navegador: {e}", C.A, "⚠️")

        self.modal_history = []
        self.strategy_index = 0
        self.attempts_with_current_strategy = 0
        self.modal_resolved_success = False
        self.modal_fechado_recentemente = False

        time.sleep(2)

        self.iniciar()
        log("Tentando restabelecer sessão...", C.C, "🔐")

        if not self.login():
            log("Falha crítica ao relogar durante o reinício!", C.E, "❌")
            raise Exception("FatalLoginError")

        log("Sistema reiniciado e pronto para continuar!", C.V, "✨")

    def executar_loop_infinito(self):
        time.sleep(5)
        self.limpar_console()
        self.menu()
        log("Vamos iniciar um loop para assistir seus vídeos", C.C, "🚀")
        while True:
            try:
                # Garante que o robô comece na página correta
                self.ir_para_meus_cursos()

                # Sub-loop para processar os cursos
                while True:
                    proximo_curso, card_curso, curso_id = self.encontrar_proximo_curso_pendente()

                    if not proximo_curso:
                        log("\n🌟 TODOS OS CURSOS CONCLUÍDOS! 🌟", C.V, "🎉")
                        return # Encerra o script de vez

                    self.processar_curso(proximo_curso, card_curso, curso_id)
                    time.sleep(3)

            except Exception as e:
                if "RestartBrowser" in str(e):
                    # Se for o nosso erro programado de reinício
                    self.reiniciar_tudo()
                    # O loop 'while True' externo vai recomeçar do 'self.ir_para_meus_cursos()'
                else:
                    # Se for um erro real do Python/Playwright que não previmos
                    log(f"Erro fatal não tratado: {e}", C.E, "☢️")
                    self.fechar()
                    break

    def menu(self):
        print(f"""
{C.C}╔══════════════════════════════════════════════════════════════════╗
║     🎮 AUTOMAÇÃO AVA-EFAPE - PARA VOCÊ PODER TRABALHAR 🎮        ║
╚══════════════════════════════════════════════════════════════════╝{C.R}
        """)

    def run(self):
        try:
            self.menu()
            self.iniciar()
            if not self.login():
                return
            self.executar_loop_infinito()
        except KeyboardInterrupt:
            log("\nInterrompido pelo usuário", C.A)
        except Exception as e:
            log(f"Erro: {e}", C.E)
            import traceback
            traceback.print_exc()
        finally:
            log(f"Cursos concluídos: {self.cursos_concluidos}", C.V)
            log(f"Vídeos assistidos: {self.total_videos_assistidos}", C.V)
            input("\nPressione Enter...")
            self.fechar()

if __name__ == "__main__":
    AVAAutomacao().run()