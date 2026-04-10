import bpy
import random
import string
import os
import math
import colorsys
import glob

# ==============================================================================
# 1. CONFIGURACIÓN DEL USUARIO (RUTAS Y PARÁMETROS)
# ==============================================================================

# Rutas de carpetas (USA RUTAS ABSOLUTAS)
CARPETA_FUENTES = "/home/randy/Python/BlenderPlateGenerator/Fonts"  # Ej: "C:/Fonts" o "/home/user/fonts"
CARPETA_HDRIS = "/home/randy/Python/BlenderPlateGenerator/HDRs"      # Ej: "C:/HDRIs"
CARPETA_SALIDA = "/home/randy/Python/BlenderPlateGenerator/Output"   # Ej: "C:/Salida" o "/home/user/salida"

CANTIDAD_A_GENERAR = 10 # Cuántas placas quieres hacer en esta tanda

# Rotación de la cámara/objeto (En grados).
# Representa el rango TOTAL de variación. Ej: X=60 significa +/- 30 grados desde su origen.
ROTACION_VAR_X = 60.0 
ROTACION_VAR_Y = 15.0
ROTACION_VAR_Z = 60.0

# Valores base de rotación del objeto en tu escena (Asumo que X está en 90 para estar de pie)
ROTACION_BASE = (90.0, 0.0, 0.0) 

# Rigurosidad (Roughness) de los materiales (Min, Max)
ROUGHNESS_MIN = 0.02
ROUGHNESS_MAX = 0.5

# Textos cortos para variar el título y subtítulo en cada placa
TITULOS_DISPONIBLES = [
    "CDMX",
    "EDOMEX",
    "JALISCO",
    "PUEBLA",
    "OAXACA",
    "SONORA",
    "YUCATAN",
    "SINALOA",
    "TABASCO",
    "COAHUILA",
    "QROO",
    "HIDALGO",
]

SUBTITULOS_DISPONIBLES = [
    "PARTICULAR",
    "PRIVADO",
    "VIG 2026",
    "VIG 2027",
    "NACIONAL",
    "ESTATAL",
    "OFICIAL",
    "SERVICIO",
    "TURISMO",
    "URBANO",
    "LOCAL",
    "FEDERAL",
]

TITULOS_ESTATALES = [
    "VEH ESTATAL",
    "AUTO ESTATAL",
    "USO ESTATAL",
    "CONTROL EST",
    "REG ESTATAL",
]

# ==============================================================================
# 2. FUNCIONES DE UTILIDAD (LÓGICA)
# ==============================================================================

def generar_texto_placa(patron):
    """Convierte un patrón como 'CCC-NNN' en 'XYZ-123'"""
    resultado = ""
    for char in patron:
        if char == 'C': resultado += random.choice(string.ascii_uppercase)
        elif char == 'N': resultado += random.choice(string.digits)
        else: resultado += char
    return resultado

def obtener_color(tipo):
    """Genera colores RGBA basados en las reglas semánticas"""
    if tipo == "blanco": return (0.9, 0.9, 0.9, 1.0) # Un blanco realista no es 1.0 absoluto
    if tipo == "negro": return (0.05, 0.05, 0.05, 1.0) # Un negro realista
    if tipo == "saturado":
        r, g, b = colorsys.hsv_to_rgb(random.random(), random.uniform(0.7, 1.0), random.uniform(0.7, 1.0))
        return (r, g, b, 1.0)
    if tipo == "saturado_claro":
        r, g, b = colorsys.hsv_to_rgb(random.random(), random.uniform(0.4, 0.7), random.uniform(0.8, 1.0))
        return (r, g, b, 1.0)
    if tipo == "oscuro":
        r, g, b = colorsys.hsv_to_rgb(random.random(), random.uniform(0.5, 1.0), random.uniform(0.1, 0.3))
        return (r, g, b, 1.0)
    return (1, 1, 1, 1)

