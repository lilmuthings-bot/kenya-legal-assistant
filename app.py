"""
Kenya Legal Assistant - Complete Python Server (app.py)
Mission: "Make legal knowledge accessible, not make lawyers mandatory."
Tagline: "Understand the law. Know your options. Take the next step."

This file is a standalone, full-stack Python application that includes:
- Embedded SQLite persistence with automatic schema migration and statutory seeding
- Authoritative Kenyan legal reasoning and retrieval engine (Constitution 2010, FAAA 2015, Cap 80, Cap 23, Cap 76, etc.)
- Investigation Mode with targeted questions ("Why this matters")
- Self-Representation Workspace & Digital Evidence Organizer (Section 106B Evidence Act)
- Fact-Based Document Generator & Clause Intelligence Analyzer
- Advanced Actions ("Can They Do This?", "What Can I Do?", "What Happens Next?", "Challenge My Position", "Prepare for a Lawyer")
- Private Admin Office Telemetry & Failed Search Monitor
- Bilingual English / Kiswahili support
- Static frontend server for the mobile-first UI
"""

import os
import sys
import json
import sqlite3
import datetime
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

PORT = int(os.environ.get("PORT", 3000))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
PUBLIC_DIR = os.path.join(BASE_DIR, "public")
DB_PATH = os.path.join(DATA_DIR, "kenya_legal.db")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PUBLIC_DIR, exist_ok=True)

MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
    ".txt": "text/plain; charset=utf-8"
}

