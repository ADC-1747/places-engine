from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from itertools import permutations
from preprocessor import Graph, PlaceNode, Edge
import json
import os


@dataclass
class SequenceResult:
    """Represents a sequence of places with total time and explanations"""
    sequence: List[str]  # List of place IDs
    total_time_minutes: float
    explanation: Dict[str, str]  # place_id -> explanation


class Engine:
    def __init__(self, weights: Dict[str, float] = None, weights_file: str = None,
                 mappings_file: str = None, times_file: str = None, sequences_file: str = None):
        """
        Initialize the engine with scoring weights and configuration data.
        
        Args:
            weights: Optional dictionary of scoring weights. If provided, overrides file-based weights.
                     Keys: "preference_match", "distance_penalty", "crowd_penalty", 
                           "time_efficiency", "logical_sequence"
            weights_file: Optional path to weights JSON file. Can be:
                         - Full path to a JSON file
                         - Filename in data/weights/ directory (e.g., "default.json" or "default")
                         - If None, uses "default.json" from data/weights/ directory
            mappings_file: Optional path to preference mappings JSON file. Can be:
                          - Full path to a JSON file
                          - Filename in data/mappings/ directory (e.g., "default.json" or "default")
                          - If None, uses "default.json" from data/mappings/ directory
            times_file: Optional path to preferred times JSON file. Can be:
                       - Full path to a JSON file
                       - Filename in data/times/ directory (e.g., "default.json" or "default")
                       - If None, uses "default.json" from data/times/ directory
            sequences_file: Optional path to logical sequences JSON file. Can be:
                          - Full path to a JSON file
                          - Filename in data/sequences/ directory (e.g., "default.json" or "default")
                          - If None, uses "default.json" from data/sequences/ directory
        """
        # Default scoring weights (fallback if file not found)
        default_weights = {
            "preference_match": 10,
            "distance_penalty": -2,  # per km
            "crowd_penalty": -5,  # if avoiding crowded
            "time_efficiency": 3,  # bonus for fitting well in time window
            "logical_sequence": 5  # bonus for logical ordering
        }
        
        # Load weights from file (default to "default.json" if not specified)
        weights_file_to_load = weights_file if weights_file is not None else "default"
        loaded_weights = self._load_weights_from_file(weights_file_to_load, default_weights)
        
        # Use provided weights dict (overrides file) or loaded weights
        if weights is not None:
            # Merge provided weights with loaded weights (provided weights override)
            self.WEIGHTS = {**loaded_weights, **weights}
        else:
            self.WEIGHTS = loaded_weights
        
        # Load preference mappings from data/mappings/ directory
        mappings_file_to_load = mappings_file if mappings_file is not None else "default"
        self.PREFERENCE_MAPPINGS = self._load_mappings_from_file(mappings_file_to_load, {})
        
        # Load preferred times from data/times/ directory
        times_file_to_load = times_file if times_file is not None else "default"
        preferred_times_raw = self._load_times_from_file(times_file_to_load, {})
        # Convert from JSON format to internal format (list of tuples)
        self.PREFERRED_TIMES = {}
        for place_type, windows in preferred_times_raw.items():
            self.PREFERRED_TIMES[place_type] = [
                (w["start_minutes"], w["end_minutes"], w["name"])
                for w in windows
            ]
        
        # Load logical sequences from data/sequences/ directory
        sequences_file_to_load = sequences_file if sequences_file is not None else "default"
        self.LOGICAL_SEQUENCES = self._load_sequences_from_file(sequences_file_to_load, [])
    
    def _get_data_dir(self) -> str:
        """Get the data directory path"""
        return os.path.join(os.path.dirname(__file__), 'data')
    
    def _load_mappings_from_file(self, mappings_file: str, default: Dict) -> Dict:
        """
        Load preference mappings from a JSON file.
        
        Args:
            mappings_file: Path to mappings file or filename in data/mappings/ directory
            default: Default mappings to use if file not found
            
        Returns:
            Dictionary of preference mappings
        """
        # Determine full path
        if os.path.isabs(mappings_file) or os.path.exists(mappings_file):
            # Full path provided
            file_path = mappings_file
        else:
            # Filename in data/mappings/ directory
            filename = mappings_file if mappings_file.endswith('.json') else f"{mappings_file}.json"
            data_dir = self._get_data_dir()
            mappings_dir = os.path.join(data_dir, 'mappings')
            file_path = os.path.join(mappings_dir, filename)
        
        # Load mappings from file
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    return json.load(f)
            else:
                print(f"Warning: Mappings file not found: {file_path}. Using default.")
                return default
        except json.JSONDecodeError as e:
            print(f"Warning: Invalid JSON in mappings file {file_path}: {e}. Using default.")
            return default
        except Exception as e:
            print(f"Warning: Error loading mappings file {file_path}: {e}. Using default.")
            return default
    
    def _load_times_from_file(self, times_file: str, default: Dict) -> Dict:
        """
        Load preferred times from a JSON file.
        
        Args:
            times_file: Path to times file or filename in data/times/ directory
            default: Default times to use if file not found
            
        Returns:
            Dictionary of preferred times
        """
        # Determine full path
        if os.path.isabs(times_file) or os.path.exists(times_file):
            # Full path provided
            file_path = times_file
        else:
            # Filename in data/times/ directory
            filename = times_file if times_file.endswith('.json') else f"{times_file}.json"
            data_dir = self._get_data_dir()
            times_dir = os.path.join(data_dir, 'times')
            file_path = os.path.join(times_dir, filename)
        
        # Load times from file
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    return json.load(f)
            else:
                print(f"Warning: Times file not found: {file_path}. Using default.")
                return default
        except json.JSONDecodeError as e:
            print(f"Warning: Invalid JSON in times file {file_path}: {e}. Using default.")
            return default
        except Exception as e:
            print(f"Warning: Error loading times file {file_path}: {e}. Using default.")
            return default
    
    def _load_sequences_from_file(self, sequences_file: str, default: List) -> List[Dict]:
        """
        Load logical sequences from a JSON file.
        
        Args:
            sequences_file: Path to sequences file or filename in data/sequences/ directory
            default: Default sequences to use if file not found
            
        Returns:
            List of sequence dictionaries
        """
        # Determine full path
        if os.path.isabs(sequences_file) or os.path.exists(sequences_file):
            # Full path provided
            file_path = sequences_file
        else:
            # Filename in data/sequences/ directory
            filename = sequences_file if sequences_file.endswith('.json') else f"{sequences_file}.json"
            data_dir = self._get_data_dir()
            sequences_dir = os.path.join(data_dir, 'sequences')
            file_path = os.path.join(sequences_dir, filename)
        
        # Load sequences from file
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    return json.load(f)
            else:
                print(f"Warning: Sequences file not found: {file_path}. Using default.")
                return default
        except json.JSONDecodeError as e:
            print(f"Warning: Invalid JSON in sequences file {file_path}: {e}. Using default.")
            return default
        except Exception as e:
            print(f"Warning: Error loading sequences file {file_path}: {e}. Using default.")
            return default
    
    def _load_weights_from_file(self, weights_file: str, default_weights: Dict[str, float]) -> Dict[str, float]:
        """
        Load weights from a JSON file.
        
        Args:
            weights_file: Path to weights file or filename in data/weights/ directory
            default_weights: Default weights to use if file not found
            
        Returns:
            Dictionary of weights
        """
        # Determine full path
        if os.path.isabs(weights_file) or os.path.exists(weights_file):
            # Full path provided
            file_path = weights_file
        else:
            # Filename in data/weights/ directory
            # Remove .json extension if present
            filename = weights_file if weights_file.endswith('.json') else f"{weights_file}.json"
            data_dir = self._get_data_dir()
            weights_dir = os.path.join(data_dir, 'weights')
            file_path = os.path.join(weights_dir, filename)
        
        # Load weights from file
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    loaded = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    return {**default_weights, **loaded}
            else:
                print(f"Warning: Weights file not found: {file_path}. Using default weights.")
                return default_weights
        except json.JSONDecodeError as e:
            print(f"Warning: Invalid JSON in weights file {file_path}: {e}. Using default weights.")
            return default_weights
        except Exception as e:
            print(f"Warning: Error loading weights file {file_path}: {e}. Using default weights.")
            return default_weights

    def time_to_minutes(self, time_str: str) -> int:
        """Convert time string (HH:MM) to minutes since midnight"""
        hours, minutes = map(int, time_str.split(":"))
        return hours * 60 + minutes

    def minutes_to_time(self, minutes: float) -> str:
        """Convert minutes since midnight to time string (HH:MM)"""
        minutes = int(round(minutes))
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"

    def is_open_at_time(self, place: PlaceNode, arrival_time_minutes: int) -> bool:
        """Check if a place is open at the given arrival time"""
        open_from = self.time_to_minutes(place.open_from)
        open_to = self.time_to_minutes(place.open_to)
        
        # Handle places open past midnight (e.g., 22:00 to 04:00)
        if open_to < open_from:
            # Place is open overnight
            return arrival_time_minutes >= open_from or arrival_time_minutes <= open_to
        else:
            return open_from <= arrival_time_minutes <= open_to

    def passes_hard_constraints(self, place: PlaceNode, user_data: Dict, 
                                arrival_time_minutes: int, strict_avoid: bool = True) -> bool:
        """
        Check if a place passes all hard constraints
        
        Args:
            place: Place to check
            user_data: User data with constraints
            arrival_time_minutes: Arrival time in minutes
            strict_avoid: If False, skip avoid list check (fallback mode)
        """
        # Check avoid list (only if strict_avoid is True)
        if strict_avoid and "avoid" in user_data:
            for avoid_term in user_data["avoid"]:
                if avoid_term.lower() == "crowded" and place.crowd_level == "high":
                    return False
        
        # Check opening hours
        if not self.is_open_at_time(place, arrival_time_minutes):
            return False
        
        return True

    def matches_preferences(self, place: PlaceNode, preferences: List[str]) -> float:
        """
        Calculate preference match score for a place.
        All preferences are treated equally - the engine decides the sequence order
        based on all factors (distance, time, logical flow, etc.), not preference order.
        Returns a score between 0 and 1 (1 = perfect match, 0 = no match)
        """
        if not preferences:
            return 0.5  # Neutral score if no preferences
        
        place_type_lower = place.type.lower()
        match_count = 0
        
        for preference in preferences:
            preference_lower = preference.lower()
            
            # Direct type match
            if preference_lower == place_type_lower:
                match_count += 1
                continue
            
            # Check preference mappings
            if preference_lower in self.PREFERENCE_MAPPINGS:
                mapped_types = self.PREFERENCE_MAPPINGS[preference_lower]
                if any(mapped_type in place_type_lower for mapped_type in mapped_types):
                    match_count += 1
        
        # Return simple ratio: matches / total preferences
        return match_count / len(preferences)

    def score_place(self, place: PlaceNode, user_data: Dict, 
                   distance_from_start_km: float, current_time_minutes: int) -> float:
        """
        Score a place based on preferences, distance, and other factors.
        Higher score = better place.
        """
        score = 0.0
        
        # Preference matching
        if "preferences" in user_data:
            preference_score = self.matches_preferences(place, user_data["preferences"])
            score += preference_score * self.WEIGHTS["preference_match"]
        
        # Distance penalty (closer is better)
        score += distance_from_start_km * self.WEIGHTS["distance_penalty"]
        
        # Crowd penalty (if avoiding crowded)
        if "avoid" in user_data and "crowded" in user_data["avoid"]:
            if place.crowd_level == "high":
                score += self.WEIGHTS["crowd_penalty"]
            elif place.crowd_level == "low":
                score += abs(self.WEIGHTS["crowd_penalty"]) * 0.5  # Bonus for low crowd
        
        # Time efficiency (bonus if place fits well in remaining time)
        time_available = user_data.get("time_available_minutes", 0)
        time_used = current_time_minutes - self.time_to_minutes(user_data.get("start_time", "00:00"))
        time_remaining = time_available - time_used
        
        if place.avg_duration_minutes <= time_remaining:
            efficiency = place.avg_duration_minutes / max(time_remaining, 1)
            score += (1 - efficiency) * self.WEIGHTS["time_efficiency"]  # Better if uses time well
        
        return score

    def calculate_sequence_time(self, sequence: List[str], graph: Graph, 
                               start_time_minutes: int) -> Tuple[float, List[int]]:
        """
        Calculate total time for a sequence including travel and visit times.
        Returns (total_time, arrival_times)
        """
        current_time = start_time_minutes
        arrival_times = [current_time]  # Start time
        
        for i, place_id in enumerate(sequence):
            place = graph.nodes[place_id]
            
            # Add travel time (from previous location)
            if i == 0:
                # Travel from start
                edge = next(e for e in graph.edges["start"] if e.to_node == place_id)
            else:
                # Travel from previous place
                prev_place_id = sequence[i - 1]
                edge = next(e for e in graph.edges[prev_place_id] if e.to_node == place_id)
            
            current_time += edge.travel_time_minutes
            arrival_times.append(int(current_time))
            
            # Add visit duration
            current_time += place.avg_duration_minutes
        
        total_time = current_time - start_time_minutes
        return total_time, arrival_times

    def is_sequence_valid(self, sequence: List[str], graph: Graph, 
                         user_data: Dict, is_fallback: bool = False) -> Tuple[bool, Optional[str]]:
        """
        Check if a sequence is valid (all constraints satisfied).
        Returns (is_valid, error_message)
        
        Args:
            sequence: List of place IDs
            graph: Graph object
            user_data: User data with constraints
            is_fallback: If True, allow slight time budget overage (5% tolerance)
        """
        start_time_minutes = self.time_to_minutes(user_data.get("start_time", "00:00"))
        time_available = user_data.get("time_available_minutes", 0)
        
        # Calculate total time
        total_time, arrival_times = self.calculate_sequence_time(sequence, graph, start_time_minutes)
        
        # Check time budget (with tolerance in fallback mode)
        time_tolerance = time_available * 0.05 if is_fallback else 0  # 5% tolerance in fallback
        if total_time > time_available + time_tolerance:
            return False, f"Sequence exceeds time budget ({total_time:.1f} > {time_available} minutes)"
        
        # Check each place's constraints
        for i, place_id in enumerate(sequence):
            place = graph.nodes[place_id]
            arrival_time = int(arrival_times[i + 1])  # +1 because first is start time
            
            # Check opening hours
            if not self.is_open_at_time(place, arrival_time):
                return False, f"{place.name} is not open at arrival time {self.minutes_to_time(arrival_time)}"
            
            # Check hard constraints (skip avoid list check in fallback mode)
            if not self.passes_hard_constraints(place, user_data, arrival_time, strict_avoid=not is_fallback):
                return False, f"{place.name} violates hard constraints"
        
        return True, None

    def score_sequence(self, sequence: List[str], graph: Graph, 
                      user_data: Dict) -> float:
        """
        Score a sequence based on time-of-day appropriateness, distance, and logical flow.
        Higher score = better sequence.
        
        Considers:
        - Time-of-day appropriateness (preferred time windows)
        - Distance efficiency (minimize travel)
        - Logical flow (e.g., park before cafe)
        """
        score = 0.0
        start_time_minutes = self.time_to_minutes(user_data.get("start_time", "00:00"))
        
        # Score each place in the sequence
        current_time = start_time_minutes
        total_distance = 0
        
        for i, place_id in enumerate(sequence):
            place = graph.nodes[place_id]
            
            # Calculate distance from previous location
            if i == 0:
                edge = next(e for e in graph.edges["start"] if e.to_node == place_id)
                distance_km = edge.distance_km
            else:
                prev_place_id = sequence[i - 1]
                edge = next(e for e in graph.edges[prev_place_id] if e.to_node == place_id)
                distance_km = edge.distance_km
            
            total_distance += distance_km
            
            # Calculate arrival time at this place
            arrival_time = current_time + edge.travel_time_minutes
            
            # Time-of-day appropriateness bonus
            is_preferred, window_name = self.is_time_in_preferred_window(place.type, arrival_time)
            if is_preferred and window_name:
                # Bonus for visiting at preferred time (e.g., cafe during breakfast)
                score += self.WEIGHTS.get("time_efficiency", 3) * 1.5  # Extra bonus for preferred time
            
            # Score this place (includes preference, distance, etc.)
            place_score = self.score_place(place, user_data, distance_km, current_time)
            score += place_score
            
            # Update current time
            current_time += edge.travel_time_minutes + place.avg_duration_minutes
            
            # Logical sequence bonus (check all configured sequences)
            if i > 0:
                prev_place = graph.nodes[sequence[i - 1]]
                prev_type = prev_place.type.lower()
                curr_type = place.type.lower()
                
                # Check if this sequence matches any configured logical sequence
                for seq_rule in self.LOGICAL_SEQUENCES:
                    if (seq_rule.get("from_type", "").lower() == prev_type and 
                        seq_rule.get("to_type", "").lower() == curr_type):
                        score += self.WEIGHTS["logical_sequence"]
                        break  # Only apply bonus once per sequence
        
        # Distance efficiency penalty (shorter total distance is better)
        score -= total_distance * abs(self.WEIGHTS.get("distance_penalty", -2))  # Penalty for total distance
        
        return score

    def generate_explanations(self, sequence: List[str], graph: Graph, 
                             user_data: Dict, is_fallback: bool = False) -> Dict[str, str]:
        """
        Generate explanations for why each place was chosen in this order
        
        Args:
            sequence: List of place IDs in order
            graph: Graph object
            user_data: User preferences and constraints
            is_fallback: If True, indicates avoid list was relaxed
        """
        explanations = {}
        start_time_minutes = self.time_to_minutes(user_data.get("start_time", "00:00"))
        preferences = user_data.get("preferences", [])
        avoid = user_data.get("avoid", [])
        
        # Add fallback note if applicable
        if is_fallback:
            explanations["_fallback"] = "No places matching all constraints found; showing best available options"
        
        current_time = start_time_minutes
        
        for i, place_id in enumerate(sequence):
            place = graph.nodes[place_id]
            reasons = []
            
            # Preference match
            if preferences:
                pref_match = self.matches_preferences(place, preferences)
                if pref_match > 0.5:
                    # Find all matching preferences
                    matching_prefs = []
                    for p in preferences:
                        preference_lower = p.lower()
                        place_type_lower = place.type.lower()
                        
                        # Direct type match
                        if preference_lower == place_type_lower:
                            matching_prefs.append(p)
                        # Check preference mappings
                        elif preference_lower in self.PREFERENCE_MAPPINGS:
                            mapped_types = self.PREFERENCE_MAPPINGS[preference_lower]
                            if any(mapped_type in place_type_lower for mapped_type in mapped_types):
                                matching_prefs.append(p)
                    
                    if matching_prefs:
                        if len(matching_prefs) == 1:
                            reasons.append(f"matches preference for '{matching_prefs[0]}'")
                        else:
                            reasons.append(f"matches preferences: '{', '.join(matching_prefs)}'")
            
            # Crowd level
            if avoid and "crowded" in avoid:
                if place.crowd_level == "low":
                    reasons.append("low crowd level")
                elif place.crowd_level == "high" and is_fallback:
                    reasons.append("note: crowded (best available option)")
            elif place.crowd_level == "low":
                reasons.append("quiet atmosphere")
            
            # Distance
            if i == 0:
                edge = next(e for e in graph.edges["start"] if e.to_node == place_id)
            else:
                prev_place_id = sequence[i - 1]
                edge = next(e for e in graph.edges[prev_place_id] if e.to_node == place_id)
            
            if edge.distance_km < 0.2:
                reasons.append("nearby")
            
            # Time of day and preferred time window
            arrival_time = current_time + edge.travel_time_minutes
            arrival_str = self.minutes_to_time(arrival_time)
            is_preferred, window_name = self.is_time_in_preferred_window(place.type, arrival_time)
            if is_preferred and window_name:
                reasons.append(f"ideal time ({window_name}) at {arrival_str}")
            elif i == 0:
                reasons.append(f"accessible at {arrival_str}")
            
            # Logical sequence (check all configured sequences)
            if i > 0:
                prev_place = graph.nodes[sequence[i - 1]]
                prev_type = prev_place.type.lower()
                curr_type = place.type.lower()
                
                # Check if this sequence matches any configured logical sequence
                for seq_rule in self.LOGICAL_SEQUENCES:
                    if (seq_rule.get("from_type", "").lower() == prev_type and 
                        seq_rule.get("to_type", "").lower() == curr_type):
                        reason = seq_rule.get("reason", "logical sequence")
                        reasons.append(reason)
                        break  # Only add one reason per sequence
            
            # Duration fit
            time_available = user_data.get("time_available_minutes", 0)
            time_used = current_time - start_time_minutes
            time_remaining = time_available - time_used
            if place.avg_duration_minutes <= time_remaining:
                reasons.append(f"fits remaining time ({time_remaining:.0f} min)")
            
            explanation = ", ".join(reasons) if reasons else "selected based on constraints"
            explanations[place_id] = explanation.capitalize()
            
            current_time += edge.travel_time_minutes + place.avg_duration_minutes
        
        return explanations

    def is_time_in_preferred_window(self, place_type: str, time_minutes: int) -> Tuple[bool, Optional[str]]:
        """
        Check if a time falls within preferred time windows for a place type.
        
        Args:
            place_type: Type of place (e.g., "cafe", "restaurant")
            time_minutes: Time in minutes since midnight
            
        Returns:
            (is_preferred, window_name) - True if time is in preferred window, and the window name
        """
        place_type_lower = place_type.lower()
        
        if place_type_lower not in self.PREFERRED_TIMES:
            return True, None  # No preferred times defined, consider it always suitable
        
        for start_min, end_min, window_name in self.PREFERRED_TIMES[place_type_lower]:
            # Handle overnight windows (e.g., 20:00 to 02:00)
            if end_min < start_min:
                # Overnight window
                if time_minutes >= start_min or time_minutes <= end_min:
                    return True, window_name
            else:
                # Normal window
                if start_min <= time_minutes <= end_min:
                    return True, window_name
        
        return False, None
    
    def filter_candidates(self, graph: Graph, strict_avoid: bool = True) -> Tuple[List[str], bool]:
        """
        Step 1: Filter candidates based on preferences and avoid list.
        
        Filters places by:
        - Preferences: Must match at least one user preference
        - Avoid list: Must not violate any avoid constraints (e.g., crowded) [if strict_avoid=True]
        - Opening hours: Must be open during visit window
        - Time budget: Must fit in available time
        - Deduplication: Only one place per type (avoids multiple cafes, parks, etc.)
        
        Args:
            graph: Graph object with places and user data
            strict_avoid: If True, enforce avoid list. If False, ignore avoid list (fallback mode)
        
        Returns:
            Tuple of (candidate place IDs, is_fallback) where is_fallback indicates if avoid list was relaxed
        """
        user_data = graph.user_data
        start_time_minutes = self.time_to_minutes(user_data.get("start_time", "00:00"))
        time_available = user_data.get("time_available_minutes", 0)
        preferences = user_data.get("preferences", [])
        avoid = user_data.get("avoid", [])
        
        # First pass: collect all valid places with their scores
        valid_places = []  # List of (place_id, place, score, distance)
        
        for place_id, place in graph.nodes.items():
            # Get distance from start
            edge = next(e for e in graph.edges["start"] if e.to_node == place_id)
            estimated_arrival = start_time_minutes + edge.travel_time_minutes
            distance_km = edge.distance_km
            
            # Check avoid list (only if strict_avoid is True)
            if strict_avoid:
                skip_place = False
                if avoid:
                    for avoid_term in avoid:
                        if avoid_term.lower() == "crowded" and place.crowd_level == "high":
                            skip_place = True
                            break
                if skip_place:
                    continue
            
            # Check opening hours (hard constraint)
            if not self.is_open_at_time(place, estimated_arrival):
                continue
            
            # Check time budget (hard constraint)
            if place.avg_duration_minutes + edge.travel_time_minutes > time_available:
                continue
            
            # Check preferences (must match at least one preference)
            if preferences:
                pref_match = self.matches_preferences(place, preferences)
                if pref_match == 0:
                    continue  # Doesn't match any preference, skip
            
            # Score this place for ranking (prefer closer, better matches, lower crowd)
            score = 0.0
            if preferences:
                score += pref_match * 10  # Preference match bonus
            score -= distance_km * 2  # Distance penalty (closer is better)
            if avoid and "crowded" in avoid:
                if place.crowd_level == "low":
                    score += 5  # Bonus for low crowd
                elif place.crowd_level == "high" and not strict_avoid:
                    score -= 5  # Penalty for high crowd in fallback mode
            
            # Place passes all filters - add to valid places
            valid_places.append((place_id, place, score, distance_km))
        
        # Second pass: deduplicate by place type - keep only the best one of each type
        # Group by place type
        places_by_type = {}  # {place_type: [(place_id, place, score, distance), ...]}
        
        for place_id, place, score, distance in valid_places:
            place_type = place.type.lower()
            if place_type not in places_by_type:
                places_by_type[place_type] = []
            places_by_type[place_type].append((place_id, place, score, distance))
        
        # For each type, keep only the best one (highest score, or if tie, closest)
        candidates = []
        for place_type, places_list in places_by_type.items():
            # Sort by score (descending), then by distance (ascending) as tiebreaker
            places_list.sort(key=lambda x: (-x[2], x[3]))
            # Keep only the best one
            best_place_id = places_list[0][0]
            candidates.append(best_place_id)
        
        return candidates, not strict_avoid
    
    def find_best_sequence(self, candidates: List[str], graph: Graph, is_fallback: bool = False) -> SequenceResult:
        """
        Step 2: From candidate places, decide sequence based on current time and distance.
        
        Considers:
        - Time-of-day appropriateness (preferred time windows for each place type)
        - Distance efficiency (minimize total travel distance)
        - Logical flow (e.g., park before cafe)
        
        Algorithm:
        1. Generate all valid sequences of 2-3 places from candidates
        2. Score ALL sequences considering time appropriateness and distance
        3. Return the sequence with the highest score
        
        Args:
            candidates: List of candidate place IDs from Step 1
            graph: Graph object with all place data
            
        Returns:
            SequenceResult with best sequence
        """
        user_data = graph.user_data
        start_time_minutes = self.time_to_minutes(user_data.get("start_time", "00:00"))
        
        if len(candidates) < 2:
            # Not enough candidates
            if len(candidates) == 1:
                sequence = candidates
            else:
                sequence = []
                return SequenceResult(
                    sequence=sequence,
                    total_time_minutes=0,
                    explanation={"error": "No valid places found matching constraints"}
                )
        
        # Generate ALL valid sequences and score them with weights
        scored_sequences = []  # List of (sequence, score) tuples
        
        # Generate sequences of length 2
        for seq in permutations(candidates, min(2, len(candidates))):
            seq_list = list(seq)
            is_valid, error = self.is_sequence_valid(seq_list, graph, user_data, is_fallback=is_fallback)
            if is_valid:
                # Score this sequence using our weights
                score = self.score_sequence(seq_list, graph, user_data)
                scored_sequences.append((seq_list, score))
        
        # Generate sequences of length 3
        if len(candidates) >= 3:
            for seq in permutations(candidates, 3):
                seq_list = list(seq)
                is_valid, error = self.is_sequence_valid(seq_list, graph, user_data, is_fallback=is_fallback)
                if is_valid:
                    # Score this sequence using our weights
                    score = self.score_sequence(seq_list, graph, user_data)
                    scored_sequences.append((seq_list, score))
        
        # If no valid sequences found, try shorter sequences as fallback
        if not scored_sequences:
            for seq_len in [2, 1]:
                if len(candidates) >= seq_len:
                    for seq in permutations(candidates, seq_len):
                        seq_list = list(seq)
                        is_valid, error = self.is_sequence_valid(seq_list, graph, user_data, is_fallback=is_fallback)
                        if is_valid:
                            score = self.score_sequence(seq_list, graph, user_data)
                            scored_sequences.append((seq_list, score))
                    if scored_sequences:
                        break
        
        # If still no valid sequences, return error
        if not scored_sequences:
            return SequenceResult(
                sequence=[],
                total_time_minutes=0,
                explanation={"error": "No valid sequence found"}
            )
        
        # Sort all scored sequences by score (highest first)
        scored_sequences.sort(key=lambda x: x[1], reverse=True)
        
        # Get the best sequence (highest score)
        best_sequence, best_score = scored_sequences[0]
        
        # Calculate total time for the best sequence
        total_time, _ = self.calculate_sequence_time(best_sequence, graph, start_time_minutes)
        
        # Generate explanations
        explanations = self.generate_explanations(best_sequence, graph, user_data, is_fallback=is_fallback)
        
        # Add score to explanation for debugging/transparency
        explanations["_score"] = f"{best_score:.2f}"
        
        return SequenceResult(
            sequence=best_sequence,
            total_time_minutes=round(total_time, 1),
            explanation=explanations
        )
    
    def process(self, graph: Graph) -> SequenceResult:
        """
        Main processing function: selects 2-3 places and determines optimal sequence.
        
        Two-phase approach:
        Phase 1: Filter and curate all valid candidate places
        Phase 2: From candidates, find best 2-3 places with optimal sequence
        
        Fallback: If no candidates found with strict constraints, relax avoid list
        """
        # Phase 1: Filter candidates (try strict first)
        candidates, is_fallback = self.filter_candidates(graph, strict_avoid=True)
        
        # If no candidates found, try again without avoid list constraint (fallback)
        if not candidates:
            candidates, is_fallback = self.filter_candidates(graph, strict_avoid=False)
        
        # Phase 2: Find best sequence from candidates
        result = self.find_best_sequence(candidates, graph, is_fallback=is_fallback)
        return result
    
    def process_with_all_scores(self, graph: Graph) -> Tuple[SequenceResult, List[Tuple[List[str], float]]]:
        """
        Process graph and return best sequence along with all scored sequences.
        Useful for debugging and understanding the scoring.
        
        Returns:
            (best_result, all_scored_sequences)
        """
        # Phase 1: Filter candidates (try strict first)
        candidates, is_fallback = self.filter_candidates(graph, strict_avoid=True)
        
        # If no candidates found, try again without avoid list constraint (fallback)
        if not candidates:
            candidates, is_fallback = self.filter_candidates(graph, strict_avoid=False)
        
        if len(candidates) < 2:
            if len(candidates) == 1:
                sequence = candidates
            else:
                sequence = []
                return (
                    SequenceResult(
                        sequence=sequence,
                        total_time_minutes=0,
                        explanation={"error": "No valid places found matching constraints"}
                    ),
                    []
                )
        
        # Phase 2: Generate and score all sequences
        user_data = graph.user_data
        scored_sequences = []
        
        # Sequences of length 2
        for seq in permutations(candidates, min(2, len(candidates))):
            seq_list = list(seq)
            is_valid, error = self.is_sequence_valid(seq_list, graph, user_data, is_fallback=is_fallback)
            if is_valid:
                score = self.score_sequence(seq_list, graph, user_data)
                scored_sequences.append((seq_list, score))
        
        # Sequences of length 3
        if len(candidates) >= 3:
            for seq in permutations(candidates, 3):
                seq_list = list(seq)
                is_valid, error = self.is_sequence_valid(seq_list, graph, user_data, is_fallback=is_fallback)
                if is_valid:
                    score = self.score_sequence(seq_list, graph, user_data)
                    scored_sequences.append((seq_list, score))
        
        # Fallback for shorter sequences
        if not scored_sequences:
            for seq_len in [2, 1]:
                if len(candidates) >= seq_len:
                    for seq in permutations(candidates, seq_len):
                        seq_list = list(seq)
                        is_valid, error = self.is_sequence_valid(seq_list, graph, user_data, is_fallback=is_fallback)
                        if is_valid:
                            score = self.score_sequence(seq_list, graph, user_data)
                            scored_sequences.append((seq_list, score))
                    if scored_sequences:
                        break
        
        if not scored_sequences:
            return (
                SequenceResult(
                    sequence=[],
                    total_time_minutes=0,
                    explanation={"error": "No valid sequence found"}
                ),
                []
            )
        
        # Sort by score (highest first)
        scored_sequences.sort(key=lambda x: x[1], reverse=True)
        
        # Get best sequence
        best_sequence, best_score = scored_sequences[0]
        start_time_minutes = self.time_to_minutes(graph.user_data.get("start_time", "00:00"))
        total_time, _ = self.calculate_sequence_time(best_sequence, graph, start_time_minutes)
        explanations = self.generate_explanations(best_sequence, graph, graph.user_data, is_fallback=is_fallback)
        explanations["_score"] = f"{best_score:.2f}"
        
        best_result = SequenceResult(
            sequence=best_sequence,
            total_time_minutes=round(total_time, 1),
            explanation=explanations
        )
        
        return best_result, scored_sequences

