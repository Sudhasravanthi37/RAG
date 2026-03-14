"""
static_db_builder.py
Run once:  python -m app.static_dbs.static_db_builder

Builds FAISS static knowledge bases for:
  - Medical mode  (data/static/vector_dbs/medical)
  - Resume mode   (data/static/vector_dbs/resume)

Legal mode has NO static DB — it retrieves only from uploaded documents.

Each builder first loads built-in knowledge (always available), then
supplements with any external data files found on disk.
"""
import os, json, csv, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from app.rag.embeddings import embed
from app.rag.vectorstore import VectorStore, EMBEDDING_DIM

MEDICAL_DIR   = "data/static/medical_jsons"
RESUME_CSV    = "data/static/job_title_des.csv"
MEDICAL_STORE = "data/static/vector_dbs/medical"
RESUME_STORE  = "data/static/vector_dbs/resume"

# ── Built-in medical reference knowledge ──────────────────────────────────
MEDICAL_BUILTIN = [
    "Hemoglobin (Hb): Men 13.5-17.5 g/dL, Women 12.0-15.5 g/dL. Low = anemia (fatigue, pallor). High = polycythemia or dehydration.",
    "WBC (White Blood Cells): Normal 4,500-11,000 cells/μL. High = infection or inflammation. Low = bone marrow disorder or immunosuppression.",
    "Platelets: Normal 150,000-400,000/μL. Low (thrombocytopenia) = bleeding risk. High (thrombocytosis) = clotting risk.",
    "Fasting Blood Glucose: Normal <100 mg/dL. 100-125 = Prediabetes. ≥126 mg/dL = Diabetes mellitus (confirm with repeat test).",
    "HbA1c: Normal <5.7%. 5.7-6.4% = Prediabetes. ≥6.5% = Diabetes. Reflects 3-month average blood sugar.",
    "Total Cholesterol: Desirable <200 mg/dL. Borderline 200-239. High ≥240 mg/dL. Increased cardiovascular risk.",
    "LDL Cholesterol (bad): Optimal <100 mg/dL. Near-optimal 100-129. High ≥160 mg/dL. Key driver of atherosclerosis.",
    "HDL Cholesterol (good): Men >40 mg/dL, Women >50 mg/dL. Higher is better. <40 = major cardiovascular risk factor.",
    "Triglycerides: Normal <150 mg/dL. Borderline 150-199. High 200-499. Very High ≥500 mg/dL (pancreatitis risk).",
    "Creatinine: Men 0.74-1.35 mg/dL, Women 0.59-1.04 mg/dL. Elevated = kidney dysfunction.",
    "eGFR (Estimated GFR): Normal ≥90 mL/min/1.73m². Stage 3 CKD: 30-59. Stage 5 (kidney failure): <15.",
    "Uric Acid: Men 3.4-7.0 mg/dL, Women 2.4-6.0 mg/dL. High = gout risk, kidney stones.",
    "TSH (Thyroid Stimulating Hormone): Normal 0.4-4.0 mIU/L. High = Hypothyroidism. Low = Hyperthyroidism.",
    "ALT (Liver): Normal 7-56 U/L. Elevated = liver damage, fatty liver, or hepatitis.",
    "AST (Liver): Normal 10-40 U/L. Elevated with ALT = liver disease. Elevated alone = muscle damage.",
    "Total Bilirubin: Normal 0.1-1.2 mg/dL. High = jaundice, liver disease, or hemolysis.",
    "Vitamin D (25-OH): Deficient <20 ng/mL. Insufficient 20-29. Optimal 30-100 ng/mL.",
    "Vitamin B12: Normal 200-900 pg/mL. Low = megaloblastic anemia, neuropathy, fatigue.",
    "Ferritin (iron stores): Men 24-336 ng/mL, Women 11-307 ng/mL. Low = iron deficiency. Very high = hemochromatosis or inflammation.",
    "CRP (C-Reactive Protein): Normal <1.0 mg/L. Elevated = active inflammation or infection. hs-CRP >3.0 = cardiovascular risk.",
    "Sodium: Normal 136-145 mEq/L. Low (hyponatremia) = confusion, seizures. High (hypernatremia) = dehydration.",
    "Potassium: Normal 3.5-5.0 mEq/L. Low (hypokalemia) = muscle weakness, arrhythmia. High (hyperkalemia) = cardiac risk.",
    "Calcium: Normal 8.5-10.5 mg/dL. Low = muscle cramps, tetany. High = kidney stones, bone disease.",
    "Diet for diabetes: Low glycemic index foods, whole grains, legumes, non-starchy vegetables. Limit refined carbs, sugary drinks. Aim 45-60g carbs per meal.",
    "Diet for high cholesterol: Increase soluble fiber (oats, beans, flaxseed), omega-3 (fish). Reduce saturated and trans fats, red meat.",
    "Exercise guidance: 150 min/week moderate aerobic activity. Strength training 2x/week. Reduces BP, blood sugar, cholesterol.",
    "Iron deficiency anemia treatment: Iron-rich foods (red meat, spinach, lentils). Iron supplements with Vitamin C. Avoid tea/coffee with meals.",
    "Hypertension lifestyle: Reduce sodium <2300 mg/day. DASH diet. Regular aerobic exercise. Limit alcohol. Quit smoking.",
]

