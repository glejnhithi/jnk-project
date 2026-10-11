# Student Kubernetes CI/CD Workshop — Jenkins në WSL (3 orë)

**GitHub → Jenkins (Built-In Node në WSL) → Python/pytest → Docker build → Docker Hub → kubectl → Minikube**

Ky laborator përdor **Jenkins të instaluar si Linux service në WSL Ubuntu**. Pipeline ekzekutohet **direkt në Jenkins Built-In Node** (përdoruesi Linux `jenkins`), **jo në Docker Agent dhe jo në Kubernetes Jenkins Agent**. Docker përdoret vetëm për ndërtimin dhe publikimin e image-it; Kubernetes përdoret vetëm për deployment të aplikacionit.

> **Status:** Konfigurimi i përdoruesit personal `glejnh` është verifikuar: context `minikube`, node `Ready`, Kubernetes v1.37.0. Nga Jenkins është verifikuar Docker Client/Server 28.1.1. Gabimi i fundit ishte `kubectl config current-context: current-context is not set` për përdoruesin `jenkins`. Hapat më poshtë e adresojnë; verifikoji para se të konsiderosh pipeline-in të suksesshëm në këtë mënyrë të re.

## 1. Arkitektura

```text
Student → git push → GitHub (glejnhithi/jnk-project)
                          |
                          v
                 Jenkins service (WSL)
                 Built-In Node: label built-in
                 Linux user: jenkins
                          |
             +------------+--------------+
             |            |              |
          pytest      docker build    kubectl
                          |              |
                      Docker Hub      Minikube
                 glejnhithi/          namespace: students
                 student-k8s-cicd     Deployment: student-app
```

Nuk kërkohet `student-k8s-agent`, Pod template, `container('tools')` ose Docker-in-Docker.

## 2. Programi 180-minutësh

| Minutat | Aktiviteti | Rezultati |
|---|---|---|
| 0–25 | Flask API dhe pytest | Testet kalojnë |
| 25–45 | Docker build dhe test lokal | `/health` përgjigjet |
| 45–60 | GitHub dhe Git | Kodi në branch `main` |
| 60–90 | Jenkins Built-In Node dhe credentials | Jenkins mund të ekzekutojë komanda |
| 90–120 | Pipeline: test, build, push | Image me tag të ri në Docker Hub |
| 120–155 | Minikube dhe deployment | Pods `Ready` në `students` |
| 155–180 | Ndryshim kodi, rerun, troubleshooting/rollback | CI/CD end-to-end |

## 3. Parakushtet

- WSL Ubuntu me Jenkins service, Git, Python 3, `python3-venv`, Docker Engine/CLI, `kubectl`, Minikube.
- Jenkins plugins: Pipeline, Git, Credentials Binding.
- GitHub repository: `https://github.com/glejnhithi/jnk-project.git`.
- Docker Hub repository publik: `glejnhithi/student-k8s-cicd`.
- Jenkins credential **Username with password**, ID `dockerhub`, ku password është Docker Hub access token.
- Jenkins Built-In Node me **1 executor** dhe label `built-in` (ose ndrysho label-in në Jenkinsfile sipas konfigurimit real).
- Minikube aktiv, namespace `students` i krijuar paraprakisht.

Kontrollo në WSL:

```bash
sudo systemctl status jenkins --no-pager
sudo systemctl status docker --no-pager
python3 --version
docker version
minikube status
kubectl config current-context
kubectl get nodes
```

## 4. Jenkins Built-In Node (pa agjent të veçantë)

Në Jenkins UI: **Manage Jenkins → Nodes → Built-In Node → Configure**. Vendos **Number of executors = 1**, **Labels = built-in**. Në Jenkinsfile përdor:

```groovy
pipeline {
    agent { label 'built-in' }
    // stages ...
}
```

**Mos përdor** `agent { label 'student-k8s-agent' }`, `container('tools')` ose një Pod template. Në një laborator të besuar mund të ekzekutosh build në controller; në prodhim rekomandohet agjent i izoluar.

