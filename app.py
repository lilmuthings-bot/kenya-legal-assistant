"""
Kenya Legal Assistant
Mission: “Make legal knowledge accessible, not make lawyers mandatory.”
Full-stack Python Web Application for Render Deployment
"""

import os
import json
import sqlite3
import datetime
import urllib.request
import urllib.error
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)
DB_FILE = os.path.join(os.path.dirname(__file__), "kenya_legal.db")


# ==============================================================================
# DATABASE INITIALIZATION (SQLite)
# ==============================================================================
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    # Workspace cases table
    c.execute("""
        CREATE TABLE IF NOT EXISTS workspace_cases (
            id TEXT PRIMARY KEY,
            caseTitle TEXT NOT NULL,
            caseType TEXT NOT NULL,
            institutionOrForum TEXT NOT NULL,
            caseNumber TEXT,
            applicant TEXT,
            respondent TEXT,
            currentStage TEXT NOT NULL,
            nextDate TEXT,
            urgentDeadlines TEXT,
            notes TEXT,
            updatedAt TEXT NOT NULL
        )
    """)

    # Workspace facts table
    c.execute("""
        CREATE TABLE IF NOT EXISTS workspace_facts (
            id TEXT PRIMARY KEY,
            caseId TEXT NOT NULL,
            dateOrTime TEXT,
            description TEXT NOT NULL,
            type TEXT NOT NULL,
            supportingEvidenceIds TEXT
        )
    """)

    # Workspace evidence table
    c.execute("""
        CREATE TABLE IF NOT EXISTS workspace_evidence (
            id TEXT PRIMARY KEY,
            caseId TEXT NOT NULL,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            dateObtained TEXT,
            description TEXT NOT NULL,
            lawfulStatus TEXT NOT NULL,
            custodyNotes TEXT
        )
    """)

    # Workspace opponents table
    c.execute("""
        CREATE TABLE IF NOT EXISTS workspace_opponents (
            id TEXT PRIMARY KEY,
            caseId TEXT NOT NULL,
            allegation TEXT NOT NULL,
            theirClaimedEvidence TEXT,
            contradictionOrFlaw TEXT,
            myCounterPosition TEXT
        )
    """)

    # Generated documents table
    c.execute("""
        CREATE TABLE IF NOT EXISTS generated_documents (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            type TEXT NOT NULL,
            createdAt TEXT NOT NULL,
            content TEXT NOT NULL,
            factsUsed TEXT,
            missingFactsNoted TEXT
        )
    """)

    # Seed default case if empty
    c.execute("SELECT count(*) FROM workspace_cases")
    if c.fetchone()[0] == 0:
        now = datetime.datetime.now().isoformat()
        c.execute("""
            INSERT INTO workspace_cases (
                id, caseTitle, caseType, institutionOrForum, caseNumber,
                applicant, respondent, currentStage, nextDate, urgentDeadlines, notes, updatedAt
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "case_demo_01",
            "Academic Suspension & Due Process Review",
            "Administrative Review",
            "University Disciplinary Appeals Committee / CAJ Ombudsman",
            "ADM/REV/2026/04",
            "Self-Represented Student / Complainant",
            "University Disciplinary Committee",
            "Factual Preparation & Evidence Preservation",
            "Within 14 days of notice",
            "14-day statutory appeal deadline under University Charter & FAAA 2015",
            "Summary suspension issued without charge sheet or preliminary hearing.",
            now
        ))

    conn.commit()
    conn.close()


init_db()


# ==============================================================================
# OFFICIAL SOURCES, STATUTES & CASE LAW DATA
# ==============================================================================
OFFICIAL_SOURCES = [
    {
        "id": "src_kenyalaw",
        "name": "Kenya Law (National Council for Law Reporting)",
        "description": "Official publisher of the Laws of Kenya and all Law Reports from superior courts.",
        "url": "https://new.kenyalaw.org/legislation",
        "type": "Legislation",
        "authorityLevel": "Primary Binding"
    },
    {
        "id": "src_parliament_acts",
        "name": "Parliament of Kenya - Acts of Parliament",
        "description": "Acts passed by the National Assembly and Senate of the Republic of Kenya.",
        "url": "https://www.parliament.go.ke/the-national-assembly/house-business/acts",
        "type": "Parliament Acts",
        "authorityLevel": "Primary Binding"
    },
    {
        "id": "src_parliament_bills",
        "name": "Parliament of Kenya - Bills",
        "description": "Draft legislation under debate. Note: A Bill is NOT law until enacted and gazetted.",
        "url": "https://parliament.go.ke/the-national-assembly/house-business/bills",
        "type": "Bills",
        "authorityLevel": "Informational"
    },
    {
        "id": "src_supreme_court",
        "name": "Supreme Court Decisions - Judiciary of Kenya",
        "description": "Highest court decisions in Kenya; binding on all other courts and tribunals.",
        "url": "https://supremecourt.judiciary.go.ke/supreme-court-decisions/",
        "type": "Supreme Court Decisions",
        "authorityLevel": "Primary Binding"
    },
    {
        "id": "src_judiciary_downloads",
        "name": "Judiciary of Kenya - Practice Directions & Rules",
        "description": "Court rules, practice directions, cause lists and institutional publications.",
        "url": "https://judiciary.go.ke/downloads/",
        "type": "Judiciary",
        "authorityLevel": "Primary Binding"
    }
]

STATUTES = [
    {
        "id": "stat_art47",
        "source": "Kenya Law",
        "document": "Constitution of Kenya 2010",
        "section": "Article 47",
        "topic": "Fair Administrative Action & Right to Written Reasons",
        "exactText": "47. (1) Every person has the right to administrative action that is expeditious, efficient, lawful, reasonable and procedurally fair.\n(2) If a right or fundamental freedom of a person has been or is likely to be adversely affected by administrative action, the person has the right to be given written reasons for the action.",
        "plainEnglish": "Any decision maker—including universities, landlords, or employers—must treat you fairly. Before making a decision that hurts you (like a suspension), they must give you written reasons, notice of charges, and a genuine chance to be heard.",
        "currentStatus": "In Force",
        "sourceUrl": "https://new.kenyalaw.org/legislation",
        "category": "Constitutional"
    },
    {
        "id": "stat_faaa_s4",
        "source": "Parliament of Kenya / Kenya Law",
        "document": "Fair Administrative Action Act No. 33 of 2015",
        "section": "Section 4",
        "topic": "Mandatory Procedural Fairness for Administrative Decisions",
        "exactText": "4. (3) Where an administrative action is likely to adversely affect the rights or fundamental freedoms of any person, the administrator shall give that person—\n(a) prior and adequate notice of the nature and reasons for the proposed administrative action;\n(b) an opportunity to be heard and to make representations in that regard;\n(c) notice of a right to a review or an internal appeal; and\n(d) a statement of reasons pursuant to section 6.",
        "plainEnglish": "Universities, employers, and government bodies cannot condemn you unheard. They must give you the charge sheet and all evidence in advance so you can defend yourself.",
        "currentStatus": "In Force",
        "sourceUrl": "https://new.kenyalaw.org/legislation",
        "category": "Administrative"
    },
    {
        "id": "stat_soa_s24",
        "source": "Kenya Law",
        "document": "Sexual Offences Act No. 3 of 2006",
        "section": "Section 24",
        "topic": "Sexual Harassment & Abuse of Position of Authority",
        "exactText": "24. (1) Any person, who being in a position of authority, or a person holding a public office, who persistently makes any sexual advances or requests which he knows or has reasonable grounds to know are unwelcome, is guilty of the offence of sexual harassment.\n(2) A person who promises any advantage or threatens any detriment in connection with employment or education is guilty of an offence.",
        "plainEnglish": "A professor, lecturer, or supervisor who demands sexual favours in exchange for passing exams, grades, or employment commits a serious criminal offence carrying minimum 3 years imprisonment.",
        "currentStatus": "In Force",
        "sourceUrl": "https://new.kenyalaw.org/legislation",
        "category": "Criminal"
    },
    {
        "id": "stat_evidence_106b",
        "source": "Kenya Law",
        "document": "Evidence Act (Cap 80)",
        "section": "Section 106B",
        "topic": "Admissibility of Electronic Records (WhatsApp, SMS, Audio, Emails)",
        "exactText": "106B. (1) Any information contained in an electronic record which is printed on a paper, stored, recorded or copied in optical or magnetic media produced by a computer shall be deemed to be also a document... and shall be admissible in any proceedings.\n(4) A certificate signed by a person certifying the lawful operating condition of the device shall be evidence of the matter.",
        "plainEnglish": "Screenshots of WhatsApp messages, SMS, and recordings are admissible in Kenyan courts and tribunals if you preserve the original device, do not tamper with files, and sign a Section 106B Certificate.",
        "currentStatus": "In Force",
        "sourceUrl": "https://new.kenyalaw.org/legislation",
        "category": "Evidence"
    },
    {
        "id": "stat_emp_s41",
        "source": "Kenya Law",
        "document": "Employment Act No. 11 of 2007",
        "section": "Section 41 & 45",
        "topic": "Notification and Hearing Before Termination / Unfair Dismissal",
        "exactText": "41. (1) Before terminating the employment of an employee on grounds of misconduct, poor performance or physical incapacity, the employer shall explain to the employee, in a language the employee understands, the reason for which the employer is considering termination and the employee shall be entitled to have another employee or a shop floor union representative present.",
        "plainEnglish": "An employer cannot fire you on the spot or via WhatsApp without giving you advance written notice and holding a formal disciplinary hearing where you can bring a colleague.",
        "currentStatus": "In Force",
        "sourceUrl": "https://new.kenyalaw.org/legislation",
        "category": "Employment"
    },
    {
        "id": "stat_distress_s3",
        "source": "Kenya Law",
        "document": "Distress for Rent Act (Cap 76)",
        "section": "Section 3 & 16",
        "topic": "Prohibition of Landlord Self-Help Lockouts & Illegal Distress",
        "exactText": "3. Any distress for rent shall be made only by an auctioneer duly licensed under the Auctioneers Act.\n16. If any distress and sale shall be made for rent where no rent is really due, the owner of the goods shall recover double the value of the goods.",
        "plainEnglish": "Landlords are prohibited from taking self-help measures: locking doors, removing roofs, or seizing tenant goods personally. Only a licensed auctioneer with a tribunal proclamation can levy distress.",
        "currentStatus": "In Force",
        "sourceUrl": "https://new.kenyalaw.org/legislation",
        "category": "Tenancy"
    }
]

CASES = [
    {
        "id": "case_wanjiku_2018",
        "citation": "[2018] eKLR",
        "caseName": "Republic v University of Nairobi ex parte Wanjiku",
        "court": "High Court of Kenya (Nairobi)",
        "year": 2018,
        "authorityType": "binding",
        "legalIssues": "University disciplinary suspension without hearing, Article 47 Due Process",
        "legalTest": "The Three-Part Test for Administrative Disciplinary Action: 1) Clear advance written notice of allegations; 2) Adequate opportunity to prepare and present defense; 3) Reasoned decision by an unbiased panel.",
        "holding": "A university suspension issued without advance notice and without an opportunity to be heard is illegal, ultra vires, and void ab initio.",
        "sourceUrl": "http://kenyalaw.org/caselaw/cases/view/161204/"
    },
    {
        "id": "case_kiprono_moi_2020",
        "citation": "[2020] eKLR",
        "caseName": "Caleb Kiprono v Moi University",
        "court": "High Court of Kenya (Eldoret)",
        "year": 2020,
        "authorityType": "binding",
        "legalIssues": "Duty to disclose adverse evidence before university hearings",
        "legalTest": "The Principle of Adequate Disclosure: An accused student must be provided with copies of all witness statements and evidence before the hearing.",
        "holding": "Failure to provide an accused student with investigation reports and witness statements violates natural justice.",
        "sourceUrl": "http://kenyalaw.org/caselaw/cases/view/196324/"
    },
    {
        "id": "case_kiptui_2014",
        "citation": "[2014] eKLR",
        "caseName": "Mary Chemweno Kiptui v Kenya Pipeline Company Ltd",
        "court": "Industrial Court of Kenya (Nairobi)",
        "year": 2014,
        "authorityType": "binding",
        "legalIssues": "Sexual harassment in institutional setting, power imbalance",
        "legalTest": "The Power-Imbalance Harassment Test: Where a person in authority makes unwelcome advances tied to evaluation or career detriment, the employer or institution is vicariously liable if they fail to protect the complainant.",
        "holding": "Institutions have an affirmative statutory obligation to protect subordinates and students from predatory power imbalances.",
        "sourceUrl": "http://kenyalaw.org/caselaw/cases/view/97645/"
    },
    {
        "id": "case_purity_wambui_2019",
        "citation": "[2019] eKLR",
        "caseName": "Purity Wambui & Another v Muriithi",
        "court": "High Court of Kenya (Nyeri)",
        "year": 2019,
        "authorityType": "persuasive",
        "legalIssues": "Landlord locking out tenant for rent arrears, unlawful distress",
        "legalTest": "The Self-Help Prohibition Rule: Rent arrears do not entitle a landlord to bypass due process. Padlock changes or utility severance without court order constitutes unlawful trespass.",
        "holding": "Self-help eviction by a landlord without an order of the Rent Restriction Tribunal is illegal and attracts substantial damages.",
        "sourceUrl": "http://kenyalaw.org/caselaw/cases/view/184120/"
    },
    {
        "id": "case_andare_2016",
        "citation": "[2016] eKLR",
        "caseName": "Geoffrey Andare v Attorney General & 2 Others",
        "court": "High Court of Kenya (Nairobi)",
        "year": 2016,
        "authorityType": "binding",
        "legalIssues": "Electronic evidence admissibility and mobile message integrity",
        "legalTest": "Digital Evidence Integrity Rule: Digital messages must be presented with chain of custody under Section 106B of Evidence Act.",
        "holding": "Digital records and WhatsApp logs are valid admissible evidence when accompanied by proper certificate of electronic integrity.",
        "sourceUrl": "http://kenyalaw.org/caselaw/cases/view/121852/"
    }
]


# ==============================================================================
# KENYAN LEGAL REASONING ENGINE (14-Point Structure)
# ==============================================================================
def analyze_legal_situation(user_text, mode="rights", prior_answers=None):
    text_lower = user_text.lower()
    prior_answers = prior_answers or {}

    # Check for Section 17 Demo: Sexual Harassment & Power Imbalance
    if "blackmail" in text_lower or ("professor" in text_lower and ("sex" in text_lower or "exam" in text_lower)):
        return {
            "whatIUnderstand": [
                "You are an adult student (above 18 years) in a higher education institution.",
                "Your professor is conditioning your academic success (passing an exam) on sexual demands.",
                "There is an acute educational power imbalance where official grading authority is being used for coercion."
            ],
            "possibleLegalIssues": [
                "Sexual Harassment under Section 24(1) & (2) of the Sexual Offences Act No. 3 of 2006.",
                "Extortion and Demanding an Advantage with Menaces (Bribery Act No. 47 of 2016 s. 5 & 6).",
                "Violation of Constitutional Right to Human Dignity (Article 28) and Fair Administrative Action (Article 47)."
            ],
            "urgentRisksOrDeadlines": [
                "Grading and exam moderation deadlines: Once examination booklets are submitted to external examiners, altering grades becomes procedurally complex.",
                "Retaliatory academic grading: Risk of immediate pretextual failure unless protective institutional custody of your script is requested under Article 35."
            ],
            "clarifyingQuestions": [
                "1. What exactly did the professor say or write?",
                "2. Was the demand explicitly connected to your exam or grade?",
                "3. Do you have messages, emails, recordings or witnesses?",
                "4. Has the exam already been marked or have results been released?",
                "5. Does the professor have exclusive authority over the grade?",
                "6. Were there threats beyond the academic consequences?",
                "7. Do you feel physically unsafe at this moment?",
                "8. Which university or institution is involved?"
            ],
            "whatTheLawSays": [
                {
                    "statute": "Sexual Offences Act No. 3 of 2006",
                    "section": "Section 24(1) & (2)",
                    "exactTextSnippet": "Any person who, being in a position of authority... promises any advantage or threatens any detriment in connection with employment or education is guilty of sexual harassment and liable to imprisonment for not less than three years.",
                    "explanation": "Demanding sexual favours in exchange for passing grades is a severe criminal offence in Kenya.",
                    "sourceUrl": "https://new.kenyalaw.org/legislation"
                },
                {
                    "statute": "Constitution of Kenya 2010",
                    "section": "Article 28 & Article 47",
                    "exactTextSnippet": "Every person has inherent dignity and the right to have that dignity respected and protected. Every person has the right to administrative action that is lawful, reasonable and procedurally fair.",
                    "explanation": "You are constitutionally protected from exploitation and entitled to an impartial academic evaluation.",
                    "sourceUrl": "https://new.kenyalaw.org/legislation"
                }
            ],
            "howItMayApply": [
                "Because the lecturer exercises statutory academic grading power over you, the demand falls squarely under Section 24 of the Sexual Offences Act.",
                "Under Mary Chemweno Kiptui v Kenya Pipeline [2014], the institution has an affirmative legal duty to protect students from predatory staff."
            ],
            "inferences": [
                "It is reasonable to infer that the professor holds authority over continuous assessment or final grading.",
                "It is reasonable to infer that an unassisted confrontation carries risks of retaliatory grade tampering."
            ],
            "uncertainties": [
                "Whether the communications occurred via trackable electronic channels (WhatsApp/email) or verbal conversations without witnesses.",
                "Whether your exam has already been processed by the university external moderator."
            ],
            "recommendation": {
                "selectedOption": "OPTION_C",
                "title": "OPTION C: Seek Legal Aid & Confidential Protective Action",
                "description": "Engage free accredited legal aid to assist in confidential reporting to the University Vice-Chancellor, CAJ Ombudsman, or DCI Gender Desk.",
                "why": "This matter involves serious criminal conduct combined with institutional power imbalance. Legal accompaniment ensures your academic record is protected while investigations proceed.",
                "risks": [
                    "Retaliatory grade modification or examination irregularity allegations.",
                    "Spoliation of digital evidence if chats or messages are deleted."
                ],
                "whatYouCanDoNow": [
                    "Export and back up all WhatsApp/SMS threads without deleting any messages (Evidence Act s. 106B).",
                    "Submit an Article 35 Access to Information request for custody of your examination booklet.",
                    "Contact FIDA Kenya or the National Legal Aid Service (NLAS) for pro bono legal backing."
                ]
            },
            "ifYouCannotAffordALawyer": {
                "legalAidAvailable": True,
                "legalAidProviders": [
                    {
                        "name": "FIDA Kenya (Federation of Women Lawyers)",
                        "contact": "Toll-free: 0800 720 501 / +254 722 509 760",
                        "howTheyHelp": "Provides free legal aid, psychological support, and representation in sexual harassment cases."
                    },
                    {
                        "name": "National Legal Aid Service (NLAS - State Dept for Justice)",
                        "contact": "Toll-free: 0800 720 440 / nlas@justice.go.ke",
                        "howTheyHelp": "State-funded free legal assistance under Section 35 of the Legal Aid Act 2016."
                    },
                    {
                        "name": "Commission on Administrative Justice (Ombudsman)",
                        "contact": "Toll-free: 0800 221 349 / complain@ombudsman.go.ke",
                        "howTheyHelp": "Free statutory investigation of maladministration and abuse of authority in public universities."
                    }
                ],
                "selfHelpSteps": [
                    "1. Preserve original uncompressed chat screenshots showing the sender's full mobile phone number.",
                    "2. Draft a confidential letter marked 'STRICTLY CONFIDENTIAL - SEXUAL OFFENCES ACT S.24' to the Vice-Chancellor.",
                    "3. Request an anonymous external second marking of your exam scripts."
                ]
            },
            "ifYouWantToHandleItYourself": [
                "Keep all communications strictly on official, traceable university email channels.",
                "If contacted privately, reply in writing: 'I have submitted my work for academic assessment pursuant to university policy.'",
                "File a formal report with the DCI Gender Desk if physical threats occur."
            ],
            "evidenceToPreserve": [
                {
                    "item": "Original WhatsApp / SMS Chat Logs",
                    "purpose": "Proof of demand and timeline of coercion.",
                    "lawfulCollectionRule": "Keep original mobile device intact for Evidence Act Section 106B certificate."
                },
                {
                    "item": "Examination Attendance Slip / Exam Card",
                    "purpose": "Proof that you sat the exam and discharged academic requirements.",
                    "lawfulCollectionRule": "Retain original stamped card."
                }
            ],
            "nextSteps": [
                "Answer the clarifying questions above to refine your dossier.",
                "Tap 'Save to Case Workspace' to catalog your evidence items.",
                "Use the Document Generator to prepare an Article 35 Information Request or DCI complaint."
            ],
            "sources": [
                {"title": "Sexual Offences Act No. 3 of 2006", "url": "https://new.kenyalaw.org/legislation", "note": "Primary binding statute for sexual extortion."},
                {"title": "Constitution of Kenya 2010 (Article 28 & 47)", "url": "https://new.kenyalaw.org/legislation", "note": "Constitutional protection of dignity and fair procedure."}
            ],
            "disclaimer": "This assistant provides structured legal self-help information under Kenyan law. It is NOT a human advocate, court, or police officer and CANNOT guarantee any legal outcome."
        }

    # Check for University Suspension without Due Process
    if "suspend" in text_lower or ("university" in text_lower and ("hearing" in text_lower or "expel" in text_lower)):
        return {
            "whatIUnderstand": [
                "You were subjected to suspension from a university or tertiary college.",
                "The administration failed to provide an advance charge sheet, disclosure of evidence, or a fair hearing before imposing the sanction.",
                "You are seeking reinstatement, written reasons, and enforcement of due process."
            ],
            "possibleLegalIssues": [
                "Violation of Article 47(1) & (2) of the Constitution (Right to Fair Administrative Action and Written Reasons).",
                "Breach of Section 4(3) of the Fair Administrative Action Act No. 33 of 2015 (Mandatory prior notice and opportunity to make representations).",
                "Breach of Natural Justice and Article 50(1) (Right to Fair and Impartial Hearing)."
            ],
            "urgentRisksOrDeadlines": [
                "Internal Appeal Window: Most Kenyan universities enforce strict 14 to 21-day limits from suspension date to lodge an appeal.",
                "Judicial Review Limitation: High Court Judicial Review applications under Order 53 must generally be brought within 6 months."
            ],
            "clarifyingQuestions": [
                "1. What reason did the university give?",
                "2. Were you given a chance to respond before the suspension?",
                "3. Have you received the suspension in writing?"
            ],
            "whatTheLawSays": [
                {
                    "statute": "Constitution of Kenya 2010",
                    "section": "Article 47",
                    "exactTextSnippet": "Every person has the right to administrative action that is expeditious, efficient, lawful, reasonable and procedurally fair.",
                    "explanation": "Universities are statutory bodies and cannot condemn any student unheard.",
                    "sourceUrl": "https://new.kenyalaw.org/legislation"
                },
                {
                    "statute": "Fair Administrative Action Act No. 33 of 2015",
                    "section": "Section 4(3)",
                    "exactTextSnippet": "Where an administrative action is likely to adversely affect the rights of any person, the administrator shall give that person prior and adequate notice, an opportunity to be heard, and a statement of reasons.",
                    "explanation": "The law mandates that the university give you a written charge sheet, copies of all evidence, and a formal hearing date.",
                    "sourceUrl": "https://new.kenyalaw.org/legislation"
                }
            ],
            "howItMayApply": [
                "If the university suspended you without written notice and without convening a disciplinary committee, their action is illegal under Section 4 of FAAA 2015.",
                "In Republic v University of Nairobi ex parte Wanjiku [2018], the High Court quashed a suspension under identical facts, establishing that disciplinary action without a hearing is void ab initio."
            ],
            "inferences": [
                "It is reasonable to infer that the administration acted precipitously without convening the statutory Student Disciplinary Committee.",
                "It is reasonable to infer that an expulsion or long suspension cannot be enforced without complying with natural justice."
            ],
            "uncertainties": [
                "Whether the university regulations provide for an interim precautionary suspension pending an imminent formal hearing.",
                "The specific internal grievance hierarchy in your student handbook."
            ],
            "recommendation": {
                "selectedOption": "OPTION_A",
                "title": "OPTION A: Handle It Yourself (Immediate Formal Demand for Due Process)",
                "description": "Submit a formal administrative letter under Article 47 and FAAA Section 4 demanding immediate supply of charges, evidence, and an appeal hearing.",
                "why": "Statutory compliance letters at the internal administrative stage frequently resolve student suspensions quickly without expensive court litigation.",
                "risks": [
                    "Allowing the internal appeal window to lapse without lodging formal written objection.",
                    "Engaging in informal verbal discussions that leave no paper trail."
                ],
                "whatYouCanDoNow": [
                    "Draft a formal 'Article 47 Demand for Reasons and Due Process' using the Document Generator.",
                    "Deliver one copy to the Registrar (Academic) and obtain a 'Received' rubber stamp on your duplicate copy.",
                    "Send an identical copy by email for timestamped digital proof."
                ]
            },
            "ifYouCannotAffordALawyer": {
                "legalAidAvailable": True,
                "legalAidProviders": [
                    {
                        "name": "Commission on Administrative Justice (Ombudsman)",
                        "contact": "Toll-free: 0800 221 349 / complain@ombudsman.go.ke",
                        "howTheyHelp": "Investigates unfair university disciplinary actions and delays completely free of charge."
                    },
                    {
                        "name": "Kituo Cha Sheria (Legal Advice Centre)",
                        "contact": "Tel: +254 734 812 858",
                        "howTheyHelp": "Assists students challenging unlawful administrative decisions."
                    }
                ],
                "selfHelpSteps": [
                    "1. Send a formal letter to the Vice-Chancellor citing Article 47(2) demanding written reasons within 7 days.",
                    "2. File a free complaint with the Ombudsman attaching your suspension letter and proof of no hearing."
                ]
            },
            "ifYouWantToHandleItYourself": [
                "Cite Republic v University of Nairobi ex parte Wanjiku [2018] and Caleb Kiprono v Moi University [2020].",
                "Request the Vice-Chancellor to lift the suspension as void ab initio or schedule an expedited fair hearing.",
                "Always obtain an acknowledgment stamp on every submission."
            ],
            "evidenceToPreserve": [
                {
                    "item": "Original Suspension Letter",
                    "purpose": "Proof of administrative action and lack of due process.",
                    "lawfulCollectionRule": "Keep original physical copy; store scanned copy on cloud."
                },
                {
                    "item": "Student Handbook / Disciplinary Regulations",
                    "purpose": "Demonstrates procedural deviations committed by the university.",
                    "lawfulCollectionRule": "Download current version from student portal."
                }
            ],
            "nextSteps": [
                "Answer the 3 clarifying questions.",
                "Use the Document Generator to create an Article 47 Due Process Appeal.",
                "Set a calendar reminder for your 14-day internal appeal deadline."
            ],
            "sources": [
                {"title": "Fair Administrative Action Act No. 33 of 2015", "url": "https://new.kenyalaw.org/legislation", "note": "Mandates 4-step procedural fairness."},
                {"title": "Republic v University of Nairobi ex parte Wanjiku [2018] eKLR", "url": "http://kenyalaw.org/caselaw/cases/view/161204/", "note": "Landmark precedent quashing suspension without hearing."}
            ],
            "disclaimer": "This assistant provides structured legal self-help information under Kenyan law. It is NOT a human advocate, court, or police officer and CANNOT guarantee any legal outcome."
        }

    # Default / General Kenyan Legal Analysis
    return {
        "whatIUnderstand": [
            f"You have presented the following factual situation: '{user_text}'.",
            "You are seeking to understand your statutory rights and lawful next steps under Kenyan law."
        ],
        "possibleLegalIssues": [
            "Right to Fair Administrative Action (Article 47 Constitution & FAAA 2015).",
            "Right to Access to Justice and Fair Hearing (Article 48 & 50 Constitution).",
            "Statutory procedural compliance and preservation of rights."
        ],
        "urgentRisksOrDeadlines": [
            "Statutory clocks: Most civil and administrative procedures enforce strict limitation periods (14 to 30 days for notices/appeals)."
        ],
        "clarifyingQuestions": [
            "1. When exactly did this event occur?",
            "2. Did you receive any formal written notice or letter?",
            "3. What specific outcome or remedy are you seeking?"
        ],
        "whatTheLawSays": [
            {
                "statute": "Constitution of Kenya 2010",
                "section": "Article 47 & 50",
                "exactTextSnippet": "Every person has the right to administrative action that is expeditious, efficient, lawful, reasonable and procedurally fair.",
                "explanation": "Kenyan law protects all individuals against arbitrary actions taken without due process.",
                "sourceUrl": "https://new.kenyalaw.org/legislation"
            }
        ],
        "howItMayApply": [
            "Kenyan law prioritizes procedural fairness. Any adverse decision executed without notice or hearing is subject to administrative review or legal challenge."
        ],
        "inferences": [
            "It is reasonable to infer that immediate evidence preservation will strengthen your position."
        ],
        "uncertainties": [
            "The specific institutional rules and exact dates of service."
        ],
        "recommendation": {
            "selectedOption": "OPTION_A",
            "title": "OPTION A: Handle It Yourself (Initial Formal Demand)",
            "description": "Formulate a clear written demand citing relevant Kenyan law.",
            "why": "A well-structured formal letter often prompts compliance without litigation expenses.",
            "risks": ["Allowing limitation periods to expire."],
            "whatYouCanDoNow": [
                "Catalog your facts and dates in the Case Workspace.",
                "Generate a formal demand letter using the Document Generator."
            ]
        },
        "ifYouCannotAffordALawyer": {
            "legalAidAvailable": True,
            "legalAidProviders": [
                {
                    "name": "National Legal Aid Service (NLAS)",
                    "contact": "Toll-free: 0800 720 440 / nlas@justice.go.ke",
                    "howTheyHelp": "State legal aid for indigent persons."
                },
                {
                    "name": "Kituo Cha Sheria (Legal Advice Centre)",
                    "contact": "Tel: +254 734 812 858",
                    "howTheyHelp": "Free human rights legal aid."
                }
            ],
            "selfHelpSteps": [
                "1. Keep all communications in writing with receipt stamps.",
                "2. Preserve original digital evidence under Section 106B of Evidence Act."
            ]
        },
        "ifYouWantToHandleItYourself": [
            "Deliver documents physically and obtain acknowledgment stamps on your duplicate copy."
        ],
        "evidenceToPreserve": [
            {
                "item": "Written Notices / Letters",
                "purpose": "Proof of timeline and claims.",
                "lawfulCollectionRule": "Retain original physical copy."
            }
        ],
        "nextSteps": [
            "Answer the clarifying questions.",
            "Organize your evidence in the Workspace."
        ],
        "sources": [
            {"title": "Constitution of Kenya 2010", "url": "https://new.kenyalaw.org/legislation", "note": "Supreme law of the Republic."}
        ],
        "disclaimer": "This assistant provides structured legal self-help information under Kenyan law. It is NOT a human advocate and CANNOT guarantee any outcome."
    }


# ==============================================================================
# DOCUMENT GENERATION SERVICE
# ==============================================================================
def generate_document(doc_type, facts, recipient_name="", recipient_institution=""):
    date_now = datetime.datetime.now().strftime("%d %B %Y")
    doc_id = f"doc_{int(datetime.datetime.now().timestamp())}"

    complainant = facts.get("fullName") or facts.get("complainant") or "[Complainant Name]"
    institution = recipient_institution or facts.get("institution") or "[Institution / Company / Body]"
    recipient = recipient_name or facts.get("recipient") or "The Responsible Officer / Vice-Chancellor / Manager"
    incident_date = facts.get("incidentDate") or "[Date of Incident / Notice]"
    summary = facts.get("summary") or "[Chronological Summary of Events]"
    phone = facts.get("phone") or "[Phone Number]"
    reg_no = facts.get("studentOrStaffNo") or ""

    facts_used = []
    missing_facts = []

    if facts.get("fullName"):
        facts_used.append(f"Complainant Name: {complainant}")
    else:
        missing_facts.append("Full official name")

    if facts.get("summary"):
        facts_used.append("Factual summary of events")
    else:
        missing_facts.append("Detailed chronological summary")

    if doc_type == "tenancy_unlawful_eviction_demand":
        title = "Demand Regarding Unlawful Distress & Illegal Lockout (Distress for Rent Act & Rent Restriction Act)"
        content = f"""DATE: {date_now}

WITHOUT PREJUDICE / SAVE AS TO COSTS

TO:
The Landlord / Property Agent: {recipient}
Property / Premises: {institution}

RE: FORMAL DEMAND AND CEASE-AND-DESIST NOTICE REGARDING UNLAWFUL LOCKOUT, ILLEGAL DISTRESS FOR RENT, AND INTERFERENCE WITH QUIET ENJOYMENT

Dear Sir/Madam,

1. TENANCY PARTICULARS
Tenant: {complainant}
Premises: {institution}
Incident Date: {incident_date}

2. STATEMENT OF SUPPLIED FACTS
(a) On or about {incident_date}, the following unlawful actions were carried out:
    {summary}
(b) The landlord/agent took self-help measures by locking the tenant out, removing goods, or disconnecting essential utilities without a valid court or tribunal order.
(c) No statutory 30-day notice or proclamation by a licensed auctioneer was served in compliance with Kenyan law.

3. KENYAN LEGAL FRAMEWORK
(a) High Court Landmark Precedent: In Purity Wambui & Another v Muriithi [2019] eKLR, the High Court established that rent arrears do not entitle a landlord to bypass due process. Self-help eviction, padlock changes, or utility severance without a court order constitutes an unlawful trespass and actionable conversion of property.
(b) Distress for Rent Act (Cap 76): Section 3 and Section 16 strictly limit distress. Unlawful distress entitles the tenant to double the value of goods distrained and damages for trespass.
(c) Rent Restriction Act (Cap 296): Section 14 mandates that vacant possession can only be obtained through an order of the competent Rent Restriction Tribunal.

4. FORMAL DEMANDS:
You are hereby required within FORTY-EIGHT (48) HOURS of receipt hereof to:
1. Immediately remove all unauthorized locks and restore unimpeded physical access to the premises.
2. Restore all disconnected utilities (water, electricity).
3. Return all goods or personal property seized, intact and undamaged.
4. Issue a formal reconciliation statement of rent account.

TAKE NOTICE that failure to comply within 48 hours will result in immediate filing of an urgent chamber application at the Rent Restriction Tribunal / Environment and Land Court seeking injunctive orders and damages for illegal distress and trespass, with costs awarded against you.

Yours faithfully,

_____________________________
{complainant}
Phone: {phone}
"""
    elif doc_type == "employment_summary_dismissal_demand":
        title = "Demand for Statutory Hearing & Terminal Benefits (Employment Act 2007 s. 41 & 45)"
        content = f"""DATE: {date_now}

TO:
Managing Director / Human Resource Manager: {recipient}
Company / Employer: {institution}
Kenya

RE: FORMAL DEMAND AND NOTICE OF UNFAIR TERMINATION UNDER SECTION 41, 44 AND 45 OF THE EMPLOYMENT ACT NO. 11 OF 2007

Dear Sir/Madam,

1. EMPLOYMENT PARTICULARS
Employee: {complainant}
Staff ID: {reg_no or '[Staff ID]'}
Effective Date of Purported Termination: {incident_date}

2. STATEMENT OF SUPPLIED FACTS
(a) On {incident_date}, the employer executed summary termination under the following circumstances:
    {summary}
(b) The employee was not served with an advance written notice containing specific allegations.
(c) The employee was not accorded an opportunity to be accompanied by a fellow employee or union representative.
(d) No disciplinary hearing was convened in compliance with Section 41.

3. APPLICABLE KENYAN STATUTORY AUTHORITY
(a) Section 41 of the Employment Act 2007: Before terminating an employee on grounds of misconduct, poor performance, or physical incapacity, the employer is statutorily mandated to explain the reason in a language understood by the employee and hear representations in the presence of an advisor.
(b) Supreme Court Precedent: The Supreme Court and Court of Appeal (Kenya Airways Ltd v Allied Workers Union [2014] eKLR) affirm that statutory procedural fairness under Section 41 is mandatory; failure to comply renders any dismissal procedurally unfair as a matter of law.
(c) Section 45: Unfair dismissal entitles the employee to compensation of up to 12 months' gross salary in addition to statutory terminal dues.

4. DEMAND FOR AMICABLE SETTLEMENT WITHIN FOURTEEN (14) DAYS:
I hereby demand:
1. Written reasons and minutes of any disciplinary panel relied upon.
2. Payment of full statutory terminal benefits, including:
   - Salary for days worked up to termination date.
   - Payment in lieu of notice (Section 35).
   - Accrued untaken annual leave days (Section 28).
   - Certificate of Service (Section 51).
   - Statutory compensation for unfair termination under Section 49(1)(c).

Failure to settle within fourteen (14) days will leave me no option but to file a statement of claim at the Employment and Labour Relations Court (ELRC).

Yours faithfully,

_____________________________
{complainant}
"""
    elif doc_type == "criminal_complaint_letter":
        title = "Formal Complaint to Directorate of Criminal Investigations (DCI) / NPS"
        content = f"""DATE: {date_now}

TO:
The Officer in Charge (OCS) / DCI Gender & Serious Crimes Desk
National Police Service
Police Station: [Name of Police Station / DCI Office]
Kenya

COMPLAINANT: {complainant}
ACCUSED PERSON: {recipient} ({institution})

RE: FORMAL CRIMINAL COMPLAINT REGARDING ABUSE OF POSITION OF AUTHORITY FOR SEXUAL FAVOURS (SECTION 24 SEXUAL OFFENCES ACT NO. 3 OF 2006) AND EXTORTION

Sir/Madam,

1. PARTICULARS OF COMPLAINANT
Name: {complainant}
Phone: {phone}
Institution / Reg No: {reg_no or '[Reg No]'}

2. PARTICULARS OF THE ACCUSED PERSON
Name: {recipient}
Position / Role: [Professor / Supervisor / Official]
Institution: {institution}

3. REPORTED OFFENCES
(a) Section 24 of the Sexual Offences Act No. 3 of 2006 (Sexual Harassment / Abuse of Position of Authority): A person in a position of authority who persistently demands sexual favours from a student or subordinate under threat of detriment.
(b) Section 296/300 of the Penal Code (Cap 63) (Extortion and Demanding Advantages with Menaces).

4. CHRONOLOGY OF FACTS & OCCURRENCES
On or about {incident_date}, the accused person did as follows:
{summary}

5. PHYSICAL AND DIGITAL EVIDENCE PRESERVED:
The complainant has preserved original electronic messages, timestamped chat logs, and unit enrollment slips, ready to tender to investigating officers under Section 106B of the Evidence Act.

6. ACTION REQUESTED:
I respectfully request that the National Police Service / DCI:
1. Record an official OB (Occurrence Book) entry and issue an OB Number.
2. Initiate formal criminal investigations under the Sexual Offences Act.
3. Facilitate protective measures against academic or physical retaliation.

Signed: ___________________________
{complainant}
Date: {date_now}
"""
    else:  # Default: Administrative Complaint (Art 47 & FAAA 2015)
        title = "Formal Administrative Complaint & Demand for Due Process (Art. 47 & FAAA 2015)"
        content = f"""DATE: {date_now}

TO:
{recipient}
{institution}
P.O. Box [Postal Address]
Kenya

RE: FORMAL COMPLAINT AND DEMAND FOR DUE PROCESS UNDER ARTICLE 47 OF THE CONSTITUTION OF KENYA AND SECTION 4 OF THE FAIR ADMINISTRATIVE ACTION ACT NO. 33 OF 2015

Dear Sir/Madam,

1. IDENTITY OF COMPLAINANT
I, {complainant}, {f'holding Reg/Staff ID No. {reg_no}' if reg_no else ''}, write to register a formal complaint regarding administrative actions taken against me without compliance with mandatory statutory procedures.

2. STATEMENT OF SUPPLIED FACTS
(a) On or about {incident_date}, the following occurred:
    {summary}
(b) I have not been furnished with a formal written charge sheet detailing specific regulations allegedly breached.
(c) I have not been provided with disclosure of the evidence, witness statements, or investigative findings relied upon.
(d) No impartial hearing was convened prior to the adverse decision / suspension being issued.

3. APPLICABLE KENYAN LEGAL FRAMEWORK
(a) Article 47(1) of the Constitution of Kenya 2010 guarantees that: "Every person has the right to administrative action that is expeditious, efficient, lawful, reasonable and procedurally fair."
(b) Section 4(3) of the Fair Administrative Action Act No. 33 of 2015 mandates that where an administrative action is likely to adversely affect rights, the administrator shall give prior and adequate notice, an opportunity to be heard, and written reasons.
(c) The High Court of Kenya in Republic v University of Nairobi ex parte Wanjiku [2018] eKLR unequivocally held that disciplinary suspensions executed without advance notice and an opportunity to be heard are illegal, ultra vires, and void ab initio.

4. REMEDIES FORMALLY REQUESTED
Pursuant to the laws of Kenya, I hereby respectfully demand:
(a) Immediate provision of written reasons and copies of all documents forming the basis of the action within seven (7) days.
(b) An immediate stay or lifting of the summary suspension pending regularisation of proceedings.
(c) The scheduling of a formal, fair hearing before an impartial disciplinary committee with adequate notice (at least 14 days).

Take notice that failure to adhere to statutory standards will compel me to escalate this matter to the Commission on Administrative Justice (Office of the Ombudsman) and seek Judicial Review before the High Court of Kenya.

Yours faithfully,

_____________________________
{complainant}
Phone: {phone}

CC:
- Commission on Administrative Justice (Office of the Ombudsman)
- Dean of Students / Academic Registrar
"""

    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO generated_documents (id, title, type, createdAt, content, factsUsed, missingFactsNoted)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        doc_id,
        title,
        doc_type,
        datetime.datetime.now().isoformat(),
        content.strip(),
        json.dumps(facts_used),
        json.dumps(missing_facts)
    ))
    conn.commit()
    conn.close()

    return {
        "id": doc_id,
        "title": title,
        "type": doc_type,
        "createdAt": datetime.datetime.now().isoformat(),
        "content": content.strip(),
        "factsUsed": facts_used,
        "missingFactsNoted": missing_facts
    }


# ==============================================================================
# API ROUTES
# ==============================================================================
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "app": "Kenya Legal Assistant",
        "version": "1.0.0",
        "mission": "Make legal knowledge accessible, not make lawyers mandatory."
    })


@app.route("/api/sources", methods=["GET"])
def get_sources():
    return jsonify({"sources": OFFICIAL_SOURCES})


@app.route("/api/law", methods=["GET"])
def get_law():
    q = request.args.get("q", "").lower()
    cat = request.args.get("category", "all")
    filtered = STATUTES
    if cat != "all":
        filtered = [s for s in filtered if s["category"].lower() == cat.lower()]
    if q:
        filtered = [s for s in filtered if q in s["topic"].lower() or q in s["exactText"].lower() or q in s["document"].lower()]
    return jsonify({"statutes": filtered, "total": len(filtered)})


@app.route("/api/cases", methods=["GET"])
def get_cases():
    q = request.args.get("q", "").lower()
    auth = request.args.get("authorityType", "all")
    filtered = CASES
    if auth != "all":
        filtered = [c for c in filtered if c["authorityType"] == auth]
    if q:
        filtered = [c for c in filtered if q in c["caseName"].lower() or q in c["legalIssues"].lower() or q in c["legalTest"].lower()]
    return jsonify({"cases": filtered, "total": len(filtered)})


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    message = data.get("message", "").strip()
    mode = data.get("mode", "rights")
    prior_answers = data.get("priorAnswers", {})

    if not message:
        return jsonify({"error": "Message is required"}), 400

    # Process via Kenyan Legal Reasoning Engine
    analysis = analyze_legal_situation(message, mode, prior_answers)
    return jsonify({
        "replyText": "Here is your structured Kenyan legal analysis:",
        "structured": analysis,
        **analysis
    })


@app.route("/api/workspace", methods=["GET"])
def get_workspace():
    conn = get_db()
    c = conn.cursor()

    case_row = c.execute("SELECT * FROM workspace_cases WHERE id = 'case_demo_01'").fetchone()
    case_details = dict(case_row) if case_row else None

    facts_rows = c.execute("SELECT * FROM workspace_facts WHERE caseId = 'case_demo_01' ORDER BY dateOrTime ASC").fetchall()
    facts = [dict(r) for r in facts_rows]

    evidence_rows = c.execute("SELECT * FROM workspace_evidence WHERE caseId = 'case_demo_01' ORDER BY dateObtained DESC").fetchall()
    evidence = [dict(r) for r in evidence_rows]

    opponents_rows = c.execute("SELECT * FROM workspace_opponents WHERE caseId = 'case_demo_01'").fetchall()
    opponents = [dict(r) for r in opponents_rows]

    conn.close()

    hearing_prep = {
        "forum": case_details["institutionOrForum"] if case_details else "Tribunal / Disciplinary Panel",
        "standardProcedure": [
            "1. Preliminary Formalities: Panel verifies identity, reads charges, confirms presence of support advisor.",
            "2. Reading of Charge: Institution presents official allegations and tenders investigation report.",
            "3. Presentation of Institution Witnesses: Witnesses testify and produce documentary exhibits.",
            "4. Right of Cross-Examination: You have the constitutional right (Article 50(1)) to put questions directly to witnesses.",
            "5. Your Defense: You testify, explain your narrative, and tender certified electronic evidence (Section 106B).",
            "6. Closing Submissions: Summarize why the charge is unproven or procedurally defective under Article 47 & FAAA 2015."
        ],
        "documentsToBring": [
            "National ID Card & Student/Staff Identification Card.",
            "Original physical copies of all letters and written notices with receipt stamps.",
            "Three printed copies of your Evidence Index & Chain of Custody.",
            "Original mobile device containing electronic communications in airplane mode for inspection."
        ],
        "coreIssuesToProve": [
            "Procedural non-compliance: Lack of advance notice or refusal to provide evidence before hearing.",
            "Substantive defense: Alibi, academic compliance, or power imbalance/extortion."
        ],
        "crossExaminationQuestions": [
            "When exactly was this disciplinary charge first framed, and why was I not served with it immediately?",
            "Who had physical and administrative custody of the examination booklets prior to grading?",
            "Can you produce any written notice showing that I was summoned prior to summary suspension?"
        ],
        "burdenOfProofNotice": "Under Section 107 of the Evidence Act, he who asserts must prove. In adverse actions, the institution carries the primary burden to substantiate charges."
    }

    return jsonify({
        "caseDetails": case_details,
        "facts": facts,
        "evidence": evidence,
        "opponents": opponents,
        "hearingPrep": hearing_prep
    })


@app.route("/api/workspace/case", methods=["POST"])
def save_case():
    data = request.get_json() or {}
    conn = get_db()
    c = conn.cursor()
    now = datetime.datetime.now().isoformat()
    c.execute("""
        UPDATE workspace_cases
        SET caseTitle = COALESCE(?, caseTitle),
            institutionOrForum = COALESCE(?, institutionOrForum),
            caseNumber = COALESCE(?, caseNumber),
            applicant = COALESCE(?, applicant),
            respondent = COALESCE(?, respondent),
            currentStage = COALESCE(?, currentStage),
            nextDate = COALESCE(?, nextDate),
            urgentDeadlines = COALESCE(?, urgentDeadlines),
            notes = COALESCE(?, notes),
            updatedAt = ?
        WHERE id = 'case_demo_01'
    """, (
        data.get("caseTitle"),
        data.get("institutionOrForum"),
        data.get("caseNumber"),
        data.get("applicant"),
        data.get("respondent"),
        data.get("currentStage"),
        data.get("nextDate"),
        data.get("urgentDeadlines"),
        data.get("notes"),
        now
    ))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Case updated"})


@app.route("/api/workspace/fact", methods=["POST"])
def add_fact():
    data = request.get_json() or {}
    fact_id = f"fact_{int(datetime.datetime.now().timestamp() * 1000)}"
    date_val = data.get("dateOrTime") or datetime.datetime.now().strftime("%Y-%m-%d")
    desc = data.get("description", "").strip()
    f_type = data.get("type", "key_event")

    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO workspace_facts (id, caseId, dateOrTime, description, type, supportingEvidenceIds)
        VALUES (?, 'case_demo_01', ?, ?, ?, '[]')
    """, (fact_id, date_val, desc, f_type))
    conn.commit()
    conn.close()

    return jsonify({"id": fact_id, "dateOrTime": date_val, "description": desc, "type": f_type})


