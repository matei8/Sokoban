import math
import random
import numpy as np
from sokoban.map import Map
from sokoban.moves import moves_meaning
from search_methods.solver import Solver
from search_methods.heuristics import target_matching_heuristic

class SimulatedAnnealingSolver(Solver):
    def __init__(self, map: Map) -> None:
        super().__init__(map)
        self.start_temp = 1000.0
        self.end_temp = 0.1
        self.cool_factor = 0.995
        self.max_steps = 100000
        self.restarts = 0
        self.heuristic = target_matching_heuristic

    def solve(self) -> list[int]:
        """
        Simulated Annealing cu restarturi inteligente, perturbări și fallback.
        Returnează lista de mutări ca int-uri.
        """
        overall_best_sequence = []
        last_best_score = float('inf')
        state = self.map.copy()

        while True:
            self.restarts += 1
            temp = self.start_temp
            moves_so_far = []
            state = self.map.copy()

            if math.isinf(last_best_score):
                perturb_moves = 5
            else:
                perturb_moves = min(10, max(3, int(last_best_score)))

            state = self._perturb_initial_state(state, perturb_moves=perturb_moves)

            score = self.heuristic(state)
            best_score_this_run = score
            best_sequence_this_run = []
            steps = 0

            while temp > self.end_temp and steps < self.max_steps:
                if state.is_solved():
                    if self._validate_solution(moves_so_far):
                        print(f"Solution found at restart {self.restarts+1} in {len(moves_so_far)} moves!")
                        return moves_so_far
                    else:
                        print(f"Invalid move sequence at restart {self.restarts+1}, ignoring it...")
                        break

                legal_moves = state.filter_possible_moves()
                if not legal_moves:
                    break

                move = random.choice(legal_moves)
                new_state = state.copy()
                new_state.apply_move(move)
                new_score = self.heuristic(new_state)

                delta = new_score - score
                accept_chance = math.exp(-delta / temp) if delta > 0 else 1.0

                if random.random() < accept_chance:
                    state = new_state
                    score = new_score
                    moves_so_far.append(move)
                    if new_score < best_score_this_run:
                        best_score_this_run = new_score
                        best_sequence_this_run = moves_so_far.copy()

                temp *= self.cool_factor
                steps += 1

            print(f"Restart {self.restarts+1}: best score {best_score_this_run} in {len(best_sequence_this_run)} moves.")
            last_best_score = best_score_this_run

            if not overall_best_sequence or (best_sequence_this_run and len(best_sequence_this_run) < len(overall_best_sequence)):
                if self._validate_solution(best_sequence_this_run):
                    overall_best_sequence = best_sequence_this_run.copy()

            if overall_best_sequence:
                print(f"Best sequence found after {self.restarts} restarts: {len(overall_best_sequence)} moves.")
                return overall_best_sequence

    def _perturb_initial_state(self, state: Map, perturb_moves: int = 5) -> Map:
        """
        Face câteva mutări aleatorii pentru a începe dintr-o stare diferită.
        Numărul de mutări poate varia adaptiv.
        """
        for _ in range(perturb_moves):
            legal_moves = state.filter_possible_moves()
            if not legal_moves:
                break
            move = random.choice(legal_moves)
            state.apply_move(move)
        return state

    def _validate_solution(self, moves: list[int]) -> bool:
        """
        Verifică dacă o secvență de mutări este validă și rezolvă mapa.
        """
        temp_map = self.map.copy()
        try:
            for move in moves:
                temp_map.apply_move(move)
            return temp_map.is_solved()
        except ValueError:
            return False