Verifiko mjetet nga përdoruesi real i Jenkins:

```bash
sudo -u jenkins -H python3 --version
sudo -u jenkins -H docker version
sudo -u jenkins -H docker info >/dev/null
sudo -u jenkins -H kubectl version --client
```

Nëse Docker kthen `permission denied`, vetëm për laboratorin lokal:

```bash
sudo usermod -aG docker jenkins
sudo systemctl restart jenkins
sudo -u jenkins -H docker info >/dev/null
```

**Siguri:** grupi `docker` jep praktikisht privilegje root. Mos ekzekuto pipeline nga kod i pabesuar në këtë node.

### Paralajmërimet e Docker plugins

Në një ekzekutim u shfaqën paralajmërime për `docker-ai`, `docker-buildx`, `docker-compose`, etj. Komandat `docker version` dhe `docker info` arritën te Docker Server; paralajmërimet nuk ishin shkaku i dështimit të asaj faze. Nëse `docker build` dështon më vonë, kontrollo veçanërisht plugin-in `buildx`.

## 5. Gabimi që rregulluam: Jenkins nuk ka kubeconfig

Përdoruesi `glejnh` ktheu:

```text
$ kubectl config current-context
minikube
$ kubectl get nodes
minikube   Ready   control-plane   ...   v1.37.0
```

Por Jenkins ktheu:

```text
$ sudo -u jenkins -H kubectl config get-contexts
CURRENT   NAME   CLUSTER   AUTHINFO   NAMESPACE
$ sudo -u jenkins -H kubectl config current-context
error: current-context is not set
$ sudo -u jenkins -H sh -c 'echo HOME=$HOME; echo KUBECONFIG=${KUBECONFIG:-unset}'
HOME=/var/lib/jenkins
KUBECONFIG=unset
```

**Shkaku:** Jenkins service ekzekutohet si përdorues tjetër Linux. Ai kërkon kubeconfig te `/var/lib/jenkins/.kube/config`, jo te home i `glejnh`.

### Zgjidhja për Minikube lokal

Ekzekuto si `glejnh` (përdoruesi që ka context funksional):

```bash
# Mos krijo skedarë të lexueshëm nga përdoruesit e tjerë.
umask 077
kubectl config view --raw --flatten --minify > /tmp/jenkins-minikube-config

# Krijo konfigurimin privat për Jenkins.
sudo install -d -m 700 -o jenkins -g jenkins /var/lib/jenkins/.kube
sudo install -m 600 -o jenkins -g jenkins \
  /tmp/jenkins-minikube-config /var/lib/jenkins/.kube/config
rm -f /tmp/jenkins-minikube-config
```

`--flatten` fut certifikatat brenda kubeconfig-it, kështu që Jenkins nuk varet nga skedarët e certifikatave në home të përdoruesit personal.

**Kujdes:** kjo kopjon kredencialet ekzistuese të Minikube dhe mund t'i japë Jenkins privilegje administratori. Përdore vetëm në laboratorin lokal; në mjedis real përdor identitet dhe kubeconfig të kufizuar me RBAC.

### Verifikimi i detyrueshëm

```bash
sudo -u jenkins -H kubectl config current-context
sudo -u jenkins -H kubectl get nodes
sudo -u jenkins -H kubectl get pods -n students
sudo -u jenkins -H kubectl auth can-i create deployments -n students
sudo -u jenkins -H kubectl auth can-i patch deployments -n students
```

Pritet `minikube`, node `Ready` dhe `yes` për të dyja komandat `can-i`. Nëse këto dështojnë, mos vazhdo te Build Now: kontrollo lidhjen me Kubernetes API dhe identitetin e kubeconfig-it.

## 6. Namespace dhe RBAC: çfarë mësuam

Namespace krijohet **një herë**, nga përdoruesi administrator:

```bash
kubectl create namespace students --dry-run=client -o yaml | kubectl apply -f -
```

Në variantin e vjetër me Kubernetes Jenkins Pod përdornim `ServiceAccount` `jenkins-deployer` në namespace `jenkins`, me `Role` dhe `RoleBinding` në `students`. Testet:

