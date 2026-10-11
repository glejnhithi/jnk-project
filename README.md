# Student Kubernetes CI/CD Workshop — 3 orë

**GitHub → Jenkins → Python tests → Docker build → Docker Hub push → Minikube deploy**

Ky është udhëzuesi i laboratorit që u realizua me sukses më **11 tetor 2026**. Nuk përdorim më udhëzimin e vjetër me një agent `docker-ready`: pipeline-i funksional përdor **Jenkins Kubernetes Agent me label `student-k8s-agent`** dhe container-in **`tools`**. Jenkins Controller është një **systemd service në WSL Ubuntu**; Minikube punon me Docker driver. Aplikacioni është Python/Flask dhe testet ekzekutohen me `pytest`.

> **Kujdes:** README dokumenton gjendjen dhe hapat e njohur të laboratorit. Metoda konkrete me të cilën container-i `tools` arrin Docker daemon nuk është e dokumentuar në log-et e disponueshme; verifiko `docker info` nga agent-i përpara workshop-it. Mos supozo se socket-i i WSL është automatikisht i disponueshëm brenda Pod-it.

## 1. Arkitektura

```text
GitHub: https://github.com/glejnhithi/jnk-project (main)
                       |
                       v
          Jenkins Controller (WSL service)
                       |
                       v
      Kubernetes Agent: student-k8s-agent
        Namespace: jenkins; container: tools
                       |
          +------------+-------------+
          |            |             |
      Python tests  Docker CLI    kubectl
                       |             |
                 Docker daemon       |  ServiceAccount:
                       |             |  jenkins:jenkins-deployer
                 Docker Hub          v
          glejnhithi/student-k8s-cicd  Minikube
                       |             namespace: students
                       +-----------> Deployment: student-app
                                      Service: student-app
```

**CI**: Checkout → Test → Check Docker Daemon → Docker Build → Docker Hub Push. **CD**: Deploy to Kubernetes → Rollout → Status.

## 2. Programi i workshop-it (180 minuta)

| Koha | Aktiviteti | Rezultati |
|---|---|---|
| 0–20 min | Shpjegimi i CI/CD dhe kontrolli i WSL, Docker, Minikube | Mjedisi gati |
| 20–45 min | Flask + Python venv + pytest | Testet kalojnë |
| 45–65 min | Dockerfile, build dhe health check | Image lokal funksional |
| 65–85 min | GitHub repo dhe Jenkins SCM | Kodi merret nga Jenkins |
| 85–115 min | Agent, Docker Hub credentials, build/push | Image i publikuar |
| 115–150 min | Kubernetes manifests, RBAC dhe deploy | Pods `Ready` |
| 150–180 min | Ndryshim kodi, pipeline i dytë, rollback, troubleshooting | CI/CD end-to-end |

Konfigurimi i Jenkins Controller, Kubernetes Cloud, Docker daemon dhe agent-it duhet të jetë bërë përpara orës mësimore.

## 3. Parakushtet

- **WSL Ubuntu** me Git, Python 3, `python3-venv`, Docker CLI/daemon, `kubectl`, Minikube.
- **Jenkins** si service, me plugins: Pipeline, Git, Kubernetes, Credentials Binding.
- **Jenkins Kubernetes Cloud** dhe Pod Template me label `student-k8s-agent`, container `tools` (me `python3`, `pip`, `docker`, `kubectl`) dhe ServiceAccount `jenkins-deployer` në namespace `jenkins`.
- Container-i `tools` duhet të ketë **akses real te Docker daemon**, jo vetëm Docker CLI.
- Docker Hub repository publik `glejnhithi/student-k8s-cicd` dhe Jenkins credential **ID `dockerhub`**, tipi **Username with password**, password = Docker Hub access token.
- Namespace Kubernetes `students` dhe RBAC i përshkruar më poshtë.
- GitHub repo: **https://github.com/glejnhithi/jnk-project.git**.

Kontrolle nga WSL:

```bash
sudo systemctl status jenkins --no-pager
docker version
docker ps
minikube status
kubectl config current-context
kubectl get nodes
kubectl get pods -n jenkins
kubectl get pods,deploy,svc -n students
```

> `docker ps` në WSL verifikon vetëm daemon-in e WSL; **nuk** provon aksesin e container-it `tools`. Këtë e provon faza `Check Docker Daemon` në Jenkins (`docker version`, `docker info`).

