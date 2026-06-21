import 'dart:io';

void main() {
  final path = 'lib/screens/pc_server_screen.dart';
  var content = File(path).readAsStringSync();
  
  // Add WindowsInput import if not there
  if (!content.contains("import '../services/windows_input.dart'")) {
    content = content.replaceFirst(
      "import '../services/pc_server.dart';",
      "import '../services/pc_server.dart';\nimport '../services/windows_input.dart';"
    );
  }
  
  // Call WindowsInput.init() inside _start() before server starts
  content = content.replaceFirst(
    'Future<void> _start() async {\n    final ip = await _server.start();',
    'Future<void> _start() async {\n    await WindowsInput.init();\n    final ip = await _server.start();'
  );
  
  File(path).writeAsStringSync(content);
  print('Fixed! WindowsInput.init() added to _start()');
}
