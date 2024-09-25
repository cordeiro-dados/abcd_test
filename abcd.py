import streamlit as st
from databricks import sql
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()
DB_SERVER_HOSTNAME = os.getenv("DB_SERVER_HOSTNAME")
DB_HTTP_PATH = os.getenv("DB_HTTP_PATH")
DB_ACCESS_TOKEN = os.getenv("DB_ACCESS_TOKEN")

# Função para conectar ao banco de dados
def conectar_banco():
    return sql.connect(
        server_hostname=DB_SERVER_HOSTNAME,
        http_path=DB_HTTP_PATH,
        access_token=DB_ACCESS_TOKEN
    )

# Função para buscar colaboradores da tabela dim_employee
def buscar_colaboradores():
    connection = conectar_banco()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT
          id AS id_employee,
          Nome AS nm_employee,
          Setor AS nm_departament,
          Gestor_Direto AS nm_gestor,
          Diretoria AS nm_diretoria
        FROM
          datalake.silver_pny.func_zoom
    """)
    colaboradores = cursor.fetchall()
    cursor.close()
    connection.close()
    return {row['nm_employee']: {'id': row['id_employee'], 'departament': row['nm_departament'], 'gestor': row['nm_gestor'], 'diretoria': row['nm_diretoria']} for row in colaboradores}


# Função para buscar o id do gestor selecionado
def buscar_id_gestor(nome_gestor):
    connection = conectar_banco()
    cursor = connection.cursor()
    cursor.execute(f"""
        SELECT id_employee
        FROM datalake.silver_pny.dim_employee
        WHERE nm_employee = '{nome_gestor}'
    """)
    resultado = cursor.fetchone()
    cursor.close()
    connection.close()
    return resultado['id_employee'] if resultado else None

# Função para buscar os funcionários do gestor selecionado
def buscar_funcionarios_por_gestor(nome_gestor):
    connection = conectar_banco()
    cursor = connection.cursor()
    cursor.execute(f"""
        SELECT
          id AS id_employee,
          Nome AS nm_employee
        FROM
          datalake.silver_pny.func_zoom
        WHERE Gestor_Direto = '{nome_gestor}'
    """)
    funcionarios = cursor.fetchall()
    cursor.close()
    connection.close()
    return {row['id_employee']: row['nm_employee'] for row in funcionarios}

# Função para verificar se o funcionário já foi avaliado
# Função para verificar se o funcionário já foi avaliado
def verificar_se_foi_avaliado(id_emp):
    connection = conectar_banco()
    cursor = connection.cursor()
    cursor.execute(f"""
        SELECT data_resposta, soma_final, nota
        FROM datalake.avaliacao_abcd.avaliacao_abcd
        WHERE id_emp = '{id_emp}'
        ORDER BY data_resposta DESC
    """)
    resultados = cursor.fetchall()
    cursor.close()
    connection.close()
    
    # Retorna a lista de avaliações com data, soma_final e nota
    return resultados if resultados else []



def abcd_page():
    # Verifica se o usuário está logado
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        st.error("Você precisa fazer login para acessar essa página.")
        return

    st.title("Avaliação ABCD")
    # Aplicando CSS para aumentar a largura da página e expandir elementos
    st.markdown(
        """
        <style>
        .main .block-container {
            max-width: 1200px;  /* Aumenta a largura máxima da página */
            padding-left: 2rem;
            padding-right: 2rem;
        }
        .stTextInput > div > div > input {
            width: 100% !important;  /* Expande a largura das caixas de texto */
        }
        .center {
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 20px;
        }
        
        </style>
        """,
        unsafe_allow_html=True
    )


    # Definindo as categorias, notas e suas pontuações com descrições para comportamental
    categorias_comportamental = ["Colaboração", "Inteligência Emocional", "Responsabilidade", "Iniciativa / Pró atividade", "Flexibilidade"]
    pontuacoes_comportamental = {
        "A": 10,
        "B+": 8,
        "B": 6,
        "C": 4,
        "D": 0
    }
    descricoes_comportamental = {
        "Colaboração": {
            "A": "Está sempre disponível para servir, tem opiniões próprias, está disposto a colaborar para o atingimento dos bons resultados, independentemente se as ideias são suas ou dos seus colegas. O interesse em colaborar deve ser nato.",
            "B+": "De modo geral tem disposição para colaborar, esforça-se para entregar bons resultados. É prestativo e coloca-se em posição de aprendiz sempre que necessário.",
            "B": "Colabora de forma aceitável, para que o time e a empresa tenham um bom fluxo nas suas atividades.",
            "C": "Tem dificuldade em colaborar com o time em prol de um resultado coletivo. Está deixando de atender as necessidades da equipe e da empresa.",
            "D": "Não se coloca mais como um colaborador. Não atende mais as expectativas do time e da empresa."
        },
        "Inteligência Emocional": {
            "A": "É sempre ponderado em situações de tensão e conflito. Transmite segurança e tranquilidade aos demais, mantendo o equilíbrio emocional de todos a sua volta.",
            "B+": "Habitualmente mantem o controle emocional em situações adversas. Nos momentos de crise e tensão sofre alterações mas volta ao equilíbrio com facilidade.",
            "B": "A perda de equilíbrio emocional é momentânea e aceitável para o seu nível de atuação e maturidade na empresa. Precisa ser desenvolvido para evoluir emocionalmente.",
            "C": "Tem muita dificuldade em manter o equilíbrio emocional. Por vezes deixa sua vida externa impactar em seus resultados na empresa.",
            "D": "Não tem equilíbrio emocional, suas ações são degradáveis e já não agrega ao time e a empresa."
        },
        "Responsabilidade": {
            "A": "Traz a responsabilidade para si, é altamente comprometido com a Empresa, líderes, pares e o time de uma forma geral. Assume seus atos e está a altura dos desafios propostos.",
            "B+": "É comprometido com a sua palavra, honra seus compromissos e entende que é exemplo para os demais do seu time e empresa.",
            "B": "Em algumas situações precisa se provocação do pelo líder, principalmente no que se refere a prazos. De maneira geral assume a responsabilidade e está aberto a mudança de comportamento.",
            "C": "Tem sempre uma justificativa para a perda de prazos. Terceiriza a responsabilidade, porém usa o discurso de que está disponível para mudar o comportamento.",
            "D": "Foge da responsabilidade, está sempre se esquivando dos seus compromissos e verbaliza a certeza de que suas atitudes são corretas e coerentes."
        },
        "Iniciativa / Pró atividade": {
            "A": "Tem alta iniciativa e determinação. Entrega sempre resultados a mais que o esperado, demonstrado a sua senioridade. Não se deixa abater diante das dificuldades, mostra-se comprometido com as suas tarefas e com o resultado dos demais.",
            "B+": "Tem iniciativa na maioria das situações. Vai além dos compromissos rotineiros na maioria das vezes. Assume com frequência os imprevistos e se coloca a disposição para ajudar o time de uma forma geral quando necessário.",
            "B": "Tem iniciativa de forma normal e pontual, dentro do esperado para um colaborador na média. Seus resultados atendem a empresa, mas não são brilhantes.",
            "C": "Não demonstra muita pro atividade e iniciativa diante das atividades propostas. Se mantem neutro nas situações evitando sempre o acúmulo de trabalho.",
            "D": "Não atende as expectativas, se esconde de novas responsabilidades e não é um bom exemplo para o time."
        },
        "Flexibilidade": {
            "A": "Adapta-se de forma veloz ao que está sendo lidado e não cria barreiras, pelo contrário- enxerga sempre uma possibilidade de crescimento.",
            "B+": "Convive na maioria das vezes muito bem com as adversidades que vão sendo impostas. Ainda precisa-se adaptar para “fazer sem reclamar”, porém traz o resultado esperado.",
            "B": "Reclama mas faz, não gosta de mudanças abruptas e resmunga para as novas diretrizes.",
            "C": "Reclama bastante e desestimula os colegas diante de novos desafios. Faz as demandas apenas sob supervisão.",
            "D": "Reclama o tempo todo e não cumpre com os prazos estipulados, pois não acredita mais nas diretrizes impostas."
        }
    }

    # Definindo a única categoria, notas e suas pontuações com descrições para técnico
    categoria_tecnica = "Conhecimento Técnico"
    pontuacoes_tecnico = {
        "A": 50,
        "B+": 40,
        "B": 30,
        "C": 20,
        "D": 0
    }

    # Simulação de descrições para a categoria técnica
    descricoes_tecnico = {
        "A": "Descrição A para Conhecimento Técnico",
        "B+": "Descrição B+ para Conhecimento Técnico",
        "B": "Descrição B para Conhecimento Técnico",
        "C": "Descrição C para Conhecimento Técnico",
        "D": "Descrição D para Conhecimento Técnico"
    }


    # Função para calcular a nota final
    def calcular_nota_final(selecoes_comportamental, selecao_tecnico):
        nota_comportamental = sum(pontuacoes_comportamental[nota] for nota in selecoes_comportamental if nota)
        nota_tecnico = pontuacoes_tecnico[selecao_tecnico] if selecao_tecnico else 0
        return nota_comportamental, nota_tecnico, nota_comportamental + nota_tecnico

    # Função para determinar a nota com base na soma final
    def determinar_nota_final(soma_final):
        if soma_final <= 29:
            return "D"
        elif 30 <= soma_final <= 49:
            return "C"
        elif 50 <= soma_final <= 69:
            return "B"
        elif 70 <= soma_final <= 89:
            return "B+"
        else:
            return "A"

    # Função para atualizar o banco de dados
    def atualizar_banco_dados(id_emp, nome_colaborador, nome_gestor, setor, diretoria, data_resposta, nota_final, soma_final, notas_categorias):
        try:
            connection = conectar_banco()
            cursor = connection.cursor()
            cursor.execute(f"""
                INSERT INTO datalake.avaliacao_abcd.avaliacao_abcd (
                    id_emp, nome_colaborador, nome_gestor, setor, diretoria, data_resposta, nota, soma_final,
                    colaboracao, inteligencia_emocional, responsabilidade, iniciativa_proatividade, flexibilidade, conhecimento_tecnico
                )
                VALUES (
                    '{id_emp}', '{nome_colaborador}', '{nome_gestor}', '{setor}', '{diretoria}', '{data_resposta}', '{nota_final}', '{soma_final}',
                    '{notas_categorias["colaboracao"]}', '{notas_categorias["inteligencia_emocional"]}', '{notas_categorias["responsabilidade"]}',
                    '{notas_categorias["iniciativa_proatividade"]}', '{notas_categorias["flexibilidade"]}', '{notas_categorias["conhecimento_tecnico"]}'
                )
            """)
            connection.commit()
            cursor.close()
            connection.close()
            st.success("Avaliação salva com sucesso no banco de dados!")
        except Exception as e:
            st.error(f"Erro ao salvar no banco de dados: {str(e)}")

    def limpar_campos():
        st.session_state['nome_colaborador'] = ""
        st.session_state['nome_gestor'] = ""
        st.session_state['setor'] = ""
        st.session_state['diretoria'] = ""
        st.session_state['data_resposta'] = datetime.today()

    # Interface em Streamlit
    # Interface em Streamlit
    st.header("Preencha as informações abaixo:")

    # Buscar colaboradores, departamentos e gestores
    colaboradores_data = buscar_colaboradores()

    # Inputs de informações do colaborador
    cols_inputs = st.columns(2)

    with cols_inputs[0]:
        nome_colaborador = st.selectbox("Nome do Colaborador", options=[""] + list(colaboradores_data.keys()))
        if nome_colaborador:
            id_emp = colaboradores_data[nome_colaborador]['id']
        else:
            id_emp = None

    with cols_inputs[1]:
        nome_gestor = st.text_input("Nome do Gestor", value=colaboradores_data[nome_colaborador]['gestor'] if nome_colaborador else "", disabled=True)

    cols_inputs2 = st.columns(2)

    with cols_inputs2[0]:
        setor = st.selectbox("Setor", options=[colaboradores_data[nome_colaborador]['departament']] if nome_colaborador else [""])

    with cols_inputs2[1]:
        diretoria = st.text_input("Diretoria", value=colaboradores_data[nome_colaborador]['diretoria'] if nome_colaborador else "", disabled=True)

    cols_date = st.columns([1, 3])

    with cols_date[0]:
        data_resposta = st.date_input("Data da Resposta", value=datetime.today(), format="DD-MM-YYYY")

    # Verifica se o colaborador foi selecionado antes de habilitar a avaliação
    if nome_colaborador:
        notas_categorias = {}

        # Avaliação Comportamental
        st.subheader("Comportamental")
        for categoria in categorias_comportamental:
            st.subheader(categoria)
            cols = st.columns([5, 5, 5, 5, 5])

            selected_nota = st.session_state.get(categoria)
            for i, (nota, desc) in enumerate(descricoes_comportamental[categoria].items()):
                with cols[i]:
                    if st.button(f"{nota}\n\n{desc}", key=f"{categoria}_{nota}"):
                        st.session_state[categoria] = nota
                        st.success(f"Selecionado: {nota} para {categoria}")

            # Exibir o feedback de seleção
            if selected_nota:
                st.write(f"Selecionado para {categoria}: {selected_nota}")

            if categoria == "Colaboração":
                notas_categorias["colaboracao"] = st.session_state.get(categoria)
            elif categoria == "Inteligência Emocional":
                notas_categorias["inteligencia_emocional"] = st.session_state.get(categoria)
            elif categoria == "Responsabilidade":
                notas_categorias["responsabilidade"] = st.session_state.get(categoria)
            elif categoria == "Iniciativa / Pró atividade":
                notas_categorias["iniciativa_proatividade"] = st.session_state.get(categoria)
            elif categoria == "Flexibilidade":
                notas_categorias["flexibilidade"] = st.session_state.get(categoria)

        # Avaliação Técnica
        st.subheader("Conhecimento Técnico")
        cols = st.columns([5, 5, 5, 5, 5])

        selected_nota = st.session_state.get(categoria_tecnica)
        for i, (nota, desc) in enumerate(descricoes_tecnico.items()):
            with cols[i]:
                if st.button(f"{nota}\n\n{desc}", key=f"{categoria_tecnica}_{nota}"):
                    st.session_state[categoria_tecnica] = nota
                    st.success(f"Selecionado: {nota} para {categoria_tecnica}")

        if selected_nota:
            st.write(f"Selecionado para Conhecimento Técnico: {selected_nota}")
        notas_categorias["conhecimento_tecnico"] = st.session_state.get(categoria_tecnica)

        # Botão para calcular a nota e salvar no banco de dados
        if st.button("Calcular Nota e Salvar"):
            selecoes_comportamental = [st.session_state.get(categoria) for categoria in categorias_comportamental]
            selecao_tecnico = st.session_state.get(categoria_tecnica)

            if None in selecoes_comportamental or not selecao_tecnico:
                st.error("Você deve selecionar uma nota para todas as categorias antes de salvar.")
            else:
                nota_comportamental, nota_tecnico, soma_final = calcular_nota_final(selecoes_comportamental, selecao_tecnico)
                nota_final = determinar_nota_final(soma_final)

                st.write(f"Nota Comportamental: {nota_comportamental}")
                st.write(f"Nota Técnica: {nota_tecnico}")
                st.write(f"Soma Final: {soma_final}")
                st.write(f"Nota Final: {nota_final}")

                atualizar_banco_dados(id_emp, nome_colaborador, nome_gestor, setor, diretoria, data_resposta, nota_final, soma_final, notas_categorias)
                limpar_campos()

    else:
        st.warning("Por favor, selecione um colaborador para habilitar as opções de avaliação.")

    # Lista de IDs de supervisores permitidos
    if nome_gestor:
        funcionarios = buscar_funcionarios_por_gestor(nome_gestor)
        if funcionarios:
            avaliados, nao_avaliados = [], []
            for id_emp, nome_funcionario in funcionarios.items():
                avaliacoes = verificar_se_foi_avaliado(id_emp)
                if avaliacoes:
                    for avaliacao in avaliacoes:
                        data_resposta, soma_final, nota_final = avaliacao
                        avaliados.append((nome_funcionario, data_resposta, soma_final, nota_final))
                else:
                    nao_avaliados.append(nome_funcionario)

            st.write("#### Funcionários Avaliados")
            st.write("NF = Nota Final, CTO = Nota Conceito")
            if avaliados:
                colunas_avaliados = st.columns(3)  # Grid de 3 colunas
                for i, (nome_funcionario, data_resposta, soma_final, nota_final) in enumerate(avaliados):
                    with colunas_avaliados[i % 3]:
                        st.write(f"✅ {nome_funcionario}: (Data: {data_resposta}) (NF {soma_final}) (CTO {nota_final})")
            else:
                st.write("Nenhum funcionário avaliado encontrado.")

            st.write("#### Funcionários Não Avaliados")
            if nao_avaliados:
                colunas_nao_avaliados = st.columns(3)  # Grid de 3 colunas
                for i, nome_funcionario in enumerate(nao_avaliados):
                    with colunas_nao_avaliados[i % 3]:
                        st.write(f"❌ {nome_funcionario}")
            else:
                st.write("Todos os funcionários já foram avaliados.")
        else:
            st.write("Nenhum funcionário encontrado.")