```bash
kubectl auth can-i create deployments -n students \
  --as=system:serviceaccount:jenkins:jenkins-deployer
kubectl auth can-i patch deployments -n students \
  --as=system:serviceaccount:jenkins:jenkins-deployer
```

kthyen `yes`. Megjithatë `kubectl get namespace students` ktheu **Forbidden**, sepse `namespaces` është burim në nivel cluster-i dhe Role në `students` nuk e autorizon. Prandaj e hoqëm atë komandë nga pipeline, në vend që të shtonim privilegje të panevojshme.

**Në konfigurimin aktual WSL**, identiteti është ai i kubeconfig-it të përdoruesit `jenkins`, jo automatikisht `jenkins-deployer`. RBAC i vjetër i Pod-it nuk zëvendëson kubeconfig-in e WSL.

## 7. Aplikacioni dhe testet lokale

Nga root i repository-t:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -v
python -m app.main
```

Në terminal tjetër:

```bash
curl http://localhost:5000/
curl http://localhost:5000/health
```

Mbylle serverin me `Ctrl+C`.

## 8. Docker build dhe test lokal

```bash
docker build -t student-k8s-cicd:local .
docker run --rm -d --name student-test -p 5000:5000 student-k8s-cicd:local
curl http://localhost:5000/health
docker stop student-test
```

Nëse porta 5000 është e zënë, përdor `-p 5001:5000` dhe testo `localhost:5001`.

## 9. GitHub dhe Jenkins job

Repository: `https://github.com/glejnhithi/jnk-project.git`.

Për projekt ekzistues:

```bash
git remote -v
git status
git add README.md Jenkinsfile
git commit -m "docs: document Jenkins WSL built-in CI/CD"
git push origin main
```

Në Jenkins: **New Item → Pipeline**; **Definition = Pipeline script from SCM**; SCM = Git; Repository URL si më sipër; Branch = `*/main`; Script Path = `Jenkinsfile`.

Në **Manage Jenkins → Credentials** krijo `dockerhub` si **Username with password**, username `glejnhithi`, password Docker Hub access token. Mos vendos token në Git.

Për Jenkins lokal `localhost:8080`, GitHub nuk mund të dërgojë webhook drejtpërdrejt. Mund të përdorësh **Build Now** ose **Poll SCM** me `H/2 * * * *`.

## 10. Jenkins Pipeline: fazat

Pipeline në Built-In Node duhet të përmbajë:

1. **Checkout** — `checkout scm`.
2. **Test** — krijon `.venv`, instalon dependencies, ekzekuton `pytest`.
3. **Check Docker and Kubernetes** — `docker version`, `docker info`, `kubectl config current-context`, `kubectl auth can-i ...`.
4. **Docker Build** — `docker build -t glejnhithi/student-k8s-cicd:$BUILD_NUMBER .`.
5. **Docker Hub Push** — përdor Jenkins credential `dockerhub` dhe `docker login --password-stdin`.
6. **Deploy to Kubernetes** — `kubectl apply` për Service/Deployment dhe pret rollout-in.

Pjesa e deploy-it nuk duhet të përmbajë `kubectl get namespace students`. Shembull:

```groovy
stage('Deploy to Kubernetes') {
    steps {
        sh '''
            set -eu
            IMAGE="$DOCKERHUB_USER/$IMAGE_NAME:$BUILD_NUMBER"
            kubectl apply -n "$K8S_NAMESPACE" -f kubernetes/service.yaml
            sed "s|image: IMAGE_PLACEHOLDER|image: $IMAGE|" \
              kubernetes/deployment.yaml | kubectl apply -n "$K8S_NAMESPACE" -f -
            kubectl rollout status deployment/student-app \
              -n "$K8S_NAMESPACE" --timeout=180s
            kubectl get pods,deployments,services -n "$K8S_NAMESPACE"
        '''
    }
}
```

