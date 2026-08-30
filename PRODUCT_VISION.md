# RecoMind — Product Vision & Architectural Mandate

> **Core Mandate**: RecoMind is a **Universal Educational Notes Analysis Platform** built for learners across all education levels, domains, subjects, and study tracks.

---

## 🎯 Universal Scope & Target Audience

RecoMind is **NOT** limited to Class 1–12 school students, nor is it limited to B.Tech / Engineering. 

RecoMind is designed to serve:

### 1. School Education
- **Levels**: Class 1 through Class 12
- **Scope**: All subjects (Science, Mathematics, Social Studies, Languages, EVS, etc.) and all boards (CBSE, ICSE, State Boards, IB, IGCSE).

### 2. College & University Education
- **Engineering & Technology**: B.Tech, BE, BCA, MCA (All branches: CS, IT, ECE, EE, Mechanical, Civil, Chemical, Aerospace, Biotech, etc.).
- **Medical & Healthcare**: MBBS, BDS, Nursing, Pharmacy (B.Pharm/M.Pharm), Physiotherapy (BPT), Allied Health Sciences.
- **Commerce & Management**: B.Com, M.Com, CA / CS / CMA related studies, BBA, MBA, Finance, Economics.
- **Arts, Humanities & Social Sciences**: BA, MA (History, Political Science, Sociology, Psychology, Philosophy, Literature).
- **Pure & Applied Sciences**: B.Sc, M.Sc (Physics, Chemistry, Biology, Mathematics, Statistics, Environmental Science).
- **Law**: LLB, LLM, Integrated Law courses (Constitutional Law, Jurisprudence, Corporate Law, Criminal Law).
- **Other Disciplines**: Architecture, Fine Arts, Journalism, Hospitality, and all other UG/PG/Professional degrees.

### 3. Competitive & Professional Examinations
- **Engineering & Science Entrance**: JEE Main, JEE Advanced, GATE.
- **Medical Entrance & Licensing**: NEET-UG, NEET-PG, USMLE, PLAB, NEXT.
- **Civil Services & Governance**: UPSC CSE, State PSCs.
- **Management Entrance**: CAT, XAT, GMAT.
- **Law & Legal**: CLAT, AILET, Bar Examinations.
- **Accounting & Finance**: CA Foundation/Inter/Final, ACCA, CFA.

### 4. Self-Learners & Professional Upskilling
- Independent learners, working professionals, researchers, or hobbyists studying any academic or technical topic autonomously.

---

## 📐 AI & ML Architectural Principles

To fulfill this universal vision, the ML/AI models, dataset design, and backend pipelines MUST adhere to the following architectural rules:

1. **Zero Hardcoded Assumptions**:
   - The backend and ML architecture MUST NOT assume a fixed education tier, single branch, or static set of engineering subjects.
   - The system must dynamically adapt whether analyzing a **Class 3 EVS note**, a **Class 12 Physics note**, an **MBBS Anatomy note**, a **B.Com Accounting note**, a **BA History note**, a **B.Tech Data Structures note**, an **LLB Constitutional Law note**, or a **UPSC Polity note**.

2. **Generalized Multi-Domain ML Architecture**:
   - **OCR / Vision Layer**: Must recognize diverse note formats (handwritten cursive, diagrams, mathematical formulas, chemical equations, anatomical sketches, tables, legal citations, ledger accounts).
   - **Domain & Difficulty Generalization**: NLP / Evaluation models must dynamically detect domain context, terminology depth, and educational level rather than enforcing rigid predefined rules.
   - **Dataset Diversity**: Datasets used for training/fine-tuning evaluation models must span multi-disciplinary academic content from elementary school to advanced postgraduate/professional subjects.

3. **Flexible API Schemas**:
   - Database schemas and API payloads must accept dynamic education levels, domains, and custom user-provided or AI-inferred tags without strict enum constraints.

---

*This document serves as the authoritative product vision for RecoMind and governs all future backend, frontend, and machine learning development.*