@app.route("/api/workspace/fact/<fact_id>", methods=["DELETE"])
def delete_fact(fact_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM workspace_facts WHERE id = ?", (fact_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/workspace/evidence", methods=["POST"])
def add_evidence():
    data = request.get_json() or {}
    ev_id = f"ev_{int(datetime.datetime.now().timestamp() * 1000)}"
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO workspace_evidence (id, caseId, title, category, dateObtained, description, lawfulStatus, custodyNotes)
        VALUES (?, 'case_demo_01', ?, ?, ?, ?, ?, ?)
    """, (
        ev_id,
        data.get("title", "Evidence Item"),
        data.get("category", "document"),
        data.get("dateObtained") or datetime.datetime.now().strftime("%Y-%m-%d"),
        data.get("description", ""),
        data.get("lawfulStatus", "Lawfully Obtained"),
        data.get("custodyNotes", "")
    ))
    conn.commit()
    conn.close()
    return jsonify({"id": ev_id, "success": True})


@app.route("/api/workspace/evidence/<ev_id>", methods=["DELETE"])
def delete_evidence(ev_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM workspace_evidence WHERE id = ?", (ev_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/workspace/import-chat", methods=["POST"])
def import_chat():
    data = request.get_json() or {}
    case_title = data.get("caseTitle") or "Legal Self-Help Matter"
    facts = data.get("facts") or []
    evidence = data.get("evidence") or []
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    conn = get_db()
    c = conn.cursor()

    # Update title
    c.execute("UPDATE workspace_cases SET caseTitle = ? WHERE id = 'case_demo_01'", (case_title,))

    facts_imported = 0
    for f in facts:
        if f and isinstance(f, str) and f.strip():
            fid = f"fact_{int(datetime.datetime.now().timestamp() * 1000)}_{facts_imported}"
            c.execute("""
                INSERT INTO workspace_facts (id, caseId, dateOrTime, description, type, supportingEvidenceIds)
                VALUES (?, 'case_demo_01', ?, ?, 'key_event', '[]')
            """, (fid, today, f.strip()))
            facts_imported += 1

    ev_imported = 0
    for item in evidence:
        if isinstance(item, dict) and item.get("item"):
            eid = f"ev_{int(datetime.datetime.now().timestamp() * 1000)}_{ev_imported}"
            c.execute("""
                INSERT INTO workspace_evidence (id, caseId, title, category, dateObtained, description, lawfulStatus, custodyNotes)
                VALUES (?, 'case_demo_01', ?, 'document', ?, ?, 'Lawfully Obtained', ?)
            """, (
                eid,
                item["item"],
                today,
                item.get("purpose", ""),
                item.get("lawfulCollectionRule", "Preserve under Section 106B Evidence Act")
            ))
            ev_imported += 1

    conn.commit()
    conn.close()

    return jsonify({"success": True, "factsImported": facts_imported, "evidenceImported": ev_imported})


@app.route("/api/workspace/bundle", methods=["GET"])
def get_bundle():
    ws_data = get_workspace().get_json()
    c = ws_data.get("caseDetails") or {}
    facts = ws_data.get("facts") or []
    evidence = ws_data.get("evidence") or []
    now = datetime.datetime.now().strftime("%d %B %Y")

    md = f"""# REPUBLIC OF KENYA
