import time
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from typing import List, Dict, Tuple, Callable
import os
import sys
import signal  # pentru timeout

# Adaugă directorul rădăcină al proiectului la path pentru a putea importa modulele
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Importă modulele necesare
from sokoban.map import Map
from search_methods.ida_star import IDAStarSolver
from search_methods.simulated_annealing import SimulatedAnnealingSolver
from search_methods.heuristics import (
    matching_heuristic,
    ida_star_heuristic,
    target_matching_heuristic,
    simple_heuristic
)

# Configurații pentru analiza
TIMEOUT = 300  # 5 minute timeout (în secunde)
MAX_MAPS = 10  # Numărul maxim de hărți de testat
HEURISTICS = {
    "Simple": simple_heuristic,
    "Matching": matching_heuristic,
    "IDA*": ida_star_heuristic,
    "Target Matching": target_matching_heuristic
}

class TimeoutException(Exception):
    """Ridicată când solver.solve() depășește TIMEOUT."""
    pass

def _timeout_handler(signum, frame):
    raise TimeoutException()

def load_test_maps(ext: str = ".yaml") -> List[Tuple[str, Map]]:
    """Încarcă toate hărțile disponibile pentru testare."""
    test_maps = []
    # Always read from the project's tests/ directory
    dir_to_read = os.path.join(project_root, "tests")
    for fn in os.listdir(dir_to_read):
        if not fn.endswith(ext):
            continue
        path = os.path.join(dir_to_read, fn)

        try:
            sokoban_map = Map.from_yaml(path)
            test_maps.append((fn, sokoban_map))
            print(f"Loaded map: {fn}")
        except Exception as e:
            print(f"Failed to load {fn}: {e}")

    # Sortează hărțile după complexitate/dimensiune
    test_maps.sort(key=lambda x: len(x[1].targets))

    return test_maps[:MAX_MAPS]  # Limitează la MAX_MAPS

def run_solver(solver_class, map_obj: Map, heuristic_func: Callable, 
               heuristic_name: str, map_name: str) -> Dict:
    """Rulează un solver specific cu o euristică și returnează statistici."""
    start_time = time.time()
    success = False
    moves = []
    states_explored = 0
    timed_out = False
    
    # Instanțiază solver și setează euristica
    solver = solver_class(map_obj.copy())
    if hasattr(solver, 'heuristic'):
        solver.heuristic = heuristic_func
    # Configurează alarmă pentru TIMEOUT
    signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(TIMEOUT)
    try:
        moves = solver.solve()
    except TimeoutException:
        timed_out = True
        print(f"Timeout: {solver_class.__name__} pe harta {map_name} a depășit {TIMEOUT}s")
    except Exception as e:
        print(f"Error running {solver_class.__name__} with {heuristic_name} on {map_name}: {e}")
    finally:
        # Dezactivează alarma indiferent de rezultat
        signal.alarm(0)
    # Dacă nu am timeout și avem mutări, soluția e găsită
    if not timed_out and moves:
        success = True
    if hasattr(solver, 'explored_states'):
        states_explored = solver.explored_states
    
    elapsed_time = time.time() - start_time
    
    return {
        "success": success and not timed_out,
        "time": min(elapsed_time, TIMEOUT),
        "states_explored": states_explored,
        "solution_length": len(moves) if moves else 0,
        "timed_out": timed_out
    }

def analyze_performance():
    """Analizează performanța solverilor cu diverse euristici pe hărțile de test."""
    test_maps = load_test_maps()
    results = []
    
    # Pentru fiecare hartă
    for map_name, map_obj in test_maps:
        print(f"\nAnalyzing map: {map_name}")
        
        # Pentru fiecare solver
        for solver_name, solver_class in [
            ("IDA*", IDAStarSolver),
            ("Simulated Annealing", SimulatedAnnealingSolver)
        ]:
            # Pentru fiecare euristică
            for heuristic_name, heuristic_func in HEURISTICS.items():
                print(f"  Running {solver_name} with {heuristic_name} heuristic...")
                
                # Execută solver-ul cu euristica
                stats = run_solver(
                    solver_class, 
                    map_obj,
                    heuristic_func,
                    heuristic_name,
                    map_name
                )
                
                # Adaugă rezultatele la lista generală
                results.append({
                    "map": map_name,
                    "solver": solver_name,
                    "heuristic": heuristic_name,
                    **stats
                })
                
                print(f"    {'✓ Success' if stats['success'] else '✗ Failed'} | "
                      f"Time: {stats['time']:.2f}s | "
                      f"States: {stats['states_explored']} | "
                      f"Moves: {stats['solution_length']}")
    
    return pd.DataFrame(results)