## 4. Struktura e projektit

```text
jnk-project/
├── app/
│   ├── __init__.py
│   └── main.py
├── tests/
│   └── test_app.py
├── kubernetes/
│   ├── deployment.yaml
│   └── service.yaml
├── Dockerfile
├── Jenkinsfile
├── requirements.txt
└── README.md
```

`kubernetes/deployment.yaml` në këtë version përdor `image: nginx:stable` si placeholder, i cili zëvendësohet nga Jenkins gjatë deploy. Deployment dhe container duhet të kenë konfigurimin e aplikacionit real, portat dhe emrat përkatës. Pipeline pret Deployment me emër **`student-app`** dhe Service me emër **`student-app`**.

## 5. Laboratori A — Flask dhe testet

Nga root-i i repository-t:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -v
python -m app.main
```

Në terminal tjetër:

```bash
curl http://localhost:5000/health
```

Ndalo Flask me `Ctrl+C`. Nëse `venv` mungon: `sudo apt update && sudo apt install -y python3-venv`. Mos e shto `.venv/` në Git.

## 6. Laboratori B — Docker lokal

```bash
docker build -t student-k8s-cicd:local .
docker run -d --rm --name student-test -p 5001:5000 student-k8s-cicd:local
curl http://localhost:5001/health
docker logs student-test
docker stop student-test
```

Përdorëm `5001` në host për të shmangur konfliktin me portën `5000`. Nëse `docker build` punon në WSL por dështon në Jenkins, kontrollo daemon-in **nga agent-i**, jo vetëm nga WSL.

## 7. Laboratori C — GitHub

Repository ekzistues:

```bash
git status
git remote -v
git branch --show-current
```

Nëse projekti lokal nuk është ende Git repository:

```bash
git init
git branch -M main
git remote add origin https://github.com/glejnhithi/jnk-project.git
```

Nëse `origin` ekziston, mos e shto dy herë: `git remote set-url origin https://github.com/glejnhithi/jnk-project.git`. Për të publikuar ndryshimet:

```bash
git add .
git commit -m "docs: update student Kubernetes CI/CD workshop"
git push -u origin main
```

Mos përdor `git push --force` dhe mos ngarko Docker Hub tokens, kubeconfig ose secrets.

## 8. Laboratori D — Jenkins Cloud, Pod Template dhe SCM

1. Jenkins → **Manage Jenkins → Clouds → Kubernetes**. Kontrollo lidhjen me Minikube dhe namespace `jenkins`.
2. Te **Pod Templates**, kontrollo label-in `student-k8s-agent`, container-in `tools` dhe ServiceAccount `jenkins-deployer`. Emri i Pod Template mund të jetë ndryshe nga label-i; pipeline-i aktual përdor **label**.
3. Kontrollo që container-i `tools` përmban Python, Docker CLI dhe `kubectl`.
4. Jenkins → **Manage Jenkins → Credentials** → krijo `Username with password`, **ID `dockerhub`**, me Docker Hub username dhe access token.
5. Jenkins → **New Item → Pipeline**. Te **Pipeline → Definition** zgjidh **Pipeline script from SCM**, SCM **Git**, URL `https://github.com/glejnhithi/jnk-project.git`, branch `*/main`, script path `Jenkinsfile`.
6. Kliko **Build Now** dhe hap **Console Output**. Për Jenkins vetëm lokal, përdor **Poll SCM** `H/2 * * * *` nëse dëshiron trigger automatik. Webhook i GitHub nuk arrin `localhost` të WSL pa një endpoint publik.

### Fazat e Jenkinsfile funksional

| Faza | Çfarë bën |
|---|---|
| Checkout | `checkout scm` |
| Test | Krijon `.venv`, instalon `requirements.txt`, ekzekuton `pytest -v` |
| Check Docker Daemon | Ekzekuton `docker version` dhe `docker info` |
| Docker Build | Ndërton `glejnhithi/student-k8s-cicd:$BUILD_NUMBER` |
| Docker Hub Push | Merr credential `dockerhub`, bën login me token dhe push |
| Deploy to Kubernetes | Aplikon Service, zëvendëson image në Deployment, pret rollout dhe liston burimet |

Të gjitha fazat e komandave ekzekutohen në **`container('tools')`** të agent-it me label `student-k8s-agent`. Kjo është arkitektura e pipeline-it të përfshirë në paketë; nuk është varianti i mëparshëm me `docker-ready`.