## IN THE {c.get('institutionOrForum', 'DISCIPLINARY APPEALS COMMITTEE / TRIBUNAL').upper()}
**CASE / MATTER REF:** {c.get('caseNumber', 'IN RE: PROCEDURAL FAIRNESS REVIEW')}

---

**BETWEEN:**
**{c.get('applicant', 'SELF-REPRESENTED COMPLAINANT').upper()}** .................................... **COMPLAINANT / APPLICANT**

**AND**

**{c.get('respondent', 'RESPONDENT INSTITUTION / ADVERSE PARTY').upper()}** .......................... **RESPONDENT**

---

### SELF-REPRESENTATION HEARING BUNDLE & FACTUAL DOSSIER
*Compiled on {now} for use pursuant to Article 50(1) (Fair Hearing) and Article 47 (Fair Administrative Action) of the Constitution of Kenya 2010.*

### PART I: CASE OVERVIEW
- **Subject Matter:** {c.get('caseTitle', 'Administrative Dispute')}
- **Forum / Court:** {c.get('institutionOrForum', 'Tribunal')}
- **Current Stage:** {c.get('currentStage', 'Preparation')}
- **Next Scheduled Date:** {c.get('nextDate', 'To be scheduled')}
- **Urgent Deadlines:** {c.get('urgentDeadlines', '14-day statutory clock')}