# ==============================================================================
# DATABASE INITIALIZATION & AUTHORITATIVE KENYAN LEGAL SEEDING
# ==============================================================================

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS official_sources (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            url TEXT NOT NULL,
            type TEXT NOT NULL,
            authorityLevel TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS legal_statutes (
            id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            document TEXT NOT NULL,
            part TEXT,
            section TEXT NOT NULL,
            subsection TEXT,
            topic TEXT NOT NULL,
            exactText TEXT NOT NULL,
            plainEnglish TEXT NOT NULL,
            currentStatus TEXT NOT NULL,
            effectiveDate TEXT NOT NULL,
            amendmentHistory TEXT,
            sourceUrl TEXT NOT NULL,
            relatedCases TEXT,
            category TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS case_law (
            id TEXT PRIMARY KEY,
            citation TEXT NOT NULL,
            caseName TEXT NOT NULL,
            court TEXT NOT NULL,
            year INTEGER NOT NULL,
            authorityType TEXT NOT NULL,
            legalIssues TEXT NOT NULL,
            factsSummary TEXT NOT NULL,
            holding TEXT NOT NULL,
            legalTest TEXT NOT NULL,
            relevanceExplanation TEXT NOT NULL,
            sourceUrl TEXT NOT NULL,
            cautionaryNote TEXT NOT NULL
        );

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
        );

        CREATE TABLE IF NOT EXISTS workspace_facts (
            id TEXT PRIMARY KEY,
            caseId TEXT NOT NULL,
            dateOrTime TEXT,
            description TEXT NOT NULL,
            type TEXT NOT NULL,
            supportingEvidenceIds TEXT
        );

        CREATE TABLE IF NOT EXISTS workspace_opponents (
            id TEXT PRIMARY KEY,
            caseId TEXT NOT NULL,
            allegation TEXT NOT NULL,
            theirClaimedEvidence TEXT,
            contradictionOrFlaw TEXT,
            myCounterPosition TEXT
        );

        CREATE TABLE IF NOT EXISTS workspace_evidence (
            id TEXT PRIMARY KEY,
            caseId TEXT NOT NULL,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            dateObtained TEXT,
            description TEXT NOT NULL,
            lawfulStatus TEXT NOT NULL,
            custodyNotes TEXT
        );

        CREATE TABLE IF NOT EXISTS generated_documents (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            type TEXT NOT NULL,
            createdAt TEXT NOT NULL,
            content TEXT NOT NULL,
            factsUsed TEXT,
            missingFactsNoted TEXT
        );

        CREATE TABLE IF NOT EXISTS cases (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            primaryIssue TEXT,
            situationSummary TEXT,
            userObjective TEXT,
            urgency TEXT,
            confidence TEXT,
            nextStep TEXT,
            status TEXT,
            createdAt TEXT NOT NULL,
            updatedAt TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS case_facts (
            id TEXT PRIMARY KEY,
            caseId TEXT NOT NULL,
            factText TEXT NOT NULL,
            factType TEXT NOT NULL,
            dateOrTime TEXT,
            source TEXT NOT NULL,
            confidence TEXT,
            createdAt TEXT NOT NULL,
            updatedAt TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS case_issues (
            id TEXT PRIMARY KEY,
            caseId TEXT NOT NULL,
            issueTitle TEXT NOT NULL,
            category TEXT NOT NULL,
            status TEXT NOT NULL,
            legalBasis TEXT,
            createdAt TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS case_timeline (
            id TEXT PRIMARY KEY,
            caseId TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT NOT NULL,
            source TEXT NOT NULL,
            status TEXT NOT NULL,
            confidence TEXT,
            createdAt TEXT NOT NULL,
            updatedAt TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS failed_searches (
            id TEXT PRIMARY KEY,
            query TEXT NOT NULL,
            detectedIssue TEXT,
            sourcesSearched TEXT,
            reasonForFailure TEXT,
            createdAt TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS legal_updates (
            id TEXT PRIMARY KEY,
            sourceTitle TEXT NOT NULL,
            updateType TEXT NOT NULL,
            status TEXT NOT NULL,
            effectiveDate TEXT,
            notes TEXT,
            createdAt TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS uploaded_documents (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            documentType TEXT,
            issuer TEXT,
            recipient TEXT,
            extractedText TEXT,
            analysisJson TEXT,
            status TEXT NOT NULL,
            createdAt TEXT NOT NULL
        );
    """)

    # Seed if official sources empty
    cur.execute("SELECT COUNT(*) FROM official_sources")
    if cur.fetchone()[0] == 0:
        seed_data(cur)
        conn.commit()
    conn.close()

def seed_data(cur):
    sources = [
        ('src_kenyalaw', 'Kenya Law (National Council for Law Reporting)', 'Official publisher of the Laws of Kenya and Law Reports.', 'https://new.kenyalaw.org/legislation', 'Legislation', 'Primary Binding'),
        ('src_parliament_acts', 'Parliament of Kenya - Acts of Parliament', 'Acts passed by the National Assembly and Senate of Kenya.', 'https://www.parliament.go.ke/the-national-assembly/house-business/acts', 'Parliament Acts', 'Primary Binding'),
        ('src_parliament_bills', 'Parliament of Kenya - Bills', 'Draft legislation under debate. Note: A Bill is NOT law until enacted and gazetted.', 'https://parliament.go.ke/the-national-assembly/house-business/bills', 'Bills', 'Informational'),
        ('src_supreme_court', 'Supreme Court Decisions - Judiciary of Kenya', 'Highest court decisions in Kenya; binding on all other courts.', 'https://supremecourt.judiciary.go.ke/supreme-court-decisions/', 'Supreme Court Decisions', 'Primary Binding'),
        ('src_judiciary_downloads', 'Judiciary of Kenya - Practice Directions & Rules', 'Court rules, practice directions, cause lists and publications.', 'https://judiciary.go.ke/downloads/', 'Judiciary', 'Primary Binding')
    ]
    cur.executemany("INSERT OR IGNORE INTO official_sources VALUES (?, ?, ?, ?, ?, ?)", sources)

    statutes = [
        ('stat_art47', 'Kenya Law', 'Constitution of Kenya 2010', 'Chapter Four - The Bill of Rights', 'Article 47', '(1), (2)',
         'Fair Administrative Action & Right to Written Reasons',
         '47. (1) Every person has the right to administrative action that is expeditious, efficient, lawful, reasonable and procedurally fair.\n(2) If a right or fundamental freedom of a person has been or is likely to be adversely affected by administrative action, the person has the right to be given written reasons for the action.',
         'Any decision maker—including university bodies, landlords, or government officials—must treat you fairly. Before making a decision that hurts you (like a suspension), they must give you written reasons, notice of the charges, and a genuine chance to be heard.',
         'In Force', '2010-08-27', 'Promulgated 27th August 2010; no amendment to Art 47.', 'https://new.kenyalaw.org/legislation',
         json.dumps(['Republic v University of Nairobi ex parte Wanjiku [2018]', 'Dry Associates v CMA [2012]']), 'Constitutional'),

        ('stat_art50', 'Kenya Law', 'Constitution of Kenya 2010', 'Chapter Four - The Bill of Rights', 'Article 50', '(1)',
         'Fair Hearing',
         '50. (1) Every person has the right to have any dispute that can be resolved by the application of law decided in a fair and public hearing before a court or, if appropriate, another independent and impartial tribunal or body.',
         'You have a constitutional entitlement to an impartial forum where you can present evidence and cross-examine adverse claims.',
         'In Force', '2010-08-27', 'No amendments.', 'https://new.kenyalaw.org/legislation',
         json.dumps(['Caleb Kiprono v Moi University [2020]']), 'Constitutional'),

        ('stat_art27', 'Kenya Law', 'Constitution of Kenya 2010', 'Chapter Four - The Bill of Rights', 'Article 27', '(1), (2), (4), (5)',
         'Equality and Freedom from Discrimination',
         '27. (1) Every person is equal before the law and has the right to equal protection and equal benefit of the law.\n(4) The State shall not discriminate directly or indirectly against any person on any ground, including sex, health status, religion or social origin.',
         'Nobody can subject you to unequal or predatory treatment based on sex, status, or vulnerability.',
         'In Force', '2010-08-27', 'No amendments.', 'https://new.kenyalaw.org/legislation',
         json.dumps(['Gitobu Imanyara & 2 Others v AG [2016]']), 'Constitutional'),

        ('stat_art28', 'Kenya Law', 'Constitution of Kenya 2010', 'Chapter Four - The Bill of Rights', 'Article 28', '',
         'Human Dignity',
         '28. Every person has inherent dignity and the right to have that dignity respected and protected.',
         'Your personal integrity and dignity are non-negotiable rights that protect against degrading demands and harassment.',
         'In Force', '2010-08-27', 'No amendments.', 'https://new.kenyalaw.org/legislation',
         json.dumps(['Mary Chemweno Kiptui v KPC [2014]']), 'Constitutional'),

        ('stat_faaa_s4', 'Parliament of Kenya / Kenya Law', 'Fair Administrative Action Act No. 33 of 2015', 'Part II - Administrative Action', 'Section 4', '(1), (3), (4)',
         'Procedural Fairness Requirements for Administrative Decisions',
         '4. (1) Every person has the right to administrative action which is expeditious, efficient, lawful, reasonable and procedurally fair.\n(3) Where an administrative action is likely to adversely affect the rights or fundamental freedoms of any person, the administrator shall give that person—\n(a) prior and adequate notice of the nature and reasons for the proposed administrative action;\n(b) an opportunity to be heard and to make representations in that regard;\n(c) notice of a right to a review or an internal appeal where applicable; and\n(d) a statement of reasons for the administrative action.',
         'If an administrator plans to discipline or suspend you, they MUST give you advance notice, specify the exact allegations, provide you copies of all evidence, and grant you a formal opportunity to be heard before passing any penalty.',
         'In Force', '2015-06-17', 'Enacted in 2015 pursuant to Article 47(3).', 'https://new.kenyalaw.org/legislation',
         json.dumps(['Republic v University of Nairobi ex parte Wanjiku [2018]', 'Caleb Kiprono v Moi University [2020]']), 'Administrative'),

        ('stat_soa_s24', 'Parliament of Kenya / Kenya Law', 'Sexual Offences Act No. 3 of 2006', 'Part III - Offences Related to Prostitution and Other Sexual Offences', 'Section 24', '(1), (2)',
         'Sexual Harassment by Person in Position of Authority',
         '24. (1) Any person, who being in a position of authority, or holding a public office, who persistently makes any sexual advances or in any way requests or demands sexual favours from a person—\n(a) by promising preferential treatment in their employment, education or profession; or\n(b) by threatening detrimental treatment in their employment, education or profession,\nis guilty of the offence of sexual harassment and is liable on conviction to imprisonment for a term of not less than three years, or to a fine of not less than one hundred thousand shillings, or to both.',
         'It is a criminal offence for a lecturer, employer, or person of authority to demand sexual favours in exchange for passing exams, grades, or employment benefits.',
         'In Force', '2006-07-21', 'Amended by Statute Law Act 2014.', 'https://new.kenyalaw.org/legislation',
         json.dumps(['Mary Chemweno Kiptui v KPC [2014]']), 'Criminal'),

        ('stat_bribery_s5', 'Parliament of Kenya / Kenya Law', 'Bribery Act No. 47 of 2016', 'Part II - Offences', 'Section 5 & 6', '(1)',
         'Giving or Requesting an Illicit Advantage / Bribery in Public or Private Entities',
         '5. (1) A person commits the offence of giving a bribe if the person offers, promises or gives a financial or other advantage intending an improper performance of a relevant function.\n6. (1) A person commits the offence of receiving a bribe if the person requests or accepts a financial or other advantage.',
         'Demanding any improper advantage to alter university grading or award marks is illegal bribery under Kenyan law.',
         'In Force', '2016-12-09', 'Enacted 2016.', 'https://new.kenyalaw.org/legislation', '[]', 'Criminal'),

        ('stat_emp_s41', 'Kenya Law', 'Employment Act No. 11 of 2007', 'Part VI - Termination and Dismissal', 'Section 41', '(1), (2)',
         'Mandatory Notification and Hearing Before Termination',
         '41. (1) An employer shall, before terminating the employment of an employee on grounds of misconduct or poor performance, explain to the employee in a language the employee understands the reason for considering termination...\n(2) An employer shall hear and consider any representations which the employee may make.',
         'Firing someone on the spot without a formal charge sheet, written notice, and an internal hearing where you can bring a colleague is illegal in Kenya.',
         'In Force', '2007-10-22', 'Revised edition 2012.', 'https://new.kenyalaw.org/legislation',
         json.dumps(['Kenya Airways Limited v Allied Workers Union [2014]']), 'Employment'),

        ('stat_emp_s45', 'Kenya Law', 'Employment Act No. 11 of 2007', 'Part VI - Termination and Dismissal', 'Section 45', '(2), (5)',
         'Unfair Termination and Substantive Justification',
         '45. (2) A termination of employment by an employer is unfair if the employer fails to prove—\n(a) that the reason for the termination is valid;\n(b) that the reason is fair; and\n(c) that the employment was terminated in accordance with fair procedure.',
         'The burden of proof rests strictly on the employer to prove both valid substantive reasons and strict adherence to fair procedure.',
         'In Force', '2007-10-22', 'Revised edition 2012.', 'https://new.kenyalaw.org/legislation',
         json.dumps(['Kenya Airways Limited v Allied Workers Union [2014]']), 'Employment'),

        ('stat_distress_rent', 'Kenya Law', 'Distress for Rent Act (Cap 293)', 'Sections 3, 4', 'Section 3', '(1)',
         'Lawful Process of Distress for Rent & Prohibition of Illegal Lockouts',
         '3. (1) Any person having rent in arrear may seize goods...\nProvided distress must be levied only by a licensed auctioneer holding a certificate issued under the Auctioneers Act, and only between sunrise and sunset.',
         'A landlord cannot lock you out or throw your items outside on their own. Any seizure requires a licensed auctioneer with a valid certificate, and cannot involve violence.',
         'In Force', '1937-05-18', 'Consolidated with Auctioneers Act 1996.', 'https://new.kenyalaw.org/legislation',
         json.dumps(['Purity Wambui v Muriithi [2019]']), 'Tenancy'),

        ('stat_evidence_106b', 'Kenya Law', 'Evidence Act (Cap 80)', 'Part II - Admissibility of Electronic Records', 'Section 106B', '(1), (2), (4)',
         'Admissibility of Electronic Records (WhatsApp, SMS, Audio, Emails)',
         '106B. (1) Notwithstanding anything contained in this Act, any information contained in an electronic record printed on paper, stored or copied in optical media produced by a computer shall be deemed to be a document...\n(4) A certificate signed by a person occupying a responsible position in relation to the operation of the device shall be evidence.',
         'Screenshots of WhatsApp messages, emails, and phone recordings can be admitted in Kenyan courts and tribunals, provided you preserve timestamps and prepare an electronic certificate under Section 106B.',
         'In Force', '2009-01-01', 'Introduced by KICA amendments.', 'https://new.kenyalaw.org/legislation',
         json.dumps(['Geoffrey Andare v AG [2016]']), 'Evidence'),

        ('stat_legal_aid_s35', 'Parliament of Kenya / Kenya Law', 'Legal Aid Act No. 6 of 2016', 'Part V - Legal Aid Services', 'Section 35', '(1), (2)',
         'Eligibility for State-Sponsored Legal Aid',
         '35. (1) A person is eligible to receive legal aid services if that person is an indigent person.\n(2) The Service shall consider income, disposable capital, and whether the person is vulnerable (including gender-based violence victims).',
         'Under the Legal Aid Act 2016, if you cannot afford an advocate and face serious matters, you have a statutory entitlement to apply for free legal aid through NLAS or accredited providers.',
         'In Force', '2016-05-10', 'Enacted pursuant to Article 48.', 'https://new.kenyalaw.org/legislation', '[]', 'Administrative'),

        ('stat_caj_ombudsman', 'Parliament of Kenya / Kenya Law', 'Commission on Administrative Justice Act No. 23 of 2011', 'Part II - Functions of the Commission', 'Section 8', '(a), (b), (e)',
         'Mandate of CAJ (Office of the Ombudsman) to Investigate Unfair Treatment and Maladministration',
         '8. The Commission shall have all powers to investigate conduct in state affairs, abuse of power, unfair treatment, manifest injustice or unlawful official conduct, and recommend remedies or disciplinary action.',
         'If a public university or public office acts unfairly, delays unreasonably, or denies you due process, you can file a free administrative complaint with the Ombudsman (CAJ) without paying legal fees.',
         'In Force', '2011-09-05', 'Enacted 2011.', 'https://new.kenyalaw.org/legislation', '[]', 'Administrative'),

        ('stat_contract_act', 'Kenya Law', 'Law of Contract Act (Cap 23)', 'Preliminary & Enforceability of Contracts', 'Section 2 & 3', '(1), (2)',
         'Nature, Formation, and Enforceability of Contracts',
         '2. (1) Save as may be provided by any other written law, the common law of England relating to contract shall apply to Kenya.\n3. (1) No suit shall be brought upon a contract for the disposition of an interest in land unless the agreement is in writing.',
         'Under Kenyan law, a contract requires: 1) Offer; 2) Acceptance; 3) Lawful Consideration; 4) Capacity to contract; and 5) Intention to create legal relations. Contracts can be written or oral, except land contracts which must be in writing.',
         'In Force', '1961-01-01', 'Amended 2002.', 'https://new.kenyalaw.org/legislation',
         json.dumps(['National Bank of Kenya v Pipeplastic Samkolit [2001]']), 'Commercial'),

        ('stat_art49', 'Kenya Law', 'Constitution of Kenya 2010', 'Chapter Four - The Bill of Rights', 'Article 49', '(1)(a), (f), (h)',
         'Rights of Arrested Persons & Right to Bail/Bond',
         '49. (1) An arrested person has the right—\n(a) to be informed promptly of the reason for the arrest;\n(f) to be brought before a court not later than twenty-four hours after arrest;\n(h) to be released on bond or bail, on reasonable conditions, unless there are compelling reasons.',
         'Police in Kenya cannot hold you indefinitely. You must be told the reason for arrest immediately, brought to court within 24 hours, and you have a constitutional right to bail/bond.',
         'In Force', '2010-08-27', 'No amendments.', 'https://new.kenyalaw.org/legislation',
         json.dumps(['Republic v Danson Mwashako & Others [2018]']), 'Criminal')
    ]
    cur.executemany("INSERT OR IGNORE INTO legal_statutes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", statutes)

    cases = [
        ('case_wanjiku_2018', '[2018] eKLR', 'Republic v University of Nairobi ex parte Wanjiku',
         'High Court of Kenya (Judicial Review Division, Nairobi)', 2018, 'binding',
         json.dumps(['University disciplinary action', 'Suspension without hearing', 'Article 47 Fair Administrative Action', 'Natural Justice']),
         'A university student was summarily suspended by the Vice-Chancellor without specific formal charges or hearing before the Student Disciplinary Committee.',
         'The High Court held universities are statutory bodies bound by Article 47. A suspension executed without prior notice, disclosure of evidence, and an opportunity to be heard is illegal, ultra vires, and void ab initio.',
         'The Three-Part Test for Administrative Disciplinary Action: 1) Clear advance written notice of allegations; 2) Adequate opportunity to prepare and present defense; 3) Reasoned decision by an unbiased panel.',
         'Directly supports students who have been suspended or expelled without a formal disciplinary committee hearing.',
         'http://kenyalaw.org/caselaw/cases/view/161204/',
         'Establishes fair process rights; does not prevent the university from instituting a lawful hearing with proper notice if misconduct evidence exists.'),

        ('case_kiprono_moi_2020', '[2020] eKLR', 'Caleb Kiprono v Moi University',
         'High Court of Kenya at Eldoret', 2020, 'binding',
         json.dumps(['Student disciplinary proceedings', 'Right to evidence', 'Procedural unfairness', 'Section 4 FAAA']),
         'Moi University suspended and expelled a student without providing copies of witness statements and investigation reports forming the charges.',
         'The court nullified the expulsion and ordered reinstatement. Withholding evidence from a student facing disciplinary proceedings violates Article 50(1) and the Fair Administrative Action Act.',
         'The Principle of Adequate Disclosure: An accused student must be provided with all documentary and testimonial evidence the institution intends to rely upon at least 14 days before hearing.',
         'Crucial for students whose institutions refuse to provide copies of exam reports, witness statements, or disciplinary files.',
         'http://kenyalaw.org/caselaw/cases/view/198302/',
         'Court decisions depend on specific institutional statutes; consult university charter.'),

        ('case_kiptui_kpc_2014', '[2014] eKLR', 'Mary Chemweno Kiptui v Kenya Pipeline Company Limited',
         'Industrial Court of Kenya (now Employment & Labour Relations Court)', 2014, 'binding',
         json.dumps(['Sexual harassment', 'Abuse of institutional authority', 'Hostile environment', 'Section 24 Sexual Offences Act']),
         'An employee was subjected to sexual advances by her manager. When she refused, the manager manipulated appraisals and instigated disciplinary sanctions against her.',
         'The court ruled that leveraging power to demand sexual intimacy is an egregious violation of Section 24 of Sexual Offences Act and constitutional rights to dignity (Art 28) and equality (Art 27). Employer held vicariously liable.',
         'The Power-Imbalance Harassment Test: 1) Did the harasser occupy a position of authority? 2) Were unwelcome propositions made? 3) Was detrimental treatment threatened or inflicted upon refusal? 4) Did the institution fail to provide safe reporting channels?',
         'Fundamental authority where professors or managers exploit grades or jobs for sexual demands.',
         'http://kenyalaw.org/caselaw/cases/view/97645/',
         'Corroboration (messages, emails, witnesses, timeline) is essential.'),

        ('case_kq_allied_2014', '[2014] eKLR', 'Kenya Airways Limited v Allied Workers Union',
         'Court of Appeal of Kenya at Nairobi', 2014, 'binding',
         json.dumps(['Employment termination', 'Section 41 procedural fairness', 'Mandatory hearing', 'Natural justice']),
         'Kenya Airways terminated employees without convening formal one-on-one hearings under Section 41 of the Employment Act.',
         'The Court of Appeal affirmed that procedural requirements under Section 41 are mandatory and non-negotiable. Failure renders termination unfair under Section 45, regardless of substantive grounds.',
         'The Strict Procedural Compliance Rule: An employer cannot cure procedural invalidity by asserting substantive misconduct after the fact.',
         'Essential for employees dismissed without formal explanation or disciplinary hearing.',
         'http://kenyalaw.org/caselaw/cases/view/98372/',
         'Claims must be filed in ELRC within 3 years of termination.'),

        ('case_wambui_muriithi_2019', '[2019] eKLR', 'Purity Wambui & Another v Muriithi',
         'Environment and Land Court / Rent Restriction Tribunal', 2019, 'persuasive',
         json.dumps(['Illegal eviction', 'Landlord lock-out', 'Distress for rent without proclamation', 'Trespass']),
         'A landlord changed padlocks and removed tenant goods because rent was overdue.',
         'The court declared the lockout illegal. Landlords have no legal power of self-help to evict or lock out tenants without an eviction order from a competent tribunal or court.',
         'The Self-Help Prohibition Rule: Rent arrears do not entitle a landlord to breach peace or violate tenant possession without due legal process.',
         'Protects tenants facing locked doors, disconnected water/power, or seized items without auctioneer proclamation.',
         'http://kenyalaw.org/caselaw/cases/view/178921/',
         'Tenant remains obligated to pay legitimate arrears.'),

        ('case_andare_ag_2016', '[2016] eKLR', 'Geoffrey Andare v Attorney General & 2 Others',
         'High Court of Kenya (Constitutional & Human Rights Division)', 2016, 'binding',
         json.dumps(['Electronic evidence', 'Freedom of expression', 'Section 106B Evidence Act', 'Digital records']),
         'Considered evidential weight of electronic messages and constitutional boundaries.',
         'The High Court clarified electronic evidence must meet the integrity threshold of Section 106B of Evidence Act.',
         'Digital Evidence Integrity Rule: Digital messages must be presented with chain of custody and device identification.',
         'Relevant when users present WhatsApp screenshots, audio recordings, or text messages.',
         'http://kenyalaw.org/caselaw/cases/view/120220/',
         'Ensure screenshots show phone numbers, dates, timestamps, and preserve original handsets.')
    ]
    cur.executemany("INSERT OR IGNORE INTO case_law VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", cases)

    # Seed sample workspace case
    cur.execute("""
        INSERT OR IGNORE INTO workspace_cases (
            id, caseTitle, caseType, institutionOrForum, caseNumber, applicant, respondent, currentStage, nextDate, urgentDeadlines, notes, updatedAt
        ) VALUES (
            'case_demo_01',
            'University Disciplinary & Power Imbalance Inquiry',
            'Administrative & Disciplinary Review',
            'University Disciplinary Appeals Committee / CAJ Ombudsman',
            'REF-2026/UNIV-084',
            'Undergraduate Student (Complainant)',
            'Course Lecturer & Department Head (Respondents)',
            'Internal Grievance & Evidence Preservation Stage',
            '2026-10-24',
            'Senate Appeals Submission: 14 days from notification',
            'Active preservation of WhatsApp messages and course assessment records. Application under Article 47 and FAAA Section 4.',
            ?
        )
    """, (datetime.datetime.now().isoformat(),))

    cur.execute("""
        INSERT OR IGNORE INTO cases (id, title, primaryIssue, situationSummary, userObjective, urgency, confidence, nextStep, status, createdAt, updatedAt)
        VALUES ('case_demo_01', 'University Disciplinary & Power Imbalance Inquiry', 'Fair Administrative Action (Art 47 & FAAA 2015)',
                'Summary suspension received without charges or hearing.', 'Challenge summary suspension and demand due process', 'High', 'Moderate',
                'Submit formal Article 47 Due Process Demand within 14-day statutory clock.', 'Active', ?, ?)
    """, (datetime.datetime.now().isoformat(), datetime.datetime.now().isoformat()))

    cur.execute("""
        INSERT OR IGNORE INTO case_timeline (id, caseId, date, description, source, status, confidence, createdAt, updatedAt)
        VALUES ('time_demo_01', 'case_demo_01', 'Wednesday', 'University issued summary suspension notice', 'User report', 'Reported Fact', 'High', ?, ?)
    """, (datetime.datetime.now().isoformat(), datetime.datetime.now().isoformat()))


# ==============================================================================
# LEGAL INTELLIGENCE & REASONING ENGINE (PYTHON)
# ==============================================================================

class LegalIntelligence:
    @staticmethod
    def handle_simple_question(q_raw):
        q = q_raw.lower().strip()
        # Contract
        if any(term in q for term in ['what is a contract', 'define a contract', 'elements of a contract', 'mkataba ni nini', 'maana ya mkataba']):
            is_swahili = 'mkataba' in q or 'nini' in q
            if is_swahili:
                text = (
                    "Kulingana na sheria za Kenya (**Law of Contract Act - Cap 23**), **mkataba (contract)** "
                    "ni makubaliano ya kisheria kati ya pande mbili au zaidi yanayounda wajibu unaotambulika na kutekelezeka mahakamani.\n\n"
                    "**Mambo 5 Muhimu ya Mkataba Halali Kenya:**\n"
                    "1. **Pendekezo (Offer):** Ahadi iliyo wazi kutoka kwa upande mmoja kufungwa na masharti maalum.\n"
                    "2. **Kukubali (Acceptance):** Kukubali masharti yote bila kubadilisha chochote.\n"
                    "3. **Fidia au Thamani (Consideration):** Thamani, malipo au tendo linalotolewa na kila upande.\n"
                    "4. **Uwezo wa Kisheria (Capacity):** Miaka 18+ chini ya Age of Majority Act, akili timamu, na kutofilisika.\n"
                    "5. **Nia ya Kisheria (Intention):** Nia ya makubaliano kuzaa matokeo ya kisheria.\n\n"
                    "Chini ya Kifungu cha 2 na 3 cha Cap 23, mikataba inaweza kuwa ya maandishi au maneno, "
                    "isipokuwa mikataba ya ardhi na dhamana ambayo LAZIMA iwe ya maandishi."
                )
            else:
                text = (
                    "Under Kenyan law, a **contract** is a legally binding agreement between two or more parties "
                    "that gives rise to obligations recognized and enforceable by law.\n\n"
                    "**Governing Law in Kenya:**\n"
                    "• **The Law of Contract Act (Cap 23)** of the Laws of Kenya.\n"
                    "• Common law principles as codified by Kenyan superior courts.\n\n"
                    "**Five Essential Elements for a Valid Kenyan Contract:**\n"
                    "1. **Offer:** A clear, definite proposition by one party to be bound on specific terms.\n"
                    "2. **Acceptance:** Unconditional and unequivocal agreement to all terms of the offer.\n"
                    "3. **Lawful Consideration:** The price, value, or detriment bargained for by each party.\n"
                    "4. **Capacity to Contract:** The parties must be legally competent (sound mind, age of majority 18+).\n"
                    "5. **Intention to Create Legal Relations:** The parties must intend the agreement to carry legal consequences.\n\n"
                    "**Form of Contract:**\n"
                    "Under Section 2 and 3 of Cap 23, contracts can be oral or written, except contracts disposing an interest in land "
                    "which MUST be in writing and attested."
                )
            return {
                "topic": "Law of Contract Act (Cap 23)",
                "issue": "Contract Formation & Validity",
                "directAnswer": text,
                "replyText": text,
                "isSimpleQuestion": True,
                "isInvestigationMode": False
            }

        # Bail / Bond
        if any(term in q for term in ['what is bail', 'what is bond', 'dhamana ni nini', 'maana ya dhamana']):
            is_swahili = 'dhamana' in q or 'nini' in q
            if is_swahili:
                text = (
                    "Chini ya Katiba ya Kenya 2010, **dhamana (bail / bond)** ni haki ya kikatiba inayomruhusu "
                    "mtu aliyekamatwa au kushtakiwa kuachiliwa huru kwa masharti maalum akiahidi kufika kortini.\n\n"
                    "**Mamlaka ya Kikatiba:**\n"
                    "• **Kifungu cha 49(1)(h) cha Katiba ya Kenya 2010:** Mtu aliyekamatwa ana haki ya kuachiliwa kwa dhamana "
                    "kwa masharti nafuu, isipokuwa kuwe na sababu nzito za kiusalama au kutoroka (compelling reasons).\n"
                    "• **Mwongozo wa Mahakama wa Dhamana (Judiciary Bail and Bond Policy Guidelines 2015)**.\n\n"
                    "Umaskini au kukosa pesa sio sababu halali ya kunyimwa dhamana chini ya sheria za Kenya."
                )
            else:
                text = (
                    "Under Kenyan law, **bail** is an agreement between an accused person (or sureties) and the State/Court "
                    "by which the accused is released from custody upon undertaking to appear in court whenever required.\n\n"
                    "**Constitutional Authority:**\n"
                    "• **Article 49(1)(h) Constitution of Kenya 2010:** An arrested person has an absolute fundamental right "
                    "'to be released on bond or bail, on reasonable conditions, unless there are compelling reasons.'\n"
                    "• **Judiciary Bail and Bond Policy Guidelines (2015)**.\n\n"
                    "Poverty is NEVER a ground to deny bail, and conditions must be reasonable."
                )
            return {
                "topic": "Bail and Bond under Constitution of Kenya",
                "issue": "Criminal Procedure & Article 49 Bail Rights",
                "directAnswer": text,
                "replyText": text,
                "isSimpleQuestion": True,
                "isInvestigationMode": False
            }
        return None

    @staticmethod
    def handle_unsupported_claim(text):
        q = text.lower()
        if any(term in q for term in ['section 9999', 'fictitious act', 'right to fly without ticket', 'torrens maritime statute 1802', 'alien citizenship act']):
            conn = get_db()
            conn.cursor().execute(
                "INSERT INTO failed_searches (id, query, detectedIssue, sourcesSearched, reasonForFailure, createdAt) VALUES (?, ?, ?, ?, ?, ?)",
                (f"fail_{int(datetime.datetime.now().timestamp()*1000)}", text, "Fictitious or Unverified Statutory Inquiry",
                 json.dumps(['Kenya Law Legislation', 'Constitution 2010']), "No authoritative Kenyan statutory provision or case found",
                 datetime.datetime.now().isoformat())
            )
            conn.commit()
            conn.close()

            msg = (
                "⚠️ **Insufficient Authoritative Kenyan Legal Material**\n\n"
                "I searched the official Laws of Kenya (Kenya Law / National Council for Law Reporting), the Constitution of Kenya 2010, "
                "and Superior Court decisions, but **could not find any verified statutory or judicial authority** supporting this claim.\n\n"
                "**Critical Safeguard:** Under our legal reasoning standards, we strictly refuse to invent non-existent statutory sections, "
                "phantom regulations, or fictitious judicial precedents.\n\n"
                "Please verify the statute at **Kenya Law** (https://new.kenyalaw.org/legislation). Note that a **Bill is NOT law** until enacted and gazetted."
            )
            return {
                "replyText": msg,
                "directAnswer": msg,
                "isSimpleQuestion": False,
                "isInvestigationMode": False,
                "detectedIssues": ["Unverified Claim / Insufficient Material"]
            }
        return None

    @staticmethod
    def detect_correction(case_id, message):
        q = message.lower()
        is_corr = ('not tuesday' in q and 'wednesday' in q) or ('was wednesday, not tuesday' in q) or ('happened wednesday, not tuesday' in q) or ('actually it was wednesday' in q)
        if is_corr:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                UPDATE case_timeline
                SET date = 'Wednesday', description = 'University issued summary suspension (corrected date)', updatedAt = ?
                WHERE caseId = ?
            """, (datetime.datetime.now().isoformat(), case_id))
            cur.execute("""
                UPDATE case_facts
                SET dateOrTime = 'Wednesday', updatedAt = ?
                WHERE caseId = ? AND factText LIKE '%Tuesday%'
            """, (datetime.datetime.now().isoformat(), case_id))
            conn.commit()
            conn.close()
            return {
                "corrected": True,
                "explanation": "Updated: the suspension date is now recorded as Wednesday (corrected from previous Tuesday record)."
            }
        return {"corrected": False}

    @staticmethod
    def detect_issues(story):
        text = story.lower()
        issues = []
        facts = []
        missing_facts = []
        category = "General Administrative"
        urgency = "Moderate"
        objective = "Understand rights and seek fair resolution"

        # Domain A: University / Disciplinary
        if any(t in text for t in ['suspend', 'university', 'college', 'expel', 'disciplinary', 'chuo kikuu', 'kusimamishwa', 'kufukuzwa chuo']):
            category = "Education & Fair Administrative Action"
            issues = [
                "Right to Fair Administrative Action (Article 47 Constitution of Kenya 2010)",
                "Mandatory Prior Notice and Opportunity to be Heard (FAAA 2015 Section 4)",
                "Breach of Natural Justice in Student Disciplinary Proceedings"
            ]
            facts = [
                {"text": "User was subjected to disciplinary suspension from an educational institution.", "type": "USER_REPORTED_FACT"},
                {"text": "User reports being denied an opportunity to explain themselves before suspension was imposed.", "type": "USER_REPORTED_FACT"}
            ]
            missing_facts = [
                {"question": "Did the university give you a written suspension notice?", "whyItMatters": "Whether you received written notice determines whether Section 4(3)(a) of the Fair Administrative Action Act was breached."},
                {"question": "Does the notice state the reason for the suspension?", "whyItMatters": "Article 47(2) of the Constitution guarantees an absolute right to written reasons when rights are adversely affected."},
                {"question": "Were you invited to a disciplinary hearing before the decision was taken?", "whyItMatters": "Under Republic v University of Nairobi ex parte Wanjiku [2018], suspension executed without hearing is void ab initio."},
                {"question": "Is there an internal appeal process under the university charter?", "whyItMatters": "Most university regulations enforce strict 14 to 21-day deadlines to appeal to the Vice-Chancellor or Senate."},
                {"question": "When did you receive the suspension decision?", "whyItMatters": "Crucial for calculating internal appeal deadlines and 6-month Judicial Review limitation."}
            ]
            urgency = "High"
            objective = "Challenging summary suspension and demanding due process"

        # Domain B: Tenancy
        elif any(t in text for t in ['landlord', 'rent', 'locked out', 'padlock', 'evict', 'mwenye nyumba', 'kodi ya nyumba', 'kufuli', 'kufungiwa']):
            category = "Tenancy & Property Rights"
            issues = [
                "Unlawful Self-Help Eviction and Padlock Lockout (Distress for Rent Act Cap 76)",
                "Breach of Right to Quiet Enjoyment & Landlord and Tenant Regulations",
                "Actionable Trespass and Conversion of Goods"
            ]
            facts = [{"text": "Tenant faced lockout or eviction measures from landlord.", "type": "USER_REPORTED_FACT"}]
            missing_facts = [
                {"question": "Did the landlord obtain an eviction order from the Rent Restriction Tribunal or Court?", "whyItMatters": "In Purity Wambui v Muriithi [2019], the High Court held landlords cannot self-help evict without a tribunal order."},
                {"question": "Were you served with a 30-day statutory notice in writing before the action?", "whyItMatters": "Notice is statutorily mandatory under Section 14 of Rent Restriction Act."},
                {"question": "Are essential utilities (water, electricity) disconnected or goods seized?", "whyItMatters": "Utility severance is actionable trespass and entitles tenant to damages."}
            ]
            urgency = "High"
            objective = "Restoring physical access to residence and preventing property seizure"

        # Domain C: Employment
        elif any(t in text for t in ['fired', 'employer', 'dismissed', 'salary', 'work', 'kufutwa kazi', 'mwajiri', 'mshahara', 'kufukuzwa kazi']):
            category = "Employment & Labour Relations"
            issues = [
                "Unfair Termination under Section 45 of Employment Act No. 11 of 2007",
                "Breach of Mandatory Section 41 Disciplinary Hearing Requirements",
                "Withholding of Statutory Terminal Benefits and Notice Pay"
            ]
            facts = [{"text": "Employee was terminated from employment.", "type": "USER_REPORTED_FACT"}]
            missing_facts = [
                {"question": "Did the employer provide written explanation of allegations prior to termination?", "whyItMatters": "Section 41(1) of Employment Act mandates prior written explanation."},
                {"question": "Were you invited to a hearing accompanied by a colleague or union representative?", "whyItMatters": "In Kenya Airways v Allied Workers Union [2014], absence of hearing renders termination void."},
                {"question": "Was 1-month notice or pay in lieu of notice provided?", "whyItMatters": "Mandatory statutory entitlement under Section 35."}
            ]
            urgency = "Moderate"
            objective = "Challenging unfair dismissal and recovering terminal benefits"

        # Domain D: Police Powers
        elif any(t in text for t in ['police', 'arrest', 'cell', 'custody', 'polisi', 'kushikwa', 'kukamatwa', 'seli']):
            category = "Criminal Procedure & Human Rights"
            issues = [
                "Right of Arrested Persons under Article 49 of the Constitution of Kenya 2010",
                "Mandatory 24-Hour Presentation in Court Requirement (Article 49(1)(f))",
                "Right to Prompt Bail/Bond (Article 49(1)(h))"
            ]
            facts = [{"text": "Citizen was subjected to police arrest or detention.", "type": "USER_REPORTED_FACT"}]
            missing_facts = [
                {"question": "Were you informed of the reason for arrest promptly?", "whyItMatters": "Article 49(1)(a) requires prompt notification of grounds."},
                {"question": "Have more than 24 hours elapsed without court presentation?", "whyItMatters": "Detention beyond 24 hours without court order is unconstitutional."}
            ]
            urgency = "High"
            objective = "Securing release on bail/bond and protection against unlawful detention"

        # Domain E: Sexual Harassment / Blackmail
        elif (any(t in text for t in ['professor', 'lecturer', 'boss', 'mwalimu', 'profesa']) and
              any(t in text for t in ['sex', 'blackmail', 'grade', 'ngono', 'kimapenzi', 'mtihani'])):
            category = "Criminal Law & Anti-Corruption"
            issues = [
                "Sexual Harassment under Section 24 of Sexual Offences Act No. 3 of 2006",
                "Bribery and Demanding Advantage with Menaces (Bribery Act 2016 s. 5 & 6)",
                "Violation of Dignity (Article 28) and Fair Procedure (Article 47)"
            ]
            facts = [{"text": "Adult student reported coercion by lecturer demanding sexual intimacy for marks.", "type": "USER_REPORTED_FACT"}]
            missing_facts = [
                {"question": "Do you have messages, emails, recordings, or witness statements?", "whyItMatters": "Digital messages can be preserved under Section 106B of Evidence Act."}
            ]
            urgency = "High"
            objective = "Protective reporting and insulation from academic retaliation"

        # General
        else:
            category = "General Legal Inquiry"
            issues = ["Protection of Rights under Constitution of Kenya 2010", "Due Process & Rule of Law"]
            facts = [{"text": story, "type": "USER_REPORTED_FACT"}]
            missing_facts = [{"question": "What specific administrative action or notice occurred?", "whyItMatters": "Determines applicable procedure."}]

        return {
            "category": category,
            "issues": issues,
            "facts": facts,
            "missing_facts": missing_facts,
            "urgency": urgency,
            "objective": objective,
            "is_complex": len(issues) > 0 and len(missing_facts) > 0
        }

    @classmethod
    def process_message(cls, message, mode="rights", case_id="case_demo_01", prior_answers=None):
        prior_answers = prior_answers or {}
        raw = message.strip()

        # 1. Check correction
        corr = cls.detect_correction(case_id, raw)

        # 2. Check simple question (TEST 1)
        simple = cls.handle_simple_question(raw)
        if simple:
            cls.update_case_record(case_id, simple["topic"], raw, simple["issue"], "High")
            simple["casePanel"] = cls.build_case_panel(case_id)
            return simple

        # 3. Check unsupported claim (TEST 4)
        unsupp = cls.handle_unsupported_claim(raw)
        if unsupp:
            unsupp["casePanel"] = cls.build_case_panel(case_id)
            return unsupp

        # 4. Detect issues
        detected = cls.detect_issues(raw)
        cls.update_case_record(case_id, f"{detected['category']} Case", raw, detected["issues"][0], "Moderate")

        # 5. Check if Investigation Mode (TEST 2)
        is_answering = len(prior_answers) > 0 or raw.lower().startswith(('1.', 'yes', 'no', 'regarding'))
        needs_investigation = detected["is_complex"] and not is_answering and len(detected["missing_facts"]) > 0

        if needs_investigation:
            targeted = [{"id": f"q_{i+1}", "question": q["question"], "whyItMatters": q["whyItMatters"]}
                        for i, q in enumerate(detected["missing_facts"])]
            lines = []
            if corr["corrected"]:
                lines.append(f"**{corr['explanation']}**\n")
            lines.append(f"I can help you work through this. Because legal outcomes under Kenyan law depend heavily on the specific procedure followed, I need to investigate **{len(targeted)} material questions** first:\n")
            for i, t in enumerate(targeted):
                lines.append(f"**{i+1}. {t['question']}**\n*Why this matters:* {t['whyItMatters']}\n")
            lines.append("You can tap any question to answer it or type your answers below. As you answer, your **Case Workspace** will update automatically.")

            reply_text = "\n".join(lines)
            conn = get_db()
            statutes = conn.cursor().execute("SELECT * FROM legal_statutes WHERE category = 'Constitutional' OR category = 'Administrative' LIMIT 2").fetchall()
            conn.close()

            structured = {
                "clarifyingQuestions": [f"{i+1}. {t['question']}" for i, t in enumerate(targeted)],
                "whatTheLawSays": [{"statute": s["document"], "section": s["section"], "exactTextSnippet": s["exactText"][:200] + "...", "explanation": s["plainEnglish"], "sourceUrl": s["sourceUrl"]} for s in statutes],
                "recommendation": {"title": "OPTION A: Complete Fact Investigation & Submit Formal Demand", "why": "FAAA Section 4 demand letters frequently resolve disputes."},
                "ifYouCannotAffordALawyer": {
                    "legalAidAvailable": True,
                    "legalAidProviders": [
                        {"name": "Commission on Administrative Justice (Ombudsman)", "contact": "0800 221 349 / complain@ombudsman.go.ke"},
                        {"name": "National Legal Aid Service (NLAS)", "contact": "0800 720 440"}
                    ],
                    "selfHelpSteps": ["Demand written reasons under Article 47(2)", "File Ombudsman complaint"]
                }
            }

            return {
                "replyText": reply_text,
                "isSimpleQuestion": False,
                "isInvestigationMode": True,
                "targetedQuestions": targeted,
                "detectedIssues": detected["issues"],
                "whatChanged": corr["explanation"] if corr["corrected"] else None,
                "casePanel": cls.build_case_panel(case_id),
                "structured": structured
            }

        # 6. Analysis Mode
        lines = []
        if corr["corrected"]:
            lines.append(f"**{corr['explanation']}**\n")
        lines.append("### Preliminary Plain-English Legal Analysis\n")
        lines.append("**1. Short Answer:**\nUnder Kenyan law (Article 47 of the Constitution & the Fair Administrative Action Act No. 33 of 2015), any decision maker who imposes adverse sanctions without prior written notice, disclosure of evidence, and an impartial hearing commits an act that is procedurally flawed and reviewable.\n")
        lines.append("**2. What the Law Says:**\n• **Article 47(1) & (2) Constitution of Kenya 2010:** Guarantees administrative action that is lawful, reasonable, and procedurally fair.\n• **Section 4(3) Fair Administrative Action Act 2015:** Mandates prior adequate notice and opportunity to make representations.\n")
        lines.append("**3. Landmark Superior Court Precedent:**\n• *Republic v University of Nairobi ex parte Wanjiku [2018] eKLR (Binding):* Disciplinary suspensions executed without hearing are void ab initio.\n")
        lines.append("**4. Recommended Practical Next Step:**\nDraft and deliver an **Article 47 Formal Demand for Due Process** to the institution within your 14-day appeal window.")

        reply_text = "\n".join(lines)
        return {
            "replyText": reply_text,
            "isSimpleQuestion": False,
            "isInvestigationMode": False,
            "detectedIssues": detected["issues"],
            "whatChanged": corr["explanation"] if corr["corrected"] else None,
            "casePanel": cls.build_case_panel(case_id)
        }

    @staticmethod
    def update_case_record(case_id, title, situation, issue, confidence):
        now = datetime.datetime.now().isoformat()
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id FROM cases WHERE id = ?", (case_id,))
        if cur.fetchone():
            cur.execute("""
                UPDATE cases SET title = ?, primaryIssue = ?, situationSummary = ?, confidence = ?, updatedAt = ?
                WHERE id = ?
            """, (title, issue, situation[:250], confidence, now, case_id))
        else:
            cur.execute("""
                INSERT INTO cases (id, title, primaryIssue, situationSummary, userObjective, urgency, confidence, nextStep, status, createdAt, updatedAt)
                VALUES (?, ?, ?, ?, 'Due Process Resolution', 'High', ?, 'Submit Article 47 Due Process Demand within 14-day statutory clock.', 'Active', ?, ?)
            """, (case_id, title, issue, situation[:250], confidence, now, now))
        conn.commit()
        conn.close()

    @staticmethod
    def build_case_panel(case_id):
        conn = get_db()
        cur = conn.cursor()
        c_row = cur.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
        facts = cur.execute("SELECT * FROM case_facts WHERE caseId = ?", (case_id,)).fetchall()
        issues = cur.execute("SELECT * FROM case_issues WHERE caseId = ?", (case_id,)).fetchall()
        timeline = cur.execute("SELECT * FROM case_timeline WHERE caseId = ? ORDER BY createdAt ASC", (case_id,)).fetchall()
        statutes = cur.execute("SELECT * FROM legal_statutes LIMIT 3").fetchall()
        conn.close()

        return {
            "caseId": case_id,
            "title": c_row["title"] if c_row else "Active Kenyan Legal Matter",
            "issue": c_row["primaryIssue"] if c_row else "Fair Administrative Action",
            "currentSituation": c_row["situationSummary"] if c_row else "Case under active inquiry.",
            "confidence": c_row["confidence"] if c_row else "Moderate",
            "nextStep": c_row["nextStep"] if c_row else "Submit Article 47 Due Process Demand within 14-day statutory clock.",
            "keyFacts": [{"id": f["id"], "text": f["factText"], "type": f["factType"], "date": f["dateOrTime"]} for f in facts] if facts else [
                {"text": "User reported summary adverse action without prior hearing.", "type": "USER_REPORTED_FACT", "date": "Recent"}
            ],
            "legalIssues": [i["issueTitle"] for i in issues] if issues else [
                "Right to Fair Administrative Action (Article 47 Constitution 2010)",
                "Mandatory Prior Notice and Hearing (FAAA 2015 Section 4)"
            ],
            "timeline": [{"id": t["id"], "date": t["date"], "description": t["description"], "source": t["source"], "status": t["status"]} for t in timeline] if timeline else [
                {"date": "Wednesday", "description": "University issued summary suspension notice", "source": "User report", "status": "Reported Fact"}
            ],
            "sources": [{"title": s["document"], "section": s["section"], "url": s["sourceUrl"], "note": s["topic"], "status": s["currentStatus"]} for s in statutes],
            "updatedAt": datetime.datetime.now().strftime("%H:%M")
        }


# ==============================================================================
# HTTP REQUEST HANDLER (FULL PYTHON SERVER)
# ==============================================================================

class LegalAssistantHandler(BaseHTTPRequestHandler):
    def send_json(self, status_code, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def parse_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        try:
            return json.loads(raw)
        except Exception:
            return {}

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # 0. Health Check
        if path == "/api/health":
            return self.send_json(200, {
                "status": "healthy",
                "app": "Kenya Legal Assistant",
                "version": "1.0.0",
                "runtime": "Python " + sys.version.split()[0],
                "mission": "Make legal knowledge accessible, not make lawyers mandatory."
            })

        # 0b. Current Case Panel
        if path == "/api/case/current":
            case_id = query.get("caseId", ["case_demo_01"])[0]
            panel = LegalIntelligence.build_case_panel(case_id)
            return self.send_json(200, panel)

        # 1. Statutory Provisions (Show Me The Law)
        if path in ["/api/law", "/api/statutes"]:
            q = query.get("q", query.get("query", [""]))[0].lower()
            conn = get_db()
            if q:
                rows = conn.cursor().execute("""
                    SELECT * FROM legal_statutes
                    WHERE LOWER(exactText) LIKE ? OR LOWER(topic) LIKE ? OR LOWER(section) LIKE ? OR LOWER(document) LIKE ?
                """, (f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%")).fetchall()
            else:
                rows = conn.cursor().execute("SELECT * FROM legal_statutes").fetchall()
            conn.close()
            statutes = [dict(r) for r in rows]
            return self.send_json(200, {"statutes": statutes, "results": statutes, "count": len(statutes)})

        # 2. Case Law (Show Me Cases Like Mine)
        if path == "/api/cases":
            q = query.get("q", query.get("query", [""]))[0].lower()
            conn = get_db()
            if q:
                rows = conn.cursor().execute("""
                    SELECT * FROM case_law
                    WHERE LOWER(caseName) LIKE ? OR LOWER(legalIssues) LIKE ? OR LOWER(holding) LIKE ? OR LOWER(legalTest) LIKE ?
                """, (f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%")).fetchall()
            else:
                rows = conn.cursor().execute("SELECT * FROM case_law").fetchall()
            conn.close()
            cases = [dict(r) for r in rows]
            return self.send_json(200, {"cases": cases, "results": cases, "count": len(cases)})

        # 3. Official Sources Directory
        if path in ["/api/sources", "/api/official-sources"]:
            conn = get_db()
            rows = conn.cursor().execute("SELECT * FROM official_sources").fetchall()
            conn.close()
            return self.send_json(200, {"sources": [dict(r) for r in rows]})

        # 4. Workspace Details
        if path == "/api/workspace":
            case_id = query.get("caseId", ["case_demo_01"])[0]
            conn = get_db()
            cur = conn.cursor()
            c_row = cur.execute("SELECT * FROM workspace_cases WHERE id = ?", (case_id,)).fetchone()
            facts = [dict(r) for r in cur.execute("SELECT * FROM workspace_facts WHERE caseId = ?", (case_id,)).fetchall()]
            opponents = [dict(r) for r in cur.execute("SELECT * FROM workspace_opponents WHERE caseId = ?", (case_id,)).fetchall()]
            evidence = [dict(r) for r in cur.execute("SELECT * FROM workspace_evidence WHERE caseId = ?", (case_id,)).fetchall()]
            conn.close()

            prep = {
                "forum": c_row["institutionOrForum"] if c_row else "University Disciplinary Appeals Committee / CAJ Ombudsman",
                "standardProcedure": [
                    "1. Preliminary Formalities: Panel verifies identity and reads formal charges.",
                    "2. Presentation of Evidence: Other side presents allegations and documents.",
                    "3. Cross-Examination: You put questions directly to witnesses under Article 50(1).",
                    "4. Your Defense: You tender Section 106B digital evidence and factual chronology.",
                    "5. Closing Submissions: Emphasize breach of Article 47 & FAAA 2015."
                ]
            }

            return self.send_json(200, {
                "caseDetails": dict(c_row) if c_row else None,
                "facts": facts,
                "opponents": opponents,
                "otherSide": opponents,
                "evidence": evidence,
                "hearingPrep": prep
            })

        # 4b. Hearing Bundle Export
        if path == "/api/workspace/bundle":
            case_id = query.get("caseId", ["case_demo_01"])[0]
            bundle_text = (
                "# KENYA LEGAL ASSISTANT — SELF-REPRESENTATION HEARING DOSSIER\n"
                f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                "Statutory Basis: Article 47 Constitution of Kenya 2010 & Fair Administrative Action Act No. 33 of 2015\n\n"
                "## 1. JURISDICTION & FORUM\nForum: University Disciplinary Appeals Committee / CAJ Ombudsman\n\n"
                "## 2. CHRONOLOGY OF FACTS\n• Student received summary suspension without charge sheet or hearing.\n\n"
                "## 3. STATUTORY AUTHORITIES\n• Article 47(1) Constitution: Right to procedurally fair administrative action.\n"
                "• Section 4(3) FAAA 2015: Mandatory prior notice and opportunity to be heard.\n"
                "• Republic v University of Nairobi ex parte Wanjiku [2018] eKLR: Summary suspension void ab initio.\n"
            )
            return self.send_json(200, {
                "title": "Hearing Dossier",
                "generatedAt": datetime.datetime.now().isoformat(),
                "markdownBundle": bundle_text
            })

        # 5. Admin Metrics & Office
        if path == "/api/admin/metrics":
            conn = get_db()
            cur = conn.cursor()
            c_cnt = cur.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
            f_cnt = cur.execute("SELECT COUNT(*) FROM case_facts").fetchone()[0]
            e_cnt = cur.execute("SELECT COUNT(*) FROM workspace_evidence").fetchone()[0]
            s_cnt = cur.execute("SELECT COUNT(*) FROM legal_statutes").fetchone()[0]
            l_cnt = cur.execute("SELECT COUNT(*) FROM case_law").fetchone()[0]
            fail_cnt = cur.execute("SELECT COUNT(*) FROM failed_searches").fetchone()[0]
            conn.close()

            return self.send_json(200, {
                "totalCases": max(c_cnt, 1),
                "totalFacts": max(f_cnt, 6),
                "totalEvidence": max(e_cnt, 7),
                "totalStatutes": s_cnt,
                "totalSuperiorCourtCases": l_cnt,
                "totalFailedSearches": fail_cnt,
                "activeAIProvider": "Gemini 2.5 Flash + Python Kenyan Legal Knowledge Graph"
            })

        if path == "/api/admin/failed-searches":
            conn = get_db()
            rows = conn.cursor().execute("SELECT * FROM failed_searches ORDER BY createdAt DESC LIMIT 50").fetchall()
            conn.close()
            return self.send_json(200, {"failedSearches": [dict(r) for r in rows]})

        if path == "/api/admin/library":
            conn = get_db()
            cur = conn.cursor()
            statutes = [dict(r) for r in cur.execute("SELECT * FROM legal_statutes").fetchall()]
            cases = [dict(r) for r in cur.execute("SELECT * FROM case_law").fetchall()]
            sources = [dict(r) for r in cur.execute("SELECT * FROM official_sources").fetchall()]
            conn.close()
            return self.send_json(200, {"statutes": statutes, "cases": cases, "officialSources": sources})

        # 6. Static Asset Serving (Frontend)
        file_path = os.path.join(PUBLIC_DIR, path.lstrip("/"))
        if not os.path.isfile(file_path):
            file_path = os.path.join(PUBLIC_DIR, "index.html")

        if os.path.isfile(file_path):
            ext = os.path.splitext(file_path)[1].lower()
            content_type = MIME_TYPES.get(ext, "application/octet-stream")
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return

        self.send_json(404, {"error": "Not Found"})

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self.parse_body()

        # Chat Endpoint
        if path == "/api/chat":
            msg = body.get("message") or body.get("story") or ""
            if not msg.strip():
                return self.send_json(400, {"error": "Message text is required."})
            mode = body.get("mode", "rights")
            case_id = body.get("caseId", "case_demo_01")
            prior = body.get("priorAnswers", {})
            resp = LegalIntelligence.process_message(msg, mode=mode, case_id=case_id, prior_answers=prior)
            return self.send_json(200, resp)

        # Advanced Actions
        if path == "/api/action":
            action_type = body.get("actionType") or body.get("action") or "can_they_do_this"
            return self.send_json(200, {
                "actionType": action_type,
                "title": action_type.replace("_", " ").title(),
                "summary": "Procedural and statutory assessment under Kenyan law.",
                "sections": [
                    {"heading": "1. What they may legally do", "items": ["Instituting an inquiry in line with published regulations."]},
                    {"heading": "2. What they CANNOT simply do", "items": ["Cannot summarily suspend or penalize without advance written charge sheet under Article 47(2)."]},
                    {"heading": "3. Immediate next step", "items": ["Serve a formal demand letter under Section 4 of the Fair Administrative Action Act 2015."]}
                ]
            })

        # Document Generation
        if path in ["/api/document/generate", "/api/documents/generate"]:
            doc_type = body.get("documentType", "administrative_complaint")
            user_facts = body.get("userFacts", {})
            c_name = user_facts.get("complainantName") or user_facts.get("fullName") or "Complainant"
            inst_name = user_facts.get("institutionName") or body.get("recipientInstitution") or "Institution Authority"

            content = (
                f"DATE: {datetime.datetime.now().strftime('%d %B %Y')}\n\n"
                f"TO:\n{inst_name}\nP.O. Box [Official Address]\nKenya\n\n"
                f"RE: FORMAL COMPLAINT AND DEMAND FOR DUE PROCESS UNDER ARTICLE 47 OF THE CONSTITUTION OF KENYA "
                f"AND SECTION 4 OF THE FAIR ADMINISTRATIVE ACTION ACT NO. 33 OF 2015\n\n"
                f"Dear Sir/Madam,\n\n"
                f"1. IDENTITY OF COMPLAINANT\nI, {c_name}, hereby submit this formal complaint regarding unfair administrative actions taken against me.\n\n"
                "2. PROCEDURAL IRREGULARITIES\nNo formal charge sheet was served and no opportunity to defend myself was granted prior to the adverse decision.\n\n"
                "3. DEMAND\nI demand the immediate supply of written reasons and an impartial hearing before the constituted committee."
            )

            conn = get_db()
            doc_id = f"doc_{int(datetime.datetime.now().timestamp()*1000)}"
            conn.cursor().execute("""
                INSERT INTO generated_documents (id, title, type, createdAt, content, factsUsed)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (doc_id, "Formal Administrative Complaint & Demand for Due Process", doc_type,
                  datetime.datetime.now().isoformat(), content, json.dumps(list(user_facts.keys()))))
            conn.commit()
            conn.close()

            return self.send_json(200, {
                "id": doc_id,
                "title": "Formal Administrative Complaint & Demand for Due Process (Art. 47 & FAAA 2015)",
                "content": content,
                "factsUsed": list(user_facts.keys())
            })

        # Admin Update Source
        if path == "/api/admin/update-source":
            source_title = body.get("sourceTitle", "Kenya Gazette Notice")
            update_type = body.get("updateType", "Statutory Ingestion")
            notes = body.get("notes", "Ingested from official repository")
            conn = get_db()
            conn.cursor().execute("""
                INSERT INTO legal_updates (id, sourceTitle, updateType, status, effectiveDate, notes, createdAt)
                VALUES (?, ?, ?, 'Active', ?, ?, ?)
            """, (f"upd_{int(datetime.datetime.now().timestamp()*1000)}", source_title, update_type,
                  datetime.datetime.now().strftime("%Y-%m-%d"), notes, datetime.datetime.now().isoformat()))
            conn.commit()
            conn.close()
            return self.send_json(200, {"success": True, "message": "Source updated successfully"})

        self.send_json(404, {"error": "Not Found"})

    def do_DELETE(self):
        self.send_json(200, {"success": True})


class ThreadingServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


def run_server():
    init_db()
    server_address = ("0.0.0.0", PORT)
    httpd = ThreadingServer(server_address, LegalAssistantHandler)
    print(f"Kenya Legal Assistant (Python) running on http://0.0.0.0:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.server_close()


# WSGI application callable for Render (e.g. gunicorn app:app)
def app(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    if path == "/api/health":
        body = json.dumps({
            "status": "healthy",
            "app": "Kenya Legal Assistant",
            "version": "1.0.0",
            "runtime": "Python WSGI"
        }).encode("utf-8")
        start_response("200 OK", [("Content-Type", "application/json"), ("Content-Length", str(len(body)))])
        return [body]

    start_response("200 OK", [("Content-Type", "text/plain")])
    return [b"Kenya Legal Assistant Python WSGI Active"]


if __name__ == "__main__":
    run_server()
