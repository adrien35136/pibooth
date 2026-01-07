# Agents IA – Adaptation de Pibooth sur Raspberry Pi 4

## 🎯 Objectif global
Adapter **Pibooth** pour fonctionner correctement sur une **Raspberry Pi 4** avec les versions récentes de **Raspberry Pi OS**, afin de **réduire le temps de génération des arrière-plans (actuellement ~25 secondes)** tout en conservant une **qualité d’image élevée**.

Ce fichier sert de **contexte projet permanent** pour les agents IA (GitHub Copilot, assistants, LLM).

---

## 📌 Contexte technique

### Situation actuelle
- Matériel : **Raspberry Pi 3 B+**
- Application : **Pibooth**
- État : ✅ Fonctionnel
- Bibliothèques utilisées :
  - `Picamera` (ancienne version, legacy)
  - `gphoto2`
- Fonctionnement :
  - Capture photo OK
  - Génération des arrière-plans lente (~25 secondes)
  - Système hybride : Raspberry Pi Camera pour le preview + Canon 1200D pour les captures
- Cause probable :
  - Limitation CPU / RAM de la Raspberry Pi 3 B+

### Version actuelle de Raspberry Pi OS :
adrien@raspberrypi:~ $ cat /etc/os-release
PRETTY_NAME="Raspbian GNU/Linux 11 (bullseye)" 
NAME="Raspbian GNU/Linux" VERSION_ID="11" VERSION="11 (bullseye)" VERSION_CODENAME=bullseye ID=raspbian ID_LIKE=debian HOME_URL="http://www.raspbian.org/" SUPPORT_URL="http://www.raspbian.org/RaspbianForums" BUG_REPORT_URL="http://www.raspbian.org/RaspbianBugs"

adrien@raspberrypi:~ $ uname -a Linux raspberrypi
6.1.21-v7+ #1642 SMP Mon Apr 3 17:20:52 BST 2023 armv7l GNU/Linux

adrien@raspberrypi:~ $ python3 --version Python 3.9.2

adrien@raspberrypi:~ $ python Python 3.9.2 (default, Mar 20 2025, 22:21:41) [GCC 10.2.1 20210110] on linux Type "help", "copyright", "credits" or "license" for more information. >>> import pygame pygame 1.9.6 Hello from the pygame community. https://www.pygame.org/contribute.html >>> import pillow Traceback (most recent call last): File "<stdin>", line 1, in <module> ModuleNotFoundError: No module named 'pillow' >>> import pyllow Traceback (most recent call last): File "<stdin>", line 1, in <module> ModuleNotFoundError: No module named 'pyllow' >>> quit() adrien@raspberrypi:~ $ gphoto2 --version gphoto2 --auto-detect gphoto2 2.5.28 Copyright (c) 2000-2021 Marcus Meissner and others gphoto2 comes with NO WARRANTY, to the extent permitted by law. You may redistribute copies of gphoto2 under the terms of the GNU General Public License. For more information about these matters, see the files named COPYING. This version of gphoto2 is using the following software versions and options: gphoto2 2.5.28 gcc, popt(m), exif, no cdk, no aa, no jpeg, no readline libgphoto2 2.5.27 standard camlibs, gcc, ltdl, EXIF libgphoto2_port 0.12.0 iolibs: disk ptpip serial usb1 usbdiskdirect usbscsi, gcc, ltdl, EXIF, USB, serial without locking Modèle Port ---------------------------------------------------------- Canon EOS 1200D usb:001,004 adrien@raspberrypi:~ $

---

### Problématique
- Migration vers une **Raspberry Pi 4** (plus performante)
- Problèmes rencontrés :
  - ❌ Le *legacy camera stack* n’existe plus
  - ❌ La bibliothèque **Picamera (v1)** n’est plus supportée
  - ❌ Pibooth ne fonctionne plus tel quel
- Les versions récentes de Raspberry Pi OS utilisent :
  - **libcamera** comme pile caméra principale
  - **Picamera2** comme API Python recommandée

➡️ **Pibooth doit être adapté pour utiliser la nouvelle pile caméra.**

---

## 🧠 Organisation des agents IA

Ce projet est découpé en plusieurs rôles logiques pour faciliter l’analyse, la migration et l’optimisation.

---

## 🤖 Agent 1 – Analyse de compatibilité (Architecte)

### Mission
Analyser l’architecture actuelle de Pibooth et identifier les éléments incompatibles avec Raspberry Pi 4.

### Responsabilités
- Identifier l’usage de :
  - `Picamera`
  - `gphoto2`
- Localiser :
  - L’initialisation caméra
  - La capture photo
  - Le pipeline de traitement d’image
- Repérer les dépendances au *legacy camera stack*

### Livrables
- Liste des fichiers/modules concernés
- Carte des dépendances caméra

---

## 🤖 Agent 2 – Expert Caméra Raspberry

### Mission
Définir une solution caméra moderne et compatible Raspberry Pi 4.

### Responsabilités
- Étudier l’intégration de :
  - **libcamera**
  - **Picamera2**
- Comparer :
  - Picamera (legacy) vs Picamera2
  - gphoto2 vs libcamera
- Proposer une stratégie de migration réaliste

### Livrables
- Choix technologique validé
- Recommandations d’API caméra

---

## 🤖 Agent 3 – Refactoring Pibooth

### Mission
Adapter le code source de Pibooth pour la nouvelle pile caméra.

### Responsabilités
- Remplacer les appels Picamera par Picamera2
- Adapter :
  - Initialisation caméra
  - Capture photo
  - Gestion des formats d’image
- Garantir la compatibilité avec le workflow Pibooth existant

### Livrables
- Version modifiée de Pibooth compatible Raspberry Pi 4
- Documentation des changements

---

## 🤖 Agent 4 – Optimisation des performances

### Mission
Réduire le temps de génération des arrière-plans.

### Responsabilités
- Identifier les goulots d’étranglement :
  - CPU
  - RAM
  - I/O disque
- Optimiser :
  - Résolution et formats
  - Pipeline de traitement d’image
  - Traitements synchrones / asynchrones
- Exploiter les capacités de la Raspberry Pi 4

### Livrables
- Stratégie d’optimisation
- Estimation des gains de performance

---

## 🤖 Agent 5 – Tests & Validation

### Mission
Valider la stabilité, les performances et la qualité.

### Responsabilités
- Tester :
  - Capture photo
  - Génération des arrière-plans
  - Temps de traitement
- Comparer :
  - Avant / après migration
- Vérifier la stabilité sur des sessions longues

### Livrables
- Rapport de tests
- Validation finale

---

## 📈 Indicateurs de succès

- ✅ Pibooth fonctionne sur Raspberry Pi 4
- ✅ Utilisation de **Picamera2 / libcamera**
- ⏱️ Temps de génération réduit de manière significative (objectif < 10 s)
- 🖼️ Qualité d’image conservée ou améliorée
- 🔧 Code maintenable et compatible avec les futures versions de Raspberry Pi OS

---

## 🧩 Prochaines étapes

1. Analyser le code existant de Pibooth
2. Valider l’utilisation de Picamera2
3. Tester une capture photo minimale avec Picamera2
4. Intégrer progressivement dans Pibooth
5. Optimiser les performances
6. Tester et valider

---

## ℹ️ Notes pour les agents IA

- Toujours privilégier **Picamera2** plutôt que Picamera legacy
- Éviter toute dépendance au *legacy camera stack*
- Tenir compte des contraintes matérielles embarquées
- Le code doit rester lisible et maintenable
