# Student Kubernetes CI/CD Workshop (3 hours)

GitHub → Jenkins → Python tests → Docker build → Docker Hub push → Minikube deploy.

## Prerequisites (prepare before workshop)
- Jenkins service on WSL, Pipeline and Git plugins.
- Jenkins agent with label `docker-ready`, Python 3 + venv, Docker CLI and daemon access, kubectl and an authorized Minikube kubeconfig.
- Docker Hub public repository `student-k8s-cicd` and Jenkins username/password credential ID `dockerhub` (password = access token).
- Set `DOCKERHUB_USER` in Jenkinsfile. Do not commit tokens or kubeconfig.
- Jenkins must be able to reach GitHub; for localhost Jenkins use SCM polling (e.g. `H/2 * * * *`) instead of an unreachable webhook URL.
- Run `kubectl config current-context` and `kubectl auth can-i create deployments -n students` as the agent user. The agent must have namespace and deployment permissions for this lab.
- For a production setup, use a dedicated namespace-scoped ServiceAccount and avoid mounting an administrator kubeconfig in the build agent.

## 0–30 min: App and GitHub
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -v
python -m app.main
```
Create an empty GitHub repository, then `git init`, `git add .`, `git commit -m 'initial workshop'`, add your remote and push.

## 30–60 min: Docker
```bash
docker build -t student-k8s-cicd:local .
docker run --rm -d --name student-test -p 5000:5000 student-k8s-cicd:local
curl http://localhost:5000/health
docker stop student-test
```

## 60–105 min: Jenkins + Docker Hub
- Set up Pipeline from SCM, branch `main`, script path `Jenkinsfile`.
- Configure Docker Hub credential ID `dockerhub`.
- Verify label `docker-ready` and Docker daemon access.
- Run the Jenkins pipeline. For local Jenkins, configure Poll SCM trigger `H/2 * * * *`.

## 105–150 min: Minikube
- Ensure Minikube is running and the agent's kubectl context targets it.
- Run the pipeline and verify:
```bash
kubectl get pods,deploy,svc -n students
kubectl port-forward -n students svc/student-app 8085:80
# In another terminal:
curl http://localhost:8085/health
```

## 150–180 min: Live demo
Change the message in `app/main.py`, commit and push. Watch Jenkins build a new tag, push it to Docker Hub, and roll out the deployment. Show `kubectl rollout history deployment/student-app -n students` and `kubectl rollout undo deployment/student-app -n students`.

## Agent note
This fast workshop uses one `docker-ready` agent for all stages, to avoid cross-agent Docker and kubeconfig problems. A Kubernetes Jenkins agent can be used for deployment as an extension after confirming its `kubectl` image, RBAC, and network access. Docker socket access is root-equivalent; only use it in an isolated teaching lab.
