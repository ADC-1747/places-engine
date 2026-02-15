import json
import math
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class PlaceNode:
    """Represents a place as a node in the graph"""
    id: str
    name: str
    type: str
    lat: float
    lng: float
    avg_duration_minutes: int
    crowd_level: str
    open_from: str
    open_to: str


@dataclass
class Edge:
    """Represents an edge between two places with distance and travel time"""
    from_node: str
    to_node: str
    distance_km: float
    travel_time_minutes: float


@dataclass
class Graph:
    """Graph representation of places and their connections"""
    nodes: Dict[str, PlaceNode]  # place_id -> PlaceNode
    edges: Dict[str, List[Edge]]  # from_node_id -> [Edge]
    start_node: PlaceNode  # Starting location as a node
    user_data: Dict  # Original user data (preferences, avoid, etc.)


class Preprocessor:
    def __init__(self):
        # Average walking speed in km/h (approximately 5 km/h)
        self.WALKING_SPEED_KMH = 5.0
        # Earth's radius in kilometers
        self.EARTH_RADIUS_KM = 6371.0

    def haversine_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """
        Calculate the great circle distance between two points on Earth
        using the Haversine formula.
        
        Returns distance in kilometers.
        """
        # Convert latitude and longitude from degrees to radians
        lat1_rad = math.radians(lat1)
        lng1_rad = math.radians(lng1)
        lat2_rad = math.radians(lat2)
        lng2_rad = math.radians(lng2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlng = lng2_rad - lng1_rad
        
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        
        distance_km = self.EARTH_RADIUS_KM * c
        return distance_km

    def distance_to_travel_time(self, distance_km: float) -> float:
        """
        Convert distance in kilometers to travel time in minutes
        assuming walking speed.
        """
        time_hours = distance_km / self.WALKING_SPEED_KMH
        time_minutes = time_hours * 60
        return time_minutes

    def create_start_node(self, user_lat: float, user_lng: float) -> PlaceNode:
        """Create a node representing the starting location"""
        return PlaceNode(
            id="start",
            name="Starting Location",
            type="start",
            lat=user_lat,
            lng=user_lng,
            avg_duration_minutes=0,
            crowd_level="none",
            open_from="00:00",
            open_to="23:59"
        )

    def create_place_nodes(self, places: List[Dict]) -> Dict[str, PlaceNode]:
        """Create PlaceNode objects from place data"""
        nodes = {}
        for place in places:
            node = PlaceNode(
                id=place["id"],
                name=place["name"],
                type=place["type"],
                lat=place["lat"],
                lng=place["lng"],
                avg_duration_minutes=place["avg_duration_minutes"],
                crowd_level=place["crowd_level"],
                open_from=place["open_from"],
                open_to=place["open_to"]
            )
            nodes[place["id"]] = node
        return nodes

    def create_edges(self, nodes: Dict[str, PlaceNode], start_node: PlaceNode) -> Dict[str, List[Edge]]:
        """
        Create edges between all nodes (fully connected graph).
        Each edge represents the distance and travel time between two places.
        """
        edges = {}
        all_nodes = {"start": start_node, **nodes}
        
        # Create edges from each node to every other node
        for from_id, from_node in all_nodes.items():
            edges[from_id] = []
            for to_id, to_node in all_nodes.items():
                if from_id != to_id:  # No self-loops
                    distance_km = self.haversine_distance(
                        from_node.lat, from_node.lng,
                        to_node.lat, to_node.lng
                    )
                    travel_time_minutes = self.distance_to_travel_time(distance_km)
                    
                    edge = Edge(
                        from_node=from_id,
                        to_node=to_id,
                        distance_km=distance_km,
                        travel_time_minutes=travel_time_minutes
                    )
                    edges[from_id].append(edge)
        
        return edges

    def preprocess(self, data: Dict) -> Graph:
        """
        Convert JSON input into a graph structure.
        
        Args:
            data: Dictionary containing 'user' and 'places' keys
            
        Returns:
            Graph object with nodes, edges, and user data
        """
        # Extract user data
        user = data["user"]
        places = data["places"]
        
        # Create starting location node
        start_node = self.create_start_node(user["lat"], user["lng"])
        
        # Create place nodes
        nodes = self.create_place_nodes(places)
        
        # Create edges (fully connected graph)
        edges = self.create_edges(nodes, start_node)
        
        # Create and return graph
        graph = Graph(
            nodes=nodes,
            edges=edges,
            start_node=start_node,
            user_data=user
        )
        
        return graph

    def preprocess_from_file(self, filepath: str) -> Graph:
        """Load JSON from file and preprocess into graph"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return self.preprocess(data)