def configurar_material(nombre, color_rgba):
    """Crea o actualiza un material con el color y roughness aleatorio"""
    mat = bpy.data.materials.get(nombre)
    if not mat:
        mat = bpy.data.materials.new(name=nombre)
        mat.use_nodes = True
    
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color_rgba
        bsdf.inputs["Roughness"].default_value = random.uniform(ROUGHNESS_MIN, ROUGHNESS_MAX)
        bsdf.inputs["Metallic"].default_value = 0.2 # Ligero toque metálico base
    return mat

def cargar_fuente_random():
    fuentes = glob.glob(os.path.join(CARPETA_FUENTES, "*.ttf")) + glob.glob(os.path.join(CARPETA_FUENTES, "*.otf"))
    if not fuentes: return None
    fuente_elegida = random.choice(fuentes)
    # Cargar en Blender
    return bpy.data.fonts.load(fuente_elegida, check_existing=True)

def configurar_hdri_random():
    hdris = glob.glob(os.path.join(CARPETA_HDRIS, "*.exr")) + glob.glob(os.path.join(CARPETA_HDRIS, "*.hdr"))
    if not hdris: return
    
    world = bpy.context.scene.world
    if not world.use_nodes: world.use_nodes = True
    tree = world.node_tree
    
    # Buscar nodos
    bg_node = tree.nodes.get("Background")
    env_node = tree.nodes.get("Environment Texture")
    map_node = tree.nodes.get("Mapping")
    tex_coord = tree.nodes.get("Texture Coordinate")
    
    # Crear nodos si no existen
    if not env_node:
        env_node = tree.nodes.new('ShaderNodeTexEnvironment')
        tree.links.new(env_node.outputs["Color"], bg_node.inputs["Color"])
    if not map_node:
        map_node = tree.nodes.new('ShaderNodeMapping')
        tree.links.new(map_node.outputs["Vector"], env_node.inputs["Vector"])
    if not tex_coord:
        tex_coord = tree.nodes.new('ShaderNodeTexCoord')
        tree.links.new(tex_coord.outputs["Generated"], map_node.inputs["Vector"])

    # Cargar imagen y rotar
    hdri_elegido = random.choice(hdris)
    img = bpy.data.images.load(hdri_elegido, check_existing=True)
    env_node.image = img
    
    # Rotación Z aleatoria (0 a 360 grados en radianes)
    map_node.inputs["Rotation"].default_value[2] = random.uniform(0, 2 * math.pi)

def construir_mapa_inputs_gn(modificador):
    """Devuelve {nombre_visible: identificador_real} de los inputs expuestos en Geometry Nodes."""
    mapa = {}
    grupo = getattr(modificador, "node_group", None)
    interfaz = getattr(grupo, "interface", None)
    if not interfaz:
        return mapa

    for item in interfaz.items_tree:
        if getattr(item, "item_type", "") == "SOCKET" and getattr(item, "in_out", "") == "INPUT":
            mapa[item.name] = item.identifier
    return mapa

def set_input_gn(modificador, mapa_inputs, nombre_input, valor):
    """Asigna un valor a un input real del modificador evitando crear custom properties no conectadas."""
    key_real = mapa_inputs.get(nombre_input)

    # Fallback por nombre solo si existe realmente en el modificador.
    if key_real is None and nombre_input in modificador.keys():
        key_real = nombre_input

    if key_real is None or key_real not in modificador.keys():
        print(f"[ADVERTENCIA] Input no encontrado en Geometry Nodes: {nombre_input}")
        return False

    modificador[key_real] = valor
    return True

# ==============================================================================
# 3. MOTOR PRINCIPAL
# ==============================================================================

