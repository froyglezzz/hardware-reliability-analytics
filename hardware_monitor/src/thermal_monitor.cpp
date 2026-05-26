#include "thermal_monitor.h"

#include <chrono>
#include <random>
#include <stdexcept>
#include <thread>

namespace ibm::hpc {

ThermalMonitor::ThermalMonitor(ThermalThresholds thresholds) : _thresholds(thresholds) {}

void ThermalMonitor::set_alert_callback(AlertCallback cb) { _callback = std::move(cb); }
void ThermalMonitor::add_sensor(const std::string& id)    { _sensors.push_back(id); }

double ThermalMonitor::_simulate_temperature(const std::string& sensor_id) const {
    // Hash sensor name to stable base temperature in [65, 95] C,
    // then add Gaussian noise to simulate real sensor drift.
    unsigned hash = 0;
    for (char c : sensor_id) hash = hash * 31u + static_cast<unsigned>(c);

    double base = 65.0 + static_cast<double>(hash % 30);

    auto tick = static_cast<unsigned>(
        std::chrono::steady_clock::now().time_since_epoch().count() & 0xFFFFFFFFu);
    std::mt19937 rng(hash ^ tick);
    std::normal_distribution<double> dist(base, 5.0);
    return dist(rng);
}

std::vector<SensorReading> ThermalMonitor::poll_once() {
    if (_sensors.empty())
        throw std::runtime_error("No sensors registered. Call add_sensor() first.");

    auto now = std::chrono::steady_clock::now();
    std::vector<SensorReading> readings;
    readings.reserve(_sensors.size());

    for (const auto& id : _sensors) {
        SensorReading r{id, _simulate_temperature(id), now};
        readings.push_back(r);
        AlertLevel level = classify(r.temperature_C);
        if (_callback && level != AlertLevel::OK)
            _callback(r, level);
    }
    return readings;
}

void ThermalMonitor::run(double duration_s, int interval_ms) {
    if (duration_s <= 0) throw std::invalid_argument("duration_s must be positive");
    if (interval_ms <= 0) throw std::invalid_argument("interval_ms must be positive");

    auto deadline = std::chrono::steady_clock::now()
                  + std::chrono::duration<double>(duration_s);
    while (std::chrono::steady_clock::now() < deadline) {
        poll_once();
        std::this_thread::sleep_for(std::chrono::milliseconds(interval_ms));
    }
}

AlertLevel ThermalMonitor::classify(double t) const noexcept {
    if (t >= _thresholds.critical_C) return AlertLevel::CRITICAL;
    if (t >= _thresholds.throttle_C) return AlertLevel::THROTTLE;
    if (t >= _thresholds.warning_C)  return AlertLevel::WARNING;
    return AlertLevel::OK;
}

std::string ThermalMonitor::level_to_string(AlertLevel level) noexcept {
    switch (level) {
        case AlertLevel::OK:       return "OK";
        case AlertLevel::WARNING:  return "WARNING";
        case AlertLevel::THROTTLE: return "THROTTLE";
        case AlertLevel::CRITICAL: return "CRITICAL";
        default:                   return "UNKNOWN";
    }
}

}  // namespace ibm::hpc
