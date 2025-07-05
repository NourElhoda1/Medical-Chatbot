from flask import Flask, request, jsonify
from flask_cors import CORS
from rdflib import Graph
import logging

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Charger l'ontologie Turtle (.ttl)
g = Graph()
try:
    g.parse("ontology.ttl", format="turtle")
    logger.info("Ontologie chargée avec succès")
except Exception as e:
    logger.error(f"Erreur lors du chargement de l'ontologie: {e}")

@app.route('/', methods=['GET'])
def home():
    return "Medical Bot Webhook is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        req = request.get_json()
        logger.info(f"Requête reçue: {req}")
        
        if not req or 'queryResult' not in req:
            return jsonify({"fulfillmentText": "Requête invalide."})
        
        parameters = req['queryResult'].get('parameters', {})
        maladie_param = parameters.get('maladie')
        intent_name = req['queryResult']['intent']['displayName']
        
        logger.info(f"Intent: {intent_name}, Maladie param: {maladie_param}")
        
        #  Salutation
        if intent_name == "Default Welcome Intent":
            return jsonify({
                "fulfillmentText": "👋 Bonjour ! Je suis un assistant médical. Posez-moi une question comme : 'Quels sont les symptômes du diabète ?'"
            })


        # Gérer le cas où maladie est une liste ou une chaîne
        if not maladie_param and intent_name != "ListeMaladies":
            return jsonify({
                "fulfillmentText": "Je n'ai pas compris quelle maladie vous mentionnez. Pouvez-vous préciser?"
            })
        if isinstance(maladie_param, list):
            maladie_user = maladie_param[0] if len(maladie_param) > 0 else None
        else:
            maladie_user = maladie_param
        
        if not maladie_user and intent_name != "ListeMaladies":
            return jsonify({
                "fulfillmentText": "Je n'ai pas compris quelle maladie vous mentionnez."
            })
        
        if intent_name != "ListeMaladies":
            logger.info(f"Maladie extraite: {maladie_user}")
        
        # Utiliser directement la valeur de Dialogflow (déjà normalisée)
        maladie = maladie_user if maladie_user else None
        
        # Traitement selon l'intent
        if intent_name == "SymptomesMaladie":
            return handle_symptoms(maladie, maladie_user)
        elif intent_name == "TraitementMaladie":
            return handle_treatments(maladie, maladie_user)
        elif intent_name == "ListeMaladies":
            return handle_list_diseases()
        else:
            return jsonify({
                "fulfillmentText": "Je ne comprends pas votre demande."
            })
        
    except Exception as e:
        logger.error(f"Erreur dans webhook: {str(e)}", exc_info=True)
        return jsonify({
            "fulfillmentText": "Je rencontre un problème technique. Veuillez réessayer plus tard."
        })

def handle_list_diseases():
    """Gère les demandes de liste des maladies"""
    try:
        # Requête SPARQL pour récupérer toutes les maladies
        query = """
        PREFIX ex: <http://www.example.org/ontology-medicale#>
        SELECT DISTINCT ?maladie WHERE {
            ?maladie ex:aCommeSymptome ?symptome .
        }
        ORDER BY ?maladie
        """
        
        logger.info(f"Requête SPARQL maladies: {query}")
        
        results = g.query(query)
        maladies = [str(row.maladie).split('#')[-1] for row in results]
        
        logger.info(f"Maladies trouvées: {maladies}")
        
        if maladies:
            # Traduire les noms techniques en noms lisibles
            maladies_lisibles = []
            for maladie in maladies:
                maladie_lisible = traduire_maladie(maladie)
                maladies_lisibles.append(maladie_lisible)
            
            message = f"Je peux vous renseigner sur les maladies suivantes :\n\n"
            for i, maladie in enumerate(maladies_lisibles, 1):
                message += f"{i}. {maladie}\n"
            
            message += f"\nAu total, je connais {len(maladies)} maladies."
            message += "\n\nPour chaque maladie, je peux vous donner les symptômes et traitements. Demandez-moi par exemple : 'Quels sont les symptômes du diabète ?' ou 'Traitement de l'hypertension ?'"
        else:
            message = "Désolé, aucune maladie n'est disponible dans ma base de connaissances actuellement."
        
        return jsonify({"fulfillmentText": message})
        
    except Exception as e:
        logger.error(f"Erreur dans handle_list_diseases: {str(e)}", exc_info=True)
        return jsonify({
            "fulfillmentText": "Je rencontre un problème pour récupérer la liste des maladies."
        })

