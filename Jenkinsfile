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
                // Installe les outils
                sh 'pip3 install -r requirements.txt --break-system-packages || true'
                sh 'pip3 install pyinstaller --break-system-packages || true'
                // Installe l'outil ZIP
                sh 'apt-get update && apt-get install -y zip || true'
                
                // 1. Fabrique l'exécutable Linux (Pour le VPS)
                sh '/var/lib/jenkins/.local/bin/pyinstaller --onefile --clean --name "EcoGest_App" main.py'
                
                // 2. Fabrique le ZIP du code source (Pour ton Mac)
                // On exclut les dossiers inutiles (.git, venv, etc.)
                sh 'zip -r dist/EcoGest_Source.zip . -x "*.git*" -x "venv/*" -x "dist/*" -x "__pycache__/*"'
            }
        }

        stage('Déploiement') {
            steps {
                // Copie les fichiers vers le site web
                sh 'cp dist/EcoGest_App /var/www/html/EcoGest_App'
                sh 'cp dist/EcoGest_Source.zip /var/www/html/EcoGest_Source.zip'
                
                // Génère la page HTML avec DEUX boutons
                sh '''
                    cat <<EOF > /var/www/html/index.html
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EcoGest App</title>
    <style>
        body { font-family: sans-serif; background: #f4f4f9; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: white; padding: 40px; border-radius: 12px; box-shadow: 0 10px 20px rgba(0,0,0,0.1); text-align: center; max-width: 400px; width: 100%; }
        h1 { color: #333; }
        .btn { display: block; width: 80%; margin: 10px auto; padding: 12px; text-decoration: none; border-radius: 8px; font-weight: bold; transition: 0.3s; }
        .btn-linux { background-color: #e67e22; color: white; } /* Orange pour Linux */
        .btn-mac { background-color: #3498db; color: white; }   /* Bleu pour Mac */
        .btn:hover { opacity: 0.8; }
        .note { font-size: 12px; color: #777; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="card">
        <h1>🌱 EcoGest V1.0</h1>
        <p>Choisissez votre version :</p>
        
        <a href="EcoGest_App" class="btn btn-linux">🐧 Télécharger Executable (Linux)</a>
        
        <a href="EcoGest_Source.zip" class="btn btn-mac"> Télécharger Code Source (Mac/Win)</a>

        <div class="note">
            Déployé automatiquement le $(date)
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