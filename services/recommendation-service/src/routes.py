from fastapi import APIRouter, HTTPException
from collections import defaultdict
from beanie import PydanticObjectId
import httpx
import os

from .models import User, Event
from .categories import (
    CategoriaBQ,
    CategoriaPadre,
    SUBCATEGORIA_A_PADRE,
    PESO_EXACTO,
    PESO_PARCIAL,
)

router = APIRouter()

EVENT_SERVICE_URL = os.getenv("EVENT_SERVICE_URL", "https://back-cumbe-events.achesito.xyz")


async def _popular_events(limit: int = 10):
    """Fetch popular events from event-service endpoint."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{EVENT_SERVICE_URL}/events/popular",
                params={"limit": limit},
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching popular events: {str(e)}")


def _build_category_profile(
    events: list[Event],
) -> tuple[dict[CategoriaBQ, float], dict[CategoriaPadre, float]]:
    """
    Construye dos perfiles a partir del historial de eventos del usuario:

    - sub_counts:    peso acumulado por subcategoría exacta
    - padre_counts:  peso acumulado por categoría padre

    Retorna ambos diccionarios para usar en el scoring ponderado.
    """
    sub_counts: dict[CategoriaBQ, float] = defaultdict(float)
    padre_counts: dict[CategoriaPadre, float] = defaultdict(float)

    for event in events:
        for cat in event.categories:
            try:
                sub = CategoriaBQ(cat)
            except ValueError:
                continue
            sub_counts[sub] += 1.0
            padre = SUBCATEGORIA_A_PADRE.get(sub)
            if padre:
                padre_counts[padre] += 1.0

    return dict(sub_counts), dict(padre_counts)


def _score_event(
    event: Event,
    sub_counts: dict[CategoriaBQ, float],
    padre_counts: dict[CategoriaPadre, float],
) -> float:
    """
    Calcula el score de un evento candidato usando ponderación jerárquica:

      score = Σ (PESO_EXACTO * sub_counts[cat])          ← coincidencia exacta de subcategoría
            + Σ (PESO_PARCIAL * padre_counts[padre(cat)]) ← coincidencia de categoría padre
                                                              (sólo cuando NO hay coincidencia exacta)

    De esta forma un evento de 'champeta' puntúa más alto para un usuario
    que ha asistido a eventos de 'champeta' (exacto) que para uno que sólo
    ha asistido a eventos de 'vallenato' (mismo padre: 'música').
    """
    total = 0.0
    for cat in event.categories:
        try:
            sub = CategoriaBQ(cat)
        except ValueError:
            continue

        exact_score = sub_counts.get(sub, 0.0)
        padre = SUBCATEGORIA_A_PADRE.get(sub)
        padre_score = padre_counts.get(padre, 0.0) if padre else 0.0

        if exact_score > 0:
            # Coincidencia exacta — puntuación completa, no sumamos parcial para evitar doble conteo
            total += PESO_EXACTO * exact_score
        elif padre_score > 0:
            # Sin coincidencia exacta pero mismo grupo padre — puntuación parcial
            total += PESO_PARCIAL * padre_score

    return total


@router.get("/{user_id}")
async def get_recommendations(user_id: str, limit: int = 10):
    """
    Retorna eventos recomendados para el usuario usando scoring jerárquico:
    - Coincidencia exacta de subcategoría: peso 1.0
    - Coincidencia de categoría padre (ej. 'música'): peso 0.4
    - Sin historial → fallback a eventos populares
    """
    user = await User.get(PydanticObjectId(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    seen_ids = set(user.favorites + user.attended_events)

    # Sin historial → cold start: eventos populares
    if not seen_ids:
        return await _popular_events(limit)

    seen_events = await Event.find(
        {"_id": {"$in": [PydanticObjectId(i) for i in seen_ids]}}
    ).to_list()

    sub_counts, padre_counts = _build_category_profile(seen_events)

    # Sin categorías reconocidas en el historial → fallback
    if not sub_counts and not padre_counts:
        return await _popular_events(limit)

    # Buscar candidatos: eventos NO vistos que pertenezcan a alguna categoría padre conocida
    known_subs = list(sub_counts.keys())
    known_padres = list(padre_counts.keys())

    # Todas las subcategorías de los padres conocidos (para ampliar el filtro de MongoDB)
    from .categories import PADRE_A_SUBCATEGORIAS
    related_subs = {
        sub.value
        for padre in known_padres
        for sub in PADRE_A_SUBCATEGORIAS.get(padre, [])
    }
    # También incluir las exactas
    related_subs.update(s.value for s in known_subs)

    candidates = await Event.find({
        "_id": {"$nin": [PydanticObjectId(i) for i in seen_ids]},
        "categories": {"$in": list(related_subs)},
    }).to_list()

    ranked = sorted(candidates, key=lambda e: _score_event(e, sub_counts, padre_counts), reverse=True)
    return ranked[:limit]