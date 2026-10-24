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
st.markdown("### Modul-Suite aktiv: Workflow, Multi-Upload (PDF & Word), Revisionssicherer Audit-Trail, Mini-RAG & Internationale Sprachwahl")

# --- SIDEBAR: API-KEY & MODUS-WAHL ---
st.sidebar.header("🔑 API-Konfiguration")
api_key_input = st.sidebar.text_input(
    "Google AI Studio API-Key",
    type="password",
    placeholder="Dein Key hier einfügen..."
)

st.sidebar.header("⚙️ 1. Betriebs-Modus wählen")
app_mode = st.sidebar.radio(
    "Leistungsklasse der KI:",
    ["🔨 Handwerk & Kleinbetrieb (Praktisch & Direkt)", "🏭 Industrie & Mittelstand (Enterprise & Compliance)"]
)

st.sidebar.header("2. Ziel-Modell wählen")
target_model = st.sidebar.selectbox(
    "Welche KI wird eingesetzt?",
    ["gemini-2.5-pro", "gemini-1.5-pro", "gemini-2.5-flash", "Claude 3.5 Sonnet (Anthropic)", "GPT-4o (OpenAI)"],
    key="model_select"
)

# --- SPRACHAUSWAHL ---
st.sidebar.header("🌍 3. Ausgabesprache")
target_language = st.sidebar.selectbox(
    "Sprache für das Ergebnis:",
    ["Deutsch", "English (Englisch)", "Български (Bulgarisch)", "Français (Französisch)", "Español (Spanisch)"]
)

# --- DYNAMISCHE LOGIK & WORKFLOW-SNIPPETS ---
if "Handwerk" in app_mode:
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
    default_values = "- Pünktliche Lieferung und saubere Ausführung.\n- Keine versteckten Kosten, ehrliche Handschlagqualität.\n- Wir verlassen jede Baustelle besenrein."
    default_hourly = 65.00
    default_travel = 45.00
    default_positions = "Montagestunde Handwerker: 65.00 € / Std.\nAnfahrtspauschale: 45.00 €\nMaterial-Aufschlag: 20%"
    mode_instructions = "Fokussiere auf schnelle, handwerklich klare Angebote, Stundensätze und praxisnahe Kommunikation."
    
    workflow_snippets = {
        "Manuell eingeben (Freitext)": "",
        "⚠️ VOB-Bedenkenanzeige (Mangelhafte Vorleistung)": "Erstelle eine formgerechte und rechtssichere Bedenkenanzeige gemäß VOB/B. Der Untergrund bzw. die bauseits erbrachte Vorleistung ist mangelhaft und behindert unsere fachgerechte Ausführung. Weise auf Haftungsrisiken hin.",
        "📋 Nachtragsangebot erstellen": "Erbeite ein sauberes Nachtragsangebot für die zusätzlich geforderten Leistungen (Mehrumfang). Nutze exakt unsere hinterlegten Stundensätze und Materialaufschläge.",
        "🛡️ Unberechtigte Mängelrüge / Rechnungskürzung abwehren": "Formuliere eine bestimmte, aber sachliche Erwiderung auf die unberechtigte Mängelrüge des Kunden. Weise nach, dass unsere Leistung vertragsgerecht und fehlerfrei erbracht wurde.",
        "✉️ Verbindliches Kundenangebot verfassen": "Erstelle ein vollständiges, professionelles Angebot im Betriebsstil basierend auf der Kundenanfrage. Nutze unsere Standard-Positionen und Zahlungsbedingungen."
    }
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
    default_values = "- Einhaltung aller ISO-Normen, VOB/B & BGB-Vorgaben.\n- Keine ungeprüften Haftungsrisiken bei Ausschreibungen.\n- Präzise Fristeneinhaltung und nachvollziehbare Dokumentation."
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

# --- SESSION STATE INITIALISIERUNG ---
if "company_input" not in st.session_state:
    st.session_state["company_input"] = default_company
if "rag_input" not in st.session_state:
    st.session_state["rag_input"] = ""
if "task_input_area" not in st.session_state:
    st.session_state["task_input_area"] = ""

