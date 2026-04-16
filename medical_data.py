"""
Base de données médicale pour le chatbot.
Contient les symptômes, spécialités, protocoles et guides médicaux.
"""

import json
from typing import Dict, List, Optional

# Chargement des données depuis le fichier JSON
with open('medical_data.json', 'r', encoding='utf-8') as f:
    MEDICAL_DATA = json.load(f)

# Base de données des symptômes
SYMPTOMS_DATABASE = {}
# Base de données des spécialités
SPECIALTIES_DATABASE = {}
# Base de données des protocoles médicaux
MEDICAL_GUIDELINES = {}
# Base de données des interactions médicamenteuses
DRUG_INTERACTIONS = {}
# Base de données des protocoles COVID
COVID_PROTOCOLS = {}

def _initialize_databases():
    """Initialise les bases de données à partir des données JSON."""
    for entry in MEDICAL_DATA:
        # Traitement des symptômes
        if "Symptômes" in entry:
            symptoms = entry["Symptômes"]
            if isinstance(symptoms, str):
                symptoms = symptoms.split(", ")
            for symptom in symptoms:
                if symptom not in SYMPTOMS_DATABASE:
                    SYMPTOMS_DATABASE[symptom] = {
                        "variations": [],
                        "related_diseases": []
                    }
                SYMPTOMS_DATABASE[symptom]["related_diseases"].append(entry.get("Maladies", ""))

        # Traitement des maladies
        if "Maladie" in entry:
            disease_name = entry["Maladie"]
            MEDICAL_GUIDELINES[disease_name] = {
                "description": entry.get("Description", ""),
                "symptoms": entry.get("Symptômes", []),
                "urgency": entry.get("Urgence", "NON"),
                "treatments": entry.get("Traitements", []),
                "medications": entry.get("Médicaments", []),
                "actions": entry.get("Actions recommandées", "")
            }

        # Traitement des médicaments
        if "Médicaments/Traitements" in entry:
            medications = entry["Médicaments/Traitements"]
            if isinstance(medications, str):
                medications = medications.split(", ")
            for med in medications:
                if med not in DRUG_INTERACTIONS:
                    DRUG_INTERACTIONS[med] = {
                        "interactions": [],
                        "contre_indications": []
                    }

# Initialisation des bases de données
_initialize_databases()

def get_symptom_info(symptom: str) -> Optional[Dict]:
    """Récupère les informations sur un symptôme."""
    return SYMPTOMS_DATABASE.get(symptom.lower())

def get_specialty_info(specialty: str) -> Optional[Dict]:
    """Récupère les informations sur une spécialité médicale."""
    return SPECIALTIES_DATABASE.get(specialty.lower())

def get_emergency_protocol(symptom: str) -> Optional[Dict]:
    """Récupère le protocole d'urgence pour un symptôme."""
    for disease, info in MEDICAL_GUIDELINES.items():
        if symptom.lower() in [s.lower() for s in info.get("symptoms", [])] and info.get("urgency") == "OUI":
            return {
                "disease": disease,
                "protocol": info.get("actions", ""),
                "medications": info.get("medications", [])
            }
    return None

def get_advice(symptom: str) -> Optional[str]:
    """Récupère les conseils pour un symptôme."""
    for disease, info in MEDICAL_GUIDELINES.items():
        if symptom.lower() in [s.lower() for s in info.get("symptoms", [])]:
            return info.get("actions", "")
    return None

def get_drug_interactions(medication: str) -> Dict:
    """Récupère les interactions médicamenteuses pour un médicament."""
    return DRUG_INTERACTIONS.get(medication, {
        "interactions": [],
        "contre_indications": []
    })

def get_covid_protocol() -> Dict:
    """Récupère les protocoles COVID-19."""
    for disease, info in MEDICAL_GUIDELINES.items():
        if "COVID" in disease.upper():
            return {
                "protocol": info.get("actions", ""),
                "symptoms": info.get("symptoms", []),
                "treatments": info.get("treatments", [])
            }
    return {
        "protocol": "Consultez un médecin si vous présentez des symptômes",
        "symptoms": ["Fièvre", "Toux", "Fatigue"],
        "treatments": ["Repos", "Hydratation"]
    }

# Fonctions pour les médecins
def add_symptom(symptom_name, variations, description, severity_level, common_causes):
    """
    Permet aux médecins d'ajouter un nouveau symptôme à la base de données.
    
    Args:
        symptom_name (str): Nom du symptôme
        variations (list): Liste des variations du symptôme
        description (str): Description du symptôme
        severity_level (int): Niveau de gravité (1-3)
        common_causes (list): Liste des causes communes
    """
    if not isinstance(severity_level, int) or severity_level not in [1, 2, 3]:
        raise ValueError("Le niveau de gravité doit être 1, 2 ou 3")
        
    SYMPTOMS_DATABASE[symptom_name.lower()] = {
        "variations": variations,
        "description": description,
        "severity_level": severity_level,
        "common_causes": common_causes
    }
    return f"Symptôme '{symptom_name}' ajouté avec succès"

