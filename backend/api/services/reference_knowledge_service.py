import re
import hashlib
import logging
from django.db import DatabaseError

logger = logging.getLogger(__name__)

# Subject Knowledge Domain Patterns & Specialized Concept Templates
DOMAIN_KNOWLEDGE_TEMPLATES = {
    "physics": {
        "definition": "Formal physics definition and fundamental governing laws.",
        "core_concepts": ["Physical phenomenon", "Governing principles", "Boundary conditions", "SI units and dimensional formula"],
        "subtopics": ["Primary relationship", "Vector/scalar properties", "Field line / wave behavior"],
        "formulas": ["Primary governing equation", "Proportionality relationship", "Vector field equation"],
        "derivations": ["Mathematical derivation from first principles", "Boundary condition proof"],
        "important_points": ["Assumptions and limitations", "Direction rules (Right hand thumb rule / Fleming rule)", "SI units"],
        "examples_or_applications": ["Real-world physical application", "Standard laboratory setup", "Numerical problem scenario"]
    },
    "chemistry": {
        "definition": "Chemical definition, molecular composition, and reaction principles.",
        "core_concepts": ["Reaction mechanism", "Thermodynamic stability", "Chemical equilibrium", "Periodic trend"],
        "subtopics": ["Synthesis / Preparation method", "Physical properties", "Chemical reactivity"],
        "formulas": ["Stoichiometric chemical equation", "Rate law / Equilibrium constant expression"],
        "derivations": ["Kinetic / Thermodynamic equation derivation"],
        "important_points": ["Catalysts and reaction conditions", "Oxidation states", "Safety and environmental impact"],
        "examples_or_applications": ["Industrial synthesis process", "Laboratory reagent test", "Commercial application"]
    },
    "biology": {
        "definition": "Biological definition, anatomical structure, and physiological function.",
        "core_concepts": ["Cellular / Structural organization", "Physiological mechanism", "Metabolic pathway", "Homeostatic regulation"],
        "subtopics": ["Anatomical components", "Functional stages", "Hormonal / Enzymatic control"],
        "formulas": [],
        "derivations": [],
        "important_points": ["Key biological terms", "Diagrammatic representation & labeling", "Pathological / Clinical relevance"],
        "examples_or_applications": ["Model organism / Human organ system example", "Ecological / Evolutionary impact"]
    },
    "geography": {
        "definition": "Geomorphic / Spatial definition and natural process overview.",
        "core_concepts": ["Exogenic / Endogenic forces", "Spatial distribution", "Geological timeframe", "Environmental interaction"],
        "subtopics": ["Formation mechanism", "Landform classification", "Climatic / Tectonic factors"],
        "formulas": [],
        "derivations": [],
        "important_points": ["Key geographical terminology", "World / Regional map distribution", "Causes and effects"],
        "examples_or_applications": ["Specific regional landform example", "Disaster mitigation & hazard mapping"]
    },
    "mathematics": {
        "definition": "Formal mathematical definition, domain conditions, and theorem statement.",
        "core_concepts": ["Fundamental theorem", "Algebraic / Geometric properties", "Existence & uniqueness conditions"],
        "subtopics": ["Standard form equation", "Special cases & identity limits"],
        "formulas": ["Primary mathematical formula", "Derivative / Integral / Series expansion"],
        "derivations": ["Rigorous step-by-step mathematical proof"],
        "important_points": ["Domain and range constraints", "Common calculation pitfalls"],
        "examples_or_applications": ["Worked numerical example", "Geometric / Applied optimization problem"]
    },
    "economics": {
        "definition": "Economic concept definition, market relationship, and behavioral principle.",
        "core_concepts": ["Demand and supply interaction", "Price elasticity", "Equilibrium condition", "Policy impact"],
        "subtopics": ["Determinants / Factors", "Market structure classification"],
        "formulas": ["Elasticity / Cost / Revenue formula", "Index calculation"],
        "derivations": ["Utility / Output maximization condition"],
        "important_points": ["Curve movements vs shifts", "Assumptions (Ceteris Paribus)"],
        "examples_or_applications": ["Real-world market scenario", "Government fiscal / Monetary policy case"]
    },
    "general": {
        "definition": "Academic concept definition and structural overview.",
        "core_concepts": ["Core theoretical framework", "Key operational principles", "Fundamental classifications"],
        "subtopics": ["Primary sub-topics", "Functional components"],
        "formulas": [],
        "derivations": [],
        "important_points": ["Essential terminology", "Critical analysis points"],
        "examples_or_applications": ["Case study example", "Practical real-world application"]
    }
}

