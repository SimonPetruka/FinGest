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
                // Installe PyInstaller pour transformer le .py en exécutable
                sh 'pip3 install -r requirements.txt --break-system-packages || true'
                sh 'pip3 install pyinstaller --break-system-packages || true'
                
                // Fabrique l'application (crée un fichier dans le dossier 'dist')
                sh '/var/lib/jenkins/.local/bin/pyinstaller --onefile --clean --name "EcoGest_App" main.py'
            }
        }

      stage('Déploiement (Mise en ligne)') {
            steps {
                echo 'Déplacement vers le site web...'
                
                // 1. Copie l'exécutable
                sh 'cp dist/EcoGest_App /var/www/html/EcoGest_App'
                
                // 2. Génère une belle page HTML moderne
                sh '''
                    cat <<EOF > /var/www/html/index.html
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Téléchargement EcoGest</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f0f2f5; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; max-width: 400px; width: 100%; }
        h1 { color: #2c3e50; margin-bottom: 20px; font-size: 24px; }
        .btn { display: inline-block; background-color: #007bff; color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: bold; transition: background 0.3s; margin-top: 20px; }
        .btn:hover { background-color: #0056b3; }
        .footer { margin-top: 30px; font-size: 12px; color: #888; }
        .status { color: #28a745; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <h1>🚀 EcoGest App</h1>
        <p>La dernière version est prête.</p>
        <a href="EcoGest_App" class="btn">⬇️ Télécharger l'application</a>
        <div class="footer">
            Build généré automatiquement par Jenkins<br>
            Date : $(date)
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