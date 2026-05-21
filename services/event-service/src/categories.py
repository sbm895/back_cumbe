from enum import Enum


class CategoriaPadre(str, Enum):
    """Categorías generales (padres) para agrupación y ponderación parcial."""
    MUSICA = "música"
    EVENTO_TRADICIONAL = "evento tradicional"
    ARTES_ESCENICAS = "artes escénicas"
    GASTRONOMIA = "gastronomía"
    DEPORTES_BIENESTAR = "deportes y bienestar"
    ACADEMIA = "academia"
    COMUNIDAD = "comunidad"
    OTROS = "otros"


class CategoriaBQ(str, Enum):
    """Subcategorías culturales específicas de Barranquilla."""

    # --- Música ---
    CHAMPETA = "champeta"
    VALLENATO = "vallenato"
    CUMBIA = "cumbia"
    MAPALE = "mapalé"
    SALSA = "salsa"
    GAITAS = "gaitas"
    PORRO = "porro"
    FANDANGO = "fandango"
    CHANDE = "chandé"
    MERECUMBE = "merecumbé"
    REGGAETON = "reggaeton"
    ELECTRONICA = "electrónica"
    JAZZ = "jazz"
    ROCK = "rock"
    RAP_HIP_HOP = "rap / hip-hop"
    REGGAE = "reggae"
    MUSICA_EN_VIVO = "música en vivo"

    # --- Evento tradicional barranquillero ---
    PICO = "picó"
    VERBENA = "verbena"
    CARNAVAL_BARRIAL = "carnaval barrial"
    FERIA_ARTESANOS = "feria de artesanos"
    FESTIVAL_GASTRONOMICO = "festival gastronómico"
    FIESTA_FIN_ANIO = "fiesta de fin de año"
    NOVENA_NAVIDENA = "novena navideña"
    DESFILE = "desfile"
    REINADO_POPULAR = "reinado popular"

    # --- Artes escénicas y cultura ---
    TEATRO_COMUNITARIO = "teatro comunitario"
    CINECLUB = "cineclub"
    DANZA_FOLKLORICA = "danza folclórica"
    STAND_UP_COMEDY = "stand-up comedy"
    PERFORMANCE = "performance"
    CIRCO = "circo"
    TITERES = "títeres / marionetas"
    POESIA = "poesía / declamación"
    EXPOSICION_ARTE = "exposición de arte"
    GALERIA = "galería"
    GRAFITI = "grafiti / arte urbano"

    # --- Gastronomía y mercados ---
    GASTRONOMIA = "gastronomía"
    MERCADO_CAMPESINO = "mercado campesino"
    FOOD_TRUCK = "food truck"
    CATA = "cata de vinos / cocteles"
    TALLER_COCINA = "taller de cocina"
    FESTIVAL_MARISCOS = "festival de mariscos"

    # --- Deportes y bienestar ---
    DEPORTES = "deportes"
    FUTBOL = "fútbol"
    ATLETISMO = "atletismo"
    CICLISMO = "ciclismo"
    YOGA = "yoga / meditación"
    CROSSFIT = "crossfit"
    ARTES_MARCIALES = "artes marciales"
    NATACION = "natación"
    VOLEIBOL_PLAYA = "voleibol de playa"
    SKATEBOARDING = "skateboarding"

    # --- Academia y desarrollo ---
    ACADEMIA = "academia"
    CONFERENCIA = "conferencia"
    TALLER = "taller / workshop"
    HACKATHON = "hackathon"
    EMPRENDIMIENTO = "emprendimiento"
    FERIA_CIENCIA = "feria de ciencia"
    CHARLA = "charla TED-style"
    NETWORKING = "networking"

    # --- Comunidad y social ---
    VOLUNTARIADO = "voluntariado"
    FERIA_COMUNITARIA = "feria comunitaria"
    MINGA_BARRIAL = "minga barrial"
    EVENTO_INFANTIL = "evento infantil"
    EVENTO_FAMILIAR = "evento familiar"
    MERCADO_PULGAS = "mercado de pulgas"

    # --- Otros ---
    RELIGIOSO = "religioso / espiritual"
    TURISMO_CULTURAL = "turismo cultural"
    FOTOGRAFIA = "fotografía"
    MODA = "moda / pasarela"
    TECNOLOGIA = "tecnología"
    VIDEOJUEGOS = "videojuegos / gaming"


