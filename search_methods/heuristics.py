from sokoban.map import Map

def blocks_other_boxes(state: Map, box) -> bool:
    """Verifică dacă o cutie blochează accesul la alte cutii"""
    for other_box in state.boxes.values():
        if other_box.name != box.name:
            if (abs(box.x - other_box.x) == 1 and box.y == other_box.y) or \
               (abs(box.y - other_box.y) == 1 and box.x == other_box.x):
                return True
    return False

def is_side_blocked(state: Map, box) -> bool:
    """Verifică dacă o cutie este blocată lateral"""
    horizontal_blocked = ((box.x-1, box.y) in state.obstacles or 
                        (box.x+1, box.y) in state.obstacles)
    vertical_blocked = ((box.x, box.y-1) in state.obstacles or 
                      (box.x, box.y+1) in state.obstacles)
    return horizontal_blocked or vertical_blocked

def manhattan_distance(x1: int, y1: int, x2: int, y2: int) -> int:
    """Calculează distanța Manhattan între două puncte"""
    return abs(x1 - x2) + abs(y1 - y2)

def is_tunnel(state: Map, x: int, y: int) -> bool:
    """Verifică dacă o poziție este într-un tunel (coridor îngust)"""
    horizontal_walls = ((x, y-1) in state.obstacles and (x, y+1) in state.obstacles)
    vertical_walls = ((x-1, y) in state.obstacles and (x+1, y) in state.obstacles)
    return horizontal_walls and vertical_walls

def is_deadlock(state: Map, x: int, y: int) -> bool:
    """
    Verifică dacă o poziție este deadlock (cutia nu mai poate fi mutată)
    Verifică colțuri și situații de blocare între pereți
    """
    if ((x == 0 or x == state.length-1) and (y == 0 or y == state.width-1)):
        return True
        
    horizontal_blocked = ((x-1, y) in state.obstacles or (x+1, y) in state.obstacles)
    vertical_blocked = ((x, y-1) in state.obstacles or (x, y+1) in state.obstacles)
    
    if horizontal_blocked and vertical_blocked:
        return True
        
    return False

def blocks_other_boxes(state: Map, box_pos: tuple) -> bool:
    """Verifică dacă o cutie blochează alte cutii"""
    x, y = box_pos
    for other_box in state.boxes.values():
        if (other_box.x, other_box.y) != box_pos:
            if (abs(x - other_box.x) == 1 and y == other_box.y) or \
               (abs(y - other_box.y) == 1 and x == other_box.x):
                return True
    return False

#                                                                                                        #
#                                                                                                        #
##########################################################################################################
##########################################################################################################
#                                                                                                        #
#                                                                                                        #

def matching_heuristic(state: Map) -> float:
    """
    Greedy matching: pentru fiecare cutie (neplasată), alegem cel mai apropiat target
    neterminat și adăugăm Manhattan-distance. Penalizare deadlock colț simplu.
    """
    total = 0.0
    boxes = [(b.x, b.y) for b in state.boxes.values() if (b.x, b.y) not in state.targets]
    targets = list(state.targets)

    if not boxes:
        return 0.0

    for bx, by in boxes:
        best = min(targets, key=lambda t: abs(bx-t[0]) + abs(by-t[1]))
        dist = abs(bx-best[0]) + abs(by-best[1])
        total += dist
        targets.remove(best)

        if ((bx-1, by) in state.obstacles and (bx, by-1) in state.obstacles) or \
           ((bx-1, by) in state.obstacles and (bx, by+1) in state.obstacles) or \
           ((bx+1, by) in state.obstacles and (bx, by-1) in state.obstacles) or \
           ((bx+1, by) in state.obstacles and (bx, by+1) in state.obstacles):
            total += 1000.0

    return total

##########################################################################################################

def ida_star_heuristic(state: Map) -> int:
    """
    Euristică îmbunătățită care ia în considerare:
    1. Distanța Manhattan minimă de la fiecare cutie la cel mai apropiat target
    2. Distanța Manhattan de la jucător la cea mai apropiată cutie nemutată
    3. Penalizări pentru diverse situații problematice
    4. Bonus pentru cutii plasate corect
    """
    total_cost = 0
    unplaced_boxes = []
    player_to_box_cost = float('inf')
    
    for box in state.boxes.values():
        box_pos = (box.x, box.y)
        
        if box_pos in state.targets:
            if not blocks_other_boxes(state, box_pos):
                total_cost -= 30
            continue
            
        min_distance = float('inf')
        for target_x, target_y in state.targets:
            distance = manhattan_distance(box.x, box.y, target_x, target_y)
            min_distance = min(min_distance, distance)
        
        total_cost += min_distance * 2
        
        if is_deadlock(state, box.x, box.y):
            total_cost += 1000
            
        if is_tunnel(state, box.x, box.y):
            if box_pos not in state.targets:
                total_cost += 50
                
        if blocks_other_boxes(state, box_pos):
            total_cost += 100
            
        player_distance = manhattan_distance(state.player.x, state.player.y, box.x, box.y)
        player_to_box_cost = min(player_to_box_cost, player_distance)
        
        unplaced_boxes.append(box_pos)
    
    if unplaced_boxes:
        total_cost += player_to_box_cost
        
    if len(unplaced_boxes) >= 2:
        max_box_spread = 0
        for i, box1 in enumerate(unplaced_boxes[:-1]):
            for box2 in unplaced_boxes[i+1:]:
                spread = manhattan_distance(box1[0], box1[1], box2[0], box2[1])
                max_box_spread = max(max_box_spread, spread)
        total_cost += max_box_spread * 2
    
    return total_cost

##########################################################################################################

def target_matching_heuristic(state: Map) -> int:
    """
    Euristică pentru cutii neplasate:
    - Alege cel mai apropiat target pentru fiecare cutie
    - Penalizare pentru deadlock și tunel
    - Penalizare pentru cutii blocate
    - Penalizare pentru cutii care oscilează
    """
    total_cost = 0
    boxes = [box for box in state.boxes.values() if (box.x, box.y) not in state.targets]
    targets = list(state.targets)

    unmatched_targets = set(targets)
    for box in boxes:
        box_pos = (box.x, box.y)
        best_distance = float('inf')
        best_target = None

        for target in unmatched_targets:
            dist = manhattan_distance(box.x, box.y, target[0], target[1])
            if dist < best_distance:
                best_distance = dist
                best_target = target

        if best_target:
            unmatched_targets.remove(best_target)
            total_cost += best_distance * 2.5

        if is_deadlock(state, box.x, box.y):
            total_cost += 1500
        if is_tunnel(state, box.x, box.y) and box_pos not in state.targets:
            total_cost += 80
        if blocks_other_boxes(state, box_pos):
            total_cost += 150

    if boxes:
        min_player_distance = min(
            manhattan_distance(state.player.x, state.player.y, box.x, box.y) 
            for box in boxes
        )
        total_cost += min_player_distance

    total_cost += state.explored_states * 0.1

    return total_cost

##########################################################################################################

def simple_heuristic(state: Map) -> int:
    """
    Euristică simplă:
    - Suma distanțelor Manhattan de la cutii la ținte
    - Penalizare dacă cutiile sunt blocate
    """
    total_cost = 0
    for box in state.boxes.values():
        if (box.x, box.y) in state.targets:
            continue

        min_distance = float('inf')
        for target_x, target_y in state.targets:
            distance = manhattan_distance(box.x, box.y, target_x, target_y)
            min_distance = min(min_distance, distance)

        total_cost += min_distance

        if is_deadlock(state, box.x, box.y):
            total_cost += 1000

    return total_cost
