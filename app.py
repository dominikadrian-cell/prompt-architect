import os
import datetime
import hashlib
import streamlit as st
from google import genai
import docx  # Für den Word-Dokumenten-Import (.docx)

# --- SEITENKONFIGURATION ---
st.set_page_config(
    page_title="Prompt-Architect // Industrial AI",
    page_icon="⚙️",
    layout="wide"
)

st.title("⚡ Prompt-Architect: Industrial & Handwerk Edition")
st.markdown("### Modul-Suite aktiv: Workflow, Multi-Upload (PDF & Word), Revisionssicherer Audit-Trail, Mini-RAG & Wert-Baukasten")

# --- SIDEBAR: NUR NOCH DAS NÖTIGSTE (GLOBAL SETUP) ---
st.sidebar.header("🔑 API & Setup")

env_api_key = os.environ.get("GEMINI_API_KEY", "")
if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
    env_api_key = st.secrets["GEMINI_API_KEY"]

api_key_input = st.sidebar.text_input(
    "Google AI Studio API-Key",
    type="password",
    value=env_api_key,
    placeholder="Dein Key hier einfügen..."
)

st.sidebar.header("⚙️ Betriebs-Modus")
app_mode = st.sidebar.radio(
    "Leistungsklasse wählen:",
    ["🔨 Handwerk & Kleinbetrieb", "🏭 Industrie & Enterprise"]
)

target_model = st.sidebar.selectbox(
    "KI-Modell",
    ["gemini-3.8-flash", "gemini-3.1-pro-preview"],
    key="model_select"
)

target_language = st.sidebar.selectbox(
    "Ausgabesprache",
    ["Deutsch", "English (Englisch)", "Български (Bulgarisch)", "Français (Französisch)", "Español (Spanisch)"]
)

# --- MODUS-WECHSEL ERKENNEN & STATE AKTUALISIEREN ---
if "last_app_mode" not in st.session_state:
    st.session_state["last_app_mode"] = app_mode

mode_changed = st.session_state["last_app_mode"] != app_mode
if mode_changed:
    st.session_state["last_app_mode"] = app_mode

is_handwerk = "Handwerk" in app_mode

if is_handwerk:
    default_company = "Tischlerei & Innenausbau Wagner e.K."
    default_history = "Gegründet 1988, Meisterbetrieb in 2. Generation"
    industry_options = [
        "Tischler- & Innenausbau", 
        "Elektrotechnik & Automation", 
        "Sanitär, Heizung & Klima (SHK)", 
        "Dachdecker & Bauhauptgewerbe", 
        "➕ Anderes Gewerk (Freitext)..."
    ]
    tone_options = [
        "Kante & Klartext: Direkt, ehrlich, handwerklich (Kein Bullshit)",
        "Meisterlich, bestimmt & rechtssicher (VOB-Standard)",
        "Kundenfreundlich, nahbar & lösungsorientiert",
        "Pragmatisch, kurz & direkt (Baustellen-Fokus)"
    ]
    default_core_values = [
        "Pünktliche Lieferung & saubere Ausführung",
        "Ehrliche Handschlagqualität & keine versteckten Kosten",
        "VOB/B & BGB Rechtssicherheit bei Verträgen"
    ]
    default_hourly = 65.00
    default_travel = 45.00
    default_positions = "Montagestunde Handwerker: 65.00 € / Std.\nAnfahrtspauschale: 45.00 €\nMaterial-Aufschlag: 20%"
    mode_instructions = "Fokussiere auf schnelle, handwerklich klare Angebote, Stundensätze und praxisnahe Kommunikation."
    
    workflow_snippets = {
        "Manuell eingeben (Freitext)": "",
        "⚠️ VOB-Bedenkenanzeige (Mangelhafte Vorleistung)": "Erstelle eine formgerechte und rechtssichere Bedenkenanzeige gemäß VOB/B. Der Untergrund bzw. die bauseits erbrachte Vorleistung ist mangelhaft und behindert unsere fachgerechte Ausführung. Weise auf Haftungsrisiken hin.",
        "📋 Nachtragsangebot erstellen": "Erstelle ein sauberes Nachtragsangebot für die zusätzlich geforderten Leistungen (Mehrumfang). Nutze exakt unsere hinterlegten Stundensätze und Materialaufschläge.",
        "🛡️ Unberechtigte Mängelrüge / Rechnungskürzung abwehren": "Formuliere eine bestimmte, aber sachliche Erwiderung auf die unberechtigte Mängelrüge des Kunden. Weise nach, dass unsere Leistung vertragsgerecht und fehlerfrei erbracht wurde.",
        "✉️ Verbindliches Kundenangebot verfassen": "Erstelle ein vollständiges, professionelles Angebot im Betriebsstil basierend auf der Kundenanfrage. Nutze unsere Standard-Positionen und Zahlungsbedingungen."
    }
    demo_task_text = """Kundenanfrage für eine massgeschneiderte Terrassenüberdachung aus Lärche (ca. 6x4m). Bauseits sind die Punktfundamente bereits gesetzt, allerdings weicht der rechte Winkel um ca. 3cm ab. 
    Erstelle ein vollständiges, verbindliches Angebot inklusive Montage, Anfahrt und Materialaufschlag. Weise im Angebot charmant aber bestimmt auf die Toleranzabweichung der Fundamente hin."""
    demo_rag_text = ""