def traduire_maladie(maladie_technique):
    """Traduit les noms techniques des maladies en français lisible"""
    traductions = {
        "DiabeteType2": "Diabète de type 2",
        "HypertensionArterielle": "Hypertension artérielle",
        "Covid19": "COVID-19",
        "Asthme": "Asthme",
        "Migraine": "Migraine", 
        "Grippe": "Grippe",
        "RefluxGastroOesophagien": "Reflux gastro-œsophagien (RGO)",
        "Diabete": "Diabète",
        "Hypertension": "Hypertension"
    }
    
    return traductions.get(maladie_technique, maladie_technique)

def handle_symptoms(maladie, maladie_user):
    """Gère les demandes de symptômes"""
    # Requête SPARQL pour les symptômes
    query = f"""
    PREFIX ex: <http://www.example.org/ontology-medicale#>
    SELECT ?symptome WHERE {{
        ex:{maladie} ex:aCommeSymptome ?symptome .
    }}
    """
    
    logger.info(f"Requête SPARQL symptômes: {query}")
    
    results = g.query(query)
    symptomes = [str(row.symptome).split('#')[-1] for row in results]
    
    logger.info(f"Symptômes trouvés: {symptomes}")
    
    if symptomes:
        message = f"Les symptômes de {maladie_user} incluent : {', '.join(symptomes)}."
        message += "\n\n⚠️ Cette information est fournie à titre informatif uniquement. Consultez toujours un professionnel de santé pour un diagnostic médical."
    else:
        message = f"Désolé, je ne trouve pas d'informations sur les symptômes de '{maladie_user}' dans ma base de connaissances."
    
    return jsonify({"fulfillmentText": message})

def handle_treatments(maladie, maladie_user):
    """Gère les demandes de traitements"""
    # Requête SPARQL pour les traitements et médicaments
    query = f"""
    PREFIX ex: <http://www.example.org/ontology-medicale#>
    PREFIX : <http://www.example.org/ontology/medicale#>
    SELECT ?traitement ?medicament ?posologie WHERE {{
        ex:{maladie} ex:aCommeTraitement ?traitement .
        ?traitement :utiliseMédicament ?medicament .
        OPTIONAL {{ ?medicament ex:posologie ?posologie }}
    }}
    """
    
    logger.info(f"Requête SPARQL traitements: {query}")
    
    results = g.query(query)
    medicaments_info = []
    
    for row in results:
        med_name = str(row.medicament).split('#')[-1]
        posologie = str(row.posologie) if row.posologie else "Posologie à définir avec votre médecin"
        medicaments_info.append(f"{med_name} ({posologie})")
    
    logger.info(f"Traitements trouvés: {medicaments_info}")
    
    if medicaments_info:
        message = f"Le traitement de {maladie_user} peut inclure :\n"
        for med_info in medicaments_info:
            message += f"• {med_info}\n"
        message += "\n⚠️ Ces informations sont données à titre indicatif. Consultez toujours un médecin avant de prendre tout médicament."
    else:
        message = f"Désolé, je ne trouve pas d'informations sur le traitement de '{maladie_user}' dans ma base de connaissances."
    
    return jsonify({"fulfillmentText": message})

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint pour vérifier l'état de santé du service"""
    try:
        ontology_status = len(g) > 0
        return jsonify({
            "status": "healthy",
            "ontology_loaded": ontology_status,
            "ontology_size": len(g),
            "timestamp": "2025-06-18"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        })

@app.route('/test-ontology', methods=['GET'])
def test_ontology():
    """Endpoint pour tester l'ontologie"""
    try:
        # Test si l'ontologie est chargée
        query = """
        PREFIX ex: <http://www.example.org/ontology-medicale#>
        SELECT ?s ?p ?o WHERE {
            ?s ?p ?o .
        } LIMIT 10
        """
        results = list(g.query(query))
        
        # Récupérer quelques exemples de maladies
        disease_query = """
        PREFIX ex: <http://www.example.org/ontology-medicale#>
        SELECT DISTINCT ?maladie WHERE {
            ?maladie ex:aCommeSymptome ?symptome .
        } LIMIT 10
        """
        diseases = list(g.query(disease_query))
        
        return jsonify({
            "ontology_size": len(g),
            "sample_triples": len(results),
            "sample_diseases": [str(d.maladie).split('#')[-1] for d in diseases],
            "status": "loaded successfully"
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error loading ontology"
        })