## 9. Laboratori E — Kubernetes Namespace dhe RBAC

Këto janë resurset që kemi krijuar te `~/jenkins-agents/docker-ready/jk.yaml` (emri i folderit nuk ndryshon arkitekturën e agent-it):

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: jenkins-deployer
  namespace: jenkins
---
apiVersion: v1
kind: Namespace
metadata:
  name: students
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: jenkins-deployer-role
  namespace: students
rules:
  - apiGroups: [""]
    resources: ["pods", "services", "configmaps"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  - apiGroups: ["apps"]
    resources: ["deployments", "replicasets"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: jenkins-deployer-binding
  namespace: students
subjects:
  - kind: ServiceAccount
    name: jenkins-deployer
    namespace: jenkins
roleRef:
  kind: Role
  name: jenkins-deployer-role
  apiGroup: rbac.authorization.k8s.io
```

Ky manifest aplikohet **një herë nga WSL me identitet administratori**:

```bash
kubectl apply -f ~/jenkins-agents/docker-ready/jk.yaml
```

Verifikuam realisht këto dy komanda, dhe të dyja kthyen **`yes`**:

```bash
kubectl auth can-i create deployments -n students \
  --as=system:serviceaccount:jenkins:jenkins-deployer
kubectl auth can-i patch deployments -n students \
  --as=system:serviceaccount:jenkins:jenkins-deployer
```

**Pse Role + RoleBinding?** ServiceAccount jeton në `jenkins`, ndërsa Role dhe RoleBinding janë në `students`. RoleBinding lejon pikërisht atë ServiceAccount të menaxhojë resurset e përcaktuara brenda `students`, pa e bërë `cluster-admin`.

## 10. Gabimet që zgjidhëm gjatë konfigurimit

### A. `docker.sock: no such file or directory`

Gabimi në agent:

```text
failed to connect to the docker API at unix:///var/run/docker.sock:
connect: no such file or directory
```

**Shkaku:** Docker CLI ishte i instaluar në container-in `tools`, por nuk kishte lidhje me Docker daemon. Në WSL, `docker ps` dhe `systemctl status docker` punonin; kjo nuk mjaftonte për Pod-in. **Kontrolli i duhur** bëhet brenda Jenkins `container('tools')` me `docker version` dhe `docker info`. Lidhja e daemon-it duhet të konfigurohet sipas mjedisit; mos monto verbërisht `/var/run/docker.sock` të Minikube node duke supozuar se është socket-i i WSL. Pipeline-i përfundimtar ka kaluar, por metoda e saktë e lidhjes së daemon-it nuk mund të nxirret nga log-et e dhëna.

### B. `401 Unauthorized` nga Kubernetes API

Ky gabim u has më herët gjatë konfigurimit të Jenkins Kubernetes Cloud. Shkaku tipik është identiteti/token i pavlefshëm ose kubeconfig i papërshtatshëm. Duhet të kontrollohen credentials të Cloud, endpoint-i API dhe ServiceAccount, jo të zëvendësohen verbërisht me `cluster-admin`.

### C. `Jenkins doesn't have label 'python-agent'`

**Shkaku:** Label-i në pipeline nuk përputhej me agent-in e disponueshëm. Në konfigurimin përfundimtar përdoret **`student-k8s-agent`**, me container **`tools`**. Kontrollo label-in te **Manage Jenkins → Clouds → Kubernetes → Pod Templates**.

### D. `Forbidden: cannot get namespaces` — gabimi që bllokoi deploy

```text
Error from server (Forbidden): namespaces "students" is forbidden:
User "system:serviceaccount:jenkins:jenkins-deployer"
cannot get resource "namespaces"
```

**Shkaku:** Pipeline ekzekutonte `kubectl get namespace "$K8S_NAMESPACE"`. Resource `namespaces` është **cluster-scoped**, ndërsa Role `jenkins-deployer-role` jep leje vetëm për resurset **namespaced** brenda `students`. Kjo nuk tregonte mungesë lejesh për Deployment.

**Fix-i real:** Hoqëm **vetëm** komandën `kubectl get namespace "$K8S_NAMESPACE"` nga Jenkinsfile. Nuk krijuam RoleBinding tjetër dhe nuk i dhamë `cluster-admin`. Kontrollet `can-i create deployments` dhe `can-i patch deployments` kthyen `yes`. Pas këtij korrigjimi, pipeline u raportua **SUCCESS**.

### E. Placeholder i image në manifest

Jenkinsfile aktual zëvendëson `image: nginx:stable` me `glejnhithi/student-k8s-cicd:$BUILD_NUMBER` përmes `sed`, pastaj bën `kubectl apply`. Është shtuar kontrolli `grep -q 'image: nginx:stable'` që pipeline të dështojë qartë nëse manifesti ndryshon. Nëse përdor Kustomize/Helm në të ardhmen, mund ta zëvendësosh këtë mekanizëm me një mënyrë më të qëndrueshme të menaxhimit të image tags.

## 11. Verifikimi pas deploy

```bash
kubectl get pods,deploy,svc -n students
kubectl rollout status deployment/student-app -n students
kubectl get deployment student-app -n students \
  -o jsonpath='{.spec.template.spec.containers[*].image}{"\n"}'
kubectl port-forward -n students svc/student-app 8085:80
```

Në një terminal tjetër:

```bash
curl http://localhost:8085/health
```

Kontrollo Docker Hub për tag-un e build-it. Nëse rollout dështon:

```bash
kubectl describe deployment student-app -n students
kubectl get events -n students --sort-by=.lastTimestamp
kubectl logs -n students deployment/student-app --tail=100
```

## 12. Demo: ndryshim kodi dhe rollout i ri

1. Ndrysho mesazhin e API në `app/main.py`.
2. Nëse duhet, përditëso `tests/test_app.py`.
3. Ekzekuto testet dhe publiko ndryshimin:

```bash
python -m pytest -v
git add app tests
git commit -m "feat: update student API message"
git push origin main
```

4. Ekzekuto Jenkins **Build Now**, ose prit Poll SCM nëse është aktiv.
5. Verifiko tag-un e ri në Docker Hub dhe në Deployment:

```bash
kubectl rollout history deployment/student-app -n students
kubectl get pods -n students -o wide
```

6. Opsional, demonstrim i rollback-ut kur ekziston një revision i mëparshëm:

```bash
kubectl rollout undo deployment/student-app -n students
kubectl rollout status deployment/student-app -n students
```

> Rollback i Kubernetes ndryshon Deployment në cluster; një ekzekutim i ri i pipeline mund ta rikthejë versionin më të fundit të image-it.

## 13. Siguria dhe kufizimet

- Docker daemon access është shumë i privilegjuar; përdore vetëm në laborator të besuar. Për prodhim përdor build runners të izoluar ose build pa daemon.
- `jenkins-deployer` ka Role të kufizuar në namespace `students`, por `delete` dhe shkrimi në ConfigMaps mund të hiqen për të ndjekur parimin *least privilege*.
- Mos ruaj token-e, fjalëkalime ose kubeconfig në Git. Përdor Jenkins Credentials dhe Kubernetes ServiceAccount.
- Docker Hub repo duhet të jetë public ose duhet `imagePullSecret` në `students`.
- `timeout(time: 20, unit: 'MINUTES')` është kufiri i pipeline-it; për mjedise të ngadalta mund të kërkojë rregullim.
- README është udhëzues i workshop-it, jo një konfigurim production-ready.

## 14. Checklist final

- [ ] Jenkins service është aktiv në WSL.
- [ ] Minikube është aktiv dhe `kubectl get nodes` funksionon.
- [ ] Kubernetes Cloud krijon agent-in `student-k8s-agent` me container `tools`.
- [ ] `docker version` dhe `docker info` punojnë **brenda agent-it**.
- [ ] Credential `dockerhub` është konfiguruar.
- [ ] Testet Python kalojnë.
- [ ] Docker image publikohet në `glejnhithi/student-k8s-cicd:BUILD_NUMBER`.
- [ ] `jenkins-deployer` ka lejet e nevojshme në `students`.
- [ ] Jenkinsfile **nuk** thërret `kubectl get namespace students`.
- [ ] Deployment `student-app` bëhet `Ready`.
- [ ] `/health` përgjigjet pas `kubectl port-forward`.

**Rezultati:** Studentët shohin rrugën e plotë nga `git push` deri te aplikacioni që ekzekutohet në Kubernetes, dhe mësojnë të diagnostikojnë problemet e Docker daemon, Jenkins labels dhe Kubernetes RBAC.