else:
    default_company = "Industrie-Anlagenbau Rhein-Ruhr GmbH"
    default_history = "Mittelständischer Anlagenbauer, 240 Mitarbeiter, gegr. 1978"
    industry_options = [
        "Maschinen- & Anlagenbau (Industrie)", 
        "Automotive & Zulieferindustrie", 
        "Prozessleittechnik & Automation", 
        "Chemie & Verfahrenstechnik", 
        "➕ Anderer Industrie-Sektor (Freitext)..."
    ]
    tone_options = [
        "Enterprise & Rechtssicher: Analytisch, präzise, VOB/B & BGB-konform",
        "Technisch-Sachlich: Ingenieursfokus, datengetrieben",
        "Verhandlungsstark & Bestimmt: Claim-Management & Risikominimierung"
    ]
    default_core_values = [
        "VOB/B & BGB Rechtssicherheit bei Verträgen",
        "Strenge Einhaltung von ISO-Normen & CE-Vorgaben",
        "Aktives Claim-Management & Fristenkontrolle"
    ]
    default_hourly = 115.00
    default_travel = 150.00
    default_positions = "Ingenieur-Stunde (Konstruktion): 115.00 € / Std.\nSPS-Programmierung & Validierung: 125.00 € / Std.\nProjektleitung & Inbetriebnahme: 105.00 € / Std."
    mode_instructions = "Fokussiere auf juristische Risikoprüfung, Compliance-Normen (ISO/CE), Lastenhefte, Fristen und Claim-Management."
    
    workflow_snippets = {
        "Manuell eingeben (Freitext)": "",
        "🔍 Lastenheft-Prüfung & Risiko-Analyse (Pönale/Haftung)": "Analysiere das hochgeladene Lastenheft / den Vertragsentwurf auf versteckte Haftungsrisiken, unzulässige Pönale-Regelungen (Vertragsstrafen) und einseitige Risikoverlagerungen. Erstelle einen strukturierten Risikoreport.",
        "🚧 Offizielles Claim-Management / Behinderungsanzeige": "Formuliere eine offizielle Behinderungsanzeige und einen Claim wegen bauseitiger Verzögerungen und Schnittstellenproblemen. Beziehe dich auf die vertraglichen Fristen.",
        "⚖️ Rechtssichere Erwiderung auf AAB / Sonderklauseln": "Prüfe die abweichenden Allgemeinen Geschäftsbedingungen (AGB/AAB) des Auftraggebers und verfasse eine rechtssichere Streichungs- bzw. Änderungsliste im Sinne unseres Unternehmens.",
        "📊 Technischer Audit-Report & Meilenstein-Freigabe": "Erstelle einen formalen Audit- und Freigabebericht für den anstehenden Projektabschnitt gemäß ISO 9001 und unseren Qualitätsstandards."
    }
    demo_task_text = """Projekt X-99: SPS-Automation und Roboterzellen-Anbindung
1. Frist: Vollständige betriebsbereite Montage und CE-Validierung innerhalb von 4 Wochen ab Vertragsschluss.
2. Pönale & Haftung: 0,5 % der Gesamtauftragssumme pro Kalendertag Verzug, maximal 25 %. Uneingeschränkte, verschuldensunabhängige Haftung für Betriebsunterbrechungen und Ausfallzeiten.
3. Schnittstellen: Gewährleistung erstreckt sich auch auf bauseits gestellte Fundamente und Vorleistungen Dritter.
4. Äquivalenz: Bis zu 15 % nachträgliche Leistungsänderungen (Change Requests) sind ohne Mehrkosten im Festpreis enthalten."""
    demo_rag_text = "Interne Regel: Jede Pönale-Klausel über 0,2% pro Tag muss vor Angebotsabgabe von der Rechtsabteilung freigegeben werden. Keine ungedeckten Schnittstellenrisiken bei Fremdfundamenten."

