# CommandState - Modern Process Monitor

A modern, feature-rich process monitor built with Python and Textual, offering a beautiful GUI-like experience in the terminal.

## 🚀 Features

### 🎨 Modern GUI Interface
- **Textual-based interface** with professional widgets
- **Tabbed layout** for organized information
- **Interactive buttons** and controls
- **Real-time updates** every 2 seconds
- **Responsive design** that adapts to terminal size

### 📊 System Monitoring
- **CPU usage** with colored progress bars
- **Memory usage** visualization
- **Swap usage** monitoring
- **System information** (uptime, CPU cores, frequency, RAM)
- **Process count** and statistics

### 🔍 Advanced Filtering & Sorting
- **Multiple filter options**:
  - All processes
  - User processes only
  - High CPU usage (>10%)
  - High memory usage (>10%)
- **Real-time search** by process name
- **Multiple sorting criteria**: CPU, Memory, PID, Name
- **Ascending/Descending** order toggle

### 📡 Process Control & Signals
- **SIGTERM (15)**: Normal termination
- **SIGKILL (9)**: Force kill
- **SIGSTOP (19)**: Pause process
- **SIGCONT (18)**: Continue paused process
- **SIGHUP (1)**: Hang up signal
- **SIGUSR1 (10)** & **SIGUSR2 (12)**: User signals
- **Error handling** with clear notifications

### 🎯 Process Information
- **Process ID** (PID)
- **Process name** (truncated for display)
- **CPU percentage** with color coding
- **Memory percentage** with color coding
- **Memory usage in MB**
- **Process status** (RUN, SLP, etc.)
- **Username** of process owner

## 🛠️ Installation

### Prerequisites
- Python 3.7 or higher
- Linux/Unix terminal (tested on Linux)

### Install Dependencies
```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install textual psutil rich
```

## 🎮 Usage

### Run the Application
```bash
python commandstate.py
```

### Keyboard Shortcuts
- **q**: Quit application
- **r**: Refresh data
- **k**: Kill selected process (SIGKILL)
- **t**: Terminate selected process (SIGTERM)
- **F5**: Refresh data

### Mouse Controls
- **Click buttons** to send signals to processes
- **Use dropdowns** for filtering
- **Type in search box** for real-time filtering
- **Click table rows** to select processes

## 🎨 Color Coding

### CPU Usage
- **Green**: Low usage (<5%)
- **White**: Normal usage (5-20%)
- **Yellow**: Medium usage (20-50%)
- **Red**: High usage (≥50%)

### Memory Usage
- **Green**: Low usage (<5%)
- **White**: Normal usage (5-15%)
- **Yellow**: Medium usage (15-30%)
- **Red**: High usage (≥30%)

### Progress Bars
- **Green**: <60%
- **Yellow**: 60-79%
- **Red**: ≥80%

## 📁 Project Structure

```
commandstate/
├── commandstate.py          # Main modern application
├── commandstate_classic.py  # Classic curses version
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🔧 Technical Details

### Built With
- **Textual 3.6.0**: Modern TUI framework
- **psutil 7.0.0**: System and process utilities
- **Rich**: Enhanced terminal formatting
- **Python 3.7+**: Core language

### Architecture
- **Modular design** with separate widgets
- **Event-driven interface** using Textual's message system
- **Real-time data updates** with efficient process iteration
- **Memory-efficient** process filtering and sorting

## 🆚 Versions

### Modern Version (commandstate.py)
- Textual GUI interface
- Mouse and keyboard support
- Advanced signal management
- Professional appearance

### Classic Version (commandstate_classic.py)
- Traditional curses interface
- Keyboard-only navigation
- Lightweight and fast
- htop-like experience

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests to improve CommandState!

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- Inspired by **htop** and **top** utilities
- Built with the amazing **Textual** framework
- Uses **psutil** for cross-platform system information

---

**CommandState** - Modern process monitoring for the terminal! 🚀