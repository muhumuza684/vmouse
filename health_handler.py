"""
Health monitoring module for VMouse PC server.
Collects CPU, RAM, Disk, Battery, and process information.
"""

import psutil
import platform
from datetime import datetime


def get_pc_health():
    """Collect all PC health metrics."""
    try:
        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.5)
        cpu_freq = psutil.cpu_freq()
        cpu_cores = psutil.cpu_count()

        # Memory (RAM)
        mem = psutil.virtual_memory()

        # Disk
        disk = psutil.disk_usage('/')

        # Battery
        battery = psutil.sensors_battery()

        # Running processes (top 10 by CPU)
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                info = proc.info
                if info.get('cpu_percent', 0) > 0.1:
                    processes.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        processes = sorted(processes, key=lambda x: x.get('cpu_percent', 0), reverse=True)[:10]

        # Network info
        net_io = psutil.net_io_counters()

        return {
            "timestamp": datetime.now().isoformat(),
            "device_type": "pc",
            "hostname": platform.node(),
            "os": platform.system() + " " + platform.release(),
            "cpu": {
                "usage_percent": round(cpu_percent, 1),
                "cores": cpu_cores,
                "frequency_mhz": round(cpu_freq.current, 0) if cpu_freq else None,
                "max_frequency_mhz": round(cpu_freq.max, 0) if cpu_freq and cpu_freq.max else None
            },
            "ram": {
                "total_gb": round(mem.total / (1024**3), 2),
                "used_gb": round(mem.used / (1024**3), 2),
                "available_gb": round(mem.available / (1024**3), 2),
                "percent": round(mem.percent, 1)
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "percent": round(disk.percent, 1)
            },
            "battery": {
                "percent": battery.percent if battery else None,
                "plugged_in": battery.power_plugged if battery else None,
                "time_remaining_sec": battery.secsleft if battery else None
            } if battery else None,
            "network": {
                "bytes_sent_mb": round(net_io.bytes_sent / (1024**2), 1),
                "bytes_recv_mb": round(net_io.bytes_recv / (1024**2), 1)
            },
            "top_processes": processes
        }
    except Exception as e:
        return {"error": str(e)}


def analyze_pc_health(health_data):
    """Analyze health data and return risks + recommendations."""
    risks = []
    recommendations = []

    if "error" in health_data:
        return {"risks": ["Could not retrieve health data"], "recommendations": ["Check server logs"]}

    # CPU analysis
    cpu_usage = health_data.get("cpu", {}).get("usage_percent", 0)
    if cpu_usage > 85:
        risks.append(f"Critical CPU usage ({cpu_usage:.0f}%)")
        recommendations.append("Close resource-intensive apps or restart your PC")
    elif cpu_usage > 70:
        risks.append(f"High CPU usage ({cpu_usage:.0f}%)")
        recommendations.append("Consider closing unused applications")

    # RAM analysis
    ram_usage = health_data.get("ram", {}).get("percent", 0)
    if ram_usage > 90:
        risks.append(f"Critical RAM usage ({ram_usage:.0f}%)")
        recommendations.append("Close unused applications or add more RAM")
    elif ram_usage > 75:
        risks.append(f"High RAM usage ({ram_usage:.0f}%)")
        recommendations.append("Consider closing some programs to free memory")

    # Disk analysis
    disk_usage = health_data.get("disk", {}).get("percent", 0)
    if disk_usage > 90:
        risks.append(f"Storage nearly full ({disk_usage:.0f}%)")
        recommendations.append("Delete unnecessary files or move data to external storage")
    elif disk_usage > 80:
        risks.append(f"Storage filling up ({disk_usage:.0f}%)")
        recommendations.append("Consider freeing up disk space")

    # Battery analysis
    battery = health_data.get("battery")
    if battery:
        battery_pct = battery.get("percent", 100)
        if battery_pct is not None:
            if battery_pct < 15 and not battery.get("plugged_in", True):
                risks.append(f"Battery critically low ({battery_pct:.0f}%)")
                recommendations.append("Plug in charger immediately")
            elif battery_pct < 30 and not battery.get("plugged_in", True):
                risks.append(f"Battery low ({battery_pct:.0f}%)")
                recommendations.append("Consider connecting to power source")

    # Process-specific risks (suspicious apps)
    suspicious_keywords = ["mining", "crypto", "bitcoin", "miner", "nicehash"]
    for proc in health_data.get("top_processes", []):
        proc_name = proc.get("name", "").lower()
        if any(keyword in proc_name for keyword in suspicious_keywords):
            risks.append(f"Suspicious process: {proc.get('name')}")
            recommendations.append("Review and uninstall unknown software")

    # No risks detected
    if not risks:
        risks = ["No critical risks detected"]
        recommendations = ["Your PC appears healthy"]

    return {
        "risks": risks,
        "recommendations": recommendations
    }
