# CommandState - Modern Process Monitor
# A modern htop clone with Textual GUI interface
# Features: Process management, signal sending, filtering, and real-time monitoring
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header, Footer, DataTable, Static, Button, Input, Select, 
    ProgressBar, Label, TabbedContent, TabPane
)
from textual.reactive import reactive
from textual.message import Message
from textual.binding import Binding
from textual import events
from rich.text import Text
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn
from rich.table import Table
import psutil
import os
import time
import signal
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class ProcessInfo:
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    status: str
    username: str
    cmdline: str
    create_time: float

class SystemStatsWidget(Static):
    """Widget to display system statistics with progress bars"""
    
    def __init__(self):
        super().__init__()
        self.update_stats()
    
    def update_stats(self):
        """Update system statistics"""
        cpu_percent = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # Get system info
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        uptime = time.time() - psutil.boot_time()
        uptime_hours = int(uptime // 3600)
        uptime_mins = int((uptime % 3600) // 60)
        
        # Create rich content with progress bars
        console = Console()
        with console.capture() as capture:
            console.print(f"[bold cyan]System Information[/bold cyan]")
            console.print(f"Uptime: {uptime_hours:02d}:{uptime_mins:02d} | CPU Cores: {cpu_count} | RAM: {memory.total / (1024**3):.1f}GB")
            if cpu_freq:
                console.print(f"CPU Frequency: {cpu_freq.current:.0f} MHz")
            console.print()
            
            # CPU Progress bar
            cpu_bar = self._create_progress_bar("CPU", cpu_percent)
            console.print(cpu_bar)
            
            # Memory Progress bar
            mem_bar = self._create_progress_bar("Memory", memory.percent)
            console.print(mem_bar)
            
            # Swap Progress bar if available
            if swap.total > 0:
                swap_bar = self._create_progress_bar("Swap", swap.percent)
                console.print(swap_bar)
        
        self.update(capture.get())
    
    def _create_progress_bar(self, label: str, percent: float) -> str:
        """Create a colored progress bar string"""
        width = 30
        filled = int((percent / 100) * width)
        
        if percent >= 80:
            color = "red"
        elif percent >= 60:
            color = "yellow"
        else:
            color = "green"
        
        bar = "█" * filled + "░" * (width - filled)
        return f"{label:>6}: [{color}]{bar}[/{color}] {percent:5.1f}%"

class ProcessTableWidget(ScrollableContainer):
    """Advanced process table with filtering and sorting"""
    
    def __init__(self):
        super().__init__()
        self.processes: List[ProcessInfo] = []
        self.sort_by = "cpu_percent"
        self.sort_reverse = True
        self.filter_mode = "all"
        self.filter_text = ""
        self.selected_pid: Optional[int] = None
        
    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal(classes="controls"):
                yield Select([
                    ("All processes", "all"),
                    ("User processes", "user"),
                    ("High CPU (>10%)", "high_cpu"),
                    ("High Memory (>10%)", "high_mem"),
                ], value="all", id="filter_select")
                yield Input(placeholder="Search process name...", id="search_input")
                yield Button("Refresh", id="refresh_btn", variant="primary")
            
            with Horizontal(classes="sort-controls"):
                yield Button("Sort: CPU", id="sort_cpu", variant="success")
                yield Button("Sort: Memory", id="sort_memory")
                yield Button("Sort: PID", id="sort_pid")
                yield Button("Sort: Name", id="sort_name")
                yield Button("Reverse", id="reverse_sort")
            
            yield DataTable(id="process_table", cursor_type="row")
    
    def on_mount(self) -> None:
        """Initialize the process table"""
        table = self.query_one("#process_table", DataTable)
        table.add_columns("PID", "Name", "CPU%", "Memory%", "Memory(MB)", "Status", "User")
        self.update_processes()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "refresh_btn":
            self.update_processes()
        elif event.button.id == "sort_cpu":
            self.sort_by = "cpu_percent"
            self._update_sort_buttons(event.button)
            self.update_processes()
        elif event.button.id == "sort_memory":
            self.sort_by = "memory_percent"
            self._update_sort_buttons(event.button)
            self.update_processes()
        elif event.button.id == "sort_pid":
            self.sort_by = "pid"
            self._update_sort_buttons(event.button)
            self.update_processes()
        elif event.button.id == "sort_name":
            self.sort_by = "name"
            self._update_sort_buttons(event.button)
            self.update_processes()
        elif event.button.id == "reverse_sort":
            self.sort_reverse = not self.sort_reverse
            event.button.label = "Ascending" if not self.sort_reverse else "Descending"
            self.update_processes()
    
    def _update_sort_buttons(self, active_button: Button) -> None:
        """Update button styles to show active sort"""
        for button in self.query("Button"):
            if button.id and button.id.startswith("sort_"):
                button.variant = "success" if button == active_button else "default"
    
    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle filter selection changes"""
        if event.select.id == "filter_select":
            self.filter_mode = event.value
            self.update_processes()
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes"""
        if event.input.id == "search_input":
            self.filter_text = event.value
            self.update_processes()
    
    def update_processes(self) -> None:
        """Update the process list"""
        self.processes = self._get_processes()
        table = self.query_one("#process_table", DataTable)
        table.clear()
        
        for proc in self.processes:
            # Color coding based on resource usage
            cpu_style = self._get_cpu_style(proc.cpu_percent)
            mem_style = self._get_memory_style(proc.memory_percent)
            
            table.add_row(
                str(proc.pid),
                Text(proc.name[:20], style="bold" if proc.cpu_percent > 50 else ""),
                Text(f"{proc.cpu_percent:.1f}", style=cpu_style),
                Text(f"{proc.memory_percent:.1f}", style=mem_style),
                f"{proc.memory_mb:.1f}",
                proc.status,
                proc.username[:10],
                key=proc.pid
            )
    
    def _get_cpu_style(self, cpu_percent: float) -> str:
        """Get style for CPU percentage"""
        if cpu_percent >= 50:
            return "bold red"
        elif cpu_percent >= 20:
            return "yellow"
        elif cpu_percent >= 5:
            return "white"
        else:
            return "green"
    
    def _get_memory_style(self, mem_percent: float) -> str:
        """Get style for memory percentage"""
        if mem_percent >= 30:
            return "bold red"
        elif mem_percent >= 15:
            return "yellow"
        elif mem_percent >= 5:
            return "white"
        else:
            return "green"
    
    def _get_processes(self) -> List[ProcessInfo]:
        """Get filtered and sorted process list"""
        processes = []
        current_user = os.getlogin()
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 
                                       'memory_info', 'status', 'username', 'cmdline', 'create_time']):
            try:
                info = proc.info
                
                # Apply filters
                if self.filter_mode == "user" and info.get('username') != current_user:
                    continue
                elif self.filter_mode == "high_cpu" and info.get('cpu_percent', 0) <= 10:
                    continue
                elif self.filter_mode == "high_mem" and info.get('memory_percent', 0) <= 10:
                    continue
                
                # Apply text filter
                if self.filter_text and self.filter_text.lower() not in info.get('name', '').lower():
                    continue
                
                # Create ProcessInfo object
                memory_info = info.get('memory_info')
                memory_mb = memory_info.rss / (1024 * 1024) if memory_info else 0
                
                cmdline = info.get('cmdline', [])
                cmdline_str = ' '.join(cmdline) if cmdline else info.get('name', '')
                
                process_info = ProcessInfo(
                    pid=info['pid'],
                    name=info.get('name', 'Unknown'),
                    cpu_percent=info.get('cpu_percent', 0),
                    memory_percent=info.get('memory_percent', 0),
                    memory_mb=memory_mb,
                    status=info.get('status', 'Unknown'),
                    username=info.get('username', 'Unknown'),
                    cmdline=cmdline_str[:100],  # Limit length
                    create_time=info.get('create_time', 0)
                )
                
                processes.append(process_info)
                
            except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
                continue
        
        # Sort processes
        processes.sort(
            key=lambda x: getattr(x, self.sort_by),
            reverse=self.sort_reverse
        )
        
        return processes
    
    def get_selected_process(self) -> Optional[ProcessInfo]:
        """Get currently selected process"""
        table = self.query_one("#process_table", DataTable)
        if table.cursor_row is not None and table.cursor_row < len(self.processes):
            return self.processes[table.cursor_row]
        return None

