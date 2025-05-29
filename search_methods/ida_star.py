from sokoban.map import Map
from sokoban.moves import *
from search_methods.solver import Solver
from typing import List, Union, Tuple
from search_methods.heuristics import ida_star_heuristic, target_matching_heuristic

class IDAStarSolver(Solver):
    def __init__(self, map: Map) -> None:
        super().__init__(map)
        self.explored_states = 0
        self.parent = {}
        self.heuristic = target_matching_heuristic
        
    def solve(self) -> List[int]:
        """
        IDA* implementation:
        1. Start with limit = heuristic(initial_state)
        2. Perform depth-first search with the current limit
        3. If a solution is found, return the path
        4. If no solution is found within the limit, increase the limit and repeat
        """
        initial_state = self.map
        limit = self.heuristic(initial_state)
        
        while limit < 10000:
            self.parent.clear()
            result = self._depth_first(initial_state, 0, limit)
            
            if isinstance(result, list):
                return result
            if result == float('inf'):
                return []
                
            limit = result
            
        return []
        
    def _depth_first(self, state: Map, g: int, limit: int) -> Union[List[int], float]:
        """
        Depth-first search with iterative deepening:
        1. If g + h(state) > limit, return g + h(state)
        2. If the state is a goal, return the path
        3. Otherwise, explore all successors and return the minimum cost
        """
        self.explored_states += 1
         
        f = g + self.heuristic(state)
        if f > limit:
            return f
            
        if state.is_solved():
            return self._reconstruct_path(state)
            
        min_cost = float('inf')
        state_hash = str(state)
        
        for move in state.filter_possible_moves():
            next_state = state.copy()
            next_state.apply_move(move)
            next_hash = str(next_state)
            
            if next_hash in self.parent:
                continue
                
            self.parent[next_hash] = (state_hash, move)
            result = self._depth_first(next_state, g + 1, limit)
            
            if isinstance(result, list):
                return result
            if result < min_cost:
                min_cost = result
                
        return min_cost
        
    def _reconstruct_path(self, state: Map) -> List[int]:
        """Reconstructs the path from the initial state to the given state."""
        path = []
        current_hash = str(state)
        initial_hash = str(self.map)
        
        while current_hash != initial_hash:
            parent_hash, move = self.parent[current_hash]
            path.append(move)
            current_hash = parent_hash
            
        return list(reversed(path))