# --- SESSION STATE INITIALISIERUNG: FIRMA SETZEN, ABER AUFGABE & RAG STANDARDMÄSSIG LEER ---
if "company_input" not in st.session_state or mode_changed:
    st.session_state["company_input"] = default_company

if "rag_input" not in st.session_state:
    st.session_state["rag_input"] = ""

if "task_input_area" not in st.session_state:
    st.session_state["task_input_area"] = ""

# Wenn der Modus gewechselt wird, leeren wir die Textfelder absichtlich, damit keine Altlasten drin bleiben
if mode_changed:
    st.session_state["rag_input"] = ""
    st.session_state["task_input_area"] = ""

# --- HAUPTBEREICH: STRUKTURIERUNG ÜBER TABS ---
tab_workflow, tab_profile, tab_stammdaten = st.tabs([
    "⚡ 1. Schnellstart & Workflow", 
    "🏢 2. Firmen-DNA & Mini-RAG", 
    "💼 3. Stammdaten & Produkte"
])

with tab_workflow:
    st.subheader("Aufgabenstellung & Ausführung")
    
    col_demo, col_reset = st.columns([3, 1])
    with col_demo:
        demo_btn_label = "🚀 Industrie-Lastenheft (Demo) laden" if not is_handwerk else "🚀 Beispiel-Anfrage für Handwerk laden"
        if st.button(demo_btn_label, use_container_width=True):
            st.session_state["rag_input"] = demo_rag_text
            st.session_state["task_input_area"] = demo_task_text
            st.rerun()
    with col_reset:
        if st.button("🗑️ Eingabe leeren", use_container_width=True):
            st.session_state["rag_input"] = ""
            st.session_state["task_input_area"] = ""
            st.rerun()

    selected_workflow = st.selectbox(
        "⚡ Schnellstart-Snippets (Optional wählen):",
        list(workflow_snippets.keys()),
        key="workflow_select"
    )

    if selected_workflow != "Manuell eingeben (Freitext)" and workflow_snippets[selected_workflow]:
        if st.session_state["task_input_area"] != workflow_snippets[selected_workflow]:
            st.session_state["task_input_area"] = workflow_snippets[selected_workflow]

    col1, col2 = st.columns([1, 1])

    with col1:
        task_description = st.text_area(
            "Konkreter Sachverhalt / Aufgabendetails:",
            height=200,
            placeholder="Beschreibe hier deinen konkreten Fall oder lade unten ein Dokument hoch...",
            key="task_input_area"
        )

    with col2:
        st.markdown("##### 📁 Dokumenten-Archiv (Multi-Upload)")
        uploaded_files = st.file_uploader(
            "PDFs, Word-Dateien (.docx) oder Textdateien hochladen:",
            type=["pdf", "txt", "docx"],
            accept_multiple_files=True,
            help="Du kannst PDFs, Word-Dokumente und Textdateien mischen."
        )
        if uploaded_files:
            file_names = ", ".join([f"`{f.name}`" for f in uploaded_files])
            total_size = sum([f.size for f in uploaded_files])
            st.info(f"📄 {len(uploaded_files)} Datei(en) geladen: {file_names} ({round(total_size / 1024, 1)} KB)")

    exec_button_label = "🚀 Industrie-Analyse & Risiko-Check starten" if not is_handwerk else "🚀 Handwerker-Angebot / Bericht generieren"
    
    if st.button(exec_button_label, type="primary", use_container_width=True):
        if not task_description and not uploaded_files:
            st.warning("Bitte gib eine Aufgabe ein oder lade mindestens ein Dokument hoch.")
        elif not api_key_input:
            st.warning("Bitte trage in der Sidebar deinen Google AI Studio API-Key ein.")
        else:
            company_name = st.session_state["company_input"]
            company_rag_context = st.session_state["rag_input"]
            
            with st.spinner(f"Kompiliere {app_mode}, Zielsprache ({target_language}), {len(uploaded_files) if uploaded_files else 0} Dokument(e) & Stammdaten..."):
                try:
                    client = genai.Client(api_key=api_key_input)

                    system_instruction = f"""
Du handelst als erfahrener kaufmännischer und technischer Experte im Auftrag von "{company_name}".
Dein Betriebs-Modus ist: {app_mode.upper()}.
Modus-Fokus: {mode_instructions}

Internes Firmen-Gedächtnis & Mini-RAG-Regeln:
{company_rag_context if company_rag_context else "Keine spezifischen Zusatzregeln hinterlegt – nutze professionellen Standard."}

Betriebliche Stammdaten & Kalkulationsgrundlagen:
- Stundenverrechnungssatz (Netto): {default_hourly} € / Std.
- Anfahrts-/Spesenpauschale: {default_travel} €
- Material-/Komponentenaufschlag: 20%
- Zahlungsbedingungen: 14 Tage netto, 2% Skonto bei Zahlung innerhalb von 7 Tagen

[OUTPUT-REGELN]
1. Die gesamte Antwort, Analyse und Ausarbeitung muss zwingend in folgender Sprache verfasst werden: {target_language}.
2. Passe Tiefe und Sprache exakt an den Modus und die Firmen-DNA an.
3. Formuliere direkt einsatzbereit (Executive-Ready / Versandfertig).
4. Strukturiere die Ausgabe übersichtlich mit sauberen Absätzen.
"""

                    user_payload = f"""
[SACHVERHALT & AUFGABE]
{task_description if task_description else "Analysiere die angehängten Dokumente im Sinne des Unternehmensprofils und des Firmen-Gedächtnisses."}
"""

                    contents_list = [user_payload]

                    if uploaded_files:
                        for uf in uploaded_files:
                            if uf.name.endswith(".docx"):
                                doc = docx.Document(uf)
                                doc_text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                                contents_list.append(f"\n[INHALT AUS WORD-DATEI: {uf.name}]\n{doc_text}\n")
                            else:
                                contents_list.append({
                                    "mime_type": uf.type,
                                    "data": uf.read()
                                })

                    response = client.models.generate_content(
                        model=target_model,
                        contents=contents_list,
                        config={
                            "system_instruction": system_instruction
                        }
                    )

                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    raw_text = response.text
                    content_hash = hashlib.sha256(raw_text.encode('utf-8')).hexdigest()[:12]

                    audit_footer = f"""
---
[REVISIONS- UND AUDIT-TRAIL PROTOKOLL]
- Zeitstempel: {timestamp}
- Unternehmen: {company_name}
- Betriebs-Modus: {app_mode}
- Zielsprache: {target_language}
- Verwendetes KI-Modell: {target_model}
- Audit-ID / Hash: #{content_hash}
- Status: Dokument generiert über Prompt-Architect // Industrial AI (Revisionssicher)
"""

                    final_output = raw_text + audit_footer

                    st.success("Erfolgreich ausgeführt & revisionssicher protokolliert!")
                    st.markdown("### 📄 Ergebnis mit Audit-Trail:")
                    st.markdown(final_output)

                    st.session_state["last_output"] = final_output

                    col_dl1, col_dl2 = st.columns(2)
                    with col_dl1:
                        st.download_button(
                            label="📥 Dokument als Textdatei herunterladen",
                            data=final_output,
                            file_name=f"Auswertung_{company_name.replace(' ', '_')}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain"
                        )
                    with col_dl2:
                        st.download_button(
                            label="📊 Audit-Protokoll als CSV exportieren",
                            data=f"Modus,Firma,Hash,Zeitstempel\n\"{app_mode}\",\"{company_name}\",#{content_hash},\"{timestamp}\"",
                            file_name=f"Audit_{company_name.replace(' ', '_')}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )

                except Exception as e:
                    st.error(f"Fehler bei der Übertragung: {e}")

with tab_profile:
    st.subheader("Unternehmens-DNA & Mini-RAG")
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        company_name = st.text_input(
            "Betriebs- / Firmenname", 
            value=st.session_state["company_input"], 
            key="company_input"
        )
        founding_year = st.text_input("Historie / Größe", value=default_history)
        selected_industry = st.selectbox("Branche / Fachbereich", industry_options)
        brand_tone = st.selectbox("Tonalität & Corporate Language", tone_options)

    with col_p2:
        company_rag_context = st.text_area(
            "🧠 Firmen-Gedächtnis & spezifische Betriebsnormen (Mini-RAG):",
            height=180,
            value=st.session_state["rag_input"],
            placeholder="Trage hier interne Regeln, Freigabegrenzen oder Klauseln ein...",
            key="rag_input"
        )

    st.markdown("### 💎 Kernwerte & Standards (Baukasten)")
    available_value_options = [
        "Pünktliche Lieferung & saubere Ausführung",
        "Ehrliche Handschlagqualität & keine versteckten Kosten",
        "VOB/B & BGB Rechtssicherheit bei Verträgen",
        "Strenge Einhaltung von ISO-Normen & CE-Vorgaben",
        "Keine ungedeckten Schnittstellenrisiken bei Fremdgewerken",
        "Saubere Baustelle / besenreine Übergabe",
        "Aktives Claim-Management & Fristenkontrolle"
    ]
    st.multiselect(
        "Wähle deine Betriebswerte:",
        available_value_options,
        default=default_core_values
    )

with tab_stammdaten:
    st.subheader("Stammdaten & Kalkulationsgrundlagen")
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        hourly_rate = st.number_input("Stundenverrechnungssatz (Netto in €)", value=default_hourly, step=5.0)
        travel_fee = st.number_input("Anfahrts- / Spesenpauschale (Netto in €)", value=default_travel, step=5.0)
    with col_s2:
        material_markup = st.slider("Material- / Komponenten-Aufschlag (%)", min_value=0, max_value=100, value=20)
        payment_terms = st.text_input("Zahlungsbedingungen", value="14 Tage netto, 2% Skonto bei Zahlung innerhalb von 7 Tagen")

    st.markdown("### 🛠️ Positionen & Produkte")
    custom_positions_input = st.text_area(
        "Deine Artikel & Leistungen (eine Position pro Zeile `Name: Preis`):",
        height=130,
        value=default_positions
    )

if "last_output" in st.session_state and st.session_state["last_output"]:
    st.divider()
    with st.expander("📋 Zuletzt generiertes Ergebnis anzeigen"):
        st.code(st.session_state["last_output"], language="markdown")
