import os
import subprocess
import time
import pyfiglet
import sys

# Habilitar colores en terminales Windows
os.system('')

texto = "hassh - crakcer"
banner = pyfiglet.figlet_format(texto, font="slant")
print(banner)

tiempo_inicio = time.time()
print("\nHora de inicio del script:", time.ctime())

hashcat_bin = "./hashcat.exe"
caracteres = "?l?d{}"
max_dentro = 8
max_fuera = 14
min_fuera = 4
carpeta_entrada = "hashes-clasificados"
carpeta_salida = "cracked-passwords"

if not os.path.exists(carpeta_salida):
    os.makedirs(carpeta_salida)

def sacar_mascaras():
    lista = []
    for d in range(4):
        if d <= max_dentro:
            lista.append(f"urjc{{{'?1' * d}}}")
            lista.append(f"flag{{{'?1' * d}}}")
    for i in range(max_fuera - min_fuera + 1):
        fuera = min_fuera + i
        dentro = i + 4
        if fuera <= max_fuera:
            lista.append("?1" * fuera)
        if dentro <= max_dentro:
            lista.append(f"urjc{{{'?1' * dentro}}}")
            lista.append(f"flag{{{'?1' * dentro}}}")
    return lista

mascaras = sacar_mascaras()

for archivo in sorted(os.listdir(carpeta_entrada)):
    ruta = os.path.join(carpeta_entrada, archivo)
    if not os.path.isfile(ruta):
        continue

    lineas = [linea.strip() for linea in open(ruta) if linea.strip()]
    if len(lineas) < 2:
        continue

    modo = lineas[0]
    hashes = lineas[1:]
    
    print(f"\nArchivo {archivo}\n")
    print(f"Hash mode de hashcat: {modo}. Hay {len(hashes)} hashes para crackear")

    archivo_hashes_temp = f"hashes_temp_{modo}.txt"
    print(f"\nProcesando {len(hashes)} hashes juntos")
    inicio_pass_time = time.time()
    print("\nHora de inicio:", time.ctime())

    hashes_pendientes = set(hashes)

    for num_mask, mascara in enumerate(mascaras, 1):
        if not hashes_pendientes:
            break

        with open(archivo_hashes_temp, "w") as f:
            f.write("\n".join(hashes_pendientes))

        comando = [
            hashcat_bin, "-a", "3", "-m", modo, "-1", caracteres,
            archivo_hashes_temp, mascara,
            "-O", "-w", "3", "--potfile-disable",
            "--status", "--status-timer=1"
        ]

        proceso = subprocess.Popen(
            comando,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        print(f"\033[0mIntento {num_mask}/{len(mascaras)}. Probando con: {mascara}")
        print(f"\033[90m    [Status] Iniciando proceso...\033[K")
        print(f"\033[90m    [Tiempo esperado] Estimando...\033[K\033[0m")

        prog = "Iniciando..."
        eta = "Calculando..."
        bloque_status = []
        colectando = False
        hubo_bingo = False

        for linea in proceso.stdout:
            stripped = linea.strip()
            if not stripped:
                continue

            if stripped.startswith("Status"):
                colectando = True
                bloque_status = [stripped]
                continue

            if colectando:
                bloque_status.append(stripped)
                if "Progress" in stripped:
                    for l in bloque_status:
                        if "Progress" in l:
                            prog = l.split(":", 1)[1].strip()
                        if "Time.Estimated" in l:
                            eta = l.split(":", 1)[1].strip()
                    
                    sys.stdout.write(f"\033[2A\r\033[90m    [Status] {prog}\033[K\n")
                    sys.stdout.write(f"\r\033[90m    [Tiempo esperado] {eta}\033[K\033[0m\n")
                    sys.stdout.flush()
                    
                    colectando = False
                    bloque_status = []
                continue

            if ":" in stripped:
                hash_match = None
                pass_match = None
                
                for h in list(hashes_pendientes):
                    if stripped.lower().startswith(h.lower() + ":"):
                        hash_match = h
                        pass_match = stripped[len(h)+1:]
                        break
                
                if hash_match and pass_match:
                    sys.stdout.write("\033[2A\r\033[K\033[1B\r\033[K\033[1A")
                    sys.stdout.flush()
                    
                    print()
                    print("\033[1;32m" + "*"*100)
                    print(f"* ¡BINGO! Contraseña encontrada para el hash {hash_match}: {pass_match}")
                    print("*"*100 + "\033[0m")
                    print()
                    
                    hashes_pendientes.discard(hash_match)
                    hubo_bingo = True
                    
                    archivo_resultado = os.path.join(carpeta_salida, f"resultados-{modo}.txt")
                    with open(archivo_resultado, "a") as f_out:
                        f_out.write(f"{hash_match}:{pass_match}\n")

                    print("\nHora de crackeo de este hash:", time.ctime())
                    tiempo_total_pass = time.time() - inicio_pass_time 
                    print(f"\nCrackeo terminado en {tiempo_total_pass:.2f} segundos.")
                    
                    print(f"Quedan {len(hashes_pendientes)} hashes por crackear\n")
                    
                    print(f"\033[90m    [Status] {prog}\033[K")
                    print(f"\033[90m    [Tiempo esperado] {eta}\033[K\033[0m")
                    
                    if not hashes_pendientes:
                        proceso.terminate()
                        break

        proceso.wait()
        
        sys.stdout.write('\033[2A\r\033[K\033[1B\r\033[K\033[1A')
        sys.stdout.flush()

        if not hubo_bingo and len(hashes_pendientes) > 0:
            print("La contraseña no es así, seguimos buscando...")

    if os.path.exists(archivo_hashes_temp):
        os.remove(archivo_hashes_temp)

print("\nScript de crackeo terminado. Revisa la carpeta de resultados.")
print("\nHora de finalización:", time.ctime())
tiempo_total = time.time() - tiempo_inicio
print(f"\nCrackeo terminado en {tiempo_total:.2f} segundos.")