# Explicit Academic Topic Profiles for Cross-Disciplinary Knowledge Retrieval
EXPLICIT_TOPIC_KNOWLEDGE_BASE = {
    "theory of plate tectonics": {
        "subject_domain": "Geography",
        "definition": "Theory explaining the large-scale movement of Earth's lithospheric plates (outer rigid layer) over the asthenosphere.",
        "core_concepts": ["Lithospheric plates / outer rigid layer of Earth", "Asthenosphere convection currents", "Seafloor spreading", "Continental drift"],
        "subtopics": ["Divergent boundaries", "Convergent boundaries", "Transform fault boundaries"],
        "formulas": [],
        "derivations": [],
        "important_points": ["Pacific Ring of Fire", "Plate boundary types and relative plate motion", "Causes of earthquakes and volcanism"],
        "examples_or_applications": ["Himalayan mountain building (Indian-Eurasian convergence)", "Mid-Atlantic Ridge", "San Andreas Fault"]
    },

    "interior of the earth": {
        "subject_domain": "Geography",
        "definition": "Concentric layer structure of Earth determined by seismic wave propagation.",
        "core_concepts": ["Crust (SiAl/SiMa)", "Mantle (Asthenosphere)", "Outer Core (liquid Fe-Ni)", "Inner Core (solid Fe-Ni)"],
        "subtopics": ["Lithosphere", "Asthenosphere", "Discontinuities (Moho, Gutenberg)"],
        "formulas": [],
        "derivations": [],
        "important_points": ["Temperature and pressure gradient with depth", "P-wave and S-wave shadow zones"],
        "examples_or_applications": ["Seismic wave velocity changes", "Geomagnetic field generation in outer core"]
    },
    "weathering and erosion": {
        "subject_domain": "Geography",
        "definition": "Exogenic processes involving rock breakdown (weathering) and sediment transport (erosion).",
        "core_concepts": ["Physical/Mechanical weathering", "Chemical weathering", "Biological weathering", "Erosion and transport"],
        "subtopics": ["Frost wedging", "Oxidation and carbonation", "Mass wasting / landslides"],
        "formulas": [],
        "derivations": [],
        "important_points": ["In-situ breakdown vs active transport", "Climate influence on weathering rate"],
        "examples_or_applications": ["Karst topography in limestone", "Soil formation processes"]
    },
    "agents of gradation": {
        "subject_domain": "Geography",
        "definition": "Exogenic geomorphic agents that erode, transport, and deposit sediments to level Earth's surface.",
        "core_concepts": ["Running water (rivers)", "Sea waves and currents", "Wind (eolian action)", "Glaciers", "Underground water"],
        "subtopics": ["Erosional landforms", "Transportation mechanisms", "Depositional landforms"],
        "formulas": [],
        "derivations": [],
        "important_points": ["Gradation = Degradation (erosion) + Aggradation (deposition)"],
        "examples_or_applications": ["V-shaped valleys & waterfalls", "U-shaped glacial troughs", "Sand dunes & deltas"]
    },
    "locate major tectonic plates": {
        "subject_domain": "Geography",
        "definition": "Locating and mapping major tectonic plates (Pacific, Eurasian, African, Indo-Australian, North/South American, Antarctic) on a world map.",
        "core_concepts": ["World map distribution of tectonic plates", "Major vs minor tectonic plate locations", "Plate boundary coordinates"],
        "subtopics": ["Pacific Ring of Fire location", "Plate boundary map identification"],
        "formulas": [],
        "derivations": [],
        "important_points": ["Map identification of 7 major plates", "Geographical position of plate boundaries on world map"],
        "examples_or_applications": ["Locating San Andreas Fault on North American map", "Locating Himalayan convergence zone on Asia map"]
    },
    "causes of natural disasters": {
        "subject_domain": "Geography",
        "definition": "Causes, environmental triggers, and mitigation strategies for natural hazards and geological disasters.",
        "core_concepts": ["Natural disaster triggers", "Earthquake, landslide, GLOF, avalanche mechanisms", "Disaster mitigation and management"],
        "subtopics": ["Early warning systems", "Hazard zoning and risk mapping", "Slope stabilization and afforestation"],
        "formulas": [],
        "derivations": [],
        "important_points": ["Proactive mitigation vs reactive response", "Structural and non-structural mitigation strategies"],
        "examples_or_applications": ["GLOF mitigation in Himalayan glacial lakes", "Earthquake resistant building design"]
    },
    "describe major landforms": {
        "subject_domain": "Geography",
        "definition": "Classification and formation processes of major erosional and depositional landforms created by geomorphic agents.",
        "core_concepts": ["Erosional landform formation", "Depositional landform formation", "Geomorphic agent action"],
        "subtopics": ["Fluvial landforms (deltas, waterfalls)", "Glacial landforms (cirques, U-shaped valleys)", "Eolian landforms (sand dunes)"],
        "formulas": [],
        "derivations": [],
        "important_points": ["Stage of river profile (youthful, mature, old)", "Glacial vs fluvial valley cross-sections"],
        "examples_or_applications": ["Grand Canyon river erosion", "Sahara desert sand dunes"]
    }
}


