#pragma once

#include <chrono>
#include <functional>
#include <string>
#include <vector>

namespace ibm::hpc {

struct SensorReading {
    std::string sensor_id;
    double temperature_C;
    std::chrono::steady_clock::time_point timestamp;
};

enum class AlertLevel {
    OK,
    WARNING,   // T >= warning_C
    THROTTLE,  // T >= throttle_C — P-state reduction applied
    CRITICAL,  // T >= critical_C — emergency shutdown initiated
};

struct ThermalThresholds {
    double warning_C  = 75.0;
    double throttle_C = 90.0;
    double critical_C = 105.0;
};

using AlertCallback = std::function<void(const SensorReading&, AlertLevel)>;

class ThermalMonitor {
public:
    explicit ThermalMonitor(ThermalThresholds thresholds = {});

    void set_alert_callback(AlertCallback cb);
    void add_sensor(const std::string& sensor_id);

    /// Poll all sensors once; fires callback for non-OK readings.
    std::vector<SensorReading> poll_once();

    /// Block for duration_s seconds, polling every interval_ms milliseconds.
    void run(double duration_s, int interval_ms = 500);

    AlertLevel classify(double temperature_C) const noexcept;
    static std::string level_to_string(AlertLevel level) noexcept;

private:
    double _simulate_temperature(const std::string& sensor_id) const;

    ThermalThresholds        _thresholds;
    AlertCallback            _callback;
    std::vector<std::string> _sensors;
};

}  // namespace ibm::hpc
