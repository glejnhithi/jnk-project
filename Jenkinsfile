pipeline {
  agent { label 'docker-ready' }
  options { timestamps(); disableConcurrentBuilds() }
  environment {
    DOCKERHUB_USER = 'REPLACE_DOCKERHUB_USER'
    IMAGE_NAME = 'student-k8s-cicd'
    K8S_NAMESPACE = 'students'
  }
  stages {
    stage('Checkout') { steps { checkout scm } }
    stage('Test') {
      steps {
        sh '''
          python3 -m venv .venv
          .venv/bin/pip install -r requirements.txt
          .venv/bin/python -m pytest -v
        '''
      }
    }
    stage('Docker Build') {
      steps { sh 'docker build -t "$DOCKERHUB_USER/$IMAGE_NAME:$BUILD_NUMBER" .' }
    }
    stage('Docker Hub Push') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'dockerhub', usernameVariable: 'DH_USER', passwordVariable: 'DH_TOKEN')]) {
          sh '''
            set +x
            export DOCKER_CONFIG="$(mktemp -d)"
            trap 'rm -rf "$DOCKER_CONFIG"' EXIT
            printf '%s' "$DH_TOKEN" | docker login -u "$DH_USER" --password-stdin
            docker push "$DOCKERHUB_USER/$IMAGE_NAME:$BUILD_NUMBER"
          '''
        }
      }
    }
    stage('Deploy to Kubernetes') {
      steps {
        sh '''
          kubectl config current-context
          kubectl apply -f kubernetes/namespace.yaml
          kubectl apply -f kubernetes/service.yaml
          sed "s|image: nginx:stable|image: $DOCKERHUB_USER/$IMAGE_NAME:$BUILD_NUMBER|" kubernetes/deployment.yaml | kubectl apply -f -
          kubectl rollout status deployment/student-app -n "$K8S_NAMESPACE" --timeout=180s
        '''
      }
    }
  }
}
