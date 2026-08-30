import os
import csv
import random

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASETS_DIR = os.path.join(BASE_DIR, 'datasets')
OUTPUT_CSV = os.path.join(DATASETS_DIR, 'recomind_domain_dataset.csv')

os.makedirs(DATASETS_DIR, exist_ok=True)

# Broad Domain Corpus Generator for RecoMind Stage 1 MVP
DOMAIN_CORPUS = {
    "STEM: Computer Science & IT": [
        "Data structures like binary search trees, hash tables, and graphs allow efficient O(log n) search and insertion.",
        "Operating systems manage hardware memory using virtual paging, process scheduling algorithms, and deadlock avoidance.",
        "Relational database management systems utilize SQL queries, ACID transaction properties, indexing, and primary key constraints.",
        "Machine learning models process feature vectors using supervised classification, gradient descent optimization, and loss minimization.",
        "Object oriented programming principles include encapsulation, inheritance, polymorphism, and abstraction across software modules.",
        "Computer networks communicate via TCP IP stack protocol layers, sockets, routing tables, and HTTP request response headers.",
        "Algorithm analysis evaluates time and space complexity using asymptotic Big O notation for worst case execution bounds.",
        "Software engineering practices involve git version control, continuous integration pipelines, agile sprints, and unit testing.",
        "Web development frontends use React components, virtual DOM state management, and asynchronous fetch APIs for REST services.",
        "Cybersecurity protocols enforce public key infrastructure, RSA encryption algorithms, digital certificates, and hashing functions.",
    ],
    "STEM: Engineering & Technology": [
        "Thermodynamics principles dictate heat transfer, entropy creation, internal energy variations, and Carnot cycle efficiency bounds.",
        "Fluid mechanics analyzes laminar vs turbulent flow regimes using Bernoulli equation and Navier Stokes conservation equations.",
        "Electrical circuit theory calculates voltage drop across resistors, inductors, and capacitors using Kirchhoff current law.",
        "Structural engineering calculates shear force diagrams, bending moment distributions, and tensile stress under load conditions.",
        "Signals and systems processing utilizes Fourier transform, Laplace transform, and impulse response to analyze linear systems.",
        "Chemical engineering processes design heat exchangers, distillation columns, mass transfer rates, and reaction kinetics.",
        "Control systems engineering calculates closed loop transfer functions, root locus stability, and PID feedback tuning parameters.",
        "Materials science investigates crystalline lattice structures, yield strength, ductility, and fatigue limits of alloy metals.",
        "Aerodynamics studies lift force generation, drag coefficient minimization, airfoil camber geometry, and boundary layer thickness.",
        "Mechatronics combines microcontrollers, stepper motor actuators, encoder feedback sensors, and automated control loops.",
    ],
    "STEM: Physical Sciences & Mathematics": [
        "Quantum mechanics describes particle wave duality, wavefunctions, Heisenberg uncertainty principle, and Schrödinger equation solutions.",
        "Linear algebra utilizes matrix transformations, eigenvalues, eigenvectors, vector spaces, and singular value decomposition.",
        "Organic chemistry studies carbon functional groups, nucleophilic substitution mechanisms, aromaticity, and synthesis pathways.",
        "Multivariable calculus calculates double integrals, gradient vectors, curl, divergence, and line integrals over vector fields.",
        "Classical mechanics formulates planetary motion using Newton laws of motion, conservation of momentum, and Lagrangian dynamics.",
        "Physical chemistry analyzes chemical equilibrium, reaction rate constants, activation energy, and Gibbs free energy change.",
        "Differential equations model dynamic physical systems using first order separable equations and linear second order operators.",
        "Electromagnetism explains electric fields, magnetic flux induction, Maxwell equations, and electromagnetic wave propagation.",
        "Real analysis rigorously proves limit convergence, continuous functions, supremum bounds, and Riemann integrability of sequences.",
        "Inorganic chemistry examines transition metal coordination complexes, crystal field theory, orbital hybridization, and valence shell bonding.",
    ],
    "Medical & Life Sciences": [
        "Human anatomy details upper extremity vascular supply, brachial plexus nerve innervation, and skeletal muscular origins.",
        "Human physiology explains cardiac muscle contraction, cardiac output determinants, action potentials, and renal filtration rates.",
        "Pathology investigates cellular injury mechanisms, inflammation cascades, apoptosis pathways, and histological tumor grading.",
        "Pharmacology studies drug receptor binding kinetics, pharmacokinetics clearance, bioavailability, and therapeutic drug monitoring.",
        "Biochemistry analyzes cellular respiration pathways including glycolysis, Krebs citric acid cycle, and oxidative phosphorylation.",
        "Microbiology classifies bacterial pathogens based on Gram stain cell wall structures, antibiotic susceptibility, and viral capsids.",
        "Immunology details T cell activation, B cell antibody production, antigen presenting cells, and adaptive immune responses.",
        "Genetics examines DNA double helix replication, transcription factor regulation, translation ribosome complexes, and mutations.",
        "Clinical neurology assesses cranial nerve pathways, reflexes, motor sensory tracts, and central nervous system pathology.",
        "Endocrinology regulates hormonal feedback loops involving pituitary thyroid adrenal axis, insulin secretion, and homeostatic balance.",
    ],
    "Business, Commerce & Economics": [
        "Financial accounting principles record double entry bookkeeping, journal entries, balance sheets, and cash flow statements.",
        "Macroeconomics evaluates national gross domestic product GDP growth, inflation rates, central bank monetary policy, and unemployment.",
        "Corporate finance calculates net present value NPV, internal rate of return IRR, weighted average cost of capital WACC, and capital budgets.",
        "Microeconomics analyzes consumer demand curves, supply elasticity, market equilibrium price, and marginal utility optimization.",
        "Cost accounting determines direct material costs, overhead cost allocation, break even analysis, and variance reporting.",
        "Marketing strategy conducts target market segmentation, positioning, pricing elasticity, and digital customer acquisition funnels.",
        "Business law regulates commercial contracts, corporate governance structures, intellectual property rights, and liability terms.",
        "International economics evaluates foreign exchange rate fluctuations, trade balance deficits, tariffs, and comparative advantage.",
        "Taxation principles calculate gross taxable income, allowable business deductions, tax liabilities, and statutory compliance.",
        "Investment analysis evaluates portfolio diversification, Sharpe ratio performance, capital asset pricing model CAPM, and stock valuations.",
    ],
    "Humanities & Social Sciences": [
        "Modern world history examines industrial revolution urbanization, colonial empire expansion, world war conflicts, and treaties.",
        "Political science analyzes democratic governance structures, executive legislative judicial balance of power, and voter behavior.",
        "Sociology investigates social stratification, cultural norms, institutional structures, demographic trends, and social mobility.",
        "General psychology studies cognitive learning theories, memory recall mechanisms, emotional regulation, and behavioral conditioning.",
        "Human geography analyzes population distribution patterns, migration flows, urban development spatial organization, and land use.",
        "Philosophy explores epistemological theories of knowledge, moral ethics frameworks, utilitarianism, and metaphysical existence.",
        "International relations studies diplomatic policy, sovereign nation state power dynamics, global alliances, and conflict resolution.",
        "Cultural anthropology examines ethnographic fieldwork, linguistic diversity, kinship systems, and traditional societal rituals.",
        "Public administration focuses on public policy formulation, bureaucratic administrative efficiency, and civic governance.",
        "Art history traces architectural movement styles, renaissance painting techniques, classical sculpture, and visual symbolism.",
    ],
    "Law & Legal Studies": [
        "Constitutional law interprets fundamental rights guarantees, judicial review doctrines, constitutional amendments, and federalism.",
        "Criminal law defines elements of offenses including mens rea intent, actus reus conduct, burden of proof beyond reasonable doubt.",
        "Law of torts addresses civil wrongs, negligence liability elements, duty of care standards, damages remedies, and strict liability.",
        "Contract law evaluates offer acceptance consideration validity, contractual breaches, performance duties, and specific remedies.",
        "Corporate law details legal incorporation, director fiduciary duties, shareholder rights, corporate governance, and liquidations.",
        "Jurisprudence explores natural law theories, legal positivism, judicial precedent doctrine of stare decisis, and legal philosophy.",
        "Administrative law regulates administrative agency rulemaking powers, fair procedure principles, and judicial review of decisions.",
        "Property law governs real estate ownership titles, land easements, leasehold tenancies, property transfers, and mortgages.",
        "Evidence law establishes rules for witness testimony admissibility, hearsay exceptions, documentary evidence, and cross examination.",
        "Intellectual property law protects patent innovation claims, registered trademarks, copyright author ownership, and trade secrets.",
    ],
    "Primary / Basic Foundation": [
        "Elementary science explains plant photosynthesis needing sunlight water, living nonliving things, and seasonal weather changes.",
        "Environmental studies EVS teaches environmental conservation, water saving habits, recycling waste, and animal habitat care.",
        "Basic arithmetic practices addition subtraction multiplication tables, basic division fractions, and simple place values.",
        "Primary social studies introduces family roles, community helpers, school rules, local neighborhood maps, and national flags.",
        "Early language arts focuses on vocabulary sentence building, phonics reading comprehension, spelling rules, and short stories.",
        "Basic geometry identifies simple shapes like circles squares triangles, counting sides, corners, and measurement units.",
        "Health and hygiene habit lessons teach hand washing cleanliness, daily exercise routines, healthy food groups, and rest.",
        "Elementary geography explains landforms like mountains rivers valleys, sun sunrise directions, and basic map reading skills.",
        "Basic safety education covers traffic signal rules, road crossing safety, fire safety rules, and emergency contact numbers.",
        "Nature studies observes seed germination growth stages, farm domestic animals, birds nests, and day night sun patterns.",
    ],
    "Competitive & General Aptitude": [
        "Quantitative aptitude calculates speed distance time, work efficiency ratios, percentage profit loss, and interest rates.",
        "Logical reasoning analyzes syllogism statement conclusions, blood relation trees, seating arrangement puzzles, and coding decoding.",
        "Data interpretation evaluates bar graphs, pie chart percentages, data tables, line graphs, and statistical trend ratios.",
        "Verbal ability tests reading comprehension passages, synonym antonym vocabulary, sentence correction, and idiom usage.",
        "General knowledge covers current affairs events, national awards, historical milestone dates, world capitals, and treaties.",
        "Analytical reasoning solves number series patterns, matrix coding puzzles, direction distance tests, and Venn diagrams.",
        "General mental ability tests critical thinking assumptions, statement cause effect conclusions, and logical deductions.",
        "Competitive math solves permutation combination probability, algebraic equations, geometry theorems, and mensuration areas.",
        "Current affairs tracking covers international summits, bilateral agreements, government welfare schemes, and science news.",
        "Aptitude test preparation practices speed calculation shortcuts, time management techniques, and accuracy optimization.",
    ]
}

