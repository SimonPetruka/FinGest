pipeline {
    agent any

    stages {
        stage('Récupération') {
            steps {
                echo 'Récupération du code...'
            }
        }

        stage('Installation & Build') {
            steps {
                // Installe les librairies Python
                sh 'pip3 install -r requirements.txt --break-system-packages || true'
                sh 'pip3 install pyinstaller --break-system-packages || true'
                
                // 1. Fabrique l'exécutable Linux (Pour le VPS)
                sh '/var/lib/jenkins/.local/bin/pyinstaller --onefile --clean --name "EcoGest_App" main.py'
                
                // 2. Fabrique le ZIP du code source (Pour ton Mac)
                // Le "apt-get" est retiré car tu l'as fait à la main en SSH
                sh 'zip -r dist/EcoGest_Source.zip . -x "*.git*" -x "venv/*" -x "dist/*" -x "__pycache__/*"'
            }
        }

        stage('Déploiement') {
            steps {
                // Copie les fichiers vers le site web
                sh 'cp dist/EcoGest_App /var/www/html/EcoGest_App'
                sh 'cp dist/EcoGest_Source.zip /var/www/html/EcoGest_Source.zip'
                
                // Génère la page HTML avec les 2 boutons
                sh '''
                    cat <<EOF > /var/www/html/index.html
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EcoGest App</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #f4f4f9; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: white; padding: 40px; border-radius: 12px; box-shadow: 0 10px 20px rgba(0,0,0,0.1); text-align: center; max-width: 400px; width: 100%; }
        h1 { color: #333; margin-bottom: 5px; }
        p { color: #666; margin-bottom: 25px; }
        .btn { display: block; width: 80%; margin: 15px auto; padding: 12px; text-decoration: none; border-radius: 8px; font-weight: bold; transition: 0.3s; color: white; }
        .btn-linux { background-color: #e67e22; }
        .btn-mac { background-color: #007aff; }
        .btn:hover { opacity: 0.8; transform: translateY(-2px); }
        .note { font-size: 11px; color: #999; margin-top: 30px; border-top: 1px solid #eee; padding-top: 10px;}
    </style>
</head>
<body>
    <div class="card">
        <h1>🌱 EcoGest V1.0</h1>
        <p>Plateforme de téléchargement sécurisée</p>
        
        <a href="EcoGest_App" class="btn btn-linux">🐧 Télécharger (Linux / Serveur)</a>
        
        <a href="EcoGest_Source.zip" class="btn btn-mac"> / ⊞ Télécharger le Code (Mac/PC)</a>

        <div class="note">
            Déploiement automatisé Jenkins • $(date)
        </div>
    </div>
</body>
</html>
EOF
                '''
            }
        }
    }
}