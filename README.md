#  Medical-Chatbot

An intelligent medical chatbot that uses a semantic ontology (OWL/Turtle) and integrates with Dialogflow and a Python Flask backend to provide users with symptom and treatment information based on diseases.

##  Features

-  Conversational interface powered by Dialogflow.
-  RDF/OWL ontology used to model medical knowledge.
-  SPARQL queries executed with RDFLib to retrieve disease symptoms and treatments.
-  Flask-based webhook service, accessible via Ngrok for development.
-  Example intents: “What are the symptoms of asthma?”, “Treatment for diabetes?”

##  Technologies Used

- Python 
- Flask
- RDFLib
- Dialogflow 
- Ngrok
- Turtle (.ttl) format for ontology
- SPARQL

##  Setup Instructions

1. **Clone the repository:**

   ```bash
   git clone https://github.com/NourElhoda1/Medical-Chatbot.git
   cd medical-chatbot
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Flask server:**

   ```bash
   python app.py
   ```

4. **Expose your local server to Dialogflow using Ngrok:**

   ```bash
   ngrok http 5000
   ```

   Copy the generated HTTPS URL and add it as your webhook endpoint in Dialogflow.

5. **Test connection:**

   Go to `http://localhost:5000` or use a tool like Postman to test the endpoint.

##  Ontology

The knowledge base is modeled using RDF/OWL in Turtle syntax. The ontology contains:

- Diseases (e.g., Asthma, Migraine, Type 2 Diabetes)
- Symptoms and their relations (`ex:aCommeSymptome`)
- Treatments and medications (`ex:aCommeTraitement`, `:utiliseMédicament`)

Sample diseases and symptoms can be queried via SPARQL.

##  Example Webhook Response

```
User: What are the symptoms of diabetes?
Bot: The symptoms of diabetes include: increased thirst, frequent urination, fatigue.
```

##  Project Structure

```
medical-chatbot/
├── app.py               # Flask app
├── ontology.ttl         # Medical ontology in Turtle format
├── requirements.txt     # Python dependencies
└── README.md
```

##  Disclaimer

This chatbot is for **educational and informational purposes only**. It is **not a substitute for professional medical advice, diagnosis, or treatment**.

