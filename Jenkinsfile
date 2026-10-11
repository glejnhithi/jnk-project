
pipeline {
    agent {
        label 'student-k8s-agent'
    }

    options {
        timestamps()
        disableConcurrentBuilds()
        timeout(time: 20, unit: 'MINUTES')
    }

    environment {
        DOCKERHUB_USER = 'glejnhithi'
        IMAGE_NAME = 'student-k8s-cicd'
        K8S_NAMESPACE = 'students'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Test') {
            steps {
                container('tools') {
                    sh '''
                        set -e

                        python3 -m venv .venv
                        .venv/bin/pip install -r requirements.txt
                        .venv/bin/python -m pytest -v
                    '''
                }
            }
        }

        stage('Check Docker Daemon') {
            steps {
                container('tools') {
                    sh '''
                        docker version
                        docker info
                    '''
                }
            }
        }

        stage('Docker Build') {
            steps {
                container('tools') {
                    sh '''
                        docker build \
                          -t "$DOCKERHUB_USER/$IMAGE_NAME:$BUILD_NUMBER" \
                          .
                    '''
                }
            }
        }

        stage('Docker Hub Push') {
            steps {
                container('tools') {
                    withCredentials([
                        usernamePassword(
                            credentialsId: 'dockerhub',
                            usernameVariable: 'DH_USER',
                            passwordVariable: 'DH_TOKEN'
                        )
                    ]) {
                        sh '''
                            set -e
                            set +x

                            export DOCKER_CONFIG="$(mktemp -d)"
                            trap 'rm -rf "$DOCKER_CONFIG"' EXIT

                            printf '%s' "$DH_TOKEN" | docker login \
                              -u "$DH_USER" \
                              --password-stdin

                            docker push \
                              "$DOCKERHUB_USER/$IMAGE_NAME:$BUILD_NUMBER"
                        '''
                    }
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                container('tools') {
                    sh '''
                        set -e

                        echo "=== Kubernetes Deployment ==="

                        kubectl get namespace "$K8S_NAMESPACE"

                        kubectl apply \
                          -n "$K8S_NAMESPACE" \
                          -f kubernetes/service.yaml

                        sed \
                          "s|image: nginx:stable|image: $DOCKERHUB_USER/$IMAGE_NAME:$BUILD_NUMBER|" \
                          kubernetes/deployment.yaml \
                          | kubectl apply -n "$K8S_NAMESPACE" -f -

                        kubectl rollout status \
                          deployment/student-app \
                          -n "$K8S_NAMESPACE" \
                          --timeout=180s

                        kubectl get pods -n "$K8S_NAMESPACE"
                        kubectl get deployments -n "$K8S_NAMESPACE"
                        kubectl get services -n "$K8S_NAMESPACE"
                    '''
                }
            }
        }
    }

    post {
        success {
            echo 'SUCCESS: CI/CD Pipeline completed!'
        }

        failure {
            echo 'FAILED: Check Jenkins Console Output.'
        }
    }
}
