import sys
import os
from sokoban import (
    Map,
    save_images,
    create_gif
)

from search_methods.ida_star import IDAStarSolver
from search_methods.simulated_annealing import SimulatedAnnealingSolver

def print_usage():
    print("Usage: python main.py <algorithm> <input_file>")
    print("Where:")
    print("  <algorithm> is either 'ida_star' or 'simulated_annealing'")
    print("  <input_file> is the path to a YAML map file")
    sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print_usage()
    
    algorithm = sys.argv[1].lower()
    input_file = sys.argv[2]
    
    if algorithm not in ['ida_star', 'simulated_annealing']:
        print(f"Error: Unknown algorithm '{algorithm}'")
        print_usage()
    
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found")
        sys.exit(1)
    
    try:
        test_map = Map.from_yaml(input_file)
    except Exception as e:
        print(f"Error loading map file: {e}")
        sys.exit(1)
    
    if algorithm == 'ida_star':
        solver = IDAStarSolver(test_map)
    else:
        solver = SimulatedAnnealingSolver(test_map)
    
    print(f"Solving map using {algorithm}...")
    solution = solver.solve()
    
    if solution:
        print(f"Solution found with {len(solution)} moves!")
        
        map_name = os.path.splitext(os.path.basename(input_file))[0]
        output_dir = f"images/{algorithm}_{map_name}"
        gif_name = f"{algorithm}_{map_name}.gif"
        
        current_state = test_map
        states = [current_state.copy()]
        
        for move in solution:
            current_state = current_state.copy()
            current_state.apply_move(move)
            states.append(current_state)
        
        if len(states) > 0:
            save_images(states, output_dir)
            create_gif(output_dir, gif_name, "images")
            print(f"Solution saved as images in '{output_dir}' and as animation in 'images/{gif_name}'")
    else:
        print("No solution found!")
        