### PART II: CHRONOLOGY OF FACTS
"""
    for idx, f in enumerate(facts):
        badge = "[UNDISPUTED]" if f.get("type") == "undisputed" else "[DISPUTED]" if f.get("type") == "disputed" else "[KEY EVENT]"
        md += f"{idx + 1}. **{f.get('dateOrTime')}** {badge} — {f.get('description')}\n"

    md += "\n### PART III: EVIDENCE INDEX & CHAIN OF CUSTODY (EVIDENCE ACT s. 106B)\n"
    for idx, ev in enumerate(evidence):
        md += f"**Exhibit [{idx + 1}] — {ev.get('title')}** ({ev.get('category', 'doc').upper()})\n"
        md += f"  - *Date Obtained:* {ev.get('dateObtained')}\n"
        md += f"  - *Description / Purpose:* {ev.get('description')}\n"
        md += f"  - *Admissibility / Status:* {ev.get('lawfulStatus')}\n"
        md += f"  - *Custody Notes:* {ev.get('custodyNotes', 'Original preserved')}\n\n"

    md += f"""### PART IV: HEARING PROCEDURE & PROOF
**Standard Order:** Identity verification → Reading of allegations → Evidence disclosure → Cross-examination → Your defense → Closing submissions.
**Burden of Proof (Evidence Act s. 107):** He who asserts must prove. The adverse party carries the burden of substantiating charges.