def generate_expanded_dataset():
    print("Generating RecoMind Stage 1 MVP Dataset...")
    records = []
    
    # Expand templates using varied prefix/suffix educational note contexts
    contexts = [
        "Study Note Section: ",
        "Key Concept Summary: ",
        "Lecture Overview: ",
        "Revision Summary: ",
        "Textbook Excerpt: ",
        "Exam Preparation Point: ",
        "Quick Note: ",
        "Core Topic Review: ",
        "Important Principle: ",
        "Subject Guide: "
    ]

    random.seed(42)

    for domain, templates in DOMAIN_CORPUS.items():
        # Generate 150 diverse text variations per domain (1,350 total samples)
        count = 0
        for i in range(15):
            for t_idx, template in enumerate(templates):
                prefix = contexts[(i + t_idx) % len(contexts)]
                varied_text = f"{prefix}{template}"
                # Add minor syntactic variations
                if i % 3 == 1:
                    varied_text += f" Important for {domain.split(':')[0]} analysis."
                elif i % 3 == 2:
                    varied_text += " Key concepts for exam revision and assessment."

                records.append({
                    "text": varied_text,
                    "domain": domain,
                    "source": "RecoMind Universal Corpus",
                    "source_category": domain.split(":")[-1].strip()
                })
                count += 1

    # Shuffle dataset
    random.shuffle(records)

    # Save to CSV
    with open(OUTPUT_CSV, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "domain", "source", "source_category"])
        writer.writeheader()
        writer.writerows(records)

    print(f"\n[SUCCESS] Prepared Stage 1 Dataset Saved to: {OUTPUT_CSV}")
    print(f"Total Samples: {len(records)}")

    # Print summary per domain
    domain_counts = {}
    for r in records:
        d = r["domain"]
        domain_counts[d] = domain_counts.get(d, 0) + 1

    print("\nSamples per Domain:")
    for d, c in domain_counts.items():
        print(f"  - {d}: {c}")

if __name__ == "__main__":
    generate_expanded_dataset()