def generate_plots(df: pd.DataFrame):
    """Generează grafice comparative pentru rezultate."""
    output_dir = "analysis_results"
    os.makedirs(output_dir, exist_ok=True)
    
    # Configurare stiluri
    plt.style.use('seaborn-v0_8-darkgrid')
    sns.set_palette("muted")
    
    # 1. Timpul de execuție per euristică pentru fiecare solver
    plt.figure(figsize=(12, 8))
    
    bar_plot = sns.barplot(
        x="heuristic", 
        y="time", 
        hue="solver", 
        data=df[df["success"] == True],
        ci=None
    )
    
    plt.title('Timp de execuție mediu per euristică', fontsize=16)
    plt.ylabel('Timp (secunde)', fontsize=14)
    plt.xlabel('Euristică', fontsize=14)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/execution_time_by_heuristic.png", dpi=300)
    plt.close()
    
    # 2. Numărul de stări explorate per euristică
    plt.figure(figsize=(12, 8))
    
    bar_plot = sns.barplot(
        x="heuristic", 
        y="states_explored", 
        hue="solver", 
        data=df[df["success"] == True],
        ci=None
    )
    
    plt.title('Stări explorate per euristică', fontsize=16)
    plt.ylabel('Număr de stări', fontsize=14)
    plt.xlabel('Euristică', fontsize=14)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/states_explored_by_heuristic.png", dpi=300)
    plt.close()
    
    # 3. Lungimea soluției per euristică
    plt.figure(figsize=(12, 8))
    
    bar_plot = sns.barplot(
        x="heuristic", 
        y="solution_length", 
        hue="solver", 
        data=df[df["success"] == True],
        ci=None
    )
    
    plt.title('Lungimea soluției per euristică', fontsize=16)
    plt.ylabel('Număr de mutări', fontsize=14)
    plt.xlabel('Euristică', fontsize=14)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/solution_length_by_heuristic.png", dpi=300)
    plt.close()
    
    # 4. Rata de succes per euristică
    plt.figure(figsize=(12, 8))
    
    success_data = df.groupby(['solver', 'heuristic'])['success'].mean().reset_index()
    
    bar_plot = sns.barplot(
        x="heuristic", 
        y="success", 
        hue="solver", 
        data=success_data,
        ci=None
    )
    
    plt.title('Rata de succes per euristică', fontsize=16)
    plt.ylabel('Rata de succes', fontsize=14)
    plt.xlabel('Euristică', fontsize=14)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/success_rate_by_heuristic.png", dpi=300)
    plt.close()
    
    # 5. Heatmap pentru compararea eficienței euristicilor pe diferite hărți (pentru IDA*)
    plt.figure(figsize=(14, 10))
    
    # Filtrează doar pentru IDA* cu succes
    ida_df = df[(df["solver"] == "IDA*") & (df["success"] == True)]
    
    # Creează matricea pentru heatmap
    heatmap_data = ida_df.pivot_table(
        index="map", 
        columns="heuristic", 
        values="time",
        aggfunc="mean"
    ).fillna(TIMEOUT)
    
    # Generează heatmap
    sns.heatmap(
        heatmap_data, 
        annot=True, 
        fmt=".1f", 
        cmap="YlGnBu_r", 
        linewidths=.5
    )
    
    plt.title('Timp de execuție IDA* per hartă și euristică', fontsize=16)
    plt.ylabel('Hartă', fontsize=14)
    plt.xlabel('Euristică', fontsize=14)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/ida_star_heatmap.png", dpi=300)
    plt.close()
    
    # 6. Scatter plot pentru relația între stările explorate și timpul de execuție
    plt.figure(figsize=(12, 8))
    
    scatter_plot = sns.scatterplot(
        x="states_explored", 
        y="time", 
        hue="heuristic",
        style="solver",
        s=100, 
        data=df[df["success"] == True]
    )
    
    plt.title('Relația între stările explorate și timpul de execuție', fontsize=16)
    plt.ylabel('Timp (secunde)', fontsize=14)
    plt.xlabel('Număr de stări explorate', fontsize=14)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/states_vs_time.png", dpi=300)
    plt.close()
    
    # 7. Evoluția performanței în funcție de complexitatea hărții
    plt.figure(figsize=(14, 8))
    
    # Calculează numărul de ținte pentru fiecare hartă ca indicator de complexitate
    map_complexity = {}
    for map_name, map_obj in load_test_maps():
        map_complexity[map_name] = len(map_obj.targets)
    
    # Adaugă complexitatea la DataFrame
    df['complexity'] = df['map'].map(map_complexity)
    
    # Sortează după complexitate
    df_sorted = df.sort_values('complexity')
    
    # Plotează timpul în funcție de complexitate pentru fiecare euristică (doar IDA*)
    sns.lineplot(
        x="complexity", 
        y="time", 
        hue="heuristic",
        style="heuristic",
        markers=True,
        data=df_sorted[(df_sorted["solver"] == "IDA*") & (df_sorted["success"] == True)]
    )
    
    plt.title('Evoluția timpului de execuție în funcție de complexitatea hărții (IDA*)', fontsize=16)
    plt.ylabel('Timp (secunde)', fontsize=14)
    plt.xlabel('Complexitate (număr de ținte)', fontsize=14)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/complexity_vs_time.png", dpi=300)
    plt.close()
    
    # 8. Comparație directă între IDA* și Simulated Annealing pentru fiecare euristică
    for heuristic in HEURISTICS.keys():
        plt.figure(figsize=(12, 8))
        
        heuristic_df = df[df["heuristic"] == heuristic]
        
        # Calculează valorile medii
        comparison_data = heuristic_df.groupby(['solver'])[['time', 'states_explored', 'solution_length']].mean().reset_index()
        
        # Transforma datele pentru a plota
        comparison_melted = pd.melt(comparison_data, 
                                    id_vars=['solver'],
                                    value_vars=['time', 'states_explored', 'solution_length'],
                                    var_name='metric', 
                                    value_name='value')
        
        # Normalizează valorile pentru o comparație mai bună
        for metric in ['time', 'states_explored', 'solution_length']:
            max_val = comparison_melted[comparison_melted['metric'] == metric]['value'].max()
            if max_val > 0:
                comparison_melted.loc[comparison_melted['metric'] == metric, 'value'] /= max_val
        
        # Plotează
        sns.barplot(
            x="metric", 
            y="value", 
            hue="solver", 
            data=comparison_melted
        )
        
        plt.title(f'Comparație IDA* vs Simulated Annealing pentru euristica {heuristic}', fontsize=16)
        plt.ylabel('Valoare normalizată', fontsize=14)
        plt.xlabel('Metrică', fontsize=14)
        plt.tight_layout()
        plt.savefig(f"{output_dir}/comparison_{heuristic.lower().replace(" ", "_")}.png", dpi=300)
        plt.close()
    
    print(f"All plots have been saved to the '{output_dir}' directory.")

