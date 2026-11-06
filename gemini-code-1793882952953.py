import numpy as np

# 1. Fonction pour lire les fichiers binaires générés par GNU Radio (ou KrakenSDR)
def read_complex_binary(filename):
    """
    Lit un fichier binaire contenant des échantillons complexes I/Q.
    Le type np.complex64 correspond au format par défaut des blocs File Sink.
    """
    return np.fromfile(filename, dtype=np.complex64)

# Remplace par les vrais noms de tes fichiers générés par Dionisio
file1 = "antenne_0_v4.bin"
file2 = "antenne_1_v4.bin"

print("Lecture des fichiers en cours...")
try:
    signal1 = read_complex_binary(file1)
    signal2 = read_complex_binary(file2)
    
    # 2. Paramètres du système
    sample_rate = 1e6      # 1 MS/s
    center_freq = 144e6    # 143 MHz (Fréquence du signal radar GRAVES)
    c = 3e8                # Vitesse de la lumière (m/s)
    
    # Remplacer par l'espacement physique EXACT entre les deux antennes du KrakenSDR
    # (par exemple : 1.0 mètre)
    d = 1.0                

    # 3. Synchronisation et troncature des tailles
    min_len = min(len(signal1), len(signal2))
    
    # On analyse un bloc (ex: 1 million de points = 1 seconde d'enregistrement)
    N = min(1000000, min_len)
    s1 = signal1[:N]
    s2 = signal2[:N]

    # 4. Calcul de la différence de phase via FFT
    print("Calcul de la FFT (cela peut prendre quelques secondes)...")
    fft_1 = np.fft.fft(s1)
    fft_2 = np.fft.fft(s2)
    
    # Identification de l'index fréquentiel où l'écho est le plus puissant
    idx_pic = np.argmax(np.abs(fft_1)) 
    
    # Différence de phase brute au niveau du pic de fréquence
    delta_phi_brut = np.angle(fft_1[idx_pic] * np.conj(fft_2[idx_pic]))

    # --- CALIBRATION FIXE (KRAKENSDR) ---
    # Valeur d'erreur mesurée avec un émetteur face aux antennes (0°)
    # À mesurer UNE SEULE FOIS puis à figer ici. 
    # Mettre 0.0 pour l'instant si vous n'avez pas encore fait la calibration.
    offset_materiel_deg = 70.61 
    offset_materiel_rad = np.radians(offset_materiel_deg)

    # Correction du déphasage
    delta_phi_corrige = delta_phi_brut - offset_materiel_rad
    
    # On s'assure que l'angle reste modulo 2*pi (entre -pi et pi)
    delta_phi_corrige = (delta_phi_corrige + np.pi) % (2 * np.pi) - np.pi

    # 5. Calcul du Time Delay (Delta t) et de l'Angle d'arrivée (Theta)
    delta_time = delta_phi_corrige / (2 * np.pi * center_freq)
    
    delta_distance = c * delta_time
    
    # np.clip force le ratio entre -1 et 1 pour éviter un crash mathématique (arcsin) dû au bruit
    ratio = np.clip(delta_distance / d, -1.0, 1.0)
    angle = np.degrees(np.arcsin(ratio))

    # Affichage des résultats
    print("\n--- RÉSULTATS DE L'ANALYSE ---")
    print(f"Déphasage brut (mesuré)      : {np.degrees(delta_phi_brut):.2f}°")
    print(f"Offset matériel soustrait    : {offset_materiel_deg:.2f}°")
    print(f"Déphasage final corrigé      : {np.degrees(delta_phi_corrige):.2f}° ({delta_phi_corrige:.4f} rad)")
    print(f"Différence de marche         : {delta_distance * 100:.2f} cm")
    print(f"Time delay réel (Delta t)    : {delta_time * 1e9:.4f} ns")
    print(f"Angle d'arrivée de l'écho    : {angle:.2f}°")
    
except FileNotFoundError:
    print(f"\n[ERREUR] Impossible de trouver les fichiers '{file1}' ou '{file2}'.")
    print("Vérifiez qu'ils sont bien dans le même dossier que ce script Python.")
except Exception as e:
    print(f"\n[ERREUR INATTENDUE] : {e}")