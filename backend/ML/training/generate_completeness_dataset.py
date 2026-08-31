import os
import csv
import random

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASETS_DIR = os.path.join(BASE_DIR, 'datasets')
OUTPUT_CSV = os.path.join(DATASETS_DIR, 'recomind_completeness_v1.csv')

os.makedirs(DATASETS_DIR, exist_ok=True)

# Master Grounded Reference-to-Student Evidence Knowledge Base
# Spans 5 Domains: Physics, Chemistry, Biology, Mathematics, Geography
RAW_DATA_SPEC = [
    # =========================================================================
    # 1. PHYSICS (Class 11 & 12 NCERT)
    # =========================================================================
    {
        "subject": "Physics",
        "education_level": "Class 12",
        "chapter": "Electrostatic Potential and Capacitance",
        "topic_name": "Parallel Plate Capacitor",
        "reference_component": "Capacitance of a parallel plate capacitor in vacuum is C = (epsilon_0 * A) / d where A is plate area and d is separation.",
        "component_type": "formula",
        "source_type": "NCERT Textbooks",
        "source_reference": "NCERT Class 12 Physics Part 1, Chapter 2, Section 2.8",
        "variations": [
            ("For two parallel conducting plates of area A separated by distance d in vacuum, capacitance is C = e0 * A / d.", "FULLY_COVERED", 1.0, False),
            ("Parallel plate cap. formula: C = epsilon0 * A / d.", "FULLY_COVERED", 1.0, False),
            ("Capacitance depends on area A and plate distance d.", "PARTIALLY_COVERED", 0.5, True),
            ("Capacitance is the ratio of charge Q to potential difference V.", "PARTIALLY_COVERED", 0.5, True),
            ("Capacitors can be connected in series and parallel combinations.", "MISSING", 0.0, True),
            ("Current in a conductor is proportional to applied potential difference.", "MISSING", 0.0, False),
        ]
    },
    {
        "subject": "Physics",
        "education_level": "Class 12",
        "chapter": "Electrostatic Potential and Capacitance",
        "topic_name": "Energy Stored in a Capacitor",
        "reference_component": "Electrostatic potential energy stored in a charged capacitor is U = (1/2) * C * V^2 = Q^2 / (2C).",
        "component_type": "formula",
        "source_type": "NCERT Textbooks",
        "source_reference": "NCERT Class 12 Physics Part 1, Chapter 2, Section 2.10",
        "variations": [
            ("The energy stored in a charged capacitor is U = 1/2 C V^2 or Q^2 / 2C.", "FULLY_COVERED", 1.0, False),
            ("Stored energy U = 0.5 * C * V^2.", "FULLY_COVERED", 1.0, False),
            ("A charged capacitor stores electrostatic potential energy in its electric field.", "PARTIALLY_COVERED", 0.5, True),
            ("Energy stored U depends on capacitance C.", "PARTIALLY_COVERED", 0.5, True),
            ("Capacitors are used to store electric charge in electronic power supplies.", "MISSING", 0.0, True),
            ("Resistance dissipates energy as heat according to Joule's law H = I^2 R t.", "MISSING", 0.0, False),
        ]
    },
    {
        "subject": "Physics",
        "education_level": "Class 12",
        "chapter": "Electric Charges and Fields",
        "topic_name": "Field Due to Infinitely Long Straight Wire",
        "reference_component": "Derivation of electric field due to infinitely long wire using Gauss's Law yielding E = lambda / (2 * pi * epsilon_0 * r).",
        "component_type": "derivation",
        "source_type": "NCERT Textbooks",
        "source_reference": "NCERT Class 12 Physics Part 1, Chapter 1, Section 1.15",
        "variations": [
            ("Construct a cylindrical Gaussian surface of radius r and length L. Flux through end caps is 0. Curved flux = E(2*pi*r*L) = Q_enclosed/e0 = lambda*L/e0 => E = lambda / (2*pi*e0*r).", "FULLY_COVERED", 1.0, False),
            ("Electric field of long line charge is E = lambda / (2 * pi * e0 * r).", "PARTIALLY_COVERED", 0.5, True),
            ("A thin charged wire produces radial electric field outward.", "PARTIALLY_COVERED", 0.5, True),
            ("Long straight wire carries linear charge density lambda.", "MISSING", 0.0, True),
            ("Biot Savart law calculates magnetic field B = mu_0 I / (2 pi r) near a current carrying wire.", "MISSING", 0.0, False),
        ]
    },
    {
        "subject": "Physics",
        "education_level": "Class 12",
        "chapter": "Electric Charges and Fields",
        "topic_name": "Field Inside a Thin Spherical Shell",
        "reference_component": "Electric field inside a uniformly charged thin spherical shell (r < R) is strictly zero (E = 0) because enclosed charge is zero.",
        "component_type": "core_concept",
        "source_type": "NCERT Textbooks",
        "source_reference": "NCERT Class 12 Physics Part 1, Chapter 1, Section 1.15.3",
        "variations": [
            ("Inside a thin charged shell (r < R), enclosed charge Q_enc = 0. By Gauss law E*(4*pi*r^2) = 0 => E = 0 everywhere inside.", "FULLY_COVERED", 1.0, False),
            ("Electric field inside a thin spherical shell is zero (E = 0 for r < R).", "FULLY_COVERED", 1.0, False),
            ("A thin spherical shell carries total charge Q distributed on surface.", "PARTIALLY_COVERED", 0.5, True),
            ("Spherical shell has surface charge density sigma.", "PARTIALLY_COVERED", 0.5, True),
            ("Outside a spherical shell, electric field behaves as if all charge were at center E = kQ/r^2.", "MISSING", 0.0, True),
            ("Gravitational potential at Earth center is negative.", "MISSING", 0.0, False),
        ]
    },
    {
        "subject": "Physics",
        "education_level": "Class 12",
        "chapter": "Electromagnetic Induction",
        "topic_name": "Faraday's Law of Induction",
        "reference_component": "Induced electromotive force emf = - d(phi_B) / dt is proportional to negative rate of change of magnetic flux.",
        "component_type": "formula",
        "source_type": "NCERT Textbooks",
        "source_reference": "NCERT Class 12 Physics Part 1, Chapter 6, Section 6.3",
        "variations": [
            ("Faraday law states induced EMF is epsilon = - d(phi_B)/dt where negative sign represents Lenz's law direction.", "FULLY_COVERED", 1.0, False),
            ("Induced voltage = - dPhi / dt.", "FULLY_COVERED", 1.0, False),
            ("Changing magnetic field produces induced electric current in closed loop.", "PARTIALLY_COVERED", 0.5, True),
            ("Magnetic flux phi_B = B * A * cos(theta).", "PARTIALLY_COVERED", 0.5, True),
            ("Self inductance of solenoid is L = mu_0 * N^2 * A / l.", "MISSING", 0.0, True),
            ("Refraction occurs when light passes between optically dense media.", "MISSING", 0.0, False),
        ]
    },
    {
        "subject": "Physics",
        "education_level": "Class 12",
        "chapter": "Ray Optics and Optical Instruments",
        "topic_name": "Lens Maker's Formula",
        "reference_component": "Lens maker's formula 1/f = (n - 1) * (1/R1 - 1/R2) relates focal length f of a thin lens to refractive index n and radii of curvature R1, R2.",
        "component_type": "formula",
        "source_type": "NCERT Textbooks",
        "source_reference": "NCERT Class 12 Physics Part 2, Chapter 9, Section 9.5",
        "variations": [
            ("Lens maker formula: 1/f = (mu - 1) * (1/R1 - 1/R2) where R1 and R2 are radii of curvature of two lens surfaces.", "FULLY_COVERED", 1.0, False),
            ("1/f = (n - 1) (1/R1 - 1/R2) for thin spherical lens in air.", "FULLY_COVERED", 1.0, False),
            ("Focal length f of a thin lens depends on refractive index and surface curvature.", "PARTIALLY_COVERED", 0.5, True),
            ("Lens formula 1/v - 1/u = 1/f relates object and image distances.", "PARTIALLY_COVERED", 0.5, True),
            ("Total internal reflection occurs when light exceeds critical angle.", "MISSING", 0.0, True),
            ("Snell's law n1 sin(theta1) = n2 sin(theta2) governs refraction.", "MISSING", 0.0, False),
        ]
    },

    # =========================================================================
    # 2. CHEMISTRY (Class 11 & 12 NCERT)
    # =========================================================================
    {
        "subject": "Chemistry",
        "education_level": "Class 12",
        "chapter": "Chemical Kinetics",
        "topic_name": "Arrhenius Equation",
        "reference_component": "Arrhenius equation k = A * exp(-Ea / (R * T)) describes temperature dependence of reaction rate constant k.",
        "component_type": "formula",
        "source_type": "NCERT Textbooks",
        "source_reference": "NCERT Class 12 Chemistry Part 1, Chapter 4, Section 4.5",
        "variations": [
            ("Arrhenius equation k = A * e^(-Ea/RT) relates rate constant k to activation energy Ea and absolute temperature T.", "FULLY_COVERED", 1.0, False),
            ("ln(k2/k1) = (Ea/R) * (1/T1 - 1/T2) derived from Arrhenius equation.", "FULLY_COVERED", 1.0, False),
            ("Reaction rate constant k increases exponentially with absolute temperature T.", "PARTIALLY_COVERED", 0.5, True),
            ("Activation energy Ea is the minimum energy required to form activated complex.", "PARTIALLY_COVERED", 0.5, True),
            ("Order of a reaction can be zero, fractional, or integer determined experimentally.", "MISSING", 0.0, True),
            ("Catalysts lower activation energy without being consumed.", "MISSING", 0.0, True),
        ]
    },
    {
        "subject": "Chemistry",
        "education_level": "Class 12",
        "chapter": "Electrochemistry",
        "topic_name": "Nernst Equation",
        "reference_component": "Nernst equation for electrode potential E = E_0 - (RT / nF) * ln(Q) where Q is reaction quotient.",
        "component_type": "formula",
        "source_type": "NCERT Textbooks",
        "source_reference": "NCERT Class 12 Chemistry Part 1, Chapter 3, Section 3.3",
        "variations": [
            ("Nernst equation at 298K: E = E0 - (0.0591 / n) * log([Red]/[Ox]). Calculates cell EMF at non-standard concentrations.", "FULLY_COVERED", 1.0, False),
            ("Cell potential E = E0 - (RT/nF) ln Q.", "FULLY_COVERED", 1.0, False),
            ("Nernst equation calculates electrode potential at non-standard concentration.", "PARTIALLY_COVERED", 0.5, True),
            ("Standard cell potential E0_cell = E0_cathode - E0_anode.", "PARTIALLY_COVERED", 0.5, True),
            ("Faraday's first law of electrolysis states mass deposited is m = Z * Q.", "MISSING", 0.0, True),
            ("Galvanic cells convert chemical energy into electrical energy.", "MISSING", 0.0, False),
        ]
    },
    {
        "subject": "Chemistry",
        "education_level": "Class 11",
        "chapter": "Equilibrium",
        "topic_name": "Le Chatelier's Principle",
        "reference_component": "Le Chatelier's principle states that if a dynamic equilibrium is disturbed by changing concentration, pressure, or temperature, the system shifts to counteract the disturbance.",
        "component_type": "core_concept",
        "source_type": "NCERT Textbooks",
        "source_reference": "NCERT Class 11 Chemistry Part 1, Chapter 7, Section 7.8",
        "variations": [
            ("Le Chatelier principle: modifying temperature, pressure, or concentration of an equilibrium system shifts position in direction that counteracts the applied change.", "FULLY_COVERED", 1.0, False),
            ("System at equilibrium responds to stress by shifting left or right to re-establish equilibrium.", "FULLY_COVERED", 1.0, False),
            ("Equilibrium constant Kc depends only on temperature.", "PARTIALLY_COVERED", 0.5, True),
            ("Exothermic reactions shift left when temperature is increased.", "PARTIALLY_COVERED", 0.5, True),
            ("Catalysts increase both forward and reverse reaction rates equally without changing Kc.", "MISSING", 0.0, True),
            ("Buffer solutions maintain constant pH upon addition of small amounts of acid or base.", "MISSING", 0.0, False),
        ]
    },
    {
        "subject": "Chemistry",
        "education_level": "Class 12",
        "chapter": "Haloalkanes and Haloarenes",
        "topic_name": "SN1 vs SN2 Nucleophilic Substitution Mechanism",
        "reference_component": "SN1 mechanism involves carbocation intermediate with inversion/racemization, while SN2 involves concerted single-step transition state with complete inversion.",
        "component_type": "process",
        "source_type": "NCERT Textbooks",
        "source_reference": "NCERT Class 12 Chemistry Part 2, Chapter 10, Section 10.7",
        "variations": [
            ("SN1 proceeds via 2 steps with carbocation intermediate giving racemization. SN2 is 1 step concerted backside attack giving stereochemical inversion of configuration.", "FULLY_COVERED", 1.0, False),
            ("SN2 mechanism: bimolecular nucleophilic substitution with Walden inversion.", "FULLY_COVERED", 1.0, False),
            ("Nucleophilic substitution replaces halogen atom with nucleophile like OH-.", "PARTIALLY_COVERED", 0.5, True),
            ("Tertiary alkyl halides prefer SN1 due to carbocation stability.", "PARTIALLY_COVERED", 0.5, True),
            ("Electrophilic aromatic substitution occurs in benzene rings using Lewis acid catalysts.", "MISSING", 0.0, True),
            ("Grignard reagents react with carbonyl compounds to form alcohols.", "MISSING", 0.0, False),
        ]
    },
    {
        "subject": "Chemistry",
        "education_level": "Class 11",
        "chapter": "States of Matter",
        "topic_name": "Ideal Gas Equation",
        "reference_component": "Ideal gas equation P * V = n * R * T combines Boyle's law, Charles's law, and Avogadro's law for ideal gas behavior.",
        "component_type": "formula",
        "source_type": "NCERT Textbooks",
        "source_reference": "NCERT Class 11 Chemistry Part 1, Chapter 5, Section 5.5",
        "variations": [
            ("Ideal gas equation: P V = n R T where P is pressure, V is volume, n is moles, R is gas constant (8.314 J/mol K), and T is absolute temperature.", "FULLY_COVERED", 1.0, False),
            ("P * V = n * R * T combines gas laws into single state equation.", "FULLY_COVERED", 1.0, False),
            ("Ideal gas equation relates pressure P, volume V, and temperature T.", "PARTIALLY_COVERED", 0.5, True),
            ("Boyle's law states P is inversely proportional to V at constant T.", "PARTIALLY_COVERED", 0.5, True),
            ("Real gases deviate from ideal behavior at high pressure and low temperature due to intermolecular forces.", "MISSING", 0.0, True),
            ("Dalton's law of partial pressures P_total = P1 + P2 + P3.", "MISSING", 0.0, False),
        ]
    },

    # =========================================================================
    # 3. BIOLOGY (Class 11 & 12 NCERT)
    # =========================================================================
    {
        "subject": "Biology",
        "education_level": "Class 11",
        "chapter": "Cell: The Unit of Life",
        "topic_name": "Fluid Mosaic Model of Cell Membrane",
        "reference_component": "Fluid mosaic model describes cell membrane as a phospholipid bilayer with polar hydrophilic heads outside and nonpolar hydrophobic tails inside, with embedded proteins.",
        "component_type": "definition",
        "source_type": "NCERT Textbooks",
        "source_reference": "NCERT Class 11 Biology, Chapter 8, Section 8.5.1",
        "variations": [
            ("Fluid mosaic model proposed by Singer and Nicolson: quasi-fluid phospholipid bilayer with polar hydrophilic heads facing outward and nonpolar hydrophobic fatty acid tails facing inward, integrated with transport proteins.", "FULLY_COVERED", 1.0, False),
            ("Membrane structure: lipid bilayer with hydrophilic heads outside, hydrophobic tails inside.", "FULLY_COVERED", 1.0, False),
            ("Plasma membrane consists of lipids and proteins arranged in a bilayer.", "PARTIALLY_COVERED", 0.5, True),
            ("Cell membrane regulates active and passive transport of molecules.", "PARTIALLY_COVERED", 0.5, True),
            ("Cell wall in plants is made of cellulose providing structural rigidity.", "MISSING", 0.0, True),
            ("Mitochondria are double membrane bound organelles responsible for ATP synthesis.", "MISSING", 0.0, False),
        ]
    },
    {
        "subject": "Biology",
        "education_level": "Class 11",
        "chapter": "Photosynthesis in Higher Plants",
        "topic_name": "Light Reaction and Photophosphorylation",
        "reference_component": "Non-cyclic photophosphorylation (Z-scheme) involves Photosystems II and I, water splitting (photolysis), ATP synthesis, and NADPH formation.",
        "component_type": "process",
        "source_type": "NCERT Textbooks",
        "source_reference": "NCERT Class 11 Biology, Chapter 13, Section 13.6",
        "variations": [
            ("Light reactions occur in thylakoid membrane. PSII absorbs 680nm light, photolysis of water releases O2, electrons flow through Z-scheme to PSI generating ATP and NADPH.", "FULLY_COVERED", 1.0, False),
            ("Z-scheme light reaction splits water into 2H+, 2e-, and O2, producing ATP & NADPH.", "FULLY_COVERED", 1.0, False),
            ("Light reaction converts solar energy into chemical energy ATP.", "PARTIALLY_COVERED", 0.5, True),
            ("Photosynthesis occurs in chloroplast stroma and thylakoid membranes.", "PARTIALLY_COVERED", 0.5, True),
            ("Calvin cycle (dark reaction) fixes CO2 into glucose using RuBisCO enzyme in C3 plants.", "MISSING", 0.0, True),
            ("Plant transpiration moves water from roots to leaves through xylem vessel tracheids.", "MISSING", 0.0, False),
        ]
    },
    {
        "subject": "Biology",
        "education_level": "Class 12",
        "chapter": "Molecular Basis of Inheritance",
        "topic_name": "DNA Double Helix Structure",
        "reference_component": "Watson and Crick DNA double helix model features antiparallel polynucleotide chains with complementary base pairing (A=T with 2 H-bonds, G=C with 3 H-bonds).",
        "component_type": "definition",
        "source_type": "NCERT Textbooks",
        "source_reference": "NCERT Class 12 Biology, Chapter 6, Section 6.1",
        "variations": [
            ("DNA double helix consists of two antiparallel sugar-phosphate backbones. Adenine pairs with Thymine via 2 hydrogen bonds, Guanine pairs with Cytosine via 3 hydrogen bonds.", "FULLY_COVERED", 1.0, False),
            ("DNA structure: antiparallel double helix with complementary base pairs A=T (2 H-bonds) and G=C (3 H-bonds).", "FULLY_COVERED", 1.0, False),
            ("DNA consists of nitrogenous bases adenine, guanine, cytosine, and thymine.", "PARTIALLY_COVERED", 0.5, True),
            ("Watson and Crick proposed double helical structure of DNA in 1953.", "PARTIALLY_COVERED", 0.5, True),
            ("RNA contains ribose sugar and uracil base instead of thymine.", "MISSING", 0.0, True),
            ("Protein synthesis occurs at ribosomes via mRNA translation.", "MISSING", 0.0, False),
        ]
    },
    {
        "subject": "Biology",
        "education_level": "Class 12",
        "chapter": "Principles of Inheritance and Variation",
        "topic_name": "Mendel's Law of Segregation",
        "reference_component": "Mendel's Law of Segregation states that allele pairs separate during gamete formation so each gamete carries only one allele for each gene.",
        "component_type": "core_concept",
        "source_type": "NCERT Textbooks",
        "source_reference": "NCERT Class 12 Biology, Chapter 5, Section 5.2.1",
        "variations": [
            ("Law of segregation: during meiosis gametogenesis, the two alleles of a gene pair segregate cleanly so each haploid gamete receives only one allele.", "FULLY_COVERED", 1.0, False),
            ("Alleles segregate during gamete formation with 1:2:1 monohybrid genotypic ratio.", "FULLY_COVERED", 1.0, False),
            ("Monohybrid cross produces a 3:1 phenotypic ratio in F2 generation.", "PARTIALLY_COVERED", 0.5, True),
            ("Dominant alleles express in heterozygous conditions while recessive alleles require homozygous condition.", "PARTIALLY_COVERED", 0.5, True),
            ("Law of independent assortment states genes for different traits segregate independently during gamete formation.", "MISSING", 0.0, True),
            ("Sex determination in humans depends on XX female and XY male chromosome combinations.", "MISSING", 0.0, False),
        ]
    },
    {
        "subject": "Biology",
        "education_level": "Class 11",
        "chapter": "Biomolecules",
        "topic_name": "Enzyme Action and Mechanism",
        "reference_component": "Enzymes lower activation energy barrier to accelerate biochemical reactions via active site substrate binding (lock and key / induced fit).",
        "component_type": "process",
        "source_type": "NCERT Textbooks",
        "source_reference": "NCERT Class 11 Biology, Chapter 9, Section 9.8",
        "variations": [
            ("Enzymes act as biocatalysts by binding substrate at active site to form ES complex, lowering activation energy Ea without changing overall equilibrium.", "FULLY_COVERED", 1.0, False),
            ("Enzyme mechanism: substrate binds active site forming ES intermediate, lowering reaction activation energy.", "FULLY_COVERED", 1.0, False),
            ("Enzymes accelerate reaction velocity at optimum temperature and pH.", "PARTIALLY_COVERED", 0.5, True),
            ("Active site of enzyme binds specific substrate molecules.", "PARTIALLY_COVERED", 0.5, True),
            ("Competitive inhibitors bind active site competing with substrate Vmax remains constant while Km increases.", "MISSING", 0.0, True),
            ("Cofactors like coenzymes and prosthetic groups increase catalytic activity.", "MISSING", 0.0, False),
        ]
    },

    # =========================================================================
    # 4. MATHEMATICS (Class 11 & 12 NCERT)
    # =========================================================================
    {
        "subject": "Mathematics",
        "education_level": "Class 12",
        "chapter": "Integrals",
        "topic_name": "Integration by Parts",
        "reference_component": "Integration by parts formula is int(u * dv) = u * v - int(v * du) with ILATE rule for selecting first function u.",
        "component_type": "formula",
        "source_type": "NCERT Textbooks",
        "source_reference": "NCERT Class 12 Mathematics Part 2, Chapter 7, Section 7.5",
        "variations": [
            ("Integration by parts formula: int(u dv) = u*v - int(v du). ILATE rule determines priority for u: Inverse trig, Logarithmic, Algebraic, Trigonometric, Exponential.", "FULLY_COVERED", 1.0, False),
            ("int(f(x)g'(x)dx) = f(x)g(x) - int(f'(x)g(x)dx) with ILATE function selection.", "FULLY_COVERED", 1.0, False),
            ("Integration by parts is used to integrate product of two functions.", "PARTIALLY_COVERED", 0.5, True),
            ("Formula int(u dv) = u v - int(v du).", "PARTIALLY_COVERED", 0.5, True),
            ("Definite integral int_a^b f(x)dx represents net area under curve f(x) between x=a and x=b.", "MISSING", 0.0, True),
            ("Derivative of sin(x) is cos(x) and integral of cos(x) is sin(x) + C.", "MISSING", 0.0, False),
        ]
    },
    {
        "subject": "Mathematics",
        "education_level": "Class 12",
        "chapter": "Matrices and Determinants",
        "topic_name": "Inverse of a Matrix",
        "reference_component": "Inverse of a square matrix A exists if det(A) != 0 (non-singular) and is calculated by A^(-1) = (1 / det(A)) * adj(A).",
        "component_type": "formula",
        "source_type": "NCERT Textbooks",
        "source_reference": "NCERT Class 12 Mathematics Part 1, Chapter 4, Section 4.5",
        "variations": [
            ("Square matrix A has inverse A^-1 = (1 / det(A)) * adj(A) provided determinant det(A) != 0.", "FULLY_COVERED", 1.0, False),
            ("Inverse A^-1 = adj(A) / |A| exists only if |A| != 0 (non-singular matrix).", "FULLY_COVERED", 1.0, False),
            ("Inverse matrix satisfies property A * A^-1 = A^-1 * A = I.", "PARTIALLY_COVERED", 0.5, True),
            ("Adjugate matrix adj(A) is the transpose of cofactor matrix.", "PARTIALLY_COVERED", 0.5, True),
            ("Determinant of 2x2 matrix [[a,b],[c,d]] is ad - bc.", "MISSING", 0.0, True),
            ("System of linear equations can be solved using Cramer's rule.", "MISSING", 0.0, False),
        ]
    },
    {
        "subject": "Mathematics",
        "education_level": "Class 11",
        "chapter": "Limits and Derivatives",
        "topic_name": "First Principles Derivation",
        "reference_component": "Derivative of function f(x) from first principles is f'(x) = lim_{h->0} [f(x+h) - f(x)] / h.",
        "component_type": "derivation",
        "source_type": "NCERT Textbooks",
        "source_reference": "NCERT Class 11 Mathematics, Chapter 13, Section 13.5",
        "variations": [
            ("First principle of derivative: f'(x) = lim(h->0) [f(x+h) - f(x)] / h. Derives rate of change from secant slope limit.", "FULLY_COVERED", 1.0, False),
            ("Definition of derivative: dy/dx = lim_{h->0} [f(x+h) - f(x)] / h.", "FULLY_COVERED", 1.0, False),
            ("Derivative represents slope of tangent line to curve at point x.", "PARTIALLY_COVERED", 0.5, True),
            ("Product rule for derivatives: (u v)' = u' v + u v'.", "MISSING", 0.0, True),
            ("L'Hopital's rule evaluates 0/0 indeterminate limits by differentiating numerator and denominator.", "MISSING", 0.0, False),
        ]
    },
    {
        "subject": "Mathematics",
        "education_level": "Class 12",
        "chapter": "Probability",
        "topic_name": "Bayes' Theorem",
        "reference_component": "Bayes' theorem calculates conditional probability P(Ai|B) = [P(Ai) * P(B|Ai)] / sum[P(Ak) * P(B|Ak)] for partition events Ai.",
        "component_type": "formula",
        "source_type": "NCERT Textbooks",
        "source_reference": "NCERT Class 12 Mathematics Part 2, Chapter 13, Section 13.3",
        "variations": [
            ("Bayes theorem formula: P(E_i|A) = [P(E_i)*P(A|E_i)] / sum_{j=1}^n [P(E_j)*P(A|E_j)] for pairwise disjoint events E_i.", "FULLY_COVERED", 1.0, False),
            ("Bayes theorem: posterior probability P(A|B) = P(B|A)*P(A) / P(B).", "FULLY_COVERED", 1.0, False),
            ("Bayes theorem calculates reverse conditional probability given prior probabilities.", "PARTIALLY_COVERED", 0.5, True),
            ("Conditional probability P(A|B) = P(A intersection B) / P(B) where P(B) != 0.", "PARTIALLY_COVERED", 0.5, True),
            ("Independent events satisfy P(A and B) = P(A) * P(B).", "MISSING", 0.0, True),
            ("Binomial distribution mean is n*p and variance is n*p*q.", "MISSING", 0.0, False),
        ]
    },
    {
        "subject": "Mathematics",
        "education_level": "Class 10",
        "chapter": "Quadratic Equations",
        "topic_name": "Quadratic Formula and Discriminant",
        "reference_component": "Quadratic formula x = [-b +- sqrt(b^2 - 4ac)] / (2a) solves ax^2 + bx + c = 0 with discriminant D = b^2 - 4ac determining root nature.",
        "component_type": "formula",
        "source_type": "NCERT Textbooks",
        "source_reference": "NCERT Class 10 Mathematics, Chapter 4, Section 4.4",
        "variations": [
            ("Roots of ax^2 + bx + c = 0 given by x = (-b +- sqrt(b^2 - 4ac)) / (2a). Discriminant D = b^2 - 4ac: D>0 real distinct, D=0 real equal, D<0 complex.", "FULLY_COVERED", 1.0, False),
            ("Quadratic formula x = (-b +- sqrt(D)) / (2a) where D = b^2 - 4ac.", "FULLY_COVERED", 1.0, False),
            ("Discriminant D = b^2 - 4ac determines whether roots are real or imaginary.", "PARTIALLY_COVERED", 0.5, True),
            ("Sum of roots is -b/a and product of roots is c/a.", "PARTIALLY_COVERED", 0.5, True),
            ("Factoring method decomposes quadratic trinomial into linear factors.", "MISSING", 0.0, True),
            ("Arithmetic progression nth term is a_n = a + (n-1)d.", "MISSING", 0.0, False),
        ]
    },

    # =========================================================================
    # 5. GEOGRAPHY (Class 9 & 11 NCERT)
    # =========================================================================
    {
        "subject": "Geography",
        "education_level": "Class 11",
        "chapter": "Fundamentals of Physical Geography",
        "topic_name": "Theory of Plate Tectonics",
        "reference_component": "Theory of plate tectonics explains large-scale movement of Earth's lithospheric plates over convective asthenosphere forming divergent, convergent, and transform boundaries.",
        "component_type": "core_concept",
        "source_type": "NCERT Textbooks",
        "source_reference": "NCERT Class 11 Geography, Chapter 4, Section 4.4",
        "variations": [
            ("Earth's rigid outer lithosphere is broken into major and minor tectonic plates moving over warm convective asthenosphere. Plate interactions form divergent, convergent, and transform boundaries.", "FULLY_COVERED", 1.0, False),
            ("Plate tectonics: lithospheric plates float on asthenosphere, interacting along divergent (rift), convergent (trench/mountain), and transform faults.", "FULLY_COVERED", 1.0, False),
            ("Plate tectonics explains continental drift and mountain formation.", "PARTIALLY_COVERED", 0.5, True),
            ("Earth's crust is divided into tectonic plates.", "PARTIALLY_COVERED", 0.5, True),
            ("Plate tectonics was proposed by Alfred Wegener in 1912.", "MISSING", 0.0, True),
            ("Weathering breaks down surface rocks physically and chemically.", "MISSING", 0.0, False),
        ]
    },
    {
        "subject": "Geography",
        "education_level": "Class 11",
        "chapter": "Fundamentals of Physical Geography",
        "topic_name": "Locating Tectonic Plates on World Map",
        "reference_component": "Locating and mapping major tectonic plates (Pacific, Eurasian, African, Indo-Australian, North American, South American, Antarctic) on a world map.",
        "component_type": "process",
        "source_type": "NCERT Textbooks",
        "source_reference": "NCERT Class 11 Geography, Chapter 4, Section 4.4.1",
        "variations": [
            ("Mapping 7 major plates: Pacific plate surrounds Ring of Fire, Indo-Australian plate meets Eurasian plate at Himalayas, Mid-Atlantic Ridge lies between American and African plates.", "FULLY_COVERED", 1.0, False),
            ("World map plate locations: Pacific, Eurasian, African, Indo-Australian, North/South American, Antarctic plates.", "FULLY_COVERED", 1.0, False),
            ("Major tectonic plates are located across ocean basins and continents.", "PARTIALLY_COVERED", 0.5, True),
            ("Himalayas formed by collision of Indian and Eurasian plates.", "PARTIALLY_COVERED", 0.5, True),
            ("Earthquakes occur along fault lines and volcanic arcs.", "MISSING", 0.0, True),
            ("Tropical rainforests are located near the equator between 10N and 10S latitude.", "MISSING", 0.0, False),
        ]
    },
    {
        "subject": "Geography",
        "education_level": "Class 11",
        "chapter": "Landforms and their Evolution",
        "topic_name": "Agents of Gradation and River Landforms",
        "reference_component": "Running water as a geomorphic agent creates erosional landforms (V-shaped valleys, waterfalls, gorges) in youthful stage and depositional landforms (deltas, alluvial fans, levees) in old stage.",
        "component_type": "process",
        "source_type": "NCERT Textbooks",
        "source_reference": "NCERT Class 11 Geography, Chapter 7, Section 7.2",
        "variations": [
            ("Rivers erode V-shaped valleys, canyons, and waterfalls in steep upper courses, and deposit alluvial fans, meanders, and deltas in lower plains.", "FULLY_COVERED", 1.0, False),
            ("Fluvial landforms: upper course erosion creates gorges/waterfalls; lower course deposition creates oxbow lakes and deltas.", "FULLY_COVERED", 1.0, False),
            ("Running water is a primary agent of gradation shaping Earth's surface.", "PARTIALLY_COVERED", 0.5, True),
            ("Deltas are depositional landforms formed at river mouths.", "PARTIALLY_COVERED", 0.5, True),
            ("Glaciers form U-shaped glacial troughs, cirques, and moraines.", "MISSING", 0.0, True),
            ("Wind erosion creates sand dunes and mushroom rocks in arid desert regions.", "MISSING", 0.0, False),
        ]
    },
    {
        "subject": "Geography",
        "education_level": "Class 11",
        "chapter": "Natural Hazards and Disasters",
        "topic_name": "Causes of Disasters and Mitigation Strategies",
        "reference_component": "Natural disasters (earthquakes, landslides, GLOF, floods) require proactive mitigation strategies including hazard risk mapping, early warning systems, slope stabilization, and afforestation.",
        "component_type": "process",
        "source_type": "NCERT Textbooks",
        "source_reference": "NCERT Class 11 Geography, Chapter 7 (Disasters), Section 7.4",
        "variations": [
            ("Disaster mitigation strategies include hazard risk mapping, early warning sensor networks, earthquake resistant building codes, slope bio-engineering, and afforestation.", "FULLY_COVERED", 1.0, False),
            ("Mitigating natural hazards (landslides, GLOF, floods): risk mapping, early warning systems, slope stabilization, and disaster management plans.", "FULLY_COVERED", 1.0, False),
            ("Disaster mitigation involves preparing for natural hazards like earthquakes and floods.", "PARTIALLY_COVERED", 0.5, True),
            ("Landslides and earthquakes cause severe loss of life and property.", "PARTIALLY_COVERED", 0.5, True),
            ("Earthquakes are measured on the Richter scale for magnitude and Mercalli scale for intensity.", "MISSING", 0.0, True),
            ("Monsoon rainfall brings heavy water to Indian subcontinent between June and September.", "MISSING", 0.0, False),
        ]
    },
    {
        "subject": "Geography",
        "education_level": "Class 11",
        "chapter": "Atmosphere and Climate",
        "topic_name": "Atmospheric Pressure Belts and Planetary Winds",
        "reference_component": "Global atmospheric circulation features Equatorial Low (Doldrums), Subtropical Highs (Horse Latitudes), Subpolar Lows, and Polar Highs driving Trade Winds, Westerlies, and Easterlies.",
        "component_type": "core_concept",
        "source_type": "NCERT Textbooks",
        "source_reference": "NCERT Class 11 Geography, Chapter 10, Section 10.4",
        "variations": [
            ("Atmospheric pressure belts: Equatorial low pressure (doldrums), Subtropical high pressure (30N/S horse latitudes), Subpolar low (60N/S), Polar high. Trade winds blow from Subtropical High towards Equatorial Low.", "FULLY_COVERED", 1.0, False),
            ("Planetary wind system: Trade winds, Westerlies, and Polar Easterlies driven by pressure gradient force and Coriolis effect.", "FULLY_COVERED", 1.0, False),
            ("Pressure belts shift north and south with apparent movement of the sun.", "PARTIALLY_COVERED", 0.5, True),
            ("Coriolis force deflects winds to right in northern hemisphere and left in southern hemisphere.", "PARTIALLY_COVERED", 0.5, True),
            ("Monsoon winds are seasonal land and sea breeze systems over South Asia.", "MISSING", 0.0, True),
            ("Ocean currents are continuous directional movements of seawater driven by wind and density.", "MISSING", 0.0, False),
        ]
    }
]