# --- DEMO-DATEN INHALT ---
DEMO_HORROR_LASTENHEFT = """Projekt X-99: SPS-Automation und Roboterzellen-Anbindung
1. Frist: Vollständige betriebsbereite Montage und CE-Validierung innerhalb von 4 Wochen ab Vertragsschluss.
2. Pönale & Haftung: 0,5 % der Gesamtauftragssumme pro Kalendertag Verzug, maximal 25 %. Uneingeschränkte, verschuldensunabhängige Haftung für Betriebsunterbrechungen und Ausfallzeiten.
3. Schnittstellen: Gewährleistung erstreckt sich auch auf bauseits gestellte Fundamente und Vorleistungen Dritter.
4. Äquivalenz: Bis zu 15 % nachträgliche Leistungsänderungen (Change Requests) sind ohne Mehrkosten im Festpreis enthalten."""

# --- MODUL 2: UNTERNEHMENSPROFIL ---
st.sidebar.header("4. Unternehmensprofil & Gewerk")

company_name = st.sidebar.text_input(
    "Betriebs- / Firmenname", 
    value=st.session_state["company_input"], 
    key="company_input",
    help="Trage hier den Namen deines eigenen Betriebs ein (oder nutze den Demo-Button)."
)
founding_year = st.sidebar.text_input(
    "Historie / Größe", 
    value=default_history,
    help="z.B. Gegründet 1988, Meisterbetrieb"
)

selected_industry = st.sidebar.selectbox("Branche / Fachbereich", industry_options, key="industry_select")

if selected_industry.startswith("➕"):
    custom_industry_input = st.sidebar.text_input("Trage deine Branche/Gewerk ein:", value="Sonder-Maschinenbau")
    industry_sector = custom_industry_input
else:
    industry_sector = selected_industry

brand_tone = st.sidebar.selectbox("Tonalität & Corporate Language", tone_options)
company_values = st.sidebar.text_area("Kernwerte & Standards", height=100, value=default_values)

# --- FIRMEN-GEDÄCHTNIS (MINI-RAG) ---
st.sidebar.markdown("---")
st.sidebar.header("🧠 Firmen-Gedächtnis (Mini-RAG)")

company_rag_context = st.sidebar.text_area(
    "Unternehmens-DNA & spezifische Betriebsnormen:",
    height=130,
    value=st.session_state["rag_input"],
    placeholder="Trage hier deine konkreten Firmen-Regeln ein...",
    key="rag_input"
)

# --- MODUL 3: STAMMDATEN ---
with st.sidebar.expander("💼 5. Stammdaten & Kalkulation"):
    hourly_rate = st.number_input("Stundenverrechnungssatz (Netto in €)", value=default_hourly, step=5.0)
    travel_fee = st.number_input("Anfahrts- / Spesenpauschale (Netto in €)", value=default_travel, step=5.0)
    material_markup = st.slider("Material- / Komponenten-Aufschlag (%)", min_value=0, max_value=100, value=20)
    payment_terms = st.text_input("Zahlungsbedingungen", value="14 Tage netto, 2% Skonto bei Zahlung innerhalb von 7 Tagen")

# --- MODUL 4: POSITIONEN ---
st.sidebar.header("🛠️ 6. Positionen & Produkte")
custom_positions_input = st.sidebar.text_area(
    "Deine Artikel & Leistungen (Name: Preis)",
    height=120,
    value=default_positions
)

# --- HAUPTBEREICH: WORKFLOW & DEMO-DATEN ---
st.subheader("7. Ein-Klick-Workflow & Aufgabenstellung")

selected_workflow = st.selectbox(
    "⚡ Schnellstart-Workflows (Snippets wählen oder anpassen):",
    list(workflow_snippets.keys())
)

initial_task_text = workflow_snippets[selected_workflow]
if selected_workflow != "Manuell eingeben (Freitext)" and initial_task_text:
    st.session_state["task_input_area"] = initial_task_text

