from fastapi import APIRouter, HTTPException
from collections import defaultdict
from beanie import PydanticObjectId
import httpx
import os
import math

from .models import User, Event
from .categories import (
    CategoriaBQ,
    CategoriaPadre,
    SUBCATEGORIA_A_PADRE,
    PESO_EXACTO,
    PESO_PARCIAL,
)

router = APIRouter(tags=["Recommendations"])

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

    for event, weight in events:
        for cat in event.categories:
            try:
                sub = CategoriaBQ(cat)
            except ValueError:
                continue
            sub_counts[sub] += weight
            padre = SUBCATEGORIA_A_PADRE.get(sub)
            if padre:
                padre_counts[padre] += weight

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

        n_sub = sub_counts.get(sub, 0.0)
        if n_sub > 0:
            # log scaling: 1 + log(N)
            total += PESO_EXACTO * (1.0 + math.log(n_sub))
            continue

        padre = SUBCATEGORIA_A_PADRE.get(sub)
        n_padre = padre_counts.get(padre, 0.0) if padre else 0.0
        if n_padre > 0:
            total += PESO_PARCIAL * (1.0 + math.log(n_padre)) * 0.4

    return total


# helpers


def _dict_to_vector(d: dict) -> tuple[dict, float]:
    """Helper to compute norm for a dict-based vector."""
    norm = math.sqrt(sum(v * v for v in d.values()))
    return d, norm


def _cosine_similarity(a: dict[CategoriaBQ, float], b: dict[CategoriaBQ, float]) -> float:
    if not a or not b:
        return 0.0
    dot = 0.0
    for k, v in a.items():
        dot += v * b.get(k, 0.0)
    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


@router.get("/{user_id}", response_model=list[Event], summary="Obtiene recomendaciones para un usuario", description="Devuelve una lista ordenada de eventos recomendados para el usuario especificado. El algoritmo combina filtrado por contenido (log-scaling), bono por usuarios seguidos y similitud entre perfiles de usuarios.", responses={404: {"description": "User not found"}, 500: {"description": "Server error"}})
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

    fav_ids = [PydanticObjectId(i) for i in user.favorites]
    att_ids = [PydanticObjectId(i) for i in user.attended_events]

    # Sin historial → cold start: eventos populares
    if not fav_ids and not att_ids:
        return await _popular_events(limit)

    # Fetch events for favorites and attended and assign weights
    events_map: dict[str, Event] = {}
    events_with_weights: list[tuple[Event, float]] = []

    if fav_ids:
        fav_events = await Event.find({"_id": {"$in": fav_ids}}).to_list()
        for e in fav_events:
            events_map[str(e.id)] = e
            events_with_weights.append((e, 2.0))

    if att_ids:
        att_events = await Event.find({"_id": {"$in": att_ids}}).to_list()
        for e in att_events:
            if str(e.id) in events_map:
                # sumar peso si ya estaba en favoritos
                # actualizar tuple in list: simpler to append and let _build aggregate
                events_with_weights.append((e, 1.0))
            else:
                events_map[str(e.id)] = e
                events_with_weights.append((e, 1.0))

    sub_counts, padre_counts = _build_category_profile(events_with_weights)

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

    seen_ids = set([str(x) for x in list(user.favorites + user.attended_events)])

    candidates = await Event.find({
        "_id": {"$nin": [PydanticObjectId(i) for i in seen_ids]},
        "categories": {"$in": list(related_subs)},
    }).to_list()

    # Pre-fetch following users for friends bonus
    following_ids = [PydanticObjectId(i) for i in user.following]
    following_users = []
    if following_ids:
        following_users = await User.find({"_id": {"$in": following_ids}}).to_list()

    # Prepare neighbor users (other users with interactions)
    other_users = await User.find({"$or": [{"favorites": {"$ne": []}}, {"attended_events": {"$ne": []}}]}).to_list()

    # Build profile vector for target user (log-scaled)
    user_vector: dict[CategoriaBQ, float] = {}
    for sub, cnt in sub_counts.items():
        if cnt > 0:
            user_vector[sub] = 1.0 + math.log(cnt)

    # Precompute neighbor profiles (careful: simple implementation)
    neighbor_profiles: list[tuple[str, dict[CategoriaBQ, float], dict]] = []  # (user_id, vector, raw_interactions)
    for other in other_users:
        if str(other.id) == str(user.id):
            continue
        # fetch their events
        other_fav_ids = [PydanticObjectId(i) for i in other.favorites]
        other_att_ids = [PydanticObjectId(i) for i in other.attended_events]
        other_events_with_weights: list[tuple[Event, float]] = []
        if other_fav_ids:
            favs = await Event.find({"_id": {"$in": other_fav_ids}}).to_list()
            for e in favs:
                other_events_with_weights.append((e, 2.0))
        if other_att_ids:
            atts = await Event.find({"_id": {"$in": other_att_ids}}).to_list()
            for e in atts:
                other_events_with_weights.append((e, 1.0))

        o_sub_counts, _ = _build_category_profile(other_events_with_weights)
        # log-scale
        o_vector: dict[CategoriaBQ, float] = {}
        for sub, cnt in o_sub_counts.items():
            if cnt > 0:
                o_vector[sub] = 1.0 + math.log(cnt)

        neighbor_profiles.append((str(other.id), o_vector, {"favorites": set(other.favorites), "attended": set(other.attended_events)}))

    # Score candidates including bonuses
    scored: list[tuple[float, Event]] = []
    for e in candidates:
        content_score = _score_event(e, sub_counts, padre_counts)

        # Friends bonus
        friends_count = 0
        cid = str(e.id)
        for f in following_users:
            if cid in f.favorites or cid in f.attended_events:
                friends_count += 1
        friends_bonus = 2.0 * friends_count

        # Neighbors bonus: top-K neighbors by similarity
        neighbor_bonus = 0.0
        sims = []
        for uid, ovec, interactions in neighbor_profiles:
            sim = _cosine_similarity(user_vector, ovec)
            if sim <= 0:
                continue
            weight = 0.0
            if cid in interactions["favorites"]:
                weight = 2.0
            elif cid in interactions["attended"]:
                weight = 1.0
            if weight > 0:
                sims.append(sim * weight)
        if sims:
            neighbor_bonus = sum(sorted(sims, reverse=True)[:5])

        total = content_score + friends_bonus + neighbor_bonus
        scored.append((total, e))

    ranked = [e for _, e in sorted(scored, key=lambda t: t[0], reverse=True)]
    return ranked[:limit]