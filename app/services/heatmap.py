"""
Heatmap & geospatial analytics for haunted locations.
"""

import math
from typing import List

from app.schemas.schemas import Hotspot


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points in km."""
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def cluster_hotspots(hotspots: List[Hotspot], radius_km: float = 50.0) -> List[dict]:
    """
    Simple greedy clustering: group hotspots within radius_km of each other.
    Returns cluster centroids with aggregated stats.
    """
    visited = set()
    clusters = []

    for i, h in enumerate(hotspots):
        if i in visited:
            continue
        cluster = [h]
        visited.add(i)
        for j, h2 in enumerate(hotspots):
            if j in visited:
                continue
            if haversine_km(h.latitude, h.longitude, h2.latitude, h2.longitude) <= radius_km:
                cluster.append(h2)
                visited.add(j)

        avg_lat = sum(x.latitude for x in cluster) / len(cluster)
        avg_lon = sum(x.longitude for x in cluster) / len(cluster)
        total_events = sum(x.event_count for x in cluster)
        avg_threat = sum(x.avg_threat for x in cluster) / len(cluster)

        clusters.append({
            "centroid_lat": round(avg_lat, 5),
            "centroid_lon": round(avg_lon, 5),
            "location_count": len(cluster),
            "total_events": total_events,
            "avg_threat": round(avg_threat, 2),
            "locations": [x.location_name for x in cluster],
        })

    return sorted(clusters, key=lambda c: c["total_events"], reverse=True)