class ProcessControlWidget(Static):
    """Widget for process control actions"""
    
    def compose(self) -> ComposeResult:
        with Horizontal(classes="process-controls"):
            yield Button("SIGTERM (15)", id="sigterm", variant="warning")
            yield Button("SIGKILL (9)", id="sigkill", variant="error")
            yield Button("SIGSTOP (19)", id="sigstop")
            yield Button("SIGCONT (18)", id="sigcont")
            yield Button("SIGHUP (1)", id="sighup")
            yield Button("SIGUSR1 (10)", id="sigusr1")
            yield Button("SIGUSR2 (12)", id="sigusr2")
        
        yield Static("Selected Process: None", id="selected_info")
    
    def send_signal_to_process(self, pid: int, signal_num: int, signal_name: str) -> None:
        """Send signal to process"""
        try:
            os.kill(pid, signal_num)
            self.notify(f"Sent {signal_name} to process {pid}", severity="information")
        except ProcessLookupError:
            self.notify(f"Process {pid} not found", severity="error")
        except PermissionError:
            self.notify(f"Permission denied to send {signal_name} to process {pid}", severity="error")
        except Exception as e:
            self.notify(f"Error sending {signal_name} to process {pid}: {e}", severity="error")
    
    def update_selected_process(self, process: Optional[ProcessInfo]) -> None:
        """Update selected process information"""
        info_widget = self.query_one("#selected_info", Static)
        if process:
            info_text = f"Selected: PID {process.pid} - {process.name} (CPU: {process.cpu_percent:.1f}%, Mem: {process.memory_percent:.1f}%)"
            info_widget.update(info_text)
        else:
            info_widget.update("Selected Process: None")