def add_specialty(specialty_name, symptoms, description, common_conditions):
    """
    Permet aux médecins d'ajouter une nouvelle spécialité médicale.
    
    Args:
        specialty_name (str): Nom de la spécialité
        symptoms (list): Liste des symptômes associés
        description (str): Description de la spécialité
        common_conditions (list): Liste des conditions communes
    """
    SPECIALTIES_DATABASE[specialty_name.lower()] = {
        "symptoms": symptoms,
        "description": description,
        "common_conditions": common_conditions
    }
    return f"Spécialité '{specialty_name}' ajoutée avec succès"

def add_emergency_protocol(symptom, action, associated_symptoms, protocol):
    """
    Permet aux médecins d'ajouter un nouveau protocole d'urgence.
    
    Args:
        symptom (str): Symptôme concerné
        action (str): Action à entreprendre
        associated_symptoms (list): Symptômes associés
        protocol (str): Protocole à suivre
    """
    if "urgence" not in MEDICAL_GUIDELINES:
        MEDICAL_GUIDELINES["urgence"] = {}
        
    MEDICAL_GUIDELINES["urgence"][symptom.lower()] = {
        "action": action,
        "symptômes_associés": associated_symptoms,
        "protocole": protocol
    }
    return f"Protocole d'urgence pour '{symptom}' ajouté avec succès"

def add_medical_advice(symptom, measures, to_avoid):
    """
    Permet aux médecins d'ajouter de nouveaux conseils médicaux.
    
    Args:
        symptom (str): Symptôme concerné
        measures (list): Liste des mesures à prendre
        to_avoid (list): Liste des choses à éviter
    """
    if "conseils" not in MEDICAL_GUIDELINES:
        MEDICAL_GUIDELINES["conseils"] = {}
        
    MEDICAL_GUIDELINES["conseils"][symptom.lower()] = {
        "mesures": measures,
        "à_éviter": to_avoid
    }
    return f"Conseils pour '{symptom}' ajoutés avec succès"

def add_drug_interaction(drug_name, interactions, contraindications):
    """
    Permet aux médecins d'ajouter des interactions médicamenteuses.
    
    Args:
        drug_name (str): Nom du médicament
        interactions (dict): Dictionnaire des interactions
        contraindications (list): Liste des contre-indications
    """
    DRUG_INTERACTIONS[drug_name.lower()] = {
        "interactions": interactions,
        "contre_indications": contraindications
    }
    return f"Interactions pour '{drug_name}' ajoutées avec succès"

def update_covid_protocol(symptoms=None, measures=None, severity_signs=None):
    """
    Permet aux médecins de mettre à jour les protocoles COVID-19.
    
    Args:
        symptoms (list, optional): Nouveaux symptômes
        measures (dict, optional): Nouvelles mesures
        severity_signs (list, optional): Nouveaux signes de gravité
    """
    if symptoms:
        COVID_PROTOCOLS["symptômes"] = symptoms
    if measures:
        COVID_PROTOCOLS["mesures"] = measures
    if severity_signs:
        COVID_PROTOCOLS["signes_gravité"] = severity_signs
    return "Protocoles COVID-19 mis à jour avec succès"

def delete_symptom(symptom_name):
    """Permet aux médecins de supprimer un symptôme."""
    if symptom_name.lower() in SYMPTOMS_DATABASE:
        del SYMPTOMS_DATABASE[symptom_name.lower()]
        return f"Symptôme '{symptom_name}' supprimé avec succès"
    return f"Symptôme '{symptom_name}' non trouvé"

def delete_specialty(specialty_name):
    """Permet aux médecins de supprimer une spécialité."""
    if specialty_name.lower() in SPECIALTIES_DATABASE:
        del SPECIALTIES_DATABASE[specialty_name.lower()]
        return f"Spécialité '{specialty_name}' supprimée avec succès"
    return f"Spécialité '{specialty_name}' non trouvée"

def export_medical_data():
    """Exporte toutes les données médicales dans un format structuré."""
    return {
        "symptoms": SYMPTOMS_DATABASE,
        "specialties": SPECIALTIES_DATABASE,
        "guidelines": MEDICAL_GUIDELINES,
        "drug_interactions": DRUG_INTERACTIONS,
        "covid_protocols": COVID_PROTOCOLS
    }

def import_medical_data(data):
    """
    Importe des données médicales depuis un format structuré.
    
    Args:
        data (dict): Données médicales structurées
    """
    global SYMPTOMS_DATABASE, SPECIALTIES_DATABASE, MEDICAL_GUIDELINES, DRUG_INTERACTIONS, COVID_PROTOCOLS
    
    if "symptoms" in data:
        SYMPTOMS_DATABASE.update(data["symptoms"])
    if "specialties" in data:
        SPECIALTIES_DATABASE.update(data["specialties"])
    if "guidelines" in data:
        MEDICAL_GUIDELINES.update(data["guidelines"])
    if "drug_interactions" in data:
        DRUG_INTERACTIONS.update(data["drug_interactions"])
    if "covid_protocols" in data:
        COVID_PROTOCOLS.update(data["covid_protocols"])
    
    return "Données médicales importées avec succès"