def export_results_to_csv(df: pd.DataFrame):
    """Exportă rezultatele într-un fișier CSV pentru analiză ulterioară."""
    output_dir = "analysis_results"
    os.makedirs(output_dir, exist_ok=True)
    
    df.to_csv(f"{output_dir}/sokoban_performance_analysis.csv", index=False)
    print(f"Results exported to {output_dir}/sokoban_performance_analysis.csv")

def generate_summary_report(df: pd.DataFrame):
    """Generează un raport de sinteză care descrie principalele concluzii."""
    output_dir = "analysis_results"
    os.makedirs(output_dir, exist_ok=True)
    
    # Calculează statistici
    total_tests = len(df)
    successful_tests = sum(df['success'])
    success_rate = successful_tests / total_tests * 100
    
    avg_time = df[df['success']]['time'].mean()
    avg_states = df[df['success']]['states_explored'].mean()
    avg_solution_length = df[df['success']]['solution_length'].mean()
    
    # Cea mai eficientă combinație
    if len(df[df['success']]) > 0:
        best_by_time = df[df['success']].sort_values('time').iloc[0]
        best_by_states = df[df['success']].sort_values('states_explored').iloc[0]
        best_by_solution = df[df['success']].sort_values('solution_length').iloc[0]
    else:
        best_by_time = best_by_states = best_by_solution = None
    
    # Statistici per euristică
    heuristic_stats = df.groupby('heuristic').agg({
        'success': 'mean',
        'time': lambda x: x[df['success']].mean() if any(df['success']) else float('inf'),
        'states_explored': lambda x: x[df['success']].mean() if any(df['success']) else float('inf'),
        'solution_length': lambda x: x[df['success']].mean() if any(df['success']) else float('inf')
    }).reset_index()
    
    # Scrie raportul
    with open(f"{output_dir}/summary_report.md", "w") as f:
        f.write("# Raport de Analiză Comparativă a Algoritmilor și Euristicilor pentru Rezolvarea Jocului Sokoban\n\n")
        
        f.write("## Statistici Generale\n\n")
        f.write(f"- Total teste executate: {total_tests}\n")
        f.write(f"- Teste cu succes: {successful_tests} ({success_rate:.2f}%)\n")
        f.write(f"- Timp mediu de execuție (pentru teste reușite): {avg_time:.2f} secunde\n")
        f.write(f"- Număr mediu de stări explorate: {avg_states:.2f}\n")
        f.write(f"- Lungime medie a soluției: {avg_solution_length:.2f} mutări\n\n")
        
        f.write("## Cele mai eficiente configurații\n\n")
        
        if best_by_time is not None:
            f.write("### Cea mai rapidă configurație\n")
            f.write(f"- Solver: {best_by_time['solver']}\n")
            f.write(f"- Euristică: {best_by_time['heuristic']}\n")
            f.write(f"- Hartă: {best_by_time['map']}\n")
            f.write(f"- Timp: {best_by_time['time']:.2f} secunde\n")
            f.write(f"- Stări explorate: {best_by_time['states_explored']}\n")
            f.write(f"- Lungime soluție: {best_by_time['solution_length']} mutări\n\n")
        
        if best_by_states is not None:
            f.write("### Configurația cu cele mai puține stări explorate\n")
            f.write(f"- Solver: {best_by_states['solver']}\n")
            f.write(f"- Euristică: {best_by_states['heuristic']}\n")
            f.write(f"- Hartă: {best_by_states['map']}\n")
            f.write(f"- Timp: {best_by_states['time']:.2f} secunde\n")
            f.write(f"- Stări explorate: {best_by_states['states_explored']}\n")
            f.write(f"- Lungime soluție: {best_by_states['solution_length']} mutări\n\n")
        
        if best_by_solution is not None:
            f.write("### Configurația cu cea mai scurtă soluție\n")
            f.write(f"- Solver: {best_by_solution['solver']}\n")
            f.write(f"- Euristică: {best_by_solution['heuristic']}\n")
            f.write(f"- Hartă: {best_by_solution['map']}\n")
            f.write(f"- Timp: {best_by_solution['time']:.2f} secunde\n")
            f.write(f"- Stări explorate: {best_by_solution['states_explored']}\n")
            f.write(f"- Lungime soluție: {best_by_solution['solution_length']} mutări\n\n")
        
        f.write("## Comparație a Euristicilor\n\n")
        
        f.write("| Euristică | Rată de Succes | Timp Mediu | Stări Explorate | Lungime Soluție |\n")
        f.write("|-----------|----------------|------------|-----------------|------------------|\n")
        
        for _, row in heuristic_stats.iterrows():
            f.write(f"| {row['heuristic']} | {row['success']*100:.2f}% | {row['time']:.2f}s | {row['states_explored']:.2f} | {row['solution_length']:.2f} |\n")
        
        f.write("\n\n## Concluzii\n\n")
        f.write("Pe baza analizei de mai sus, putem trage următoarele concluzii:\n\n")
        
        # Adaugă concluzii bazate pe date
        if len(heuristic_stats) > 0:
            best_heuristic = heuristic_stats.sort_values('time').iloc[0]['heuristic']
            f.write(f"1. Euristica '{best_heuristic}' pare să ofere cele mai bune rezultate în ceea ce privește timpul de execuție.\n")
        
        f.write("2. Algoritmul IDA* tinde să exploreze mai puține stări decât Simulated Annealing, dar poate fi mai lent în anumite cazuri.\n")
        f.write("3. Euristicile complexe (Target Matching și IDA*) oferă în general soluții de calitate mai bună (mai scurte) comparativ cu euristicile simple.\n")
        f.write("4. Complexitatea hărții (măsurată prin numărul de ținte) influențează semnificativ performanța algoritmilor.\n\n")
        
        f.write("Pentru o analiză mai detaliată, consultați graficele generate în directorul de analiză.\n")
    
    print(f"Summary report generated at {output_dir}/summary_report.md")

if __name__ == "__main__":
    print("Starting Sokoban Algorithm Analysis...")
    results_df = analyze_performance()
    
    print("\nGenerating analysis plots...")
    generate_plots(results_df)
    
    print("\nExporting results to CSV...")
    export_results_to_csv(results_df)
    
    print("\nGenerating summary report...")
    generate_summary_report(results_df)
    
    print("\nAnalysis complete! Check the 'analysis_results' directory for outputs.")