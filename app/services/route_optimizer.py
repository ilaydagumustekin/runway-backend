"""
Çevresel skorlara dayalı A* tabanlı rota optimizasyon motoru.
"""
import math
import heapq
import logging
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.neighborhood import Neighborhood
from app.services.myki_service import calculate_myki_from_environmental_data

logger = logging.getLogger(__name__)

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """İki koordinat arası kuş uçuşu mesafeyi km cinsinden hesaplar."""
    R = 6371.0 # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

from app.models.environmental_data import EnvironmentalData

def get_environmental_cost(db: Session, neighborhood: Neighborhood) -> float:
    """
    Mahallenin çevresel maliyetini hesaplar.
    Düşük MYKI skoru yüksek maliyet demektir.
    """
    stmt = select(EnvironmentalData).where(
        EnvironmentalData.neighborhood_id == neighborhood.id
    ).order_by(EnvironmentalData.created_at.desc()).limit(1)
    
    env_data = db.scalars(stmt).first()
    
    if not env_data:
        return 50.0 # Default/Neutral cost
        
    score, _ = calculate_myki_from_environmental_data(env_data)
    # Skor 0-100 arasi, maliyet ise ters orantili: 100 - skor. 
    # Yüksek skor -> düşük maliyet.
    return 100.0 - score

def find_best_route(db: Session, start_lat: float, start_lon: float, end_lat: float, end_lon: float, optimize_for: str = "environment"):
    """
    Basit graf yaklasimiyla, baslangic ve bitise en yakin mahalleler uzerinden
    çevresel olarak en iyi (veya en kısa) rotayi dondurur.
    
    Bu, gercek bir yol agi (OSRM/Google Maps) entegrasyonu degildir,
    mahalle merkezleri arasinda A* rotasi cizer.
    """
    # Tum mahalleleri alalim (kucuk sehirler/demolar icin uygun, gercekten R-Tree lazim)
    neighborhoods = db.scalars(select(Neighborhood)).all()
    if not neighborhoods:
        return None
        
    # Başlangıç ve bitiş mahallelerini bul
    start_n = min(neighborhoods, key=lambda n: haversine_distance(start_lat, start_lon, n.latitude, n.longitude))
    end_n = min(neighborhoods, key=lambda n: haversine_distance(end_lat, end_lon, n.latitude, n.longitude))
    
    # Eger ayni mahalleyse
    if start_n.id == end_n.id:
        return [start_n]
        
    # A* Algoritmasi icin graf tanimi: Her mahalle en yakin 15 mahalleye bagli
    edges = {}
    for n in neighborhoods:
        dists = [(haversine_distance(n.latitude, n.longitude, other.latitude, other.longitude), other) 
                 for other in neighborhoods if other.id != n.id]
        dists.sort(key=lambda x: x[0])
        # Daha fazla komşu ile grafın kopuk olmasını engelliyoruz
        edges[n.id] = [(d, o) for d, o in dists[:15]]
        
    # A* arama
    def heuristic(n: Neighborhood) -> float:
        return haversine_distance(n.latitude, n.longitude, end_n.latitude, end_n.longitude)
        
    open_set = [(0, start_n.id)]
    came_from = {}
    
    # g_score: start -> node gercek maliyeti
    g_score = {n.id: float('inf') for n in neighborhoods}
    g_score[start_n.id] = 0
    
    # f_score: g_score + heuristic
    f_score = {n.id: float('inf') for n in neighborhoods}
    f_score[start_n.id] = heuristic(start_n)
    
    n_dict = {n.id: n for n in neighborhoods}
    
    while open_set:
        _, current_id = heapq.heappop(open_set)
        
        if current_id == end_n.id:
            # Reconstruct path
            path = [n_dict[current_id]]
            while current_id in came_from:
                current_id = came_from[current_id]
                path.append(n_dict[current_id])
            return path[::-1]
            
        current_node = n_dict[current_id]
        
        for dist, neighbor in edges[current_id]:
            # Maliyet hesaplama
            if optimize_for == "environment":
                env_cost = get_environmental_cost(db, neighbor)
                # Mesafe * Cevresel Maliyet Carpani
                tentative_g_score = g_score[current_id] + dist * (1.0 + (env_cost / 50.0)) 
            else:
                # Sadece kisa mesafe
                tentative_g_score = g_score[current_id] + dist
                
            if tentative_g_score < g_score[neighbor.id]:
                came_from[neighbor.id] = current_id
                g_score[neighbor.id] = tentative_g_score
                f_score[neighbor.id] = tentative_g_score + heuristic(neighbor)
                heapq.heappush(open_set, (f_score[neighbor.id], neighbor.id))
                
    return None # Path not found