# ── Built-in resume reference knowledge ───────────────────────────────────
RESUME_BUILTIN = [
    "Software Engineer key skills: Python, Java, C++, algorithms, data structures, system design, REST APIs, Git, CI/CD pipelines, AWS/GCP/Azure cloud.",
    "Data Scientist key skills: Python, R, machine learning, deep learning, pandas, NumPy, scikit-learn, TensorFlow, PyTorch, SQL, data visualization, statistics.",
    "Frontend Developer key skills: React, Angular, Vue.js, TypeScript, HTML5, CSS3, responsive design, webpack, accessibility (WCAG), performance optimization.",
    "Backend Developer key skills: Node.js, Python/Django/FastAPI, Java Spring Boot, PostgreSQL, MySQL, MongoDB, REST APIs, GraphQL, microservices, Docker.",
    "DevOps / SRE key skills: Docker, Kubernetes, Terraform, CI/CD (Jenkins, GitHub Actions), AWS/GCP/Azure, Prometheus, Grafana, Linux, bash scripting.",
    "Product Manager key skills: Agile/Scrum, product roadmap, stakeholder management, user stories, KPI tracking, market research, Jira, PRD writing.",
    "Machine Learning Engineer key skills: MLOps, model deployment, feature engineering, model monitoring, Kubeflow, MLflow, A/B testing, SageMaker.",
    "Cybersecurity Analyst key skills: SIEM, vulnerability assessment, penetration testing, OWASP, network security, incident response, CompTIA Security+.",
    "ATS resume tips: Use standard section headings (Experience, Education, Skills). Include exact keywords from the job description. Avoid tables, graphics, and columns. Submit as .docx or plain PDF.",
    "Strong resume action verbs: Led, Built, Designed, Implemented, Reduced, Increased, Optimized, Delivered, Architected, Scaled, Launched, Streamlined.",
    "Quantify achievements: Write 'Reduced API latency by 40% serving 10M daily active users' instead of 'improved system performance'.",
    "Resume red flags: Unexplained employment gaps >6 months, job-hopping (<1 year per role consistently), generic objective statements, missing contact information.",
    "Senior vs Staff Engineer: Staff Engineer focuses on cross-team technical strategy, org-level architecture decisions, and engineering culture vs feature delivery.",
    "Resume length: 1 page for <10 years experience. 2 pages for senior/principal roles. Never exceed 2 pages. No photos or personal details (age, nationality).",
    "Cover letter best practice: Tailor to each role. Open with a specific hook. Address the hiring manager by name if possible. 3 paragraphs max — why you, why them, call to action.",
]


def build_medical():
    print("⚙ Building medical static DB...")
    texts = list(MEDICAL_BUILTIN)   # start with built-in reference knowledge

    # Supplement with any external JSON files from the data directory
    if os.path.isdir(MEDICAL_DIR):
        for fname in os.listdir(MEDICAL_DIR):
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(MEDICAL_DIR, fname)
            try:
                with open(fpath, encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                print(f"  ✗ Skipping {fname}: {e}")
                continue
            panel = fname.replace(".json", "")
            for entry in data:
                chunk = (
                    f"Panel: {panel} | Test: {entry.get('test_name','')} | "
                    f"Normal: {entry.get('lower_limit','?')}-{entry.get('upper_limit','?')} {entry.get('unit','')} | "
                    f"Notes: {entry.get('notes','')}"
                )
                texts.append(chunk)

    print(f"  → {len(texts)} total entries")
    embs = embed(texts)
    store = VectorStore(EMBEDDING_DIM, store_path=MEDICAL_STORE)
    store.add(embs, texts)
    store.save()
    print(f"  ✓ Saved to {MEDICAL_STORE}")


def build_resume():
    print("⚙ Building resume static DB...")
    texts = list(RESUME_BUILTIN)   # start with built-in tips

    # Supplement with CSV data if available
    if os.path.isfile(RESUME_CSV):
        with open(RESUME_CSV, encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for row in reader:
                title = (row.get("Job Title") or "").strip()
                desc  = (row.get("Job Description") or "").strip()
                if title and desc:
                    texts.append(f"Job Title: {title}\nDescription:\n{desc[:400]}")
        texts = texts[:5000]

    print(f"  → {len(texts)} total entries")
    embs = embed(texts)
    store = VectorStore(EMBEDDING_DIM, store_path=RESUME_STORE)
    store.add(embs, texts)
    store.save()
    print(f"  ✓ Saved to {RESUME_STORE}")


if __name__ == "__main__":
    os.makedirs(MEDICAL_STORE, exist_ok=True)
    os.makedirs(RESUME_STORE, exist_ok=True)
    build_medical()
    build_resume()
    print("\n✅ Static DBs built (Medical + Resume). Legal mode uses uploaded docs only.")