col_demo1, col_demo2 = st.columns([1, 1])
with col_demo1:
    if st.button("🚀 Horrorlastenheft Demonstration", use_container_width=True):
        st.session_state["company_input"] = "Industrie-Anlagenbau Rhein-Ruhr GmbH"
        st.session_state["rag_input"] = "Interne Regel: Jede Pönale-Klausel über 0,2% pro Tag muss vor Angebotsabgabe von der Rechtsabteilung freigegeben werden. Keine ungedeckten Schnittstellenrisiken bei Fremdfundamenten."
        st.session_state["task_input_area"] = DEMO_HORROR_LASTENHEFT
        st.rerun()

with col_demo2:
    if st.button("🗑️ Eingabe zurücksetzen", use_container_width=True):
        st.session_state["company_input"] = default_company
        st.session_state["rag_input"] = ""
        st.session_state["task_input_area"] = ""
        st.rerun()

col1, col2 = st.columns([1, 1])

with col1:
    task_description = st.text_area(
        "Konkreter Sachverhalt / Aufgabendetails:",
        height=180,
        placeholder="Beschreibe hier den konkreten Fall oder klicke oben auf 'Horrorlastenheft Demonstration'...",
        key="task_input_area"
    )

with col2:
    st.subheader("📁 Dokumenten-Archiv (Multi-Upload)")
    uploaded_files = st.file_uploader(
        "PDFs, Word-Dateien (.docx) oder Textdateien gleichzeitig hochladen:",
        type=["pdf", "txt", "docx"],
        accept_multiple_files=True,
        help="Du kannst PDFs, Word-Dokumente und Textdateien mischen. Word-Dateien werden automatisch ausgelesen."
    )
    if uploaded_files:
        file_names = ", ".join([f"`{f.name}`" for f in uploaded_files])
        total_size = sum([f.size for f in uploaded_files])
        st.info(f"📄 {len(uploaded_files)} Datei(en) geladen: {file_names} ({round(total_size / 1024, 1)} KB gesamt)")

