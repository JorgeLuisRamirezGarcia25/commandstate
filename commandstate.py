# htop_clone.py
import curses
import psutil
import os
import time
import signal

SORT_OPTIONS = ['cpu', 'memory', 'pid']
SORT_LABELS = {'cpu': 'CPU%', 'memory': 'MEM%', 'pid': 'PID'}

# Color pairs
COLOR_HEADER = 1
COLOR_HIGH_CPU = 2
COLOR_HIGH_MEM = 3
COLOR_NORMAL = 4
COLOR_LOW = 5
COLOR_BAR_GREEN = 6
COLOR_BAR_YELLOW = 7
COLOR_BAR_RED = 8
COLOR_SELECTED = 9

def init_colors():
    """Initialize color pairs for the interface"""
    curses.start_color()
    curses.init_pair(COLOR_HEADER, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(COLOR_HIGH_CPU, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(COLOR_HIGH_MEM, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(COLOR_NORMAL, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(COLOR_LOW, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(COLOR_BAR_GREEN, curses.COLOR_BLACK, curses.COLOR_GREEN)
    curses.init_pair(COLOR_BAR_YELLOW, curses.COLOR_BLACK, curses.COLOR_YELLOW)
    curses.init_pair(COLOR_BAR_RED, curses.COLOR_BLACK, curses.COLOR_RED)
    curses.init_pair(COLOR_SELECTED, curses.COLOR_BLACK, curses.COLOR_WHITE)

def draw_bar(stdscr, y, x, value, width=20, label=""):
    """Draw a visual progress bar"""
    if value > 100:
        value = 100
    if value < 0:
        value = 0
    
    filled = int((value / 100) * width)
    
    # Choose color based on value
    if value >= 80:
        color = curses.color_pair(COLOR_BAR_RED)
    elif value >= 60:
        color = curses.color_pair(COLOR_BAR_YELLOW)
    else:
        color = curses.color_pair(COLOR_BAR_GREEN)
    
    # Draw the bar
    bar_str = "#" * filled + "." * (width - filled)
    stdscr.addstr(y, x, f"{label}", curses.color_pair(COLOR_HEADER))
    stdscr.addstr(y, x + len(label), "[", curses.color_pair(COLOR_NORMAL))
    stdscr.addstr(y, x + len(label) + 1, bar_str, color)
    stdscr.addstr(y, x + len(label) + 1 + width, f"] {value:5.1f}%", curses.color_pair(COLOR_NORMAL))

def get_system_info():
    """Get detailed system information"""
    cpu_count = psutil.cpu_count()
    cpu_freq = psutil.cpu_freq()
    memory = psutil.virtual_memory()
    
    info = {
        'cpu_count': cpu_count,
        'cpu_freq': cpu_freq.current if cpu_freq else 0,
        'memory_total_gb': memory.total / (1024**3),
        'uptime': time.time() - psutil.boot_time()
    }
    return info

def get_processes(sort_by):
    procs = []
    for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            procs.append(p.info)
        except psutil.NoSuchProcess:
            continue
    if sort_by == 'cpu':
        procs.sort(key=lambda x: x['cpu_percent'], reverse=True)
    elif sort_by == 'memory':
        procs.sort(key=lambda x: x['memory_percent'], reverse=True)
    elif sort_by == 'pid':
        procs.sort(key=lambda x: x['pid'])
    return procs

def draw_header(stdscr, cpu, mem, swap):
    """Draw enhanced header with system info and progress bars"""
    h, w = stdscr.getmaxyx()
    
    # System info
    sys_info = get_system_info()
    uptime_hours = int(sys_info['uptime'] // 3600)
    uptime_mins = int((sys_info['uptime'] % 3600) // 60)
    
    # Header line with system info
    header_text = f"Uptime: {uptime_hours:02d}:{uptime_mins:02d} | CPU cores: {sys_info['cpu_count']} | RAM: {sys_info['memory_total_gb']:.1f}GB"
    if sys_info['cpu_freq'] > 0:
        header_text += f" | CPU freq: {sys_info['cpu_freq']:.0f}MHz"
    
    stdscr.addstr(0, 0, header_text[:w-1], curses.color_pair(COLOR_HEADER))
    
    # Progress bars
    bar_width = min(25, w // 4)
    draw_bar(stdscr, 1, 0, cpu, bar_width, "CPU ")
    draw_bar(stdscr, 2, 0, mem, bar_width, "MEM ")
    draw_bar(stdscr, 3, 0, swap, bar_width, "SWP ")
    
    # Process list header
    stdscr.addstr(5, 0, "PID     NAME                CPU%   MEM%    STATUS", curses.color_pair(COLOR_HEADER))
    stdscr.hline(6, 0, '-', min(w-1, 50))

def get_process_color(proc):
    """Determine color based on process resource usage"""
    cpu_percent = proc.get('cpu_percent', 0)
    mem_percent = proc.get('memory_percent', 0)
    
    if cpu_percent >= 50:
        return curses.color_pair(COLOR_HIGH_CPU)
    elif mem_percent >= 30:
        return curses.color_pair(COLOR_HIGH_MEM)
    elif cpu_percent >= 10 or mem_percent >= 10:
        return curses.color_pair(COLOR_NORMAL)
    else:
        return curses.color_pair(COLOR_LOW)

def get_process_status(pid):
    """Get process status string"""
    try:
        proc = psutil.Process(pid)
        status = proc.status()
        status_map = {
            psutil.STATUS_RUNNING: "RUN",
            psutil.STATUS_SLEEPING: "SLP",
            psutil.STATUS_DISK_SLEEP: "DSK",
            psutil.STATUS_STOPPED: "STP",
            psutil.STATUS_TRACING_STOP: "TRC",
            psutil.STATUS_ZOMBIE: "ZOM",
            psutil.STATUS_DEAD: "DEA",
            psutil.STATUS_WAKE_KILL: "WKL",
            psutil.STATUS_WAKING: "WAK",
            psutil.STATUS_IDLE: "IDL",
            psutil.STATUS_LOCKED: "LCK",
            psutil.STATUS_WAITING: "WAI"
        }
        return status_map.get(status, "UNK")
    except:
        return "---"

def draw_processes(stdscr, procs, selected, start):
    """Draw process list with colors and enhanced information"""
    h, w = stdscr.getmaxyx()
    max_processes = h - 9  # Account for header and footer
    
    for idx, proc in enumerate(procs[start:start+max_processes]):
        if idx + 7 >= h - 2:  # Leave space for footer
            break
            
        status = get_process_status(proc['pid'])
        line = f"{proc['pid']:<7} {proc['name'][:18]:<18} {proc['cpu_percent']:>5.1f} {proc['memory_percent']:>6.1f}  {status}"
        
        y_pos = idx + 7
        
        if idx + start == selected:
            # Selected process - highlighted
            stdscr.addstr(y_pos, 0, line[:w-1], curses.color_pair(COLOR_SELECTED))
        else:
            # Normal process - colored by resource usage
            color = get_process_color(proc)
            stdscr.addstr(y_pos, 0, line[:w-1], color)

def main(stdscr):
    curses.curs_set(0)
    init_colors()  # Initialize color support
    
    selected = 0
    start = 0
    sort_idx = 0
    sort_by = SORT_OPTIONS[sort_idx]
    
    while True:
        stdscr.clear()
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory().percent
        swap = psutil.swap_memory().percent
        procs = get_processes(sort_by)
        n = len(procs)
        
        if selected >= n:
            selected = n-1
        if selected < 0:
            selected = 0
            
        h, w = stdscr.getmaxyx()
        max_visible = h - 9  # Adjusted for new header size
        
        if selected < start:
            start = selected
        elif selected >= start + max_visible:
            start = selected - max_visible + 1
            
        draw_header(stdscr, cpu, mem, swap)
        draw_processes(stdscr, procs, selected, start)
        
        # Footer with controls and key speed info
        footer_y = h - 2
        controls = f"Sort: {SORT_LABELS[sort_by]} | ↑↓: Navegar | ←→: Ordenar | k: matar | q: salir"
        stdscr.addstr(footer_y, 0, controls[:w-1], curses.color_pair(COLOR_HEADER))
        
        stdscr.refresh()
        key = stdscr.getch()
        
        if key == curses.KEY_UP:
            selected -= 1
        elif key == curses.KEY_DOWN:
            selected += 1
        elif key == curses.KEY_LEFT:
            sort_idx = (sort_idx - 1) % len(SORT_OPTIONS)
            sort_by = SORT_OPTIONS[sort_idx]
        elif key == curses.KEY_RIGHT:
            sort_idx = (sort_idx + 1) % len(SORT_OPTIONS)
            sort_by = SORT_OPTIONS[sort_idx]
        elif key == ord('k'):
            try:
                os.kill(procs[selected]['pid'], signal.SIGTERM)
            except Exception:
                pass
        elif key == ord('q'):
            break
            
        # Key speed measurement
        if not hasattr(main, "last_key_time"):
            main.last_key_time = time.time()
            main.key_speeds = []
        now = time.time()
        if 'key' in locals() and key != -1:
            interval = now - main.last_key_time
            main.key_speeds.append(interval)
            if len(main.key_speeds) > 20:
                main.key_speeds.pop(0)
            avg_speed = sum(main.key_speeds) / len(main.key_speeds)
            speed_text = f"Velocidad promedio de teclas: {avg_speed:.3f} s"
            stdscr.addstr(h-1, 0, speed_text[:w-1], curses.color_pair(COLOR_LOW))
            main.last_key_time = now
            
        time.sleep(0.1)

if __name__ == "__main__":
    curses.wrapper(main)