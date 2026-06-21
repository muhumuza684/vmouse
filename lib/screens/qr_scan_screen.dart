import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'trackpad_screen.dart';

class QRScanScreen extends StatefulWidget {
  const QRScanScreen({super.key});

  @override
  State<QRScanScreen> createState() => _QRScanScreenState();
}

class _QRScanScreenState extends State<QRScanScreen> {
  final MobileScannerController _controller = MobileScannerController();
  final TextEditingController _ipController = TextEditingController();
  bool _scanned = false;
  String _error = '';

  @override
  void dispose() {
    _controller.dispose();
    _ipController.dispose();
    super.dispose();
  }

  void _onQRDetected(BarcodeCapture capture) {
    if (_scanned) return;
    final barcode = capture.barcodes.firstOrNull;
    if (barcode?.rawValue == null) return;
    final value = barcode!.rawValue!;
    // Extract IP from ws://IP:PORT
    final match = RegExp(r'ws[s]?://([^:]+)').firstMatch(value);
    final ip = match?.group(1) ?? value;
    setState(() => _scanned = true);
    _controller.stop();
    _connectToPC(ip);
  }

  void _connectManual() {
    final ip = _ipController.text.trim();
    if (ip.isEmpty) {
      setState(() => _error = 'Enter PC IP address');
      return;
    }
    _connectToPC(ip);
  }

  void _connectToPC(String ip) {
    Navigator.pushReplacement(context,
      MaterialPageRoute(builder: (_) => TrackpadScreen(ip: ip)));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(children: [
        // Camera
        MobileScanner(controller: _controller, onDetect: _onQRDetected),

        // Dark overlay with frame cutout
        ColorFiltered(
          colorFilter: const ColorFilter.mode(Colors.transparent, BlendMode.dstOut),
          child: Container(
            color: Colors.black.withOpacity(0.65),
            child: Center(
              child: Container(
                width: 260, height: 260,
                decoration: BoxDecoration(borderRadius: BorderRadius.circular(16), color: Colors.black),
              ),
            ),
          ),
        ),
        Container(color: Colors.black.withOpacity(0.65)),
        Center(
          child: Container(
            width: 260, height: 260,
            decoration: BoxDecoration(
              border: Border.all(color: const Color(0xFF6C5CE7), width: 2),
              borderRadius: BorderRadius.circular(16),
              color: Colors.transparent,
            ),
            child: Stack(children: [
              // Scan line animation
              _ScanLine(),
              // Corners
              ...[Alignment.topLeft, Alignment.topRight, Alignment.bottomLeft, Alignment.bottomRight]
                .map((a) => Align(alignment: a, child: _Corner(alignment: a))),
            ]),
          ),
        ),

        // Back button
        SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: IconButton(
              onPressed: () => Navigator.pop(context),
              icon: const Icon(Icons.arrow_back, color: Colors.white),
              style: IconButton.styleFrom(backgroundColor: Colors.black54),
            ),
          ),
        ),

        // Title
        const SafeArea(
          child: Padding(
            padding: EdgeInsets.only(top: 60),
            child: Center(child: Text('Scan QR Code',
              style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.w600))),
          ),
        ),

        // Hint + manual input at bottom
        Align(alignment: Alignment.bottomCenter,
          child: SafeArea(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(24, 0, 24, 24),
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                Text('Point camera at the QR on your PC screen',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: Colors.white.withOpacity(0.6), fontSize: 13)),
                const SizedBox(height: 20),
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.black.withOpacity(0.8),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: Colors.white.withOpacity(0.1)),
                  ),
                  child: Column(children: [
                    TextField(
                      controller: _ipController,
                      style: const TextStyle(color: Colors.white, fontFamily: 'monospace', fontSize: 16),
                      textAlign: TextAlign.center,
                      keyboardType: TextInputType.number,
                      decoration: InputDecoration(
                        hintText: 'Or type PC IP: 192.168.x.x',
                        hintStyle: TextStyle(color: Colors.white.withOpacity(0.3)),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(10),
                          borderSide: BorderSide(color: Colors.white.withOpacity(0.1)),
                        ),
                        enabledBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(10),
                          borderSide: BorderSide(color: Colors.white.withOpacity(0.1)),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(10),
                          borderSide: const BorderSide(color: Color(0xFF6C5CE7)),
                        ),
                        filled: true, fillColor: Colors.white.withOpacity(0.05),
                      ),
                    ),
                    const SizedBox(height: 10),
                    SizedBox(
                      width: double.infinity,
                      child: FilledButton(
                        onPressed: _connectManual,
                        style: FilledButton.styleFrom(
                          backgroundColor: const Color(0xFF6C5CE7),
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                        ),
                        child: const Text('Connect →', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
                      ),
                    ),
                    if (_error.isNotEmpty) ...[
                      const SizedBox(height: 8),
                      Text(_error, style: const TextStyle(color: Color(0xFFFF5C6A), fontSize: 12)),
                    ],
                  ]),
                ),
              ]),
            ),
          ),
        ),
      ]),
    );
  }
}

class _ScanLine extends StatefulWidget {
  @override
  State<_ScanLine> createState() => _ScanLineState();
}
class _ScanLineState extends State<_ScanLine> with SingleTickerProviderStateMixin {
  late AnimationController _ac;
  late Animation<double> _anim;
  @override
  void initState() {
    super.initState();
    _ac = AnimationController(duration: const Duration(seconds: 2), vsync: this)..repeat(reverse: true);
    _anim = Tween(begin: 0.05, end: 0.92).animate(CurvedAnimation(parent: _ac, curve: Curves.easeInOut));
  }
  @override
  void dispose() { _ac.dispose(); super.dispose(); }
  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(animation: _anim, builder: (_, __) => Positioned(
      top: 260 * _anim.value, left: 8, right: 8,
      child: Container(height: 2,
        decoration: BoxDecoration(
          gradient: const LinearGradient(colors: [Colors.transparent, Color(0xFF6C5CE7), Colors.transparent]),
          borderRadius: BorderRadius.circular(1),
        )),
    ));
  }
}

class _Corner extends StatelessWidget {
  final Alignment alignment;
  const _Corner({required this.alignment});
  @override
  Widget build(BuildContext context) {
    final isLeft = alignment == Alignment.topLeft || alignment == Alignment.bottomLeft;
    final isTop = alignment == Alignment.topLeft || alignment == Alignment.topRight;
    return Padding(
      padding: const EdgeInsets.all(0),
      child: Align(alignment: alignment,
        child: SizedBox(width: 24, height: 24,
          child: CustomPaint(painter: _CornerPainter(isLeft: isLeft, isTop: isTop)))),
    );
  }
}
class _CornerPainter extends CustomPainter {
  final bool isLeft, isTop;
  _CornerPainter({required this.isLeft, required this.isTop});
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()..color = const Color(0xFF6C5CE7)..strokeWidth = 3..style = PaintingStyle.stroke;
    final path = Path();
    if (isLeft && isTop) { path.moveTo(0, size.height); path.lineTo(0, 0); path.lineTo(size.width, 0); }
    else if (!isLeft && isTop) { path.moveTo(0, 0); path.lineTo(size.width, 0); path.lineTo(size.width, size.height); }
    else if (isLeft && !isTop) { path.moveTo(0, 0); path.lineTo(0, size.height); path.lineTo(size.width, size.height); }
    else { path.moveTo(0, size.height); path.lineTo(size.width, size.height); path.lineTo(size.width, 0); }
    canvas.drawPath(path, paint);
  }
  @override
  bool shouldRepaint(_) => false;
}