# Formatting & Variation Generators to produce ~800 high-quality unique pairs
FORMATTING_STYLES = [
    lambda s: s, # Standard textbook line
    lambda s: f"- {s}", # Bullet point
    lambda s: f"Note: {s}", # Exam note
    lambda s: s.lower(), # Lowercase student text
    lambda s: s.replace("capacitance", "capcitance").replace("electric", "electrc").replace("formula", "formla").replace("mechanism", "mechnism"), # Simulated OCR typo
    lambda s: f"Exam Revision: {s} (Important for final exam)", # Exam revision note
    lambda s: s.replace("is", "=").replace("equals", "="), # ASCII formula heavy
    lambda s: f"Key Point: {s} [Summary]", # Summary note style
    lambda s: f"Student summary -- {s}", # Explicit student header
]

def generate_completeness_dataset():
    print("Generating RecoMind Phase 2 Supervised Note Completeness Dataset (recomind_completeness_v1.csv)...")
    records = []
    record_id_counter = 1

    random.seed(42)

    # Generate realistic student note variations across specifications
    for spec in RAW_DATA_SPEC:
        subject = spec["subject"]
        edu = spec["education_level"]
        chapter = spec["chapter"]
        topic = spec["topic_name"]
        ref_comp = spec["reference_component"]
        comp_type = spec["component_type"]
        src_type = spec["source_type"]
        src_ref = spec["source_reference"]

        for (evidence_template, label, score, is_hn) in spec["variations"]:
            # Generate 8 realistic student note variations per template
            for idx in range(8):
                style_func = FORMATTING_STYLES[idx % len(FORMATTING_STYLES)]
                student_ev = style_func(evidence_template)
                
                # Add realistic note noise
                if idx == 2 and label == "FULLY_COVERED":
                    student_ev += " [Ref: NCERT Chapter notes]"
                elif idx == 4 and label == "PARTIALLY_COVERED":
                    student_ev += " (refer to diagram for full details)"

                rec_id = f"REC-{subject[:3].upper()}-{record_id_counter:05d}"
                record_id_counter += 1

                records.append({
                    "id": rec_id,
                    "subject": subject,
                    "education_level": edu,
                    "chapter": chapter,
                    "topic_name": topic,
                    "reference_component": ref_comp,
                    "component_type": comp_type,
                    "student_note_evidence": student_ev,
                    "label": label,
                    "numeric_score": score,
                    "is_hard_negative": is_hn,
                    "source_type": src_type,
                    "source_reference": src_ref
                })

    # Exact Duplicate Removal
    unique_records = []
    seen_pairs = set()
    for r in records:
        pair_key = (r["reference_component"].strip().lower(), r["student_note_evidence"].strip().lower())
        if pair_key not in seen_pairs:
            seen_pairs.add(pair_key)
            unique_records.append(r)

    # Shuffle dataset deterministically
    random.shuffle(unique_records)

    # Save to CSV
    fieldnames = [
        "id", "subject", "education_level", "chapter", "topic_name",
        "reference_component", "component_type", "student_note_evidence",
        "label", "numeric_score", "is_hard_negative", "source_type", "source_reference"
    ]

    with open(OUTPUT_CSV, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(unique_records)

    print(f"\n[SUCCESS] Generated and saved dataset to: {OUTPUT_CSV}")
    print(f"Total Unique Records: {len(unique_records)}")

if __name__ == "__main__":
    generate_completeness_dataset()