**Kontroll i rëndësishëm i manifestit:** në versionin e projektit të disponueshëm, `kubernetes/deployment.yaml` përmban `image: IMAGE_PLACEHOLDER`. Prandaj `sed` duhet të zëvendësojë pikërisht `IMAGE_PLACEHOLDER`. Nëse Jenkinsfile aktual kërkon `image: nginx:stable`, përshtate atë me manifestin real përpara ekzekutimit. Mos përdor `sed` që nuk gjen asnjë përputhje.

## 11. Kontrollo deployment në Minikube

```bash
kubectl get pods,deploy,svc -n students
kubectl rollout status deployment/student-app -n students
kubectl get deployment student-app -n students \
  -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
kubectl port-forward -n students svc/student-app 8085:80
```

Në terminal tjetër:

```bash
curl http://localhost:8085/
curl http://localhost:8085/health
```

Deployment është konfiguruar me **2 replika**, Service `student-app` port 80 → container port 5000.

## 12. Live demo dhe rollback

Ndrysho mesazhin në `app/main.py`, përditëso testet nëse nevojitet, pastaj:

```bash
python -m pytest -v
git add app/main.py tests/
git commit -m "feat: update student welcome message"
git push origin main
```

Në Jenkins kliko **Build Now** (ose prit Poll SCM). Kontrollo tag-un e ri dhe endpoint-in pas rollout-it.

```bash
kubectl rollout history deployment/student-app -n students
kubectl rollout undo deployment/student-app -n students
kubectl rollout status deployment/student-app -n students
```

Rollback funksionon vetëm nëse ekziston revision i mëparshëm.

## 13. Troubleshooting: gabimet që hasëm

| Gabimi | Shkaku | Zgjidhja |
|---|---|---|
| `Jenkins doesn't have label 'python-agent'` | Label/agent i pakonfiguruar | Përdor Built-In Node me label `built-in` në këtë variant |
| `docker.sock: no such file` në Kubernetes Pod | Pod nuk kishte Docker daemon/socket | Mos bëj build në Pod; përdor Docker daemon në WSL |
| Kubernetes Cloud `401 Unauthorized` | Credentials të Kubernetes Agent | Nuk përdoret më Kubernetes Cloud për këtë pipeline |
| `namespaces "students" is forbidden` | Namespace është cluster-scoped | Hiq `kubectl get namespace` nga pipeline |
| `current-context is not set` | Përdoruesi `jenkins` nuk ka kubeconfig | Instalo kubeconfig të veçantë te `/var/lib/jenkins/.kube/config` |
| `docker: permission denied` | Jenkins nuk ka akses te Docker socket | Kontrollo permissions; për lab mund të përdoret grupi `docker` |
| `ImagePullBackOff` | Image/tag i pasaktë ose registry privat | Verifiko Docker Hub repository dhe tag |
| `rollout status` timeout | Pods nuk bëhen Ready | `kubectl describe pods -n students` dhe `kubectl logs` |
| `sed` nuk ndryshon image | Placeholder nuk përputhet | Përdor `IMAGE_PLACEHOLDER` sipas manifestit real |

## 14. Siguria dhe kufizimet

- **Mos commit** kubeconfig, token, certifikata private apo Docker Hub credentials.
- Kubeconfig i kopjuar me `--raw --flatten` përmban kredenciale sensitive dhe mund të ketë privilegje të larta; përdore vetëm për këtë laborator lokal.
- Docker socket dhe ekzekutimi në Jenkins controller janë me privilegje të larta. Në prodhim përdor agent të dedikuar, RBAC minimal dhe menaxhim të sigurt të kredencialeve.
- Pipeline në këtë version nuk ekzekutohet në Kubernetes Pod. Minikube është vetëm mjedisi ku deploy-ohet aplikacioni.

**Kriteri i suksesit:** Jenkins Built-In Node ekzekuton testet, ndërton/publikon image-in dhe përdor kubeconfig-in e vet për të deploy-uar `student-app` në namespace `students`; `curl http://localhost:8085/health` përgjigjet me sukses pas port-forward.
