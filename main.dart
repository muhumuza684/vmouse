import 'dart:io';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'screens/qr_scan_screen.dart';
import 'screens/pc_server_screen.dart';

void main() {
  runApp(const VMouseApp());
}

class VMouseApp extends StatelessWidget {
  const VMouseApp({super.key});

  @override
  Widget build(BuildContext context) {
    // Platform decides the role — no menu, no asking.
    // Windows build = the PC being controlled, opens straight to the QR/server screen.
    // Android (and anything else) build = the remote, opens straight to the scanner.
    final Widget startScreen =
        Platform.isWindows ? const PCServerScreen() : const QRScanScreen();

    return MaterialApp(
      title: 'VMouse',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF6C5CE7),
          brightness: Brightness.dark,
          surface: const Color(0xFF0A0A12),
          onSurface: const Color(0xFFF0F0F8),
        ),
        scaffoldBackgroundColor: const Color(0xFF000000),
        textTheme: GoogleFonts.dmSansTextTheme(
          ThemeData.dark().textTheme,
        ),
        cardTheme: CardTheme(
          color: const Color(0xFF111120),
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
            side: const BorderSide(color: Color(0xFF1E1E32)),
          ),
        ),
      ),
      home: startScreen,
    );
  }
}
