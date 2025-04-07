import requests

# URL dell'API
url = "http://127.0.0.1:5000/admin/calendario/eventi"

# Parametri di esempio (puoi modificarli se necessario)
params = {
    'docente_id': 'all',
    'corso_id': 'all',
    'stato': 'all'
}

# Esegui la richiesta GET
response = requests.get(url, params=params)

# Stampa lo stato della risposta e i dati
print("Status Code:", response.status_code)
print("Response JSON:", response.json())