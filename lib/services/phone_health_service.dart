import 'package:battery_plus/battery_plus.dart';
import 'package:device_info_plus/device_info_plus.dart';

/// Reads what's reliably available cross-platform via battery_plus and
/// device_info_plus. Free/total RAM and disk space aren't exposed by any
/// well-maintained Flutter plugin without native platform-channel code,
/// so this reports battery + device info only. If you want storage/RAM
/// numbers too, that needs a small native (Kotlin) MethodChannel — happy
/// to add one if you want to go that route.
class PhoneHealthService {
  final Battery _battery = Battery();
  final DeviceInfoPlugin _deviceInfo = DeviceInfoPlugin();

  Future<Map<String, dynamic>> getPhoneHealth() async {
    try {
      final int batteryLevel = await _battery.batteryLevel;
      final BatteryState batteryState = await _battery.batteryState;
      final AndroidDeviceInfo androidInfo = await _deviceInfo.androidInfo;

      return {
        "device_type": "phone",
        "model": androidInfo.model,
        "manufacturer": androidInfo.manufacturer,
        "android_version": androidInfo.version.release,
        "api_level": androidInfo.version.sdkInt,
        "battery": {
          "percent": batteryLevel,
          "is_charging": batteryState == BatteryState.charging ||
              batteryState == BatteryState.full,
          "status": batteryState.toString().split('.').last,
        },
      };
    } catch (e) {
      return {"error": e.toString()};
    }
  }

  Map<String, dynamic> analyzePhoneHealth(Map<String, dynamic> health) {
    final List<String> issues = [];
    final List<String> advice = [];

    if (health.containsKey("error")) {
      return {
        "has_issues": true,
        "issues": ["Could not retrieve phone health"],
        "advice": ["Check app permissions"],
        "summary": "Error reading health data",
      };
    }

    final int battery = health["battery"]?["percent"] ?? 100;
    final bool charging = health["battery"]?["is_charging"] ?? false;

    if (battery < 15 && !charging) {
      issues.add("Battery critically low ($battery%)");
      advice.add("Plug in your charger.");
    } else if (battery < 30 && !charging) {
      issues.add("Battery below 30%");
      advice.add("Consider charging soon.");
    }

    return {
      "has_issues": issues.isNotEmpty,
      "issues": issues.isEmpty ? ["Your phone battery looks fine"] : issues,
      "advice": advice.isEmpty ? ["Nothing to do right now"] : advice,
      "summary": issues.isEmpty
          ? "Phone is healthy"
          : "${issues.length} issue${issues.length > 1 ? 's' : ''} found",
    };
  }
}