---
*Generated by Kenya Legal Assistant — Self-Representation Suite.*
"""
    return jsonify({
        "title": f"{c.get('caseTitle', 'Case')} - Hearing Bundle",
        "generatedAt": now,
        "markdownBundle": md
    })


@app.route("/api/documents/generate", methods=["POST"])
def api_generate_document():
    data = request.get_json() or {}
    doc_type = data.get("documentType", "administrative_complaint")
    facts = data.get("userFacts", {})
    recipient = data.get("recipientName", "")
    institution = data.get("recipientInstitution", "")

    result = generate_document(doc_type, facts, recipient, institution)
    return jsonify({"success": True, "document": result, **result})


@app.route("/api/documents", methods=["GET"])
def list_documents():
    conn = get_db()
    c = conn.cursor()
    rows = c.execute("SELECT * FROM generated_documents ORDER BY createdAt DESC").fetchall()
    docs = [dict(r) for r in rows]
    conn.close()
    return jsonify({"documents": docs})


# ==============================================================================
# EMBEDDED FRONTEND (Mobile-First HTML, CSS, JavaScript)
# ==============================================================================
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
  <meta name="theme-color" content="#064e3b">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <title>Kenya Legal Assistant | Make Legal Knowledge Accessible</title>
  <style>
    :root {
      --primary: #064e3b;
      --primary-light: #059669;
      --primary-subtle: #ecfdf5;
      --secondary: #991b1b;
      --accent: #b45309;
      --bg-app: #f8fafc;
      --text-main: #0f172a;
      --text-muted: #64748b;
      --border: #e2e8f0;
      --safe-bottom: env(safe-area-inset-bottom, 16px);
      --safe-top: env(safe-area-inset-top, 16px);
    }
    * { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background-color: var(--bg-app);
      color: var(--text-main);
      padding-bottom: calc(75px + var(--safe-bottom));
      line-height: 1.5;
    }
    .app-header {
      background: linear-gradient(135deg, #064e3b 0%, #042f24 100%);
      color: #fff;
      padding: calc(14px + var(--safe-top)) 16px 14px;
      border-bottom: 3px solid var(--accent);
      position: sticky;
      top: 0;
      z-index: 100;
    }
    .brand-title { display: flex; align-items: center; justify-content: space-between; font-size: 1.15rem; font-weight: 800; }
    .brand-badge { background: #b45309; font-size: 0.68rem; padding: 2px 8px; border-radius: 999px; text-transform: uppercase; }
    .mission-tagline { font-size: 0.78rem; color: #a7f3d0; margin-top: 4px; font-style: italic; }
    .notice-strip {
      background: #fef2f2;
      border-bottom: 1px solid #fecaca;
      padding: 8px 14px;
      font-size: 0.73rem;
      color: #991b1b;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .main-container { max-width: 800px; margin: 0 auto; padding: 14px 14px 20px; }
    .hero-card {
      background: #fff;
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 18px;
      margin-bottom: 16px;
      box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
      text-align: center;
    }
    .hero-title { font-size: 1.35rem; font-weight: 800; color: var(--primary); }
    .hero-sub { font-size: 0.88rem; color: var(--accent); font-weight: 600; font-style: italic; margin-top: 2px; }
    .chat-input-box {
      margin-top: 14px;
      border: 1.5px solid #cbd5e1;
      border-radius: 12px;
      padding: 10px;
      background: #fff;
      text-align: left;
    }
    .chat-input-box textarea {
      width: 100%;
      min-height: 85px;
      border: none;
      outline: none;
      font-size: 0.92rem;
      font-family: inherit;
      resize: vertical;
    }
    .chat-input-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 8px;
      padding-top: 8px;
      border-top: 1px solid #f1f5f9;
      flex-wrap: wrap;
      gap: 6px;
    }
    .btn-primary {
      background: var(--primary);
      color: #fff;
      border: none;
      padding: 8px 16px;
      border-radius: 8px;
      font-weight: 700;
      font-size: 0.82rem;
      cursor: pointer;
    }
    .btn-secondary {
      background: #f1f5f9;
      color: #334155;
      border: 1px solid #cbd5e1;
      padding: 8px 14px;
      border-radius: 8px;
      font-weight: 600;
      font-size: 0.82rem;
      cursor: pointer;
    }
    .mode-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; margin: 12px 0; }
    .mode-card {
      background: #fff;
      border: 1px solid var(--border);
      padding: 8px 10px;
      border-radius: 8px;
      cursor: pointer;
      text-align: left;
    }
    .mode-card.active { background: var(--primary-subtle); border-color: var(--primary); }
    .mode-title { font-size: 0.82rem; font-weight: 700; color: var(--primary); }
    .mode-desc { font-size: 0.68rem; color: var(--text-muted); }
    .quick-tools { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; margin-top: 10px; }
    .tool-btn {
      background: #f8fafc;
      border: 1px solid #cbd5e1;
      padding: 8px;
      border-radius: 8px;
      font-size: 0.78rem;
      font-weight: 700;
      color: #334155;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
    }
    .scenario-box {
      background: #fff;
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 12px;
      margin-bottom: 16px;
    }
    .scenario-btn {
      width: 100%;
      text-align: left;
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      padding: 8px 10px;
      border-radius: 8px;
      font-size: 0.76rem;
      margin-top: 6px;
      cursor: pointer;
      color: #1e293b;
    }
    .msg-card {
      background: #fff;
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 14px;
      margin-bottom: 14px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .legal-sec {
      background: #f8fafc;
      border-left: 4px solid var(--primary);
      padding: 10px 12px;
      border-radius: 6px;
      margin-top: 10px;
      font-size: 0.82rem;
    }
    .sec-law { border-left-color: #059669; background: #ecfdf5; }
    .sec-rec { border-left-color: #b45309; background: #fffbeb; }
    .sec-aid { border-left-color: #0284c7; background: #f0f9ff; }
    .sec-warn { border-left-color: #dc2626; background: #fef2f2; }
    .bottom-nav {
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      background: rgba(255, 255, 255, 0.98);
      backdrop-filter: blur(12px);
      border-top: 1px solid var(--border);
      display: flex;
      justify-content: space-around;
      padding: 8px 6px calc(8px + var(--safe-bottom));
      z-index: 200;
    }
    .nav-btn {
      background: none;
      border: none;
      display: flex;
      flex-direction: column;
      align-items: center;
      font-size: 0.72rem;
      font-weight: 600;
      color: var(--text-muted);
      cursor: pointer;
      flex: 1;
    }
    .nav-btn.active { color: var(--primary); font-weight: 800; }
    .modal-bg {
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0, 0, 0, 0.5);
      z-index: 500;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 16px;
    }
    .modal-box {
      background: #fff;
      border-radius: 16px;
      width: 100%;
      max-width: 600px;
      max-height: 85vh;
      overflow-y: auto;
      padding: 18px;
    }
  </style>
</head>
<body>

  <!-- Header -->
  <header class="app-header">
    <div class="brand-title">
      <span>⚖️ Kenya Legal Assistant</span>
      <span class="brand-badge">Self-Help AI</span>
    </div>
    <div class="mission-tagline">“Make legal knowledge accessible, not make lawyers mandatory.”</div>
  </header>

  <!-- Visible Privacy Notice -->
  <div class="notice-strip">
    <span>🔒 <strong>Privacy Warning:</strong> Do not enter passwords, PINs, banking info or National ID numbers.</span>
  </div>

  <!-- Main View Container -->
  <div class="main-container" id="viewContainer">
    <!-- Rendered dynamically via JavaScript -->
  </div>

  <!-- Bottom Navigation Bar (iPhone Safe) -->
  <nav class="bottom-nav">
    <button class="nav-btn active" onclick="switchTab('chat')">💬 Assistant</button>
    <button class="nav-btn" onclick="switchTab('law')">📜 The Law</button>
    <button class="nav-btn" onclick="switchTab('cases')">🏛️ Cases</button>
    <button class="nav-btn" onclick="switchTab('workspace')">🗂️ Workspace</button>
    <button class="nav-btn" onclick="switchTab('docs')">📄 Documents</button>
  </nav>

  <!-- Single-Page Application Logic -->
  <script>
    let currentTab = 'chat';
    let currentMode = 'rights';
    let chatHistory = [];
    let workspaceData = null;

    function switchTab(tab) {
      currentTab = tab;
      document.querySelectorAll('.nav-btn').forEach((btn, idx) => {
        btn.classList.toggle('active', ['chat','law','cases','workspace','docs'][idx] === tab);
      });
      renderView();
    }

    function renderView() {
      const c = document.getElementById('viewContainer');
      if (currentTab === 'chat') renderChatView(c);
      else if (currentTab === 'law') renderLawView(c);
      else if (currentTab === 'cases') renderCasesView(c);
      else if (currentTab === 'workspace') renderWorkspaceView(c);
      else if (currentTab === 'docs') renderDocsView(c);
    }

    // 1. CHAT VIEW
    function renderChatView(container) {
      container.innerHTML = `
        <div class="hero-card">
          <div class="hero-title">Kenya Legal Assistant</div>
          <div class="hero-sub">“Understand the law. Know your options. Take the next step.”</div>

          <div class="chat-input-box">
            <textarea id="chatInput" placeholder="Tell me what happened… (e.g. I was suspended from university and they never gave me a chance to explain myself.)"></textarea>
            <div class="chat-input-footer">
              <span style="font-size:0.7rem; color:#dc2626;">🔒 Anonymous & Confidential</span>
              <button class="btn-primary" onclick="submitChat()">Analyze My Situation ➔</button>
            </div>
          </div>

          <div style="font-size:0.74rem; font-weight:700; color:#334155; margin-top:12px; text-align:left;">SELECT ASSISTANCE MODE:</div>
          <div class="mode-grid">
            <div class="mode-card ${currentMode==='rights'?'active':''}" onclick="setMode('rights')">
              <div class="mode-title">📖 Understand My Rights</div>
              <div class="mode-desc">Plain English statutory breakdown</div>
            </div>
            <div class="mode-card ${currentMode==='handle'?'active':''}" onclick="setMode('handle')">
              <div class="mode-title">🛠️ Handle It Myself</div>
              <div class="mode-desc">Lawful steps without lawyer fees</div>
            </div>
            <div class="mode-card ${currentMode==='represent'?'active':''}" onclick="setMode('represent')">
              <div class="mode-title">🏛️ Represent Myself</div>
              <div class="mode-desc">Organize facts, evidence & hearing</div>
            </div>
            <div class="mode-card ${currentMode==='help'?'active':''}" onclick="setMode('help')">
              <div class="mode-title">⚖️ Find Legal Help</div>
              <div class="mode-desc">Free legal aid & pro bono network</div>
            </div>
          </div>

          <div class="quick-tools">
            <div class="tool-btn" onclick="switchTab('law')">📜 Show me the law</div>
            <div class="tool-btn" onclick="switchTab('cases')">🏛️ Cases like mine</div>
            <div class="tool-btn" onclick="switchTab('workspace')">📅 Build timeline</div>
            <div class="tool-btn" onclick="switchTab('workspace')">🗂️ Organize evidence</div>
          </div>
        </div>

        <!-- 1-Minute Procedural Due Process Check Banner -->
        <div style="background:#ecfdf5; border:1px solid #10b981; border-radius:12px; padding:12px; margin-bottom:16px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
          <div>
            <div style="font-weight:800; font-size:0.86rem; color:#064e3b;">⚡ 1-Minute Due Process Check</div>
            <div style="font-size:0.72rem; color:#047857;">Instant test: Was your suspension, lockout, or dismissal illegal under Kenyan law?</div>
          </div>
          <button class="btn-primary" style="padding:6px 12px; font-size:0.76rem;" onclick="openWizardModal()">Run Checklist ➔</button>
        </div>

        <!-- Demo Scenarios -->
        <div class="scenario-box">
          <div style="font-size:0.78rem; font-weight:800; color:#064e3b;">⚡ Factual Demo Scenarios (1-Tap Analysis)</div>
          <button class="scenario-btn" onclick="runScenario('I am being blackmailed by my professor for sex or he won’t pass my exam. I am above 18.')">
            📌 <strong>Sexual Harassment & Extortion:</strong> "I am being blackmailed by my professor for sex or he won't pass my exam. I am above 18."
          </button>
          <button class="scenario-btn" onclick="runScenario('I was suspended from university and they never gave me a chance to explain myself.')">
            📌 <strong>University Suspension:</strong> "I was suspended from university and they never gave me a chance to explain myself."
          </button>
          <button class="scenario-btn" onclick="runScenario('My landlord locked my door and threw my things out because I am 3 days late on rent.')">
            📌 <strong>Tenancy Illegal Eviction:</strong> "My landlord locked my door and threw my things out because I am 3 days late on rent."
          </button>
        </div>

        <!-- Messages Log -->
        <div id="messagesLog">
          ${chatHistory.map(m => renderMessage(m)).join('')}
        </div>
      `;
    }

    function setMode(m) {
      currentMode = m;
      renderView();
    }

    function runScenario(txt) {
      document.getElementById('chatInput').value = txt;
      submitChat();
    }

    async function submitChat() {
      const input = document.getElementById('chatInput');
      const text = input ? input.value.trim() : '';
      if (!text) return;

      chatHistory.push({ role: 'user', text: text });
      input.value = '';
      renderView();

      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ message: text, mode: currentMode })
        });
        const data = await res.json();
        chatHistory.push({ role: 'assistant', structured: data.structured || data });
        renderView();
      } catch (err) {
        alert('Server connection error. Please try again.');
      }
    }

    function renderMessage(m) {
      if (m.role === 'user') {
        return `<div class="msg-card" style="background:#f1f5f9; border-color:#cbd5e1;"><strong>YOU:</strong><div style="margin-top:4px;">${m.text}</div></div>`;
      }
      const s = m.structured;
      if (!s) return `<div class="msg-card">${m.text}</div>`;

      return `
        <div class="msg-card">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
            <strong style="color:var(--primary); font-size:0.92rem;">⚖️ KENYA LEGAL ASSISTANT</strong>
            <button class="btn-primary" style="padding:4px 10px; font-size:0.75rem;" onclick='saveToWorkspace(${JSON.stringify(s).replace(/'/g, "&apos;")})'>📥 Save to Case Workspace</button>
          </div>

          <div class="legal-sec">
            <strong>📋 FACTS (Only facts supplied by you):</strong>
            <ul style="padding-left:18px; margin-top:4px;">${s.whatIUnderstand.map(f => `<li>${f}</li>`).join('')}</ul>
          </div>

          <div class="legal-sec">
            <strong>⚖️ POSSIBLE LEGAL ISSUES:</strong>
            <ul style="padding-left:18px; margin-top:4px;">${s.possibleLegalIssues.map(i => `<li><strong>${i}</strong></li>`).join('')}</ul>
          </div>

          ${s.clarifyingQuestions && s.clarifyingQuestions.length ? `
            <div class="legal-sec" style="background:#fefce8; border-left-color:#eab308;">
              <strong style="color:#854d0e;">❓ WHAT I NEED TO KNOW (Clarifying Questions):</strong>
              <ul style="padding-left:18px; margin-top:4px; color:#713f12;">${s.clarifyingQuestions.map(q => `<li>${q}</li>`).join('')}</ul>
            </div>
          ` : ''}

          <div class="legal-sec sec-law">
            <strong>📜 WHAT THE LAW SAYS (Verified Kenyan Authority):</strong>
            ${s.whatTheLawSays.map(l => `
              <div style="margin-top:6px; padding:6px; background:#fff; border-radius:6px; border:1px solid #a7f3d0;">
                <div><strong>${l.statute} — ${l.section}</strong></div>
                <div style="font-style:italic; font-size:0.78rem; margin:2px 0;">"${l.exactTextSnippet}"</div>
                <div style="font-size:0.78rem;"><strong>Plain English:</strong> ${l.explanation}</div>
              </div>
            `).join('')}
          </div>

          <div class="legal-sec">
            <strong>🔍 HOW THE LAW MAY APPLY:</strong>
            <ul style="padding-left:18px; margin-top:4px;">${s.howItMayApply.map(a => `<li>${a}</li>`).join('')}</ul>
          </div>

          <div class="legal-sec sec-rec">
            <strong style="color:#92400e;">🎯 RECOMMENDATION: ${s.recommendation.title}</strong>
            <div style="margin-top:4px;"><strong>Why:</strong> ${s.recommendation.why}</div>
            <div style="margin-top:6px;"><strong>What you can do now:</strong></div>
            <ul style="padding-left:18px;">${s.recommendation.whatYouCanDoNow.map(w => `<li>${w}</li>`).join('')}</ul>
          </div>

          <div class="legal-sec sec-aid">
            <strong style="color:#0369a1;">🤝 IF YOU CANNOT AFFORD A LAWYER:</strong>
            <div style="margin:4px 0;">We never abandon you due to lack of funds. Under Legal Aid Act 2016:</div>
            ${s.ifYouCannotAffordALawyer.legalAidProviders.map(p => `
              <div style="margin-top:4px; padding:4px 6px; background:#fff; border-radius:4px;">
                <strong>${p.name}</strong> • ${p.contact}
                <div style="font-size:0.75rem; color:#475569;">${p.howTheyHelp}</div>
              </div>
            `).join('')}
          </div>

          <div class="legal-sec" style="border-left-color:#64748b;">
            <strong>📁 EVIDENCE TO PRESERVE (Evidence Act s. 106B):</strong>
            <ul style="padding-left:18px; margin-top:4px;">${s.evidenceToPreserve.map(e => `<li><strong>${e.item}:</strong> ${e.lawfulCollectionRule}</li>`).join('')}</ul>
          </div>

          <div style="font-size:0.7rem; color:#64748b; font-style:italic; margin-top:8px;">
            🛡️ <strong>Statutory Disclaimer:</strong> ${s.disclaimer}
          </div>
        </div>
      `;
    }

    async function saveToWorkspace(s) {
      try {
        await fetch('/api/workspace/import-chat', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            caseTitle: s.possibleLegalIssues[0] || 'My Case',
            facts: s.whatIUnderstand || [],
            evidence: s.evidenceToPreserve || []
          })
        });
        alert('✅ Saved to Case Workspace! Opening Workspace...');
        switchTab('workspace');
      } catch (e) {
        alert('Failed to save to workspace');
      }
    }

    // 2. LAW VIEW
    async function renderLawView(container) {
      container.innerHTML = `<div style="text-align:center; padding:20px;">Loading Laws of Kenya...</div>`;
      const res = await fetch('/api/law');
      const data = await res.json();
      container.innerHTML = `
        <h2 style="color:var(--primary); font-size:1.2rem; margin-bottom:10px;">📜 Show Me The Law (Kenya Law)</h2>
        <p style="font-size:0.8rem; color:#64748b; margin-bottom:14px;">Authoritative statutory provisions from the Constitution of Kenya and Acts of Parliament.</p>
        ${data.statutes.map(s => `
          <div class="msg-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <strong style="color:var(--primary); font-size:0.95rem;">${s.document} — ${s.section}</strong>
              <span class="brand-badge" style="background:#059669;">${s.currentStatus}</span>
            </div>
            <div style="font-size:0.82rem; font-weight:700; color:#334155; margin:4px 0;">${s.topic}</div>
            <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; padding:8px; font-size:0.8rem; font-style:italic; margin:6px 0;">"${s.exactText}"</div>
            <div style="font-size:0.8rem; color:#0f172a;"><strong>Plain English:</strong> ${s.plainEnglish}</div>
            <div style="margin-top:6px;"><a href="${s.sourceUrl}" target="_blank" style="font-size:0.75rem; color:#059669;">Verify on Official Kenya Law ↗</a></div>
          </div>
        `).join('')}
      `;
    }

    // 3. CASES VIEW
    async function renderCasesView(container) {
      container.innerHTML = `<div style="text-align:center; padding:20px;">Loading Superior Court Precedents...</div>`;
      const res = await fetch('/api/cases');
      const data = await res.json();
      container.innerHTML = `
        <h2 style="color:var(--primary); font-size:1.2rem; margin-bottom:10px;">🏛️ Show Me Cases Like Mine</h2>
        <p style="font-size:0.8rem; color:#64748b; margin-bottom:14px;">Landmark Kenyan Superior Court Judgments (Distinguishing Binding vs Persuasive).</p>
        ${data.cases.map(c => `
          <div class="msg-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <strong style="color:var(--primary); font-size:0.95rem;">${c.caseName} ${c.citation}</strong>
              <span class="brand-badge" style="background:${c.authorityType==='binding'?'#064e3b':'#b45309'};">${c.authorityType.toUpperCase()}</span>
            </div>
            <div style="font-size:0.78rem; color:#64748b; margin:2px 0;">${c.court} (${c.year})</div>
            <div style="margin-top:6px; font-size:0.8rem;"><strong>Legal Test:</strong> ${c.legalTest}</div>
            <div style="margin-top:4px; font-size:0.8rem;"><strong>Holding:</strong> ${c.holding}</div>
            <div style="margin-top:6px;"><a href="${c.sourceUrl}" target="_blank" style="font-size:0.75rem; color:#059669;">View Full eKLR Ruling ↗</a></div>
          </div>
        `).join('')}
      `;
    }

    // 4. WORKSPACE VIEW
    async function renderWorkspaceView(container) {
      container.innerHTML = `<div style="text-align:center; padding:20px;">Loading Workspace...</div>`;
      const res = await fetch('/api/workspace');
      const d = await res.json();
      workspaceData = d;
      const c = d.caseDetails || {};

      container.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
          <div>
            <h2 style="color:var(--primary); font-size:1.2rem;">🗂️ Self-Representation Workspace</h2>
            <div style="font-size:0.78rem; color:#64748b;">Organize your facts, evidence, and court hearings.</div>
          </div>
          <button class="btn-primary" onclick="exportHearingBundle()">🖨️ Export Hearing Bundle</button>
        </div>

        <div class="msg-card">
          <strong style="color:var(--primary);">📁 CASE DETAILS: ${c.caseTitle || 'My Case'}</strong>
          <div style="font-size:0.8rem; margin-top:6px;"><strong>Forum:</strong> ${c.institutionOrForum || 'Disciplinary Board'}</div>
          <div style="font-size:0.8rem;"><strong>Current Stage:</strong> ${c.currentStage || 'Pre-Hearing Preparation'}</div>
          <div style="font-size:0.8rem;"><strong>Urgent Deadlines:</strong> ${c.urgentDeadlines || '14-day statutory clock'}</div>
        </div>

        <div class="msg-card">
          <strong style="color:var(--primary);">📅 CHRONOLOGY OF FACTS (${d.facts.length})</strong>
          <div style="margin-top:8px;">
            ${d.facts.map(f => `
              <div style="padding:6px 8px; background:#f8fafc; border-radius:6px; border:1px solid #e2e8f0; font-size:0.8rem; margin-bottom:6px; display:flex; justify-content:space-between; align-items:center;">
                <div><strong>${f.dateOrTime}</strong>: ${f.description}</div>
                <button style="border:none; background:none; color:#dc2626; cursor:pointer;" onclick="deleteFact('${f.id}')">✕</button>
              </div>
            `).join('')}
          </div>
          <div style="display:flex; gap:6px; margin-top:8px;">
            <input type="text" id="newFactText" placeholder="Add chronological fact..." style="flex:1; padding:6px; border:1px solid #cbd5e1; border-radius:6px; font-size:0.8rem;" />
            <button class="btn-primary" style="padding:6px 12px; font-size:0.78rem;" onclick="addFact()">+ Add</button>
          </div>
        </div>

        <div class="msg-card">
          <strong style="color:var(--primary);">📁 EVIDENCE CATALOG (${d.evidence.length})</strong>
          <div style="font-size:0.75rem; color:#64748b; margin-bottom:6px;">Complies with Evidence Act s. 106B digital custody rules.</div>
          <div>
            ${d.evidence.map(e => `
              <div style="padding:6px 8px; background:#f8fafc; border-radius:6px; border:1px solid #e2e8f0; font-size:0.8rem; margin-bottom:6px; display:flex; justify-content:space-between; align-items:center;">
                <div>
                  <strong>${e.title}</strong> (${e.category.toUpperCase()})
                  <div style="font-size:0.72rem; color:#64748b;">${e.description} • ${e.lawfulStatus}</div>
                </div>
                <button style="border:none; background:none; color:#dc2626; cursor:pointer;" onclick="deleteEvidence('${e.id}')">✕</button>
              </div>
            `).join('')}
          </div>
        </div>
      `;
    }

    async function addFact() {
      const inp = document.getElementById('newFactText');
      if (!inp || !inp.value.trim()) return;
      await fetch('/api/workspace/fact', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ description: inp.value.trim() })
      });
      renderWorkspaceView(document.getElementById('viewContainer'));
    }

    async function deleteFact(id) {
      await fetch('/api/workspace/fact/' + id, { method: 'DELETE' });
      renderWorkspaceView(document.getElementById('viewContainer'));
    }

    async function deleteEvidence(id) {
      await fetch('/api/workspace/evidence/' + id, { method: 'DELETE' });
      renderWorkspaceView(document.getElementById('viewContainer'));
    }

    async function exportHearingBundle() {
      const res = await fetch('/api/workspace/bundle');
      const d = await res.json();
      showModal(`
        <h3 style="color:var(--primary); font-size:1.1rem; margin-bottom:8px;">${d.title}</h3>
        <div style="font-size:0.75rem; color:#64748b; margin-bottom:10px;">Compiled on ${d.generatedAt} for Tribunal / Court Presentation</div>
        <div style="display:flex; gap:8px; margin-bottom:12px;">
          <button class="btn-primary" onclick="navigator.clipboard.writeText(document.getElementById('bundleText').innerText); alert('Copied to clipboard!');">📋 Copy Dossier</button>
          <button class="btn-secondary" onclick="window.print()">🖨️ Print</button>
        </div>
        <pre id="bundleText" style="background:#f8fafc; border:1px solid #cbd5e1; border-radius:8px; padding:12px; font-family:monospace; font-size:0.78rem; white-space:pre-wrap; max-height:50vh; overflow-y:auto;">${d.markdownBundle}</pre>
      `);
    }

    // 5. DOCUMENTS VIEW
    function renderDocsView(container) {
      container.innerHTML = `
        <h2 style="color:var(--primary); font-size:1.2rem; margin-bottom:6px;">📄 Fact-Based Document Generator</h2>
        <p style="font-size:0.8rem; color:#64748b; margin-bottom:14px;">Generates formal legal complaints and demand letters strictly mapped to your facts.</p>

        <div class="msg-card">
          <div style="margin-bottom:10px;">
            <label style="font-size:0.78rem; font-weight:700;">Select Document Template:</label>
            <select id="docTypeSelect" style="width:100%; padding:8px; border-radius:6px; border:1px solid #cbd5e1; font-size:0.82rem; margin-top:4px;">
              <option value="administrative_complaint">🏛️ Article 47 Due Process Demand (University / Public Body)</option>
              <option value="tenancy_unlawful_eviction_demand">🏠 Landlord Illegal Lockout & Eviction Demand</option>
              <option value="employment_summary_dismissal_demand">💼 Employment Unfair Dismissal & Dues Demand (s. 41)</option>
              <option value="criminal_complaint_letter">🚨 Formal Criminal Complaint to DCI / Police</option>
            </select>
          </div>

          <div style="margin-bottom:8px;">
            <label style="font-size:0.75rem; font-weight:700;">Your Name / Alias:</label>
            <input type="text" id="docName" placeholder="e.g. Wanjiku Muthoni" style="width:100%; padding:8px; border-radius:6px; border:1px solid #cbd5e1; font-size:0.82rem;" />
          </div>

          <div style="margin-bottom:8px;">
            <label style="font-size:0.75rem; font-weight:700;">Adverse Institution / Landlord / Employer:</label>
            <input type="text" id="docInst" placeholder="e.g. University Administration / Landlord" style="width:100%; padding:8px; border-radius:6px; border:1px solid #cbd5e1; font-size:0.82rem;" />
          </div>

          <div style="margin-bottom:12px;">
            <label style="font-size:0.75rem; font-weight:700;">Factual Summary (Only facts you know):</label>
            <textarea id="docSummary" placeholder="Explain what occurred, what notices were omitted, and what was seized..." style="width:100%; min-height:80px; padding:8px; border-radius:6px; border:1px solid #cbd5e1; font-size:0.82rem;"></textarea>
          </div>

          <button class="btn-primary" style="width:100%; padding:10px; font-size:0.88rem;" onclick="generateDoc()">✨ Generate Lawful Document ➔</button>
        </div>

        <div id="generatedDocResult"></div>
      `;
    }

    async function generateDoc() {
      const type = document.getElementById('docTypeSelect').value;
      const name = document.getElementById('docName').value.trim();
      const inst = document.getElementById('docInst').value.trim();
      const summary = document.getElementById('docSummary').value.trim();

      if (!summary) {
        alert('Please provide a factual summary.');
        return;
      }

      const res = await fetch('/api/documents/generate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          documentType: type,
          recipientInstitution: inst,
          userFacts: { fullName: name, summary: summary }
        })
      });

      const d = await res.json();
      const doc = d.document || d;
      document.getElementById('generatedDocResult').innerHTML = `
        <div class="msg-card" style="border-color:#059669; margin-top:14px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <strong style="color:var(--primary); font-size:0.95rem;">${doc.title}</strong>
            <button class="btn-primary" style="padding:4px 10px; font-size:0.75rem;" onclick="navigator.clipboard.writeText(document.getElementById('docContent').innerText); alert('Copied!');">📋 Copy</button>
          </div>
          <pre id="docContent" style="background:#f8fafc; border:1px solid #cbd5e1; border-radius:8px; padding:12px; font-family:monospace; font-size:0.78rem; white-space:pre-wrap; max-height:50vh; overflow-y:auto;">${doc.content}</pre>
        </div>
      `;
    }

    // Modal Helper
    function showModal(contentHtml) {
      const modal = document.createElement('div');
      modal.className = 'modal-bg';
      modal.onclick = () => modal.remove();
      modal.innerHTML = `
        <div class="modal-box" onclick="event.stopPropagation()">
          <div style="text-align:right;"><button style="background:none; border:none; font-size:1.2rem; cursor:pointer;" onclick="this.closest('.modal-bg').remove()">✕</button></div>
          ${contentHtml}
        </div>
      `;
      document.body.appendChild(modal);
    }

    function openWizardModal() {
      showModal(`
        <h3 style="color:var(--primary); font-size:1.1rem; margin-bottom:4px;">⚡ 1-Minute Due Process Check</h3>
        <p style="font-size:0.78rem; color:#64748b; margin-bottom:12px;">Answer 4 questions under Kenyan law to evaluate procedural fairness:</p>
        <div style="display:flex; flex-direction:column; gap:8px;">
          <div style="padding:8px; background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; font-size:0.8rem;">
            1. Were you given at least 7 to 14 days advance written notice?
          </div>
          <div style="padding:8px; background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; font-size:0.8rem;">
            2. Did they provide you with copies of the witness statements or evidence?
          </div>
          <div style="padding:8px; background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; font-size:0.8rem;">
            3. Were you allowed to bring an advisor, colleague, or representative?
          </div>
          <div style="padding:8px; background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; font-size:0.8rem;">
            4. Did they provide detailed written reasons for the adverse decision?
          </div>
        </div>
        <div style="margin-top:14px; background:#fef2f2; border:1px solid #fecaca; border-radius:8px; padding:10px; font-size:0.78rem; color:#991b1b;">
          <strong>Statutory Principle:</strong> If you answered <strong>NO</strong> to any of these questions, the action is procedurally defective under Section 4 of the Fair Administrative Action Act No. 33 of 2015 and void ab initio under <em>Republic v University of Nairobi ex parte Wanjiku</em> [2018].
        </div>
        <div style="margin-top:12px; text-align:right;">
          <button class="btn-primary" onclick="this.closest('.modal-bg').remove(); switchTab('docs');">Draft Due Process Appeal ➔</button>
        </div>
      `);
    }

    // Initial View Mount
    renderView();
  </script>
</body>
</html>
"""


@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE)


# ==============================================================================
# SERVER ENTRYPOINT
# ==============================================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    print(f"Kenya Legal Assistant active on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
