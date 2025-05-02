# RASPTANK - Raspberry Pi Robot Controller

---

## Introduction

**RASPTANK** est un robot contrôlé par un Raspberry Pi et développé en Python. Il intègre des fonctionnalités avancées comme le suivi de ligne, la détection infrarouge, un module de tir, la commande à distance via MQTT, des effets lumineux, ainsi que la lecture de sons contextuels.

---

##  Collaborateurs

- Rafik BENNACER
- Felix Saint Jore
---

## Capacités du robot

| Capacité                          | Description |
|----------------------------------|-------------|
| Contrôle moteur                  | Avancer, reculer, pivoter avec précision. |
| Suivi de ligne                   | Détection de lignes au sol pour navigation autonome. |
| Détection infrarouge             | Évitement d'obstacles grâce à des capteurs IR. |
| LEDs                             | Signalisation visuelle avec animations. |
| Contrôle à distance              | Communication et commande via MQTT. |
| Module de tir                    | Simulation de tirs avec effets sonores/lumineux. |
| Lecture de sons                  | Sons associés à des actions (tir, démarrage, etc.). |

---

## Structure du code

### `song/` - Sons et gestion audio

Ce dossier contient tous les fichiers sonores (.mp3) utilisés par le robot, ainsi qu’un script Python pour les lire.

| Fichier                         | Description |
|---------------------------------|-------------|
| `acceleration.mp3`              | Son joué lors de l'accélération |
| `disco.mp3`                     | Mode disco (musique + lumières) |
| `missile.mp3`                   | Son de tir |
| `silence.mp3`                   | Arrêt ou neutralisation sonore |
| `start_engine.mp3`              | Démarrage du robot |
| `sui.mp3`                       | Son pour suivi ou événement personnalisé |
| `song.py`                       | Script Python pour lire les sons selon les événements |

---

### Dossier principal `RASPTANK/`

| Fichier/Dossier         | Description |
|-------------------------|-------------|
| `fire.py`               | Gère le système de tir du robot |
| `findline.py`           | Implémente la détection/suivi de ligne |
| `InfraLib.py`           | Librairie pour capteurs infrarouges |
| `LED.py`                | Contrôle des LEDs |
| `move.py`               | Mouvements (avancer, reculer, tourner) |
| `telecommande.py`       | Réception de commandes distantes (via MQTT) |
| `server.py`             | Serveur de contrôle principal |
| `setup.py`              | Script de configuration (optionnel) |
| `test.py`               | Tests unitaires ou d’intégration |
| `requirements.txt`      | Dépendances Python |

---

## Améliorations 
 - Interface web/mobile pour le contrôle distant
 - Computer vision pour automatisation des tirs.