def generar_lote():
    obj = bpy.data.objects.get("Plane") # Asegúrate de que tu objeto se llame así
    if obj is None:
        raise RuntimeError("No se encontró el objeto 'Plane'.")

    mod = obj.modifiers.get("GeometryNodes")
    if mod is None:
        raise RuntimeError("No se encontró el modificador 'GeometryNodes' en 'Plane'.")

    mapa_inputs = construir_mapa_inputs_gn(mod)
    if not mapa_inputs:
        print("[ADVERTENCIA] No se pudo leer la interfaz de Geometry Nodes. Se intentará con claves directas.")
    
    if not os.path.isdir(CARPETA_SALIDA):
        raise FileNotFoundError(
            f"La carpeta de salida no existe o no es válida: {CARPETA_SALIDA}"
        )

    # Identificar nombres de los enchufes del modificador (Para Blender 4.0+)
    # Asumimos que los nombres expuestos coinciden con los de tu captura
    
    for i in range(CANTIDAD_A_GENERAR):
        # --- 1. SELECCIÓN DE TEMPLATES ---
        id_struct = random.randint(1, 4)
        id_color = random.randint(1, 5)
        
        # --- 2. APLICAR STRUCTURAL TEMPLATE ---
        texto_placa = ""
        titulo = random.choice(TITULOS_DISPONIBLES)
        subtitulo = random.choice(SUBTITULOS_DISPONIBLES)
        
        # Valores por defecto para resetear
        barra_izquierda = False
        barra_derecha = False
        barra_arriba = False
        barra_abajo = False
        borde = True
        alto = 2.5
        ancho_barras = 0.0
        
        if id_struct == 1:
            texto_placa = generar_texto_placa("CCC-NNN-C")
            barra_arriba = True
            barra_abajo = True
            alto = 2.5
            ancho_barras = 1.0
        elif id_struct == 2:
            texto_placa = generar_texto_placa("CCC-NNN")
            barra_izquierda = True
            barra_derecha = True
            alto = 2.5
            ancho_barras = 1.0
        elif id_struct == 3:
            titulo = random.choice(TITULOS_ESTATALES)
            subtitulo = "" # Sin subtitulo
            texto_placa = generar_texto_placa("CC NN")
            barra_izquierda = True
            barra_derecha = True
            alto = 2.5
            ancho_barras = 2.0
        elif id_struct == 4:
            texto_placa = generar_texto_placa("CCC-NNN")
            alto = 2.5
            ancho_barras = 0.0 # Sin barras

        # Aplicar parámetros estructurales
        set_input_gn(mod, mapa_inputs, "Barra_Izquierda", barra_izquierda)
        set_input_gn(mod, mapa_inputs, "Barra_Derecha", barra_derecha)
        set_input_gn(mod, mapa_inputs, "Barra_Arriba", barra_arriba)
        set_input_gn(mod, mapa_inputs, "Barra_Abajo", barra_abajo)
        set_input_gn(mod, mapa_inputs, "Borde", borde)
        set_input_gn(mod, mapa_inputs, "Alto", alto)
        set_input_gn(mod, mapa_inputs, "Ancho_Barras", ancho_barras)
            
        # Asignar Textos
        set_input_gn(mod, mapa_inputs, "Title", titulo)
        set_input_gn(mod, mapa_inputs, "Plate", texto_placa)
        set_input_gn(mod, mapa_inputs, "Subtitle", subtitulo)
        
        # --- 3. CÁLCULO DINÁMICO DEL LARGO ---
        # Regla: 6.0 de largo aloja 9 letras (0.666 por letra). 
        letras_reales = len(texto_placa)
        largo_dinamico = letras_reales * 0.666
        # Si hay barras laterales, sumar espacio (aprox 1.0 o el ancho de la barra)
        if barra_izquierda or barra_derecha:
            largo_dinamico += (ancho_barras * 1.5) # Ajuste compensatorio
        
        # Si la placa generada es muy corta, no queremos que sea cuadrada, ponemos un mínimo
        set_input_gn(mod, mapa_inputs, "Largo", max(largo_dinamico, 4.5))

        # --- 4. FUENTES ALEATORIAS ---
        fuente_rand = cargar_fuente_random()
        if fuente_rand:
            set_input_gn(mod, mapa_inputs, "FontPlate", fuente_rand)
            set_input_gn(mod, mapa_inputs, "FontOther", fuente_rand) # O cargar otra diferente para el titulo

        # --- 5. COLOR TEMPLATES (Materiales) ---
        c_title = c_sub = c_plate = c_bg = c_out = c_bar = None
        
        if id_color == 1:
            c_title = c_sub = c_bg = obtener_color("blanco")
            c_plate = c_out = obtener_color("negro")
            c_bar = obtener_color("saturado")
        elif id_color == 2:
            c_title = c_sub = obtener_color("saturado_claro")
            c_bg = obtener_color("blanco")
            c_plate = c_out = obtener_color("negro")
            c_bar = obtener_color("oscuro")
            if random.choice([True, False]): c_bar = obtener_color("negro")
        elif id_color == 3:
            c_title = c_sub = c_bg = obtener_color("negro")
            c_plate = c_out = obtener_color("blanco")
            c_bar = obtener_color("saturado")
        elif id_color == 4:
            c_title = c_sub = c_bg = obtener_color("negro")
            c_out = obtener_color("blanco")
            c_plate = obtener_color("saturado")
            c_bar = obtener_color("saturado")
        elif id_color == 5:
            c_title = c_sub = c_bg = obtener_color("blanco")
            c_out = obtener_color("negro")
            c_plate = obtener_color("saturado")
            c_bar = obtener_color("saturado")

        # Generar materiales únicos en Blender y conectarlos al modificador
        set_input_gn(mod, mapa_inputs, "Mat_Title", configurar_material("MatGen_Title", c_title))
        set_input_gn(mod, mapa_inputs, "Mat_SubTitle", configurar_material("MatGen_SubTitle", c_sub))
        set_input_gn(mod, mapa_inputs, "Mat_Char_Plate", configurar_material("MatGen_CharPlate", c_plate))
        set_input_gn(mod, mapa_inputs, "Mat_Background", configurar_material("MatGen_Background", c_bg))
        set_input_gn(mod, mapa_inputs, "Mat_Outlines", configurar_material("MatGen_Outlines", c_out))
        set_input_gn(mod, mapa_inputs, "Mat_Bars", configurar_material("MatGen_Bars", c_bar))

        # --- 6. ROTACIÓN ALEATORIA DEL OBJETO ---
        rot_x = math.radians(ROTACION_BASE[0] + random.uniform(-ROTACION_VAR_X/2, ROTACION_VAR_X/2))
        rot_y = math.radians(ROTACION_BASE[1] + random.uniform(-ROTACION_VAR_Y/2, ROTACION_VAR_Y/2))
        rot_z = math.radians(ROTACION_BASE[2] + random.uniform(-ROTACION_VAR_Z/2, ROTACION_VAR_Z/2))
        obj.rotation_euler = (rot_x, rot_y, rot_z)

        # --- 7. HDRI ALEATORIO ---
        configurar_hdri_random()

        # --- 8. RENDERIZAR ---
        # Evitar sobreescribir si dos placas casualmente generan la misma secuencia
        nombre_archivo = f"{texto_placa}_{i}.png" 
        ruta_final = os.path.join(CARPETA_SALIDA, nombre_archivo)
        
        bpy.context.scene.render.filepath = ruta_final
        print(f"[{i+1}/{CANTIDAD_A_GENERAR}] Renderizando placa: {texto_placa} en Template {id_struct} Color {id_color}")
        
        # Forzar actualización de la escena antes de renderizar
        bpy.context.view_layer.update()
        bpy.ops.render.render(write_still=True)

    print(f"¡Lote completado! {CANTIDAD_A_GENERAR} imágenes generadas en {CARPETA_SALIDA}")

# Iniciar la generación
generar_lote()