def detect_subject_domain(topic: str, chapter_title: str = "", syllabus_title: str = "") -> str:
    """
    Detects the academic subject domain for a given topic, chapter, and syllabus string.
    """
    text = f"{syllabus_title} {chapter_title} {topic}".lower()

    if any(k in text for k in ['physics', 'electric', 'magnetic', 'charge', 'optics', 'mechanics', 'force', 'energy', 'wave']):
        return "physics"
    elif any(k in text for k in ['chemistry', 'reaction', 'molecule', 'organic', 'acid', 'base', 'atom', 'periodic']):
        return "chemistry"
    elif any(k in text for k in ['biology', 'cell', 'organism', 'anatomy', 'gene', 'tissue', 'plant', 'human']):
        return "biology"
    elif any(k in text for k in ['geography', 'earth', 'plate', 'climate', 'landform', 'river', 'weather', 'disaster']):
        return "geography"
    elif any(k in text for k in ['math', 'calculus', 'algebra', 'matrix', 'vector', 'geometry', 'equation', 'integral']):
        return "mathematics"
    elif any(k in text for k in ['economics', 'market', 'demand', 'supply', 'finance', 'budget', 'cost', 'trade']):
        return "economics"
    return "general"


def clean_topic_heading(topic: str) -> str:
    """
    Strips bloom's taxonomy verbs and noise words from topic strings.
    e.g. 'Describe major landforms and explain the processes involved...' -> 'Major landforms and formation processes'
    """
    t = topic.strip()
    t = re.sub(r'^(describe|explain|locate|analyse|analyze|understand|identify|categorise|categorize|propose|evaluate)\s+', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\s+(with suitable examples|operating in a given region|and analyse its relevance).*$', '', t, flags=re.IGNORECASE)
    return t.strip()


def build_topic_knowledge_profile(topic: str, chapter_title: str = "", syllabus_title: str = "") -> dict:
    """
    Retrieves or constructs a structured Academic Reference Knowledge Profile for a given topic.
    Returns structured content: definition, core_concepts, subtopics, formulas, derivations, important_points, examples.
    """
    topic_clean = topic.strip()
    topic_lower = topic_clean.lower()

    # 1. Check explicit knowledge base
    for k_key, k_profile in EXPLICIT_TOPIC_KNOWLEDGE_BASE.items():
        if k_key in topic_lower or topic_lower in k_key:
            res = dict(k_profile)
            res["topic"] = topic_clean
            res["source_type"] = "official_curriculum"
            return res

    # 2. Dynamic subject domain detection & clean core keyword extraction
    domain_key = detect_subject_domain(topic_clean, chapter_title, syllabus_title)
    kw_str = clean_topic_heading(topic_clean)

    structured_profile = {
        "topic": topic_clean,
        "subject_domain": domain_key.capitalize(),
        "definition": f"Core academic definition and theoretical principles governing {kw_str}.",
        "core_concepts": [
            f"Fundamental principles of {kw_str}",
            f"Primary mechanisms and governing factors of {kw_str}",
            f"Classification and properties of {kw_str}"
        ],
        "subtopics": [
            f"Key components and stages of {kw_str}",
            f"Quantitative/qualitative properties of {kw_str}"
        ],
        "formulas": [f"Primary governing formula for {kw_str}"] if domain_key in ["physics", "chemistry", "mathematics", "economics"] else [],
        "derivations": [f"Mathematical derivation for {kw_str}"] if domain_key in ["physics", "mathematics"] else [],
        "important_points": [
            f"Key definitions and terminology related to {kw_str}",
            f"Primary boundary conditions and assumptions",
            f"Standard exam questions and retention points for {kw_str}"
        ],
        "examples_or_applications": [
            f"Standard real-world application of {kw_str}",
            f"Practical case study / experimental example of {kw_str}"
        ],
        "source_type": "educational_reference"
    }

    return structured_profile



def get_or_create_reference_profile(topic: str, chapter_title: str = "", syllabus_title: str = "") -> dict:
    """
    High-performance Reference Knowledge Layer with DB Caching.
    Retrieves stored profile from ReferenceKnowledgeCache or creates and caches a fresh profile.
    """
    if not topic or not isinstance(topic, str) or not topic.strip():
        return {}

    topic_clean = topic.strip()
    key_str = f"{syllabus_title}:{chapter_title}:{topic_clean}".lower()
    cache_key = hashlib.sha256(key_str.encode('utf-8')).hexdigest()[:32]

    # Try DB cache
    try:
        from api.models import ReferenceKnowledgeCache
        cached_entry = ReferenceKnowledgeCache.objects.filter(cache_key=cache_key).first()
        if cached_entry and cached_entry.structured_profile:
            logger.info(f"Loaded reference knowledge profile from cache for topic: '{topic_clean}'")
            return cached_entry.structured_profile
    except Exception as e:
        logger.warning(f"Reference cache read skipped: {e}")

    # Generate reference profile
    profile = build_topic_knowledge_profile(topic_clean, chapter_title, syllabus_title)

    # Save to DB cache
    try:
        from api.models import ReferenceKnowledgeCache
        ReferenceKnowledgeCache.objects.create(
            cache_key=cache_key,
            syllabus_title=syllabus_title[:250],
            chapter_title=chapter_title[:250],
            topic_name=topic_clean[:250],
            structured_profile=profile,
            source_type=profile.get("source_type", "academic_curriculum")
        )
        logger.info(f"Cached new reference knowledge profile for topic: '{topic_clean}'")
    except Exception as e:
        logger.warning(f"Reference cache write skipped: {e}")

    return profile
