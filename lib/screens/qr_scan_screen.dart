import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'trackpad_screen.dart';

class QRScanScreen extends StatefulWidget {
  const QRScanScreen({super.key});

  @override
  State<QRScanScreen> createState() => _QRScanScreenState();
}

class _QRScanScreenState extends State<QRScanScreen> {
  MobileScannerController? _controller;
  bool _scanned = false;
  bool _torchOn = false;

  @override
  void initState() {
    super.initState();
    _controller = MobileScannerController(
      detectionSpeed: DetectionSpeed.noDuplicates,
    );
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  void _onDetect(BarcodeCapture capture) {
    if (_scanned) return;
    final barcode = capture.barcodes.firstOrNull;
    if (barcode == null) return;
    final raw = barcode.rawValue ?? '';
    // Expect ws://192.168.x.x:8765
    if (!raw.startsWith('ws://') && !raw.startsWith('wss://')) return;

    setState(() => _scanned = true);
    _controller?.stop();

    Navigator.of(context).pushReplacement(
      MaterialPageRoute(
        builder: (_) => TrackpadScreen(wsUrl: raw),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: SafeArea(
        child: Column(
          children: [
            // Header
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
              child: Row(
                children: [
                  const SizedBox(
                    width: 36,
                    height: 36,
                    child: Icon(Icons.mouse, color: Color(0xFF6C5CE7), size: 28),
                  ),
                  const SizedBox(width: 10),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'VMouse',
                        style: TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.w700,
                          fontSize: 18,
                        ),
                      ),
                      Text(
                        'by Bryt Ma Tech',
                        style: TextStyle(
                          color: const Color(0xFF6C5CE7),
                          fontSize: 10,
                          letterSpacing: 0.5,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),

            // Instructions
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Connect to PC',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 22,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    'Run VMouse.exe on your PC then scan the QR code shown on screen.',
                    style: TextStyle(color: const Color(0xFF888899), fontSize: 13),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 24),

            // Scanner box
            Expanded(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 24),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(20),
                  child: Stack(
                    children: [
                      MobileScanner(
                        controller: _controller!,
                        onDetect: _onDetect,
                      ),
                      // Corner overlay
                      CustomPaint(
                        size: Size.infinite,
                        painter: _ScannerOverlayPainter(),
                      ),
                    ],
                  ),
                ),
              ),
            ),

            const SizedBox(height: 20),

            // Torch toggle
            GestureDetector(
              onTap: () {
                setState(() => _torchOn = !_torchOn);
                _controller?.toggleTorch();
              },
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                decoration: BoxDecoration(
                  color: const Color(0xFF111120),
                  borderRadius: BorderRadius.circular(30),
                  border: Border.all(color: const Color(0xFF1E1E32)),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      _torchOn ? Icons.flashlight_off : Icons.flashlight_on,
                      color: _torchOn ? const Color(0xFF6C5CE7) : Colors.white54,
                      size: 18,
                    ),
                    const SizedBox(width: 8),
                    Text(
                      _torchOn ? 'Torch On' : 'Torch Off',
                      style: TextStyle(color: Colors.white70, fontSize: 13),
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }
}

class _ScannerOverlayPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = const Color(0xFF6C5CE7)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3
      ..strokeCap = StrokeCap.round;

    const len = 30.0;
    const r = 12.0;
    final l = size.width * 0.1;
    final t = size.height * 0.15;
    final ri = size.width * 0.9;
    final bo = size.height * 0.85;

    // Top-left
    canvas.drawLine(Offset(l + r, t), Offset(l + r + len, t), paint);
    canvas.drawLine(Offset(l, t + r), Offset(l, t + r + len), paint);
    // Top-right
    canvas.drawLine(Offset(ri - r, t), Offset(ri - r - len, t), paint);
    canvas.drawLine(Offset(ri, t + r), Offset(ri, t + r + len), paint);
    // Bottom-left
    canvas.drawLine(Offset(l + r, bo), Offset(l + r + len, bo), paint);
    canvas.drawLine(Offset(l, bo - r), Offset(l, bo - r - len), paint);
    // Bottom-right
    canvas.drawLine(Offset(ri - r, bo), Offset(ri - r - len, bo), paint);
    canvas.drawLine(Offset(ri, bo - r), Offset(ri, bo - r - len), paint);
  }

  @override
  bool shouldRepaint(_) => false;
}
