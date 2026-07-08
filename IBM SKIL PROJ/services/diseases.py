"""
services/diseases.py
─────────────────────
Curated pest & disease database for the dedicated Diseases page.
"""

DISEASE_DB = [
    {
        "id": 1, "name": "Fall Armyworm", "scientific": "Spodoptera frugiperda",
        "crop": "Maize", "type": "Pest", "severity": "High",
        "symptoms": "Window-pane feeding on leaves; frass (excrement) visible in the whorl; ragged leaf edges.",
        "spread": "Adult moths fly at night; larvae spread through wind and movement.",
        "chemical_control": "Spinetoram 11.7% SC @ 0.5 ml/L water",
        "organic_control": "Release Trichogramma cards @ 50,000/ha; HNPV spray @ 500 LE/ha",
        "prevention": "Early sowing; crop rotation with non-host crops; install pheromone traps @ 5/ha.",
        "icon": "🐛", "color": "#dc2626"
    },
    {
        "id": 2, "name": "Tomato Leaf Curl Virus", "scientific": "Tomato Yellow Leaf Curl Virus (TYLCV)",
        "crop": "Tomato", "type": "Virus", "severity": "High",
        "symptoms": "Upward leaf curling; yellowing of leaf margins; stunted plant growth; reduced fruit set.",
        "spread": "Whitefly (Bemisia tabaci) is the primary vector; spreads rapidly in dry, hot weather.",
        "chemical_control": "Imidacloprid 17.8% SL @ 0.25 ml/L to control whitefly vector",
        "organic_control": "Yellow sticky traps; neem oil 3% spray; reflective mulches to repel whitefly",
        "prevention": "Use TYLCV-resistant varieties; avoid planting near tobacco; remove infected plants immediately.",
        "icon": "🍃", "color": "#dc2626"
    },
    {
        "id": 3, "name": "Rice Blast", "scientific": "Magnaporthe oryzae",
        "crop": "Rice", "type": "Fungal", "severity": "High",
        "symptoms": "Diamond or spindle-shaped lesions with grey/white center and brown border on leaves; neck rot in severe cases.",
        "spread": "Wind-dispersed spores; favoured by 24–28°C temperatures and high humidity.",
        "chemical_control": "Tricyclazole 75% WP @ 0.6 g/L or Propiconazole 25% EC @ 1 ml/L",
        "organic_control": "Silicon-rich soil amendments; Pseudomonas fluorescens @ 5 g/L as foliar spray",
        "prevention": "Avoid excess nitrogen; use resistant varieties; maintain field hygiene; balanced fertilisation.",
        "icon": "🌾", "color": "#dc2626"
    },
    {
        "id": 4, "name": "Cotton Bollworm", "scientific": "Helicoverpa armigera",
        "crop": "Cotton", "type": "Pest", "severity": "High",
        "symptoms": "Bored entry holes in bolls; dark frass at entry points; premature boll opening.",
        "spread": "Adult moths lay eggs singly on tender plant parts; larvae bore into bolls.",
        "chemical_control": "Emamectin benzoate 5% SG @ 0.4 g/L or Spinosad 45% SC @ 0.3 ml/L",
        "organic_control": "Pheromone traps @ 5/ha; NPV spray @ 250 LE/ha; release Chrysoperla @ 50,000 eggs/ha",
        "prevention": "Avoid monoculture; inter-crop with marigold; avoid late sowing; monitor with pheromone traps.",
        "icon": "🐚", "color": "#dc2626"
    },
    {
        "id": 5, "name": "Aphids", "scientific": "Various spp.",
        "crop": "Mustard", "type": "Pest", "severity": "Medium",
        "symptoms": "Colonies of small soft-bodied insects on tender shoots; honeydew secretion; sooty mould.",
        "spread": "Winged forms spread to new plants; populations explode in cool, moist weather.",
        "chemical_control": "Dimethoate 30% EC @ 1 ml/L or Thiamethoxam 25% WG @ 0.3 g/L",
        "organic_control": "Introduce ladybird beetles (Coccinella spp.); neem oil 2% spray; soap water spray",
        "prevention": "Avoid excess nitrogen; plant border crops of mustard to trap aphids; timely monitoring.",
        "icon": "🐞", "color": "#ea580c"
    },
    {
        "id": 6, "name": "Helicoverpa (Gram Pod Borer)", "scientific": "Helicoverpa armigera",
        "crop": "Chickpea", "type": "Pest", "severity": "Medium",
        "symptoms": "Circular holes in pods; partly eaten grains; greenish larvae with lateral stripes.",
        "spread": "Adult moths attracted to flowering plants; highly polyphagous pest.",
        "chemical_control": "Indoxacarb 15.8% EC @ 0.7 ml/L or Chlorantraniliprole 18.5% SC @ 0.3 ml/L",
        "organic_control": "HNPV spray @ 250 LE/ha; pheromone traps @ 5/ha; Bt (Bacillus thuringiensis) spray",
        "prevention": "Inter-cropping with coriander or fennel; avoid late sowing; use resistant varieties (Vijay, Avrodhi).",
        "icon": "🫘", "color": "#ea580c"
    },
    {
        "id": 7, "name": "Wheat Yellow Rust", "scientific": "Puccinia striiformis",
        "crop": "Wheat", "type": "Fungal", "severity": "High",
        "symptoms": "Yellow-orange pustules in stripes along leaf veins; severe cases cause entire leaf yellowing.",
        "spread": "Wind-borne uredospores; favoured by cool (10–15°C) and moist conditions.",
        "chemical_control": "Propiconazole 25% EC @ 1 ml/L or Tebuconazole 25.9% EC @ 1 ml/L",
        "organic_control": "Spray of Trichoderma viride @ 5 g/L as preventive; potassium silicate foliar spray",
        "prevention": "Use resistant varieties (HD-2967, HD-3086); avoid dense sowing; timely sowing in October–November.",
        "icon": "🌻", "color": "#dc2626"
    },
    {
        "id": 8, "name": "Early Blight", "scientific": "Alternaria solani",
        "crop": "Potato", "type": "Fungal", "severity": "Medium",
        "symptoms": "Dark brown concentric ring lesions on older leaves; premature defoliation; tuber rot in severe cases.",
        "spread": "Soil-borne and air-borne spores; spreads rapidly in warm (24–29°C) humid conditions.",
        "chemical_control": "Mancozeb 75% WP @ 2 g/L or Chlorothalonil 75% WP @ 2 g/L",
        "organic_control": "Copper oxychloride 50% WP @ 3 g/L; Bordeaux mixture 1%; remove and destroy infected leaves",
        "prevention": "Certified disease-free seed tubers; crop rotation; avoid overhead irrigation; proper plant spacing.",
        "icon": "🥔", "color": "#ea580c"
    },
    {
        "id": 9, "name": "Pink Bollworm", "scientific": "Pectinophora gossypiella",
        "crop": "Cotton", "type": "Pest", "severity": "Medium",
        "symptoms": "Rosette flowers (failed squares); pink larvae inside bolls; stained lint.",
        "spread": "Larvae overwinter in old bolls; major in areas with late harvest.",
        "chemical_control": "Cypermethrin 10% EC @ 1 ml/L; avoid early harvest losses by timely picking",
        "organic_control": "Pheromone traps (Gossyplure); hot water seed treatment before sowing",
        "prevention": "Destroy crop stubble; use Bt-cotton varieties; avoid ratoon cotton; early planting.",
        "icon": "🩷", "color": "#ea580c"
    },
    {
        "id": 10, "name": "Sooty Mould", "scientific": "Capnodium spp.",
        "crop": "Sugarcane", "type": "Fungal", "severity": "Low",
        "symptoms": "Black sooty coating on leaves; grows on honeydew excreted by mealybugs or aphids.",
        "spread": "Secondary to honeydew-secreting insect infestations.",
        "chemical_control": "Control primary insect vector first; wash leaves with water jet",
        "organic_control": "Starch solution spray to peel off sooty mould; neem oil to control vectors",
        "prevention": "Control mealybug and aphid populations; ensure good air circulation in the canopy.",
        "icon": "🖤", "color": "#16a34a"
    },
    {
        "id": 11, "name": "Brown Plant Hopper", "scientific": "Nilaparvata lugens",
        "crop": "Rice", "type": "Pest", "severity": "High",
        "symptoms": "'Hopper burn' — circular patches of dried, dead rice plants; heavily populated plants collapse.",
        "spread": "Migrates on wind currents; populations explode with excess nitrogen and close plant spacing.",
        "chemical_control": "Buprofezin 25% SC @ 1.25 ml/L or Thiamethoxam 25% WG @ 0.3 g/L",
        "organic_control": "Drain water for 3–4 days (breaks humid micro-climate); spiders as natural predators",
        "prevention": "Avoid excess nitrogen; maintain recommended plant spacing; use BPH-resistant varieties.",
        "icon": "🦗", "color": "#dc2626"
    },
    {
        "id": 12, "name": "Collar Rot", "scientific": "Sclerotium rolfsii",
        "crop": "Groundnut", "type": "Fungal", "severity": "Medium",
        "symptoms": "Water-soaked lesions at stem base near soil; white mycelial growth; wilting and plant death.",
        "spread": "Soil-borne; favoured by warm (28–35°C), moist conditions; spreads through infected soil and water.",
        "chemical_control": "Carbendazim 50% WP @ 1 g/L as soil drench; Tebuconazole 25.9% EC @ 1 ml/L",
        "organic_control": "Trichoderma viride @ 4 g/kg seed treatment; apply FYM-Trichoderma mixture in furrow",
        "prevention": "Crop rotation (avoid groundnut–groundnut); deep ploughing to expose sclerotia; seed treatment.",
        "icon": "🥜", "color": "#ea580c"
    },
]
