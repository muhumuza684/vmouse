// Stub — compiled on Android/Linux. All methods are no-ops.
// The phone app never calls these; the conditional import in pc_server.dart
// ensures this file is used everywhere except Windows.
class WindowsInput {
  static Future<void> init() async {}
  static void moveRelative(int dx, int dy) {}
  static void click(String button, int clicks) {}
  static void scroll(int dy) {}
  static void hotkey(List<String> keys) {}
  static void typeText(String text) {}
  static void keypress(String key) {}
  static void dispose() {}
}
