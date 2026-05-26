#include "thermal_monitor.h"

#include <iomanip>
#include <iostream>
#include <sstream>

using namespace ibm::hpc;

static std::string format_reading(const SensorReading& r, AlertLevel level) {
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        r.timestamp.time_since_epoch()).count();
    std::ostringstream oss;
    oss << "[" << ms << " ms]  "
        << std::left << std::setw(22) << r.sensor_id
        << std::fixed << std::setprecision(1) << r.temperature_C << " C  -> "
        << ThermalMonitor::level_to_string(level);
    return oss.str();
}

int main(int argc, char* argv[]) {
    std::cout << "=== IBM HPC Thermal Monitor Daemon ===\n"
              << "Component : POWER10 Multi-Chip Module\n"
              << "Thresholds: WARNING=75C  THROTTLE=90C  CRITICAL=105C\n\n";

    ThermalMonitor monitor({75.0, 90.0, 105.0});

    for (const char* id : {
            "PROC0_DIE_TEMP", "PROC1_DIE_TEMP",
            "DIMM_A0_TEMP",   "DIMM_B0_TEMP",
            "VRM_VCORE_TEMP", "PCB_INLET_TEMP", "HEATSINK_BASE"})
        monitor.add_sensor(id);

    monitor.set_alert_callback([](const SensorReading& r, AlertLevel lvl) {
        const char* prefix =
            lvl == AlertLevel::CRITICAL ? "\033[1;31m[CRITICAL]\033[0m " :
            lvl == AlertLevel::THROTTLE ? "\033[1;33m[THROTTLE]\033[0m " :
                                          "\033[1;34m[WARNING ]\033[0m ";
        std::cerr << prefix << format_reading(r, lvl) << "\n";
        if (lvl == AlertLevel::THROTTLE)
            std::cerr << "           -> Reducing P-state on " << r.sensor_id << "\n";
        else if (lvl == AlertLevel::CRITICAL)
            std::cerr << "           -> EMERGENCY: initiating thermal shutdown\n";
    });

    double duration_s = (argc > 1) ? std::stod(argv[1]) : 5.0;
    std::cout << "Monitoring for " << duration_s << " seconds...\n\n";

    try {
        monitor.run(duration_s, 500);
    } catch (const std::exception& ex) {
        std::cerr << "Fatal: " << ex.what() << "\n";
        return 1;
    }
    std::cout << "\nMonitoring complete.\n";
    return 0;
}