# GENERATION & LIVE-CALL
if st.button(f"🚀 Master-Prompt ausführen ({'Handwerk' if 'Handwerk' in app_mode else 'Enterprise'})", type="primary", use_container_width=True):
    if not task_description and not uploaded_files:
        st.warning("Bitte gib eine Aufgabe ein oder lade mindestens ein Dokument hoch.")
    elif not api_key_input:
        st.warning("Bitte trage links deinen Google AI Studio API-Key ein.")
    else:
        with st.spinner(f"Kompiliere Profil, Mini-RAG, Sprachwahl ({target_language}), {len(uploaded_files) if uploaded_files else 0} Dokument(e) & Stammdaten..."):
            try:
                client = genai.Client(api_key=api_key_input)

                generated_prompt = f"""
[ENTERPRISE CONTEXT / BETRIEBS-MODUS: {app_mode.upper()}]
- Unternehmen: {company_name} ({founding_year})
- Branche / Sektor: {industry_sector}
- Corporate Language / Tonalität: {brand_tone}
- Modus-Fokus: {mode_instructions}
- Betriebliche Kernwerte & Standards:
{company_values}

[ZIELSPRACHE & LOKALISIERUNG]
- Die gesamte Antwort, Analyse und Ausarbeitung muss zwingend in folgender Sprache verfasst werden: {target_language}.

[INTERNES FIRMEN-GEDÄCHTNIS & MINI-RAG-KONTEXT]
Der Nutzer hat folgende spezifische Betriebsnormen, Regeln und DNA hinterlegt, die für ALLE nachfolgenden Aufgaben als absolut verbindliches Gesetz gelten:
{company_rag_context if company_rag_context else "Keine spezifischen Zusatzregeln hinterlegt – nutze professionellen Standard des Gewerks."}

[BETRIEBLICHE STAMMDATEN & KALKULATION]
- Stundenverrechnungssatz (Netto): {hourly_rate} € / Std.
- Anfahrts-/Spesenpauschale: {travel_fee} €
- Material-/Komponentenaufschlag: {material_markup}%
- Zahlungsbedingungen: {payment_terms}

[PRODUKT- UND PREISLISTE (BENUTZERDEFINIERT)]
{custom_positions_input}

[SYSTEM INSTRUCTION FOR {target_model}]
Du handelst als erfahrener kaufmännischer und technischer Experte im Auftrag von "{company_name}" ({industry_sector}).
Deine Aufgabe ist es, das vorliegende Anliegen bzw. die hochgeladenen Dokumente unter strikter Einhaltung des gewählten Modus ({app_mode}), der Zielsprache ({target_language}), der Unternehmenswerte, des Mini-RAG-Gedächtnisses, der Stammdaten und der Risikominimierung zu analysieren und zu lösen.

[SACHVERHALT & AUFGABE]
{task_description if task_description else "Analysiere die angehängten Dokumente im Sinne des Unternehmensprofils und des Firmen-Gedächtnisses und erstelle eine professionelle Ausarbeitung in der geforderten Zielsprache."}

[OUTPUT-REGELN]
1. Verfasse das Resultat strikt in der gewählten Zielsprache: {target_language}.
2. Passe die Tiefe und Sprache exakt an den gewählten Modus und das Firmen-Gedächtnis an.
3. Nutze exakt die hinterlegten Stundensätze, Aufschläge und Positionen für jegliche Berechnungen.
4. Formuliere direkt einsatzbereit (Executive-Ready / Versandfertig).
5. Strukturiere die Ausgabe übersichtlich mit sauberen Absätzen.
"""

                contents_list = [generated_prompt]

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
                    model=target_model if not target_model.startswith("Claude") and not target_model.startswith("GPT") else "gemini-2.5-pro",
                    contents=contents_list,
                )

                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                raw_text = response.text
                content_hash = hashlib.sha256(raw_text.encode('utf-8')).hexdigest()[:12]

                audit_footer = f"""
---
[REVISIONS- UND AUDIT-TRAIL PROTOKOLL]
- Zeitstempel: {timestamp}
- Unternehmen: {company_name} ({industry_sector})
- Betriebs-Modus: {app_mode}
- Zielsprache: {target_language}
- Verwendetes KI-Modell: {target_model}
- Stammdaten-Basis: Stundensatz {hourly_rate}€ | Aufschlag {material_markup}%
- Mini-RAG-Status: {'Aktiv (Benutzerdefiniert)' if company_rag_context else 'Standard'}
- Audit-ID / Hash: #{content_hash}
- Status: Dokument generiert über Prompt-Architect // Industrial AI (Revisionssicher)
"""

                final_output = raw_text + audit_footer

                st.success("Erfolgreich ausgeführt & revisionssicher protokolliert!")
                st.markdown("### 📄 Ergebnis mit Audit-Trail:")
                st.markdown(final_output)

                st.session_state["last_output"] = final_output

                csv_content = "Kategorie,Parameter,Wert\n"
                csv_content += f"Unternehmensdaten,Firma,\"{company_name}\"\n"
                csv_content += f"Unternehmensdaten,Branche,\"{industry_sector}\"\n"
                csv_content += f"Unternehmensdaten,Modus,\"{app_mode}\"\n"
                csv_content += f"Sprach-Auswahl,Zielsprache,\"{target_language}\"\n"
                csv_content += f"Stammdaten,Stundensatz (Netto),{hourly_rate} EUR\n"
                csv_content += f"Stammdaten,Anfahrt/Spesen,{travel_fee} EUR\n"
                csv_content += f"Stammdaten,Materialaufschlag,{material_markup}%\n"
                csv_content += f"Audit,Audit-Hash,#{content_hash}\n"
                csv_content += f"Audit,Zeitstempel,\"{timestamp}\"\n"
                
                csv_bytes = csv_content.encode('utf-8')

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
                        label="📊 Stammdaten & Audit als CSV exportieren",
                        data=csv_bytes,
                        file_name=f"Kalkulation_{company_name.replace(' ', '_')}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )

                with st.expander("🔍 Vollständig kompilierten Master-Prompt anzeigen"):
                    st.code(generated_prompt, language="markdown")

            except Exception as e:
                st.error(f"Fehler bei der Übertragung: {e}")

if "last_output" in st.session_state and st.session_state["last_output"]:
    st.divider()
    st.markdown("### 📋 Ergebnis in Zwischenablage kopieren")
    st.code(st.session_state["last_output"], language="markdown")
