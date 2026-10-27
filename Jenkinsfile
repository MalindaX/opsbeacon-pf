pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        skipDefaultCheckout(true)
    }

    parameters {
        booleanParam(name: 'DEPLOY_LOCAL_CONTAINER', defaultValue: false,
                     description: 'Restart local Docker Compose container with the freshly built image')
    }

    environment {
        DOCKER_HUB_REPO = 'sandaruwanx/opsbeacon'
        IMAGE_TAG = "jenkins-${BUILD_NUMBER}"
        DOCKER_CONFIG = "${WORKSPACE}/.docker-ci"
    }

    stages {
        stage('Checkout Code') {
            steps {
                checkout scm
            }
        }

        stage('Install & Test') {
            steps {
                echo 'Building test image and running lint and pytest...'
                bat 'docker build --target test -t opsbeacon-ci-test:%BUILD_NUMBER% .'
                bat 'docker run --rm opsbeacon-ci-test:%BUILD_NUMBER% python -m flake8 app/ tests/ --select=E9,F63,F7,F82 --show-source --statistics'
                bat 'docker run --rm opsbeacon-ci-test:%BUILD_NUMBER%'
            }
        }

        stage('Build Docker Image') {
            steps {
                echo "Building runtime image ${env.DOCKER_HUB_REPO}:${env.IMAGE_TAG}..."
                bat 'docker build --target runtime -t %DOCKER_HUB_REPO%:%IMAGE_TAG% -t %DOCKER_HUB_REPO%:latest .'
            }
        }

        stage('Push to Docker Hub') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    bat '@docker login -u %DOCKER_USER% -p %DOCKER_PASS%'
                    bat 'docker push %DOCKER_HUB_REPO%:%IMAGE_TAG%'
                    bat 'docker push %DOCKER_HUB_REPO%:latest'
                }
            }
        }

        stage('Deploy to Docker') {
            when { expression { params.DEPLOY_LOCAL_CONTAINER } }
            steps {
                echo 'Deploying updated image to local Docker Compose...'
                bat 'docker compose up -d'
            }
        }
    }

    post {
        always {
            bat 'docker logout'
        }
        success {
            echo 'Pipeline succeeded: tests passed and image was published to Docker Hub.'
        }
        failure {
            echo 'Pipeline failed. Check the first failing stage in the console output.'
        }
    }
}
