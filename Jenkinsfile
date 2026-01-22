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
                sh 'pyinstaller --onefile --clean --name "EcoGest_App" main.py'
            }
        }

        stage('Déploiement (Mise en ligne)') {
            steps {
                echo 'Déplacement vers le site web...'
                // Copie l'exécutable vers le dossier du site web Nginx
                sh 'cp dist/EcoGest_App /var/www/html/EcoGest_App'
                
                // Crée une petite page HTML simple pour télécharger
                sh '''
                    echo "<h1>Dernière version de EcoGest</h1><br><a href='EcoGest_App'>Télécharger l'application (Linux)</a><br><p>Généré le $(date)</p>" > /var/www/html/index.html
                '''
            }
        }
    }
}