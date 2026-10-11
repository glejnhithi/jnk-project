
pipeline {
    agent {
        kubernetes {
            inheritFrom 'student-k8s-agent'
            defaultContainer 'tools'

            yaml '''
apiVersion: v1
kind: Pod
spec:
  containers:
    - name: kaniko
      image: gcr.io/kaniko-project/executor:v1.23.2-debug
      command:
        - /busybox/cat
      tty: true
'''
        }
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

        stage('Check Environment') {
            steps {
                container('tools') {
                    sh '''
                        set -e

                        echo "=== Python ==="
                        python3 --version

                        echo "=== Kubernetes ==="
                        kubectl version --client

                        echo "=== Workspace ==="
                        pwd
                        ls -la
                    '''
                }
            }
        }

        stage('Build and Push Docker Image') {
            steps {
                container('kaniko') {
                    withCredentials([
                        usernamePassword(
                            credentialsId: 'dockerhub',
                            usernameVariable: 'DH_USER',
                            passwordVariable: 'DH_TOKEN'
                        )
                    ]) {
                        sh '''
                            set -eu
                            set +x

                            mkdir -p /kaniko/.docker

                            AUTH=$(printf '%s:%s' \
                              "$DH_USER" "$DH_TOKEN" \
                              | base64 | tr -d '\\n')

                            printf '{"auths":{"https://index.docker.io/v1/":{"auth":"%s"}}}' \
                              "$AUTH" \
                              > /kaniko/.docker/config.json

                            trap 'rm -f /kaniko/.docker/config.json' EXIT

                            /kaniko/executor \
                              --context "dir://$WORKSPACE" \
                              --dockerfile "$WORKSPACE/Dockerfile" \
                              --destination "$DOCKERHUB_USER/$IMAGE_NAME:$BUILD_NUMBER" \
                              --cache=false
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