# ---------------------------------------------------------------------------
# Mapeo subcategoría → categoría padre
# Usado por el motor de recomendación para ponderación parcial.
# ---------------------------------------------------------------------------
SUBCATEGORIA_A_PADRE: dict[CategoriaBQ, CategoriaPadre] = {
    # Música
    CategoriaBQ.CHAMPETA:       CategoriaPadre.MUSICA,
    CategoriaBQ.VALLENATO:      CategoriaPadre.MUSICA,
    CategoriaBQ.CUMBIA:         CategoriaPadre.MUSICA,
    CategoriaBQ.MAPALE:         CategoriaPadre.MUSICA,
    CategoriaBQ.SALSA:          CategoriaPadre.MUSICA,
    CategoriaBQ.GAITAS:         CategoriaPadre.MUSICA,
    CategoriaBQ.PORRO:          CategoriaPadre.MUSICA,
    CategoriaBQ.FANDANGO:       CategoriaPadre.MUSICA,
    CategoriaBQ.CHANDE:         CategoriaPadre.MUSICA,
    CategoriaBQ.MERECUMBE:      CategoriaPadre.MUSICA,
    CategoriaBQ.REGGAETON:      CategoriaPadre.MUSICA,
    CategoriaBQ.ELECTRONICA:    CategoriaPadre.MUSICA,
    CategoriaBQ.JAZZ:           CategoriaPadre.MUSICA,
    CategoriaBQ.ROCK:           CategoriaPadre.MUSICA,
    CategoriaBQ.RAP_HIP_HOP:    CategoriaPadre.MUSICA,
    CategoriaBQ.REGGAE:         CategoriaPadre.MUSICA,
    CategoriaBQ.MUSICA_EN_VIVO: CategoriaPadre.MUSICA,

    # Evento tradicional barranquillero
    CategoriaBQ.PICO:                  CategoriaPadre.EVENTO_TRADICIONAL,
    CategoriaBQ.VERBENA:               CategoriaPadre.EVENTO_TRADICIONAL,
    CategoriaBQ.CARNAVAL_BARRIAL:      CategoriaPadre.EVENTO_TRADICIONAL,
    CategoriaBQ.FERIA_ARTESANOS:       CategoriaPadre.EVENTO_TRADICIONAL,
    CategoriaBQ.FESTIVAL_GASTRONOMICO: CategoriaPadre.EVENTO_TRADICIONAL,
    CategoriaBQ.FIESTA_FIN_ANIO:       CategoriaPadre.EVENTO_TRADICIONAL,
    CategoriaBQ.NOVENA_NAVIDENA:       CategoriaPadre.EVENTO_TRADICIONAL,
    CategoriaBQ.DESFILE:               CategoriaPadre.EVENTO_TRADICIONAL,
    CategoriaBQ.REINADO_POPULAR:       CategoriaPadre.EVENTO_TRADICIONAL,

    # Artes escénicas
    CategoriaBQ.TEATRO_COMUNITARIO: CategoriaPadre.ARTES_ESCENICAS,
    CategoriaBQ.CINECLUB:           CategoriaPadre.ARTES_ESCENICAS,
    CategoriaBQ.DANZA_FOLKLORICA:   CategoriaPadre.ARTES_ESCENICAS,
    CategoriaBQ.STAND_UP_COMEDY:    CategoriaPadre.ARTES_ESCENICAS,
    CategoriaBQ.PERFORMANCE:        CategoriaPadre.ARTES_ESCENICAS,
    CategoriaBQ.CIRCO:              CategoriaPadre.ARTES_ESCENICAS,
    CategoriaBQ.TITERES:            CategoriaPadre.ARTES_ESCENICAS,
    CategoriaBQ.POESIA:             CategoriaPadre.ARTES_ESCENICAS,
    CategoriaBQ.EXPOSICION_ARTE:    CategoriaPadre.ARTES_ESCENICAS,
    CategoriaBQ.GALERIA:            CategoriaPadre.ARTES_ESCENICAS,
    CategoriaBQ.GRAFITI:            CategoriaPadre.ARTES_ESCENICAS,

    # Gastronomía
    CategoriaBQ.GASTRONOMIA:      CategoriaPadre.GASTRONOMIA,
    CategoriaBQ.MERCADO_CAMPESINO: CategoriaPadre.GASTRONOMIA,
    CategoriaBQ.FOOD_TRUCK:        CategoriaPadre.GASTRONOMIA,
    CategoriaBQ.CATA:              CategoriaPadre.GASTRONOMIA,
    CategoriaBQ.TALLER_COCINA:     CategoriaPadre.GASTRONOMIA,
    CategoriaBQ.FESTIVAL_MARISCOS: CategoriaPadre.GASTRONOMIA,

    # Deportes y bienestar
    CategoriaBQ.DEPORTES:       CategoriaPadre.DEPORTES_BIENESTAR,
    CategoriaBQ.FUTBOL:         CategoriaPadre.DEPORTES_BIENESTAR,
    CategoriaBQ.ATLETISMO:      CategoriaPadre.DEPORTES_BIENESTAR,
    CategoriaBQ.CICLISMO:       CategoriaPadre.DEPORTES_BIENESTAR,
    CategoriaBQ.YOGA:           CategoriaPadre.DEPORTES_BIENESTAR,
    CategoriaBQ.CROSSFIT:       CategoriaPadre.DEPORTES_BIENESTAR,
    CategoriaBQ.ARTES_MARCIALES: CategoriaPadre.DEPORTES_BIENESTAR,
    CategoriaBQ.NATACION:       CategoriaPadre.DEPORTES_BIENESTAR,
    CategoriaBQ.VOLEIBOL_PLAYA: CategoriaPadre.DEPORTES_BIENESTAR,
    CategoriaBQ.SKATEBOARDING:  CategoriaPadre.DEPORTES_BIENESTAR,

    # Academia
    CategoriaBQ.ACADEMIA:      CategoriaPadre.ACADEMIA,
    CategoriaBQ.CONFERENCIA:   CategoriaPadre.ACADEMIA,
    CategoriaBQ.TALLER:        CategoriaPadre.ACADEMIA,
    CategoriaBQ.HACKATHON:     CategoriaPadre.ACADEMIA,
    CategoriaBQ.EMPRENDIMIENTO: CategoriaPadre.ACADEMIA,
    CategoriaBQ.FERIA_CIENCIA: CategoriaPadre.ACADEMIA,
    CategoriaBQ.CHARLA:        CategoriaPadre.ACADEMIA,
    CategoriaBQ.NETWORKING:    CategoriaPadre.ACADEMIA,

    # Comunidad
    CategoriaBQ.VOLUNTARIADO:     CategoriaPadre.COMUNIDAD,
    CategoriaBQ.FERIA_COMUNITARIA: CategoriaPadre.COMUNIDAD,
    CategoriaBQ.MINGA_BARRIAL:    CategoriaPadre.COMUNIDAD,
    CategoriaBQ.EVENTO_INFANTIL:  CategoriaPadre.COMUNIDAD,
    CategoriaBQ.EVENTO_FAMILIAR:  CategoriaPadre.COMUNIDAD,
    CategoriaBQ.MERCADO_PULGAS:   CategoriaPadre.COMUNIDAD,

    # Otros
    CategoriaBQ.RELIGIOSO:       CategoriaPadre.OTROS,
    CategoriaBQ.TURISMO_CULTURAL: CategoriaPadre.OTROS,
    CategoriaBQ.FOTOGRAFIA:      CategoriaPadre.OTROS,
    CategoriaBQ.MODA:            CategoriaPadre.OTROS,
    CategoriaBQ.TECNOLOGIA:      CategoriaPadre.OTROS,
    CategoriaBQ.VIDEOJUEGOS:     CategoriaPadre.OTROS,
}


# Mapeo inverso: categoría padre → lista de subcategorías
PADRE_A_SUBCATEGORIAS: dict[CategoriaPadre, list[CategoriaBQ]] = {}
for _sub, _padre in SUBCATEGORIA_A_PADRE.items():
    PADRE_A_SUBCATEGORIAS.setdefault(_padre, []).append(_sub)


# Pesos de coincidencia para el motor de recomendación
PESO_EXACTO: float = 1.0    # Misma subcategoría exacta
PESO_PARCIAL: float = 0.4   # Misma categoría padre, distinta subcategoría
