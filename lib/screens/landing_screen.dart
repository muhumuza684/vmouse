import 'package:flutter/material.dart';
import 'trackpad_screen.dart';
import 'system_control_screen.dart';
import 'health_monitor_screen.dart';

/// Landing page shown right after a successful QR connection. All module
/// screens reuse the app-wide ConnectionService — nothing here needs to
/// pass a wsUrl around anymore.
class LandingScreen extends StatelessWidget {
  const LandingScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: const [
                  Icon(Icons.mouse, color: Color(0xFF6C5CE7), size: 26),
                  SizedBox(width: 10),
                  Text(
                    'VMouse',
                    style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 20),
                  ),
                ],
              ),
              const SizedBox(height: 4),
              const Text(
                'Connected — choose what to control',
                style: TextStyle(color: Color(0xFF8888aa), fontSize: 13),
              ),
              const SizedBox(height: 28),
              Expanded(
                child: GridView.count(
                  crossAxisCount: 2,
                  crossAxisSpacing: 14,
                  mainAxisSpacing: 14,
                  children: [
                    _ModuleButton(
                      icon: Icons.touch_app,
                      label: 'Mouse Control',
                      subtitle: 'Move · Click · Scroll · Drag',
                      onTap: () => Navigator.of(context).push(
                        MaterialPageRoute(
                          builder: (_) => const TrackpadScreen(initialTab: 0),
                        ),
                      ),
                    ),
                    _ModuleButton(
                      icon: Icons.keyboard,
                      label: 'Keyboard Control',
                      subtitle: 'Text input · Hotkeys',
                      onTap: () => Navigator.of(context).push(
                        MaterialPageRoute(
                          builder: (_) => const TrackpadScreen(initialTab: 1),
                        ),
                      ),
                    ),
                    _ModuleButton(
                      icon: Icons.power_settings_new,
                      label: 'System Controls',
                      subtitle: 'Shutdown · Restart · Lock',
                      onTap: () => Navigator.of(context).push(
                        MaterialPageRoute(
                          builder: (_) => const SystemControlScreen(),
                        ),
                      ),
                    ),
                    _ModuleButton(
                      icon: Icons.health_and_safety,
                      label: 'Health Monitor',
                      subtitle: 'PC + phone status',
                      onTap: () => Navigator.of(context).push(
                        MaterialPageRoute(
                          builder: (_) => const HealthMonitorScreen(),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ModuleButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final String subtitle;
  final VoidCallback onTap;

  const _ModuleButton({
    required this.icon,
    required this.label,
    required this.subtitle,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: const Color(0xFF111120),
      borderRadius: BorderRadius.circular(18),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(18),
        child: Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(18),
            border: Border.all(color: const Color(0xFF1E1E32)),
          ),
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: const Color(0xFF6C5CE7).withOpacity(0.15),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(icon, color: const Color(0xFF6C5CE7), size: 22),
              ),
              const SizedBox(height: 14),
              Text(
                label,
                style: const TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 4),
              Text(
                subtitle,
                style: const TextStyle(color: Color(0xFF8888aa), fontSize: 11),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
