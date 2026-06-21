import 'dart:io';

// Fix pc_server.dart — remove await from void calls
void main() {
  final path = 'lib/services/pc_server.dart';
  var content = File(path).readAsStringSync();
  
  // Remove await from void WindowsInput calls
  content = content.replaceAll('await WindowsInput.typeText(', 'WindowsInput.typeText(');
  content = content.replaceAll('await WindowsInput.keypress(', 'WindowsInput.keypress(');
  content = content.replaceAll('await WindowsInput.hotkey(', 'WindowsInput.hotkey(');
  content = content.replaceAll('await WindowsInput.click(', 'WindowsInput.click(');
  content = content.replaceAll('await WindowsInput.scroll(', 'WindowsInput.scroll(');
  content = content.replaceAll('await WindowsInput.moveRelative(', 'WindowsInput.moveRelative(');
  
  File(path).writeAsStringSync(content);
  print('Fixed! Removed await from void WindowsInput calls');
}
