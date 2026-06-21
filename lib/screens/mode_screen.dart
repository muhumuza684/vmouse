import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'trackpad_screen.dart';
import 'qr_scan_screen.dart';

class ModeScreen extends StatelessWidget {
  const ModeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 40),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // Logo
              Container(
                width: 80, height: 80,
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFF6C5CE7), Color(0xFF9B59B6)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(22),
                  boxShadow: [
                    BoxShadow(
                      color: const Color(0xFF6C5CE7).withOpacity(0.4),
                      blurRadius: 32, spreadRadius: 4,
                    ),
                  ],
                ),
                child: const Icon(Icons.mouse, color: Colors.white, size: 40),
              ),
              const SizedBox(height: 28),

              // Title
              Text('VMouse',
                style: GoogleFonts.dmSans(
                  fontSize: 36, fontWeight: FontWeight.w600,
                  color: Colors.white, letterSpacing: -1,
                )),
              const SizedBox(height: 8),
              Text('Control your PC from your phone',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 15, color: Colors.white.withOpacity(0.5),
                  height: 1.6,
                )),
              const SizedBox(height: 52),

              // Mode cards
              Row(children: [
                Expanded(child: _ModeCard(
                  icon: Icons.computer,
                  title: "I'm on PC",
                  desc: "Show QR code\nfor phone to scan",
                  color: const Color(0xFF00D68F),
                  onTap: () => _showPCDialog(context),
                )),
                const SizedBox(width: 12),
                Expanded(child: _ModeCard(
                  icon: Icons.phone_android,
                  title: "I'm on Phone",
                  desc: "Scan QR or\nenter PC IP",
                  color: const Color(0xFF6C5CE7),
                  onTap: () => Navigator.push(context,
                    MaterialPageRoute(builder: (_) => const QRScanScreen())),
                )),
              ]),
              const SizedBox(height: 40),

              // Version
              Text('VMouse v4.0 • Flutter Edition',
                style: TextStyle(
                  fontSize: 11, color: Colors.white.withOpacity(0.2),
                )),
            ],
          ),
        ),
      ),
    );
  }

  void _showPCDialog(BuildContext context) {
    showDialog(context: context, builder: (_) => AlertDialog(
      backgroundColor: const Color(0xFF111120),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      title: const Text('PC Setup', style: TextStyle(color: Colors.white)),
      content: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('On your PC:', style: TextStyle(color: Colors.white.withOpacity(0.7), fontWeight: FontWeight.w500)),
        const SizedBox(height: 12),
        _Step('1', 'Run VMouse.exe (or python pc_server.py)'),
        _Step('2', 'A QR code popup appears on screen'),
        _Step('3', 'Open VMouse on your phone'),
        _Step('4', 'Tap "I\'m on Phone" and scan the QR'),
      ]),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Got it', style: TextStyle(color: Color(0xFF6C5CE7))),
        ),
      ],
    ));
  }
}

class _Step extends StatelessWidget {
  final String num;
  final String text;
  const _Step(this.num, this.text);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(children: [
        Container(
          width: 22, height: 22,
          decoration: BoxDecoration(
            color: const Color(0xFF6C5CE7),
            borderRadius: BorderRadius.circular(11),
          ),
          child: Center(child: Text(num,
            style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold))),
        ),
        const SizedBox(width: 10),
        Expanded(child: Text(text,
          style: TextStyle(color: Colors.white.withOpacity(0.7), fontSize: 13))),
      ]),
    );
  }
}

class _ModeCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String desc;
  final Color color;
  final VoidCallback onTap;
  const _ModeCard({required this.icon, required this.title, required this.desc, required this.color, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: const Color(0xFF111120),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: color.withOpacity(0.3), width: 1.5),
        ),
        child: Column(children: [
          Icon(icon, color: color, size: 36),
          const SizedBox(height: 12),
          Text(title, style: const TextStyle(
            color: Colors.white, fontSize: 15, fontWeight: FontWeight.w600)),
          const SizedBox(height: 6),
          Text(desc, textAlign: TextAlign.center,
            style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 11, height: 1.5)),
        ]),
      ),
    );
  }
}