@app.route('/diseases-detailed', methods=['GET'])
def list_diseases_detailed():
    """Endpoint pour lister toutes les maladies avec détails"""
    try:
        query = """
        PREFIX ex: <http://www.example.org/ontology-medicale#>
        PREFIX : <http://www.example.org/ontology/medicale#>
        SELECT DISTINCT ?maladie 
               (COUNT(DISTINCT ?symptome) AS ?nb_symptomes)
               (COUNT(DISTINCT ?medicament) AS ?nb_medicaments)
        WHERE {
            ?maladie ex:aCommeSymptome ?symptome .
            OPTIONAL {
                ?maladie ex:aCommeTraitement ?traitement .
                ?traitement :utiliseMédicament ?medicament .
            }
        }
        GROUP BY ?maladie
        ORDER BY ?maladie
        """
        
        results = g.query(query)
        diseases_info = []
        
        for row in results:
            disease_name = str(row.maladie).split('#')[-1]
            disease_readable = traduire_maladie(disease_name)
            diseases_info.append({
                "technical_name": disease_name,
                "readable_name": disease_readable,
                "symptoms_count": int(row.nb_symptomes),
                "medications_count": int(row.nb_medicaments) if row.nb_medicaments else 0
            })
        
        return jsonify({
            "diseases": diseases_info,
            "total_count": len(diseases_info)
        })
    except Exception as e:
        return jsonify({
            "error": str(e)
        })

@app.route('/diseases', methods=['GET'])
def list_diseases():
    """Endpoint pour lister toutes les maladies disponibles"""
    try:
        query = """
        PREFIX ex: <http://www.example.org/ontology-medicale#>
        SELECT DISTINCT ?maladie WHERE {
            ?maladie ex:aCommeSymptome ?symptome .
        }
        """
        results = g.query(query)
        diseases = [str(row.maladie).split('#')[-1] for row in results]
        
        return jsonify({
            "available_diseases": diseases,
            "count": len(diseases)
        })
    except Exception as e:
        return jsonify({
            "error": str(e)
        })

@app.route('/symptoms/<disease>', methods=['GET'])
def get_symptoms(disease):
    """Endpoint pour récupérer les symptômes d'une maladie spécifique"""
    try:
        query = f"""
        PREFIX ex: <http://www.example.org/ontology-medicale#>
        SELECT ?symptome WHERE {{
            ex:{disease} ex:aCommeSymptome ?symptome .
        }}
        """
        
        results = g.query(query)
        symptoms = [str(row.symptome).split('#')[-1] for row in results]
        
        return jsonify({
            "disease": disease,
            "symptoms": symptoms,
            "count": len(symptoms)
        })
    except Exception as e:
        return jsonify({
            "error": str(e)
        })

@app.route('/treatments/<disease>', methods=['GET'])
def get_treatments(disease):
    """Endpoint pour récupérer les traitements d'une maladie spécifique"""
    try:
        query = f"""
        PREFIX ex: <http://www.example.org/ontology-medicale#>
        PREFIX : <http://www.example.org/ontology/medicale#>
        SELECT ?traitement ?medicament ?posologie WHERE {{
            ex:{disease} ex:aCommeTraitement ?traitement .
            ?traitement :utiliseMédicament ?medicament .
            OPTIONAL {{ ?medicament ex:posologie ?posologie }}
        }}
        """
        
        results = g.query(query)
        treatments = []
        
        for row in results:
            med_name = str(row.medicament).split('#')[-1]
            posologie = str(row.posologie) if row.posologie else "Non spécifiée"
            treatments.append({
                "medication": med_name,
                "dosage": posologie
            })
        
        return jsonify({
            "disease": disease,
            "treatments": treatments,
            "count": len(treatments)
        })
    except Exception as e:
        return jsonify({
            "error": str(e)
        })
    
    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)