class CommandStateApp(App):
    """CommandState - Modern Process Monitor with Textual GUI"""
    
    CSS = """
    .controls {
        height: 3;
        background: $surface;
        padding: 1;
    }
    
    .sort-controls {
        height: 3;
        background: $surface-lighten-1;
        padding: 1;
    }
    
    .process-controls {
        height: 3;
        background: $surface-lighten-2;
        padding: 1;
    }
    
    DataTable {
        height: 1fr;
    }
    
    #selected_info {
        background: $primary 20%;
        color: $text;
        padding: 1;
        margin: 1;
    }
    
    Button {
        margin: 0 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("k", "kill_selected", "Kill Selected"),
        Binding("t", "terminate_selected", "Terminate Selected"),
        Binding("f5", "refresh", "Refresh"),
    ]
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        with TabbedContent(initial="processes"):
            with TabPane("Processes", id="processes"):
                with Vertical():
                    yield SystemStatsWidget()
                    yield ProcessTableWidget()
                    yield ProcessControlWidget()
            
            with TabPane("System Info", id="sysinfo"):
                yield Static("Detailed system information coming soon...", id="detailed_stats")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the app"""
        self.set_interval(2.0, self.update_data)  # Update every 2 seconds
    
    def update_data(self) -> None:
        """Update all data periodically"""
        # Update system stats
        system_widget = self.query_one(SystemStatsWidget)
        system_widget.update_stats()
        
        # Update process table
        process_widget = self.query_one(ProcessTableWidget)
        process_widget.update_processes()
    
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle process selection"""
        process_widget = self.query_one(ProcessTableWidget)
        control_widget = self.query_one(ProcessControlWidget)
        
        selected_process = process_widget.get_selected_process()
        control_widget.update_selected_process(selected_process)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle signal button presses"""
        signal_map = {
            "sigterm": (signal.SIGTERM, "SIGTERM"),
            "sigkill": (signal.SIGKILL, "SIGKILL"),
            "sigstop": (signal.SIGSTOP, "SIGSTOP"),
            "sigcont": (signal.SIGCONT, "SIGCONT"),
            "sighup": (signal.SIGHUP, "SIGHUP"),
            "sigusr1": (signal.SIGUSR1, "SIGUSR1"),
            "sigusr2": (signal.SIGUSR2, "SIGUSR2"),
        }
        
        if event.button.id in signal_map:
            process_widget = self.query_one(ProcessTableWidget)
            control_widget = self.query_one(ProcessControlWidget)
            
            selected_process = process_widget.get_selected_process()
            if selected_process:
                signal_num, signal_name = signal_map[event.button.id]
                control_widget.send_signal_to_process(
                    selected_process.pid, signal_num, signal_name
                )
                # Refresh after signal
                self.call_later(process_widget.update_processes)
    
    def action_quit(self) -> None:
        """Quit the application"""
        self.exit()
    
    def action_refresh(self) -> None:
        """Refresh all data"""
        self.update_data()
    
    def action_kill_selected(self) -> None:
        """Kill selected process with SIGKILL"""
        process_widget = self.query_one(ProcessTableWidget)
        control_widget = self.query_one(ProcessControlWidget)
        
        selected_process = process_widget.get_selected_process()
        if selected_process:
            control_widget.send_signal_to_process(
                selected_process.pid, signal.SIGKILL, "SIGKILL"
            )
            self.call_later(process_widget.update_processes)
    
    def action_terminate_selected(self) -> None:
        """Terminate selected process with SIGTERM"""
        process_widget = self.query_one(ProcessTableWidget)
        control_widget = self.query_one(ProcessControlWidget)
        
        selected_process = process_widget.get_selected_process()
        if selected_process:
            control_widget.send_signal_to_process(
                selected_process.pid, signal.SIGTERM, "SIGTERM"
            )
            self.call_later(process_widget.update_processes)

if __name__ == "__main__":
    app = CommandStateApp()
